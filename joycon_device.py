import math
import time
import hid

NINTENDO_VENDOR_ID = 0x057E
JOYCON_L_PRODUCT_ID = 0x2006
JOYCON_R_PRODUCT_ID = 0x2007
PRO_CONTROLLER_PRODUCT_ID = 0x2009

NEUTRAL_RUMBLE = bytes([0x00, 0x01, 0x40, 0x40])


def list_supported_devices():
    devices = []
    for d in hid.enumerate():
        vendor_id = d.get("vendor_id")
        product_id = d.get("product_id")
        if vendor_id == NINTENDO_VENDOR_ID and product_id in {
            JOYCON_L_PRODUCT_ID,
            JOYCON_R_PRODUCT_ID,
            PRO_CONTROLLER_PRODUCT_ID,
        }:
            devices.append(d)
            continue
        product_name = (d.get("product_string") or "").lower()
        manufacturer = (d.get("manufacturer_string") or "").lower()
        if "joy-con" in product_name or ("nintendo" in manufacturer and "controller" in product_name):
            devices.append(d)
    return devices


def classify_device(info):
    pid = info.get("product_id")
    product_name = (info.get("product_string") or "").lower()

    if pid == JOYCON_L_PRODUCT_ID:
        return "L"
    if pid == JOYCON_R_PRODUCT_ID:
        return "R"
    if pid == PRO_CONTROLLER_PRODUCT_ID:
        return "P"
    if "joy-con (l)" in product_name:
        return "L"
    if "joy-con (r)" in product_name:
        return "R"
    if "pro controller" in product_name:
        return "P"
    if "joy-con" in product_name:
        return "U"
    return "U"


def find_joycon_pair():
    devices = list_supported_devices()
    left = None
    right = None

    for d in devices:
        side = classify_device(d)
        if side == "L" and left is None:
            left = d
        elif side == "R" and right is None:
            right = d

    if left is None or right is None:
        names = []
        for d in devices:
            product = d.get("product_string") or "Unknown"
            manufacturer = d.get("manufacturer_string") or "Unknown"
            names.append(f"{manufacturer} / {product}")
        detail = "\n".join(names) if names else "候補デバイスなし"
        raise RuntimeError(f"Joy-Con(L) と Joy-Con(R) の両方が見つかりません\n{detail}")

    return {"L": left, "R": right}


def fit_freq(freq):
    while freq < 41.0:
        freq *= 2.0
    while freq > 1252.0:
        freq /= 2.0
    return freq


def encode_amp(amp):
    amp = max(0.0, min(amp, 1.0))
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


def encode_rumble(freq, amp):
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


class JoyConDevice:
    def __init__(self, device_info, side):
        self.device_info = device_info
        self.side = side
        self.dev = hid.device()
        self.dev.open_path(device_info["path"])
        self.packet_number = 0

    def _next_packet_number(self):
        value = self.packet_number & 0x0F
        self.packet_number = (self.packet_number + 1) & 0x0F
        return value

    def close(self):
        try:
            self.stop()
        finally:
            self.dev.close()

    def send_subcommand(self, subcommand, payload=b"", left_rumble=NEUTRAL_RUMBLE, right_rumble=NEUTRAL_RUMBLE):
        buf = bytearray(0x40)
        buf[0] = 0x01
        buf[1] = self._next_packet_number()
        buf[2:6] = left_rumble
        buf[6:10] = right_rumble
        buf[10] = subcommand
        buf[11:11 + len(payload)] = payload
        self.dev.write(bytes(buf))

    def enable_vibration(self):
        self.send_subcommand(0x48, b"\x01")
        time.sleep(0.05)

    def make_packet(self, hz, amp):
        return encode_rumble(hz, amp)

    def rumble(self, packet):
        if self.side == "L":
            left = packet
            right = NEUTRAL_RUMBLE
        elif self.side == "R":
            left = NEUTRAL_RUMBLE
            right = packet
        else:
            left = packet
            right = packet

        buf = bytearray(10)
        buf[0] = 0x10
        buf[1] = self._next_packet_number()
        buf[2:6] = left
        buf[6:10] = right
        self.dev.write(bytes(buf))

    def stop(self):
        self.rumble(NEUTRAL_RUMBLE)