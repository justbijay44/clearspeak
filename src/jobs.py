import sqlite3
import uuid
import contextlib

DB_PATH = "data/jobs.db"

def init_db():
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id              TEXT PRIMARY KEY,
                status          TEXT NOT NULL,
                output_path     TEXT,
                error           TEXT
            )
        """)
        conn.commit()

def create_job():
    job_id = str(uuid.uuid4())
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("INSERT INTO jobs (id, status) VALUES (?, ?)", (job_id, "pending"))
        conn.commit()
    return job_id

def update_job(job_id, status, output_path=None, error=None):
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "UPDATE jobs SET status = ?, output_path = ?, error = ? WHERE id = ?",
            (status, output_path, error, job_id)
        )
        conn.commit()

def get_job(job_id):
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None