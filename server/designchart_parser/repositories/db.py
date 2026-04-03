from __future__ import annotations

import json
import urllib.parse
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def load_db_profile(json_path: str | Path, profile_name: str | None = None) -> dict:
    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"Config file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    profiles = cfg.get("profiles", {})
    if not profiles:
        raise ValueError("No profiles found in config")

    # Nếu không truyền profile → dùng default
    if not profile_name:
        profile_name = cfg.get("default")

    if profile_name not in profiles:
        raise ValueError(f"Profile '{profile_name}' not found in config")

    return profiles[profile_name]


def make_sql_server_engine(
    json_path: str | Path,
    profile_name: str | None = None,
) -> Engine:
    profile = load_db_profile(json_path, profile_name)

    server = profile["server"]
    database = profile["database"]
    username = profile["user"]
    password = profile["password"]

    # Encode password để tránh lỗi ký tự đặc biệt
    password = urllib.parse.quote_plus(password)

    driver = "ODBC Driver 18 for SQL Server"

    conn_str = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}"
        f"?driver={driver.replace(' ', '+')}"
        f"&TrustServerCertificate=yes"
    )

    engine = create_engine(
        conn_str,
        fast_executemany=True,
        future=True,
    )

    return engine