from silero_vad import load_silero_vad, get_speech_timestamps, read_audio

def merge_speech_chunks(timestamps, max_gap=0.4):
    merged = [dict(timestamps[0])]
    for ts in timestamps[1:]:
        if ts["start"] - merged[-1]["end"] <= max_gap:
            merged[-1]["end"] = ts["end"]
        else:
            merged.append(dict(ts))
    return merged

def detect_speech(audio_path, max_gap=0.4):
    model = load_silero_vad()
    wav = read_audio(audio_path)
    timestamps = get_speech_timestamps(wav, model, return_seconds=True)
    return merge_speech_chunks(timestamps, max_gap)