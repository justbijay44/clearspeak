# whisper loading + transcription

import subprocess
import whisper

def extract_audio(video_path, audio_path):
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", video_path,
        "-ar", "16000", "-ac", "1",
        audio_path
    ], check=True)
    return audio_path

def transcribe(audio_path, model_size="base"):
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, verbose=None)
    return result["segments"]

