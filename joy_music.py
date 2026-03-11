import math
import sys
import time
import hid

NEUTRAL = bytes([0x00, 0x01, 0x40, 0x40])
DEFAULT_AMP = 0.4
MAX_AMP = 0.5

NINTENDO_VID = 0x057E
JOYCON_PIDS = {
    0x2006,  # Joy-Con (L)
    0x2007,  # Joy-Con (R)
    0x2009,  # Pro Controller (reference)
}


def _text_fields(d):
    name = d.get("product_string") or ""
    maker = d.get("manufacturer_string") or ""
    serial = d.get("serial_number") or ""
    return (f"{name} {maker} {serial}").lower()


def _format_device(d):
    vid = d.get("vendor_id", 0)
    pid = d.get("product_id", 0)
    product = d.get("product_string") or "(unknown product)"
    maker = d.get("manufacturer_string") or "(unknown maker)"
    return f"VID:PID={vid:04X}:{pid:04X} / {product} / {maker}"

def find_joycons():
    devices = hid.enumerate()

    # Primary match: Nintendo VID + known Joy-Con/Pro PID
    for d in devices:
        if d.get("vendor_id") == NINTENDO_VID and d.get("product_id") in JOYCON_PIDS:
            return d["path"]

    # Fallback match: product/manufacturer text contains Joy-Con
    for d in devices:
        text = _text_fields(d)
        if "joy-con" in text or "joycon" in text:
            return d["path"]

    hints = []
    for d in devices:
        text = _text_fields(d)
        if any(k in text for k in ("nintendo", "controller", "gamepad", "wireless")):
            hints.append(_format_device(d))

    detail = "\n".join(hints[:8]) if hints else "(候補デバイスなし)"
    raise RuntimeError(
        "Joy-Con が見つかりません。\n"
        "確認: 1) Joy-Con をBluetooth接続 2) Pythonを管理者権限で実行 3) 他アプリがJoy-Conを専有していないこと\n"
        f"検出候補:\n{detail}"
    )

def fit_freq(freq):
    while freq < 41.0:
        freq *= 2.0
    while freq > 1252.0:
        freq /= 2.0
    return freq

def encode_amp(amp):
    amp = max(0.0, min(MAX_AMP, amp))
    if amp <= 0.0:
        return 0, 0x40
    x = math.log2(amp * 1000.0) * 32.0 - 0x60
    if amp < 0.117:
        encoded = int(round(x / (5.0 - amp * amp) - 1.0))
    elif amp < 0.23:
        encoded = int(round(x - 0x5C))
    else:
        encoded = int(round(x * 2.0 - 0xF6))
    encoded = max(1, min(encoded, 100))
    hf_amp = min(encoded * 2, 0x01FC)
    lf_amp = min(encoded // 2 + 0x40, 0x0072)
    return hf_amp, lf_amp

def encode_rumble(freq, amp=DEFAULT_AMP):
    freq = fit_freq(freq)
    encoded_freq = int(round(math.log2(freq / 10.0) * 32.0))
    hf_freq = (encoded_freq - 0x60) * 4
    lf_freq = encoded_freq - 0x40
    hf_amp, lf_amp = encode_amp(amp)
    b0 = hf_freq & 0xFF
    b1 = ((hf_freq >> 8) & 0xFF) | (hf_amp & 0xFF)
    b2 = (lf_freq & 0x7F) | (((lf_amp >> 8) & 0x01) << 7)
    b3 = lf_amp & 0xFF
    return bytes([b0, b1, b2, b3])

class JoyConRumbler:
    def __init__(self, path):
        self.dev = hid.device()
        self.dev.open_path(path)
        self.packet_num = 0

    def next_packet_num(self):
        n = self.packet_num & 0x0F
        self.packet_num = (self.packet_num + 1) & 0x0F
        return n

    def send_subcmd(self, subcmd, payload=b"", rumble_left=NEUTRAL, rumble_right=NEUTRAL):
        buf = bytearray(0x40)
        buf[0] = 0x01
        buf[1] = self.next_packet_num()
        buf[2:6] = rumble_left
        buf[6:10] = rumble_right
        buf[10] = subcmd
        buf[11:11 + len(payload)] = payload
        self.dev.write(bytes(buf))

    def enable_vibration(self):
        self.send_subcmd(0x48, b"\x01")
        time.sleep(0.05)

    def rumble(self, left_packet=NEUTRAL, right_packet=NEUTRAL):
        buf = bytearray(10)
        buf[0] = 0x10
        buf[1] = self.next_packet_num()
        buf[2:6] = left_packet
        buf[6:10] = right_packet
        self.dev.write(bytes(buf))

    def stop(self):
        self.rumble(NEUTRAL, NEUTRAL)

    def play_tone(self, hz, duration, amp=DEFAULT_AMP, both=True):
        packet = encode_rumble(hz, amp)
        left = packet
        right = packet if both else NEUTRAL
        end = time.perf_counter() + duration
        while time.perf_counter() < end:
            self.rumble(left, right)
            time.sleep(0.0)
        self.stop()

    def play_melody(self, notes, amp=DEFAULT_AMP, gap=0.02):
        for hz, dur in notes:
            if hz <= 0:
                self.stop()
                time.sleep(dur)
            else:
                self.play_tone(hz, dur, amp=amp, both=True)
                time.sleep(gap)

    def close(self):
        self.stop()
        self.dev.close()

melody = [
    (440.00, 0.25),
    (493.88, 0.25),
    (523.25, 0.25),
    (587.33, 0.25),
    (659.25, 0.40),
    (0, 0.10),
    (659.25, 0.20),
    (587.33, 0.20),
    (523.25, 0.20),
    (493.88, 0.20),
    (440.00, 0.40),
]

def main():
    try:
        path = find_joycons()
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    jc = JoyConRumbler(path)
    jc.enable_vibration()
    jc.play_melody(melody, amp=DEFAULT_AMP)
    jc.close()


if __name__ == "__main__":
    main()