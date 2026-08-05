# generate tts_rate, trim_silence

import time
import edge_tts             
import asyncio
import nest_asyncio
import librosa
import numpy as np
import soundfile as sf

from utils.logger import get_logger
logger = get_logger(__name__)

nest_asyncio.apply()

async def _generate(text, out_path, rate_percent, voice):
    rate_str = f"{rate_percent:+.0f}%"
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    await communicate.save(out_path)

def generate_tts_rate(text, out_path, rate_percent=0, voice="en-US-AndrewNeural", retries=3):
    for attempt in range(1, retries + 1):
        try:
            asyncio.run(_generate(text, out_path, rate_percent, voice))
            return out_path
        except edge_tts.exceptions.NoAudioReceived:
            if attempt == retries:
                raise
            logger.warning(f"Edge-tts NoAudioReceived, retrying ({attempt}/{retries})")
            time.sleep(1 * attempt)

def trim_silence(path, threshold=0.01):
    y, sr = librosa.load(path, sr=None)
    non_silent = np.where(np.abs(y) > threshold)[0]
    if len(non_silent) == 0:
        return path
    trimmed = y[non_silent[0]:non_silent[-1]]
    trimmed_path = path.rsplit(".", 1)[0] + "_trimmed.wav"
    sf.write(trimmed_path, trimmed, sr)
    return trimmed_path