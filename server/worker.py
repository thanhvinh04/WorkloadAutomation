import queue
import threading
from pathlib import Path

from jobs_db import JobDB
from runner import run_pipeline

class JobWorker:
    def __init__(self, db: JobDB):
        self.db = db
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._loop, daemon=True)
        self.t.start()

    def enqueue(self, job_id: str):
        self.q.put(job_id)

    def _loop(self):
        while True:
            job_id = self.q.get()
            try:
                job = self.db.get(job_id)
                input_dir = Path(job["input_dir"])
                log_file = Path(job["log_path"])

                self.db.update(job_id, status="running", progress=0.1, error=None)

                exit_code = run_pipeline(input_dir=input_dir, log_file=log_file)
                if exit_code == 0:
                    self.db.update(job_id, status="succeeded", progress=1.0, result={"message": "Done"}, error=None)
                else:
                    self.db.update(job_id, status="failed", progress=1.0, error=f"Pipeline exit code: {exit_code}")

            except Exception as e:
                self.db.update(job_id, status="failed", progress=1.0, error=str(e))
            finally:
                self.q.task_done()