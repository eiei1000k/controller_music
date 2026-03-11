import argparse
from pathlib import Path

from joycon_device import JoyConDevice, find_joycon_pair
from music_engine import load_song, play_song


def build_devices():
    pair = find_joycon_pair()
    devices = {
        "L": JoyConDevice(pair["L"], "L"),
        "R": JoyConDevice(pair["R"], "R"),
    }
    for device in devices.values():
        device.enable_vibration()
    return devices


def close_devices(devices):
    for device in devices.values():
        try:
            device.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("song", nargs="?", default="songs/family_mart.json")
    args = parser.parse_args()

    song_path = Path(args.song)
    if not song_path.exists():
        raise FileNotFoundError(f"曲データが見つかりません: {song_path}")

    song = load_song(song_path)

    devices = build_devices()
    try:
        play_song(song, devices)
    finally:
        close_devices(devices)


if __name__ == "__main__":
    main()