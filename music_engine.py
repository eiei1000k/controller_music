import json
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
    if note == "REST" or note == "R":
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


def parse_sequence(sequence):
    if not isinstance(sequence, str):
        raise ValueError("sequence は文字列である必要があります")

    tokens = sequence.split()
    notes = []

    for token in tokens:
        if ":" not in token:
            raise ValueError(f"無効なトークンです: {token}")

        note_part, length_part = token.split(":", 1)
        note = note_part.strip()
        length = float(length_part.strip())

        if not note:
            raise ValueError(f"音名が空です: {token}")
        if length <= 0:
            raise ValueError(f"長さは正の値である必要があります: {token}")

        notes.append({
            "note": note,
            "length": length,
        })

    return notes


def get_track_notes(track):
    has_notes = "notes" in track
    has_sequence = "sequence" in track

    if has_notes and has_sequence:
        raise ValueError(f"track は notes と sequence を同時に持てません: {track.get('name', track)}")
    if not has_notes and not has_sequence:
        raise ValueError(f"track に notes または sequence が必要です: {track.get('name', track)}")

    if has_notes:
        if not isinstance(track["notes"], list) or not track["notes"]:
            raise ValueError(f"track.notes が不正です: {track.get('name', track)}")
        return track["notes"]

    parsed = parse_sequence(track["sequence"])
    if not parsed:
        raise ValueError(f"track.sequence が空です: {track.get('name', track)}")
    return parsed


def build_timeline(song):
    validate_song(song)

    bpm = float(song["bpm"])
    division = int(song.get("division", 4))
    default_amp = float(song.get("default_amp", 0.18))

    timelines = {}
    total_duration = 0.0

    for track in song["tracks"]:
        if "device" not in track:
            raise ValueError(f"track に device がありません: {track}")

        device = track["device"]
        current_time = 0.0
        track_amp = float(track.get("amp", default_amp))
        events = []
        notes = get_track_notes(track)

        for index, item in enumerate(notes):
            if "note" not in item or "length" not in item:
                raise ValueError(f"各ノートには note と length が必要です: {item}")

            note = item["note"]
            length = float(item["length"])
            amp = float(item.get("amp", track_amp))
            hz = note_to_hz(note)
            duration = length_to_seconds(length, bpm, division)

            events.append({
                "index": index,
                "start": current_time,
                "end": current_time + duration,
                "hz": hz,
                "amp": amp,
            })
            current_time += duration

        timelines[device] = events
        total_duration = max(total_duration, current_time)

    return timelines, total_duration


def get_event_at(events, now):
    for event in events:
        if event["start"] <= now < event["end"]:
            return event
    return None


def play_song(song, devices, tick=0.005, retrigger_gap=0.002):
    timelines, total_duration = build_timeline(song)
    device_names = list(devices.keys())
    last_state = {name: None for name in device_names}

    start_time = time.perf_counter()
    next_tick = start_time

    while True:
        now = time.perf_counter() - start_time
        if now >= total_duration:
            break

        for name in device_names:
            device = devices[name]
            events = timelines.get(name, [])
            event = get_event_at(events, now)

            if event is None or event["hz"] is None:
                state = None
            else:
                state = (event["index"], round(event["hz"], 4), round(event["amp"], 4))

            if state != last_state[name]:
                if state is None:
                    device.stop()
                else:
                    prev_state = last_state[name]
                    if prev_state is not None and prev_state[1] == state[1]:
                        device.stop()
                        if retrigger_gap > 0:
                            time.sleep(retrigger_gap)
                    packet = device.make_packet(event["hz"], event["amp"])
                    device.rumble(packet)
                last_state[name] = state
            elif state is not None:
                packet = device.make_packet(event["hz"], event["amp"])
                device.rumble(packet)

        next_tick += tick
        sleep_time = next_tick - time.perf_counter()
        if sleep_time > 0:
            time.sleep(sleep_time)

    for device in devices.values():
        device.stop()