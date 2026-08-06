# ClearSpeak

Upload a video, get back the same video with a clear English voiceover dubbed over it. Background audio/music is kept, only the detected speech gets replaced.

## How it works

1. Audio gets pulled out of the video with ffmpeg.
2. Silero VAD finds the speech regions so we're not wasting Whisper calls on music or silence.
3. Whisper (`medium` by default) transcribes each speech block, carrying a rolling prompt from block to block so names/terms introduced earlier in the video help transcription later on.
4. For each segment, edge-tts generates a voiceover clip. If it runs longer than the original segment, we try speeding it up (capped at 25%) to fit.
5. The original audio track gets muted exactly where the new clip lands (not just where the original segment was — covers both in case of drift) and the TTS clip is overlaid on top.
6. ffmpeg muxes the new audio back with the original video.

All of this is wrapped in a small FastAPI app so it can run as background jobs instead of blocking on a request.

## Setup

```
python -m venv venv
venv\Scripts\activate       # or source venv/bin/activate on mac/linux
pip install -r requirements.txt
```

You also need `ffmpeg` on your PATH.

## Running it

As a one-off script:

```
python -m src.pipeline
```

(edit the video path in `pipeline.py`'s `__main__` block, or call `run_pipeline()` directly)

As a server:

```
uvicorn src.api:app --reload
```

Then open `http://127.0.0.1:8000/` — there's a small frontend for uploading a video, watching job status, and comparing the original vs. dubbed result side by side once it's done.

### API

- `POST /jobs` — multipart upload (`file`, optional `domain_hint`). Returns `{job_id}`.
- `GET /jobs/{id}` — status: `pending` / `processing` / `complete` / `failed`.
- `GET /jobs/{id}/download` — the dubbed video, once complete.
- `GET /jobs/{id}/original` — the original upload, for comparison.

`domain_hint` is optional free text (names, topics) that gets passed to Whisper as an `initial_prompt` — helps with proper nouns Whisper otherwise tends to mishear.

## Project layout

```
src/
  transcribe.py   # ffmpeg extraction + whisper transcription
  vad.py          # silero VAD, merges speech timestamps into blocks
  tts.py          # edge-tts generation + silence trimming
  align.py        # per-segment TTS generation, timing, mute/overlay onto original track
  pipeline.py      # ties it all together
  api.py          # FastAPI app, job queue, endpoints
  jobs.py         # sqlite-backed job status tracking
utils/
  logger.py       # console + daily rotating file logger
static/           # frontend (plain html/css/js, no build step)
notebooks/
  jiwer.ipynb     # WER evaluation against manually transcribed reference clips
data/             # generated at runtime, gitignored (per-job audio/video, jobs.db)
logs/             # generated at runtime, gitignored
```

## Known limitations

- Accuracy depends a lot on Whisper model size. `base` mishears things like proper nouns fairly often (mixed up names, misheard "Hugging Face" as "erging face" during testing); `medium` is noticeably better but slower. WER on a couple of test clips lands around 5-12% with `medium`.
- Multiple people talking over each other or close together is going to be harder for Whisper to separate cleanly — haven't hit a specific failure from this yet, just something to watch for on videos with more than one speaker.
- No speaker diarization, so everyone gets the same TTS voice.
- Only dubs into English right now (translation from other source languages was tried and pulled back out — not needed for now).
- Timing fit is approximate: TTS clips get sped up to fit the original segment length, capped at 25%, so a segment that's much longer than the original speech will still run over a bit.

## Evaluating transcription quality

`notebooks/jiwer.ipynb` has the WER setup — extracts audio, transcribes, compares against a manually written reference transcript with `jiwer`, and includes a normalization pass (case, punctuation, some casual-word substitutions) so formatting differences don't inflate the error rate. Useful for A/B-ing model size or prompt changes before committing to them.
