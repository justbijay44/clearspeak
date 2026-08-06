import uuid
import threading

_jobs = {}
_lock = threading.Lock()

def init_db():
    pass

def create_job():
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {"id": job_id, "status": "pending", "output_path": None, "error": None}
    return job_id

def update_job(job_id, status, output_path=None, error=None):
    with _lock:
        if job_id in _jobs:
            _jobs[job_id].update(status=status, output_path=output_path, error=error)

def get_job(job_id):
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None