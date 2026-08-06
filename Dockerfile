FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV WHISPER_MODEL_SIZE=small
RUN python -c "import whisper; whisper.load_model('small')"
RUN python -c "from silero_vad import load_silero_vad; load_silero_vad()"

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000}"]