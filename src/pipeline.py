import os
from src.transcribe import extract_audio, transcribe
from src.vad import detect_speech
from src.align import stitch_segments
import subprocess

from utils.logger import get_logger
logger = get_logger(__name__)

def run_pipeline(video_path, work_dir = "data", voice="en-US-AndrewNeural", model_size="medium", domain_hint=None):
    audio_path = f"{work_dir}/audio/audio.wav"
    output_path = f"{work_dir}/video/output.mp4"

    os.makedirs(f"{work_dir}/audio", exist_ok=True)
    os.makedirs(f"{work_dir}/video", exist_ok=True)

    logger.info(f"Extracting audio from {video_path}")
    extract_audio(video_path, audio_path)

    logger.info(f"Running VAD")
    blocks = detect_speech(audio_path)
    logger.info(f"VAD found {len(blocks)} speech blocks")

    logger.info(f"Transcribing with model_size {model_size}")
    segments = transcribe(audio_path, blocks, model_size=model_size, work_dir=work_dir, initial_prompt=domain_hint)
    logger.info(f"Transcribed {len(segments)} segments")

    logger.info("Stitching TTS audio")
    timeline = stitch_segments(segments, audio_path, audio_dir=f"{work_dir}/audio", voice=voice)
    new_audio_path = f"{work_dir}/audio/new_audio.wav"
    timeline.export(new_audio_path, format="wav")

    logger.info("Creating final video")
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

    logger.info(f"Pipeline complete: {output_path}")
    return output_path

if __name__ == "__main__":
    output = run_pipeline("data/video/vid2.mp4")