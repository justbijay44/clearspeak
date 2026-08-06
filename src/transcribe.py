# whisper loading + transcription

import os
import subprocess
import whisper
from pydub import AudioSegment

from utils.logger import get_logger
logger = get_logger(__name__)

def extract_audio(video_path, audio_path):
    logger.info(f"Extracting audio: {video_path} -> {audio_path}")
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", video_path,
        "-ar", "16000", "-ac", "1",
        audio_path
    ], check=True)
    return audio_path

def transcribe(audio_path, blocks, model_size, work_dir="data", initial_prompt=None):
    logger.info(f"Loading whisper model: {model_size}")
    model = whisper.load_model(model_size)
    full_audio = AudioSegment.from_file(audio_path)

    chunk_path = f"{work_dir}/audio/temp_block.wav"

    all_segments = []
    prompt = initial_prompt
    for idx, block in enumerate(blocks):
        logger.info(f"Transcribing block {idx+1} / {len(blocks)} ({block['start']:.1f}s - {block['end']:.1f}s)")
        start_ms = int(block["start"] * 1000)
        end_ms = int(block["end"] * 1000)
        chunk = full_audio[start_ms:end_ms]

        chunk.export(chunk_path, format="wav")

        result = model.transcribe(
            chunk_path, 
            verbose=None, 
            initial_prompt=prompt,
            condition_on_previous_text=False,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6
        )

        block_text = " ".join(seg["text"].strip() for seg in result["segments"])
        if block_text:
            prompt = block_text[-200:]

        for seg in result["segments"]:
            seg["start"] += block["start"]
            seg["end"] += block["start"]
            all_segments.append(seg)

    if os.path.exists(chunk_path):
        os.remove(chunk_path)

    logger.info(f"Transcription Done: {len(all_segments)} segments from {len(blocks)} blocks")
    return all_segments
