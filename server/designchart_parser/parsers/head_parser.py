from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber

from ..core.pdf_core import extract_top_left_first_line

COL_SEP = "|"
ROW_SEP = "\\n"

def clean_multiline_value(s: str) -> str:
    if s is None:
        return ""

    lines = []
    for line in str(s).splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)

    return "\n".join(lines)  # vẫn giữ xuống dòng thật

def encode_size_for_sql(s: str) -> str:
    if not s:
        return ""

    rows = []

    for line in s.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = [x.strip() for x in line.split("|")]

        left = parts[0] if len(parts) > 0 else ""
        right = parts[1] if len(parts) > 1 else ""

        rows.append(f"{left}{COL_SEP}{right}")

    return ROW_SEP.join(rows)   # dùng "\\n"

def norm(v: Any) -> str:
    if v is None:
        return ""
    s = str(v)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def clean_key(s: str) -> str:
    s = norm(s).upper()
    s = s.replace(":", "")
    s = re.sub(r"\s+", " ", s)
    return s


def extract_first_page_style(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            return ""
        first_page = pdf.pages[0]
        return extract_top_left_first_line(
            first_page,
            x_max_ratio=0.55,
            y_max_ratio=0.20,
            line_tol=3,
        )


def extract_first_page_tables(pdf_path: str) -> list[pd.DataFrame]:
    out: list[pd.DataFrame] = []

    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            return out

        page = pdf.pages[0]
        tables = page.extract_tables() or []

        for tbl in tables:
            df = pd.DataFrame(tbl)
            if df is None or df.empty:
                continue
            df = df.replace({None: "", "": ""})
            out.append(df)

    return out


def is_head_table(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        return False

    all_text = " | ".join(
        norm(df.iat[r, c])
        for r in range(df.shape[0])
        for c in range(df.shape[1])
        if norm(df.iat[r, c])
    ).upper()

    must_have = [
        "NAME",
        "SEASON",
        "YEAR",
        "BRAND",
        "GENDER",
        "PLAYER",
        "SIZE",
        "TP CREATED BY",
        "SPEC BY",
        "CREATE",
    ]
    hit = sum(1 for k in must_have if k in all_text)
    return hit >= 6


def pick_head_table(pdf_path: str) -> pd.DataFrame:
    tables = extract_first_page_tables(pdf_path)
    if not tables:
        return pd.DataFrame()

    for df in tables:
        if is_head_table(df):
            return df.copy()

    best = max(tables, key=lambda x: x.shape[0] * x.shape[1])
    return best.copy()


def table_to_key_values(df: pd.DataFrame) -> dict[str, str]:
    kv: dict[str, str] = {}

    if df is None or df.empty:
        return kv

    nrows, ncols = df.shape
    current_key = ""

    for r in range(nrows):
        c0 = norm(df.iat[r, 0]) if ncols >= 1 else ""
        c1 = norm(df.iat[r, 1]) if ncols >= 2 else ""
        c2 = norm(df.iat[r, 2]) if ncols >= 3 else ""

        key = clean_key(c0)

        if key:
            current_key = key

        if not current_key:
            continue

        if current_key in {"SIZE / SAMPLE", "SIZE/SAMPLE"}:
            left = c1
            right = c2
            line = " | ".join([x for x in [left, right] if x])

            if not line:
                continue

            if "SIZE / SAMPLE" not in kv:
                kv["SIZE / SAMPLE"] = line
            else:
                kv["SIZE / SAMPLE"] += "\n" + line
            continue

        if c1:
            kv[current_key] = c1

    return kv


def clean_value(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_head_from_pdf(pdf_path: str) -> dict[str, Any]:
    df = pick_head_table(pdf_path)
    kv = table_to_key_values(df)

    file_name = Path(pdf_path).name
    style = extract_first_page_style(pdf_path)
    # style = re.sub(r"\s+", "", style)
    
    size_raw = clean_multiline_value(
        kv.get("SIZE / SAMPLE", kv.get("SIZE/SAMPLE", ""))
    )

    size_sql = encode_size_for_sql(size_raw)

    out = {
        "File_name": file_name,
        "CustomerId": "HA",
        "Style": style,
        "Name": clean_value(kv.get("NAME", "")),
        "Season": clean_value(kv.get("SEASON", "")),
        "Year": clean_value(kv.get("YEAR", "")),
        "Brand": clean_value(kv.get("BRAND", "")),
        "Gender": clean_value(kv.get("GENDER", "")),
        "Player": clean_value(kv.get("PLAYER", "")),
        "Size": size_sql,
        "TPCreatedBy": clean_value(kv.get("TP CREATED BY", "")),
        "SpecBy": clean_value(kv.get("SPEC BY", "")),
        "CreateDate": clean_value(kv.get("CREATE", "")),
        "Image": None,
    }

    return out