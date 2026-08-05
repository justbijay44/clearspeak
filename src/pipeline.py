import os
from src.transcribe import extract_audio, transcribe
from src.align import stitch_segments
import subprocess

def run_pipeline(video_path, work_dir = "data", voice="en-US-AndrewNeural", model_size="base"):
    audio_path = f"{work_dir}/audio/audio.wav"
    output_path = f"{work_dir}/video/output.mp4"

    os.makedirs(f"{work_dir}/audio", exist_ok=True)
    os.makedirs(f"{work_dir}/video", exist_ok=True)

    extract_audio(video_path, audio_path)
    segments = transcribe(audio_path, model_size=model_size)

    timeline = stitch_segments(segments, segments[-1]["end"], audio_dir=f"{work_dir}/audio", voice=voice)
    new_audio_path = f"{work_dir}/audio/new_audio.wav"
    timeline.export(new_audio_path, format="wav")

    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", video_path,
        "-i", new_audio_path,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ], check=True)

    return output_path

if __name__ == "__main__":

    output = run_pipeline("data/video/input.mp4")
    print(f"done: {output}")