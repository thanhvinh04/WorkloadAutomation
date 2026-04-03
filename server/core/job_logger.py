import json
import logging
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
import threading


class JobLogger:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance
    
    def _init(self):
        self._loggers = {}
    
    def get_logger(self, job_id: str, log_dir: Path) -> logging.Logger:
        if job_id in self._loggers:
            return self._loggers[job_id]
        
        logger = logging.getLogger(f"job_{job_id}")
        logger.setLevel(logging.DEBUG)
        logger.handlers = []
        
        log_file = log_dir / f"{job_id}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        self._loggers[job_id] = logger
        
        return logger
    
    def log(self, job_id: str, log_dir: Path, level: str, message: str):
        logger = self.get_logger(job_id, log_dir)
        getattr(logger, level.lower())(message)
    
    def clear_old_logs(self, jobs_dir: Path, keep_last: int = 5):
        if not jobs_dir.exists():
            return
        
        job_dirs = sorted(jobs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
        
        for job_dir in job_dirs[keep_last:]:
            if job_dir.is_dir():
                import shutil
                try:
                    shutil.rmtree(job_dir)
                except Exception:
                    pass


job_logger = JobLogger()
