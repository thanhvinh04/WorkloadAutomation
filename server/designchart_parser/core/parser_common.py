from __future__ import annotations

import re
from typing import Any

import pandas as pd


def norm(v: Any) -> str:
    if v is None:
        return ""
    s = str(v)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_for_match(s: str) -> str:
    s = norm(s).upper()
    return re.sub(r"[^A-Z0-9]+", "", s)


def is_color_value(s: str) -> bool:
    s = norm(s)
    if not s:
        return False
    if s.upper() in {"N/A", "NA"}:
        return False
    return len(s) >= 3


def get_joined_cell(row: pd.Series, cols: list[str]) -> str:
    return " ".join(norm(row.get(c, "")) for c in cols if norm(row.get(c, "")))


def read_color_under_position(row: pd.Series, col: str, cols: list[str], join_width: int = 2) -> str:
    if col not in cols:
        return ""

    idx = cols.index(col)
    vals = []
    for j in range(idx, min(idx + join_width, len(cols))):
        vals.append(norm(row.get(cols[j], "")))

    joined = " ".join(v for v in vals if v)
    return norm(joined)


def find_colorway_row_and_span(df_table: pd.DataFrame, cols: list[str], max_window: int = 6):
    kw1 = normalize_for_match("COLORWAY")
    kw2 = normalize_for_match("COLORWAYS")

    best = None
    for i in range(len(df_table)):
        row = df_table.iloc[i]
        whole = normalize_for_match(" ".join(norm(row.get(c, "")) for c in cols))
        if kw1 not in whole and kw2 not in whole:
            continue

        for start in range(len(cols)):
            for w in range(1, min(max_window, len(cols) - start) + 1):
                span = cols[start : start + w]
                joined = normalize_for_match(get_joined_cell(row, span))
                if not joined:
                    continue

                matched = None
                if joined == kw2 or kw2 in joined:
                    matched = kw2
                elif joined == kw1 or kw1 in joined:
                    matched = kw1

                if matched:
                    extra = max(0, len(joined) - len(matched))
                    score = (w, extra, start)
                    cand = (score, i, span)
                    if best is None or cand[0] < best[0]:
                        best = cand

    if best is None:
        for i in range(len(df_table)):
            row = df_table.iloc[i]
            row_text = " | ".join(norm(row.get(c, "")) for c in cols if norm(row.get(c, "")))
            if re.search(r"\bCOLORWAYS?\b", row_text, flags=re.IGNORECASE):
                return i, []
        return None, []

    _, row_idx, span_cols = best
    return row_idx, span_cols


def build_position_cols(df_table: pd.DataFrame) -> list[tuple[str, str]]:
    cols = [c for c in df_table.columns if re.fullmatch(r"c\d+", c)]
    if not cols:
        return []

    header = df_table.iloc[0].to_dict()
    position_cols: list[tuple[str, str]] = []

    for c in cols:
        if c == "c0":
            continue
        pos = norm(header.get(c))
        if pos and pos.upper() not in ("NAN", "NONE", "NULL", ""):
            position_cols.append((c, pos))

    return position_cols


def build_label_to_row(df_table: pd.DataFrame) -> dict[str, pd.Series]:
    label_to_row: dict[str, pd.Series] = {}
    for i in range(len(df_table)):
        label = norm(df_table.iloc[i].get("c0", ""))
        if label:
            label_to_row[label.upper()] = df_table.iloc[i]
    return label_to_row


def pick_value(label_to_row: dict[str, pd.Series], label: str, col: str) -> str:
    key = label.upper()
    if key not in label_to_row:
        return ""
    v = label_to_row[key].get(col, "")
    return norm(v)


def pick_first_value(label_to_row: dict[str, pd.Series], labels: list[str], col: str) -> str:
    for lb in labels:
        key = lb.upper()
        if key in label_to_row:
            return norm(label_to_row[key].get(col, ""))
    return ""


def pick_dev_or_vendor(label_to_row: dict[str, pd.Series], col: str, dev_labels: list[str], vendor_ref_labels: list[str]) -> str:
    dev = pick_first_value(label_to_row, dev_labels, col)
    if dev:
        return dev
    return pick_first_value(label_to_row, vendor_ref_labels, col)


def empty_if_nan(v: Any) -> str:
    if pd.isna(v):
        return ""
    return norm(v)


def ensure_dataframe_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = pd.DataFrame() if df is None else df.copy()
    for c in columns:
        if c not in df.columns:
            df[c] = None
    return df[columns].copy()