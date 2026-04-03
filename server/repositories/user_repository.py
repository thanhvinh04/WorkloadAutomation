import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import json
import os

from config import DB_TYPE, get_db_connection_string


def now_datetime():
    return "DATEADD(HOUR, 7, GETUTCDATE())"


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()


class UserRepository:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path
        self._init()

    def _get_sqlserver_conn(self):
        import pyodbc
        conn_str = get_db_connection_string()
        return pyodbc.connect(conn_str)

    def _get_sqlite_conn(self):
        db_path = self.db_path or get_db_connection_string()
        return sqlite3.connect(str(db_path), check_same_thread=False)

    def _init(self):
        if DB_TYPE == "sqlserver":
            conn = self._get_sqlserver_conn()
            cursor = conn.cursor()
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
            CREATE TABLE users (
                username NVARCHAR(100) PRIMARY KEY,
                password_hash NVARCHAR(255) NOT NULL,
                customer NVARCHAR(50) NOT NULL,
                allowed_tasks_json NVARCHAR(500) NOT NULL,
                is_active INT DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT GETDATE(),
                updated_at DATETIME NOT NULL DEFAULT GETDATE()
            )
            """)
            conn.commit()
            conn.close()
        else:
            conn = self._get_sqlite_conn()
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
              username TEXT PRIMARY KEY,
              password_hash TEXT NOT NULL,
              customer TEXT NOT NULL,
              allowed_tasks_json TEXT NOT NULL,
              is_active INTEGER DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """)
            conn.commit()
            conn.close()

    def create_user(self, username: str, password_hash: str, customer: str, allowed_tasks: List[str]):
        tasks_json = json.dumps(allowed_tasks)
        
        if DB_TYPE == "sqlserver":
            conn = self._get_sqlserver_conn()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO users (username, password_hash, customer, allowed_tasks_json, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, DATEADD(HOUR, 7, GETUTCDATE()), DATEADD(HOUR, 7, GETUTCDATE()))
            """, (username, password_hash, customer, tasks_json))
            conn.commit()
            conn.close()
        else:
            now = now_iso()
            conn = self._get_sqlite_conn()
            conn.execute(
                """INSERT INTO users(username,password_hash,customer,allowed_tasks_json,is_active,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (username, password_hash, customer, tasks_json, 1, now, now)
            )
            conn.commit()
            conn.close()

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        if DB_TYPE == "sqlserver":
            conn = self._get_sqlserver_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username,password_hash,customer,allowed_tasks_json,is_active FROM users WHERE username=?",
                (username,)
            )
            row = cursor.fetchone()
            conn.close()
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.execute(
                "SELECT username,password_hash,customer,allowed_tasks_json,is_active FROM users WHERE username=?",
                (username,)
            )
            row = cursor.fetchone()
            conn.close()
        
        if not row:
            return None
        return {
            "username": row[0],
            "password_hash": row[1],
            "customer": row[2],
            "allowed_tasks": json.loads(row[3]) if row[3] else [],
            "is_active": bool(row[4]),
        }

    def verify_password(self, username: str, password: str) -> bool:
        from passlib.hash import bcrypt
        user = self.get_user(username)
        if not user or not user["is_active"]:
            return False
        try:
            return bcrypt.verify(password, user["password_hash"])
        except Exception:
            return False

    def update_password(self, username: str, new_password_hash: str):
        if DB_TYPE == "sqlserver":
            conn = self._get_sqlserver_conn()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash=?, updated_at=DATEADD(HOUR, 7, GETUTCDATE()) WHERE username=?", (new_password_hash, username))
            conn.commit()
            conn.close()
        else:
            conn = self._get_sqlite_conn()
            conn.execute("UPDATE users SET password_hash=?, updated_at=? WHERE username=?", (new_password_hash, now_iso(), username))
            conn.commit()
            conn.close()

    def update_allowed_tasks(self, username: str, allowed_tasks: List[str]):
        tasks_json = json.dumps(allowed_tasks)
        if DB_TYPE == "sqlserver":
            conn = self._get_sqlserver_conn()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET allowed_tasks_json=?, updated_at=DATEADD(HOUR, 7, GETUTCDATE()) WHERE username=?", (tasks_json, username))
            conn.commit()
            conn.close()
        else:
            conn = self._get_sqlite_conn()
            conn.execute("UPDATE users SET allowed_tasks_json=?, updated_at=? WHERE username=?", (tasks_json, now_iso(), username))
            conn.commit()
            conn.close()

    def list_users(self) -> List[Dict[str, Any]]:
        if DB_TYPE == "sqlserver":
            conn = self._get_sqlserver_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT username,customer,allowed_tasks_json,is_active,created_at FROM users")
            rows = cursor.fetchall()
            conn.close()
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.execute("SELECT username,customer,allowed_tasks_json,is_active,created_at FROM users")
            rows = cursor.fetchall()
            conn.close()
        
        return [
            {
                "username": row[0],
                "customer": row[1],
                "allowed_tasks": json.loads(row[2]) if row[2] else [],
                "is_active": bool(row[3]),
                "created_at": row[4],
            }
            for row in rows
        ]

    def delete_user(self, username: str):
        if DB_TYPE == "sqlserver":
            conn = self._get_sqlserver_conn()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username=?", (username,))
            conn.commit()
            conn.close()
        else:
            conn = self._get_sqlite_conn()
            conn.execute("DELETE FROM users WHERE username=?", (username,))
            conn.commit()
            conn.close()