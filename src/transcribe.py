# whisper loading + transcription

import os
import subprocess
import whisper
from pydub import AudioSegment

def extract_audio(video_path, audio_path):
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", video_path,
        "-ar", "16000", "-ac", "1",
        audio_path
    ], check=True)
    return audio_path

def transcribe(audio_path, blocks, model_size="base", work_dir="data"):
    model = whisper.load_model(model_size)
    full_audio = AudioSegment.from_file(audio_path)

    chunk_path = f"{work_dir}/audio/temp_block.wav"

    all_segments = []
    for block in blocks:
        start_ms = int(block["start"] * 1000)
        end_ms = int(block["end"] * 1000)
        chunk = full_audio[start_ms:end_ms]

        chunk.export(chunk_path, format="wav")

        result = model.transcribe(chunk_path, verbose=None)

        for seg in result["segments"]:
            seg["start"] += block["start"]
            seg["end"] += block["start"]
            all_segments.append(seg)

    if os.path.exists(chunk_path):
        os.remove(chunk_path)
        
    return all_segments
