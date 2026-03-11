import json
import threading
import time

NOTE_INDEX = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
}


def load_song(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_song(song):
    if "bpm" not in song:
        raise ValueError("song に bpm がありません")
    if "tracks" not in song or not isinstance(song["tracks"], list) or not song["tracks"]:
        raise ValueError("song に tracks がありません")
    if "assignment" not in song or "pair_1" not in song["assignment"]:
        raise ValueError("song に assignment.pair_1 がありません")


def normalize_note_name(note):
    return note.strip().upper()


def note_to_midi(note):
    note = normalize_note_name(note)
    if note == "REST":
        return None

    if len(note) < 2:
        raise ValueError(f"無効な音名です: {note}")

    if len(note) >= 3 and note[1] in {"#", "B"} and note[2:].lstrip("-").isdigit():
        name = note[:2]
        octave = int(note[2:])
    else:
        name = note[:1]
        octave = int(note[1:])

    if name not in NOTE_INDEX:
        raise ValueError(f"未対応の音名です: {note}")

    return (octave + 1) * 12 + NOTE_INDEX[name]


def midi_to_hz(midi_note):
    return 440.0 * (2 ** ((midi_note - 69) / 12))


def note_to_hz(note):
    midi_note = note_to_midi(note)
    if midi_note is None:
        return None
    return midi_to_hz(midi_note)


def length_to_seconds(length, bpm, division=4):
    beat_seconds = 60.0 / bpm
    base = 4.0 / division
    return beat_seconds * length * base


def expand_track(track, bpm, division, default_amp):
    expanded = []
    track_amp = track.get("amp", default_amp)

    for item in track["notes"]:
        note = item["note"]
        length = float(item["length"])
        amp = float(item.get("amp", track_amp))
        hz = note_to_hz(note)
        duration = length_to_seconds(length, bpm, division)
        expanded.append({
            "hz": hz,
            "duration": duration,
            "amp": amp,
        })
    return expanded


def build_playback_plan(song):
    validate_song(song)
    bpm = float(song["bpm"])
    division = int(song.get("division", 4))
    default_amp = float(song.get("default_amp", 0.18))

    plan = []
    for track in song["tracks"]:
        if "device" not in track:
            raise ValueError(f"track に device がありません: {track}")
        if "notes" not in track:
            raise ValueError(f"track に notes がありません: {track}")
        plan.append({
            "name": track.get("name", track["device"]),
            "device": track["device"],
            "events": expand_track(track, bpm, division, default_amp),
        })
    return plan


def play_track(device, events):
    for event in events:
        hz = event["hz"]
        duration = event["duration"]
        amp = event["amp"]

        if hz is None:
            device.stop()
            time.sleep(duration)
        else:
            device.play_tone(hz, duration, amp=amp)


def play_song(song, devices):
    plan = build_playback_plan(song)
    threads = []

    for track in plan:
        device_name = track["device"]
        if device_name not in devices:
            raise RuntimeError(f"必要なデバイスがありません: {device_name}")
        t = threading.Thread(target=play_track, args=(devices[device_name], track["events"]))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()