import os
import shutil

from fastapi import FastAPI, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from src.jobs import init_db, create_job, update_job, get_job
from src.pipeline import run_pipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data", exist_ok=True)
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/jobs")
async def submit_video(file: UploadFile, background_tasks: BackgroundTasks):
    job_id = create_job()
    work_dir = f"data/jobs/{job_id}"
    os.makedirs(f"{work_dir}/video", exist_ok=True)

    video_path = f"{work_dir}/video/input.mp4"
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    background_tasks.add_task(process_job, job_id, video_path, work_dir)
    return {"job_id": job_id}

def process_job(job_id, video_path, work_dir):
    update_job(job_id, "processing")
    try:
        output_path = run_pipeline(video_path, work_dir)
        update_job(job_id, "complete", output_path=output_path)
    except Exception as e:
        update_job(job_id, "failed", error=str(e))

@app.get("/jobs/{job_id}")
async def get_video_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job

@app.get("/jobs/{job_id}/download")
async def download_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job["status"] != "complete":
        raise HTTPException(status_code=409, detail=f"job is {job['status']}, not complete")
    return FileResponse(job["output_path"], media_type="video/mp4", filename="output.mp4")