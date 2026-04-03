import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import json

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()

class JobDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init()

    def _conn(self):
        return sqlite3.connect(str(self.db_path), check_same_thread=False)

    def _init(self):
        with self._conn() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY,
              status TEXT NOT NULL,
              progress REAL NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              owner TEXT NOT NULL,
              input_dir TEXT NOT NULL,
              log_path TEXT NOT NULL,
              result_json TEXT,
              error TEXT
            )
            """)
            c.commit()

    def create(self, job_id: str, owner: str, input_dir: str, log_path: str):
        with self._conn() as c:
            c.execute(
                "INSERT INTO jobs(job_id,status,progress,created_at,updated_at,owner,input_dir,log_path,result_json,error) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (job_id, "queued", 0.0, now_iso(), now_iso(), owner, input_dir, log_path, None, None)
            )
            c.commit()

    def get(self, job_id: str) -> Dict[str, Any]:
        with self._conn() as c:
            cur = c.execute("SELECT job_id,status,progress,created_at,updated_at,owner,input_dir,log_path,result_json,error FROM jobs WHERE job_id=?",
                            (job_id,))
            row = cur.fetchone()
        if not row:
            raise KeyError(job_id)

        result = {
            "job_id": row[0],
            "status": row[1],
            "progress": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "owner": row[5],
            "input_dir": row[6],
            "log_path": row[7],
            "result": json.loads(row[8]) if row[8] else None,
            "error": row[9],
        }
        return result

    def update(self, job_id: str, **kwargs):
        fields = []
        vals = []
        for k, v in kwargs.items():
            if k == "result":
                k = "result_json"
                v = json.dumps(v, ensure_ascii=False)
            fields.append(f"{k}=?")
            vals.append(v)
        fields.append("updated_at=?")
        vals.append(now_iso())
        vals.append(job_id)

        with self._conn() as c:
            c.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE job_id=?", tuple(vals))
            c.commit()