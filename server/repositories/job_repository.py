import sqlite3
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone
import json
import os

from config import DB_TYPE, get_db_connection_string


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()


class JobRepository:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path
        self._init()

    def _get_sqlserver_conn(self):
        import pyodbc
        conn_str = get_db_connection_string()
        return pyodbc.connect(conn_str)

    def _get_sqlite_conn(self):
        path = self.db_path or get_db_connection_string()
        return sqlite3.connect(str(path), str(path))

    def _conn(self):
        if DB_TYPE == "sqlserver":
            return self._get_sqlserver_conn()
        return self._get_sqlite_conn()

    def _init(self):
        if DB_TYPE == "sqlserver":
            conn = self._get_sqlserver_conn()
            cursor = conn.cursor()
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='jobs' AND xtype='U')
            CREATE TABLE jobs (
                job_id NVARCHAR(100) PRIMARY KEY,
                task_code NVARCHAR(50) DEFAULT '',
                status NVARCHAR(50) NOT NULL,
                progress FLOAT NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT DATEADD(HOUR, 7, GETUTCDATE()),
                updated_at DATETIME NOT NULL DEFAULT DATEADD(HOUR, 7, GETUTCDATE()),
                owner NVARCHAR(100) NOT NULL,
                input_dir NVARCHAR(500) NOT NULL,
                log_path NVARCHAR(500) NOT NULL,
                result_json NVARCHAR(MAX),
                error NVARCHAR(MAX)
            )
            """)
            conn.commit()
            conn.close()
        else:
            conn = self._get_sqlite_conn()[0]
            conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY,
              task_code TEXT NOT NULL DEFAULT '',
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
            conn.commit()
            conn.close()

    def create(self, job_id: str, owner: str, input_dir: str, log_path: str):
        if DB_TYPE == "sqlserver":
            conn = self._get_sqlserver_conn()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO jobs (job_id, task_code, status, progress, created_at, updated_at, owner, input_dir, log_path, result_json, error)
            VALUES (?, '', 'queued', 0, DATEADD(HOUR, 7, GETUTCDATE()), DATEADD(HOUR, 7, GETUTCDATE()), ?, ?, ?, NULL, NULL)
            """, (job_id, owner, input_dir, log_path))
            conn.commit()
            conn.close()
        else:
            now = now_iso()
            conn = self._get_sqlite_conn()[0]
            conn.execute(
                "INSERT INTO jobs(job_id,task_code,status,progress,created_at,updated_at,owner,input_dir,log_path,result_json,error) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (job_id, "", "queued", 0.0, now, now, owner, input_dir, log_path, None, None)
            )
            conn.commit()
            conn.close()

    def get(self, job_id: str) -> Dict[str, Any]:
        if DB_TYPE == "sqlserver":
            conn = self._get_sqlserver_conn()
            cursor = conn.cursor()
            cursor.execute("""
            SELECT job_id, task_code, status, progress, created_at, updated_at, owner, input_dir, log_path, result_json, error
            FROM jobs WHERE job_id=?
            """, (job_id,))
            row = cursor.fetchone()
            conn.close()
        else:
            conn = self._get_sqlite_conn()[0]
            cursor = conn.execute(
                "SELECT job_id,task_code,status,progress,created_at,updated_at,owner,input_dir,log_path,result_json,error FROM jobs WHERE job_id=?",
                (job_id,)
            )
            row = cursor.fetchone()
            conn.close()
        
        if not row:
            raise KeyError(job_id)

        return {
            "job_id": row[0],
            "task_code": row[1] or "",
            "status": row[2],
            "progress": float(row[3]) if row[3] else 0.0,
            "created_at": str(row[4]) if row[4] else "",
            "updated_at": str(row[5]) if row[5] else "",
            "owner": row[6],
            "input_dir": row[7],
            "log_path": row[8],
            "result": json.loads(row[9]) if row[9] else None,
            "error": row[10],
        }

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
        if DB_TYPE == "sqlserver":
            vals.append("DATEADD(HOUR, 7, GETUTCDATE())")
        else:
            vals.append(now_iso())
        vals.append(job_id)

        if DB_TYPE == "sqlserver":
            conn = self._get_sqlserver_conn()
            cursor = conn.cursor()
            set_clause = ", ".join(fields)
            if "updated_at=?" in set_clause:
                set_clause = set_clause.replace("updated_at=?", "updated_at=DATEADD(HOUR, 7, GETUTCDATE())")
            cursor.execute(f"UPDATE jobs SET {set_clause} WHERE job_id=?", tuple(vals))
            conn.commit()
            conn.close()
        else:
            conn = self._get_sqlite_conn()[0]
            conn.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE job_id=?", tuple(vals))
            conn.commit()
            conn.close()