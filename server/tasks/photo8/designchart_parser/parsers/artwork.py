from __future__ import annotations

import re
from typing import Any

import pandas as pd

from ..core.parser_common import norm


ARTWORK_COLUMNS = [
    "DesignChartHeadId",
    "ColorGarment",
    "ColorCodeAndName",
    "ProviderAndSwatch",
    "Type",
    "Technique",
    "Execution",
    "AdditionalCallouts",
    "ColumnIndex",
    "Page",
]


_LABEL_MAP = {
    "COLOR CODE&NAME": "ColorCodeAndName",
    "COLOR CODE & NAME": "ColorCodeAndName",
    "PROVIDER AND SWATCH": "ProviderAndSwatch",
    "TYPE": "Type",
    "TECHNIQUE": "Technique",
    "EXECUTION": "Execution",
    "ADDITIONAL CALLOUTS": "AdditionalCallouts",
}


def _norm_label(s: Any) -> str:
    s = norm(s).upper()
    s = s.replace("&", " AND ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _is_block_code(s: Any) -> bool:
    s = norm(s).upper()
    return bool(re.fullmatch(r"[A-Z0-9]{2,6}", s))


def find_artwork_columns(df_table: pd.DataFrame) -> dict[str, Any] | None:
    cols = [c for c in df_table.columns if re.fullmatch(r"c\d+", c)]
    if len(cols) < 4:
        return None

    return {
        "block_code_col": cols[0],
        "label_col": cols[2],
        "data_cols": cols[3:],
    }


def find_block_starts(df_table: pd.DataFrame, block_code_col: str, label_col: str) -> list[int]:
    starts = []
    for i in range(len(df_table)):
        code = norm(df_table.iloc[i].get(block_code_col, ""))
        label = norm(df_table.iloc[i].get(label_col, ""))
        if _is_block_code(code) and not label:
            starts.append(i)
    return starts


def find_block_end(df_table: pd.DataFrame, start_idx: int, next_start: int | None, label_col: str) -> int:
    hard_end = start_idx + 7
    if next_start is not None:
        hard_end = min(hard_end, next_start - 1)

    for i in range(start_idx, hard_end + 1):
        if _norm_label(df_table.iloc[i].get(label_col, "")) == "ADDITIONAL CALLOUTS":
            return i

    return hard_end


def build_label_to_row(block_df: pd.DataFrame, label_col: str) -> dict[str, int]:
    out = {}
    for i in range(len(block_df)):
        key = _norm_label(block_df.iloc[i].get(label_col, ""))
        if key in _LABEL_MAP:
            out[_LABEL_MAP[key]] = i
    return out


def parse_artwork_table(df_table: pd.DataFrame, meta: dict) -> list[dict]:
    layout = find_artwork_columns(df_table)
    if not layout:
        return []

    block_code_col = layout["block_code_col"]
    label_col = layout["label_col"]
    data_cols = layout["data_cols"]

    starts = find_block_starts(df_table, block_code_col, label_col)
    if not starts:
        return []

    out = []

    for idx, start_idx in enumerate(starts):
        next_start = starts[idx + 1] if idx + 1 < len(starts) else None
        end_idx = find_block_end(df_table, start_idx, next_start, label_col)

        block_df = df_table.iloc[start_idx:end_idx + 1].reset_index(drop=True)
        if block_df.empty:
            continue

        block_code = norm(block_df.iloc[0].get(block_code_col, ""))
        color_garment = norm(block_df.iloc[2].get(block_code_col, "")) if len(block_df) > 2 else ""

        label_to_row = build_label_to_row(block_df, label_col)

        for col_idx, data_col in enumerate(data_cols, start=1):
            row_out = {
                "DesignChartHeadId": meta.design_chart_head_id,
                "ColorGarment": color_garment,
                "ColorCodeAndName": "",
                "ProviderAndSwatch": "",
                "Type": "",
                "Technique": "",
                "Execution": "",
                "AdditionalCallouts": "",
                "ColumnIndex": col_idx,
                "Page": meta.page,
            }

            for field, row_i in label_to_row.items():
                row_out[field] = norm(block_df.iloc[row_i].get(data_col, ""))

            if any(row_out.get(f) for f in [
                "ColorCodeAndName", "ProviderAndSwatch", "Type",
                "Technique", "Execution", "AdditionalCallouts"
            ]):
                out.append(row_out)

    return out


def rows_to_artwork_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    for col in ARTWORK_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[ARTWORK_COLUMNS]