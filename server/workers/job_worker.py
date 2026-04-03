import queue
import threading
from pathlib import Path

from repositories.job_repository import JobRepository
from services.pipeline_service import PipelineService


class JobWorker:
    def __init__(self, repository: JobRepository):
        self.repository = repository
        self.pipeline_service = PipelineService()
        self.job_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.worker_thread.start()

    def enqueue(self, job_id: str, task_code: str = ""):
        self.job_queue.put((job_id, task_code))

    def _run_loop(self):
        while True:
            item = self.job_queue.get()
            try:
                job_id, task_code = item
                self._process_job(job_id, task_code)
            except Exception as e:
                job_id = item[0] if isinstance(item, tuple) else item
                self.repository.update(job_id, status="failed", progress=1.0, error=str(e))
            finally:
                self.job_queue.task_done()

    def _process_job(self, job_id: str, task_code: str):
        job = self.repository.get(job_id)
        input_dir = Path(job["input_dir"])
        log_file = Path(job["log_path"])

        self.repository.update(job_id, status="running", progress=0.1, error=None)

        if task_code == "PHOTO8":
            exit_code = self.pipeline_service.execute(input_dir=input_dir, log_file=log_file)
        else:
            exit_code = 0

        if exit_code == 0:
            self.repository.update(job_id, status="succeeded", progress=1.0, result={"message": "Done"}, error=None)
        else:
            self.repository.update(job_id, status="failed", progress=1.0, error=f"Pipeline exit code: {exit_code}")