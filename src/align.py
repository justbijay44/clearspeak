# process segment and stitching/cursor logic

import os
from pydub import AudioSegment
import librosa
from src.tts import generate_tts_rate, trim_silence

from utils.logger import get_logger
logger = get_logger(__name__)

def process_segment(seg, idx, voice="en-US-AndrewNeural", audio_dir="data/audio"):
    text = seg["text"]
    original_dur = seg["end"] - seg["start"]

    raw_path = f"{audio_dir}/tts_{idx}_raw.mp3"
    generate_tts_rate(text, raw_path, 0, voice)
    raw_trimmed = trim_silence(raw_path)
    raw_trimmed_dur = librosa.get_duration(path=raw_trimmed)

    gap = raw_trimmed_dur - original_dur

    if gap > 0:
        needed_rate = (raw_trimmed_dur / original_dur - 1) * 100
        applied_rate = min(25, needed_rate)
        adjusted_path = f"{audio_dir}/tts_{idx}_final.mp3"
        generate_tts_rate(text, adjusted_path, applied_rate, voice)
        final_path = trim_silence(adjusted_path)
    else:
        final_path = raw_trimmed

    for path in {raw_path, raw_trimmed, adjusted_path if gap > 0 else None}:
        if path and path != final_path and os.path.exists(path):
            os.remove(path)
    return final_path, gap

def stitch_segments(segments, original_audio_path, audio_dir="data/audio", voice="en-US-AndrewNeural"):
    timeline = AudioSegment.from_file(original_audio_path)
    cursor = 0.0

    for idx, seg in enumerate(segments):
        if not seg["text"].strip():
            logger.info(f"Segment {idx} has no text, skipping")
            continue

        path, gap = process_segment(seg, idx, voice=voice, audio_dir=audio_dir)
        clip = AudioSegment.from_file(path)
        clip_dur = len(clip) / 1000.0

        os.remove(path)

        placement = max(seg["start"], cursor)
        start_ms = int(placement * 1000)
        logger.info(f"Segment {idx}: placed at {placement:.2f}s, clip_dur={clip_dur:.2f}s")

        seg_start_ms = int(seg["start"] * 1000)
        seg_end_ms = int(seg["end"] * 1000)
        clip_end_ms = start_ms + int(clip_dur * 1000)

        mute_start_ms = min(seg_start_ms, start_ms)
        mute_end_ms = max(seg_end_ms, clip_end_ms)
        silence = AudioSegment.silent(duration=mute_end_ms-mute_start_ms)
        timeline = timeline[:mute_start_ms] + silence + timeline[mute_end_ms:]

        timeline = timeline.overlay(clip, position=start_ms)
        cursor = placement + clip_dur

    return timeline