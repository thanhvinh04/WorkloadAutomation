from __future__ import annotations

import os
from typing import Any

import pandas as pd

from ..config import (
    FABRIC_COLUMNS,
    FILTER_GROUPS_ALL,
    FILTER_GROUPS_FABRIC,
    FILTER_GROUPS_LABELS,
    FILTER_GROUPS_TRIM,
    FILTER_GROUPS_ARTWORK,
    LABELS_COLUMNS,
    TRIM_COLUMNS,
)
from ..parsers.fabric_parser import parse_fabric_table, rows_to_fabric_df
from ..parsers.labels_parser import parse_labels_table, rows_to_labels_df
from ..parsers.trim_parser import parse_trim_table, rows_to_trim_df
from ..parsers.artwork import parse_artwork_table, rows_to_artwork_df
from ..core.pdf_core import pdf_to_detect_and_tables_wide
from ..core.types import TableMeta


def _build_page_to_style(df_detect: pd.DataFrame) -> dict[int, str]:
    if df_detect is None or df_detect.empty:
        return {}
    return (
        df_detect.drop_duplicates(subset=["page"])
        .set_index("page")["top_left_first_line"]
        .fillna("")
        .astype(str)
        .to_dict()
    )


def _iter_group_tables(
    pdf_path: str,
    design_chart_head_id: int,
    filter_groups: list[dict[str, Any]],
):
    df_detect, df_wide = pdf_to_detect_and_tables_wide(pdf_path, filter_groups)
    if df_detect.empty or df_wide.empty:
        return df_detect, df_wide, []

    page_to_style = _build_page_to_style(df_detect)
    file_name = os.path.basename(pdf_path)

    items = []
    for (page, table_index), g in df_wide.groupby(["page", "table_index"], sort=True):
        g = g.sort_values("row").reset_index(drop=True)
        page_int = int(page)

        meta = TableMeta(
            page=page_int,
            table_index=int(table_index),
            style_number=page_to_style.get(page_int, ""),
            matched_groups=str(g["matched_groups"].iloc[0]) if "matched_groups" in g.columns else "",
            top_right_text=str(g["top_right_text"].iloc[0]) if "top_right_text" in g.columns else "",
            file_name=file_name,
            design_chart_head_id=design_chart_head_id,
        )
        items.append((g, meta))

    return df_detect, df_wide, items


def build_fabric_rows_from_pdf(pdf_path: str, design_chart_head_id: int) -> pd.DataFrame:
    _df_detect, _df_wide, items = _iter_group_tables(
        pdf_path=pdf_path,
        design_chart_head_id=design_chart_head_id,
        filter_groups=FILTER_GROUPS_FABRIC,
    )

    rows: list[dict[str, Any]] = []
    for g, meta in items:
        if "FABRIC" not in meta.matched_groups.upper():
            continue
        rows.extend(parse_fabric_table(g, meta))

    return rows_to_fabric_df(rows)


def build_trim_rows_from_pdf(pdf_path: str, design_chart_head_id: int) -> pd.DataFrame:
    _df_detect, _df_wide, items = _iter_group_tables(
        pdf_path=pdf_path,
        design_chart_head_id=design_chart_head_id,
        filter_groups=FILTER_GROUPS_TRIM,
    )

    rows: list[dict[str, Any]] = []
    for g, meta in items:
        if "TRIM" not in meta.matched_groups.upper():
            continue
        rows.extend(parse_trim_table(g, meta))

    return rows_to_trim_df(rows)


def build_labels_rows_from_pdf(pdf_path: str, design_chart_head_id: int) -> pd.DataFrame:
    _df_detect, _df_wide, items = _iter_group_tables(
        pdf_path=pdf_path,
        design_chart_head_id=design_chart_head_id,
        filter_groups=FILTER_GROUPS_LABELS,
    )

    rows: list[dict[str, Any]] = []
    for g, meta in items:
        if "LABELS" not in meta.matched_groups.upper():
            continue
        rows.extend(parse_labels_table(g, meta))

    return rows_to_labels_df(rows)


def build_artwork_rows_from_pdf(pdf_path: str, design_chart_head_id: int) -> pd.DataFrame:
    _df_detect, _df_wide, items = _iter_group_tables(
        pdf_path=pdf_path,
        design_chart_head_id=design_chart_head_id,
        filter_groups=FILTER_GROUPS_ARTWORK,
    )

    rows: list[dict[str, Any]] = []
    for g, meta in items:
        if "ARTWORK" not in meta.matched_groups.upper():
            continue
        rows.extend(parse_artwork_table(g, meta))

    return rows_to_artwork_df(rows)


def build_all_detail_tables_from_pdf(pdf_path: str, design_chart_head_id: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    _df_detect, _df_wide, items = _iter_group_tables(
        pdf_path=pdf_path,
        design_chart_head_id=design_chart_head_id,
        filter_groups=FILTER_GROUPS_ALL,
    )

    fabric_rows: list[dict[str, Any]] = []
    trim_rows: list[dict[str, Any]] = []
    labels_rows: list[dict[str, Any]] = []

    for g, meta in items:
        mg = meta.matched_groups.upper()

        if "FABRIC" in mg:
            fabric_rows.extend(parse_fabric_table(g, meta))

        if "TRIM" in mg:
            trim_rows.extend(parse_trim_table(g, meta))

        if "LABELS" in mg:
            labels_rows.extend(parse_labels_table(g, meta))

    df_fabric = rows_to_fabric_df(fabric_rows)
    df_trim = rows_to_trim_df(trim_rows)
    df_labels = rows_to_labels_df(labels_rows)

    return df_fabric, df_trim, df_labels


def build_all_detail_tables_from_pdf_v2(pdf_path: str, design_chart_head_id: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    _df_detect, df_wide, items = _iter_group_tables(
        pdf_path=pdf_path,
        design_chart_head_id=design_chart_head_id,
        filter_groups=FILTER_GROUPS_ALL,
    )

    fabric_rows: list[dict[str, Any]] = []
    trim_rows: list[dict[str, Any]] = []
    labels_rows: list[dict[str, Any]] = []
    artwork_rows: list[dict[str, Any]] = []

    for g, meta in items:
        mg = meta.matched_groups.upper()

        if "FABRIC" in mg:
            fabric_rows.extend(parse_fabric_table(g, meta))

        if "TRIM" in mg:
            trim_rows.extend(parse_trim_table(g, meta))

        if "LABELS" in mg:
            labels_rows.extend(parse_labels_table(g, meta))

        if "ARTWORK" in mg:
            artwork_rows.extend(parse_artwork_table(g, meta))

    df_fabric = rows_to_fabric_df(fabric_rows)
    df_trim = rows_to_trim_df(trim_rows)
    df_labels = rows_to_labels_df(labels_rows)
    df_artwork = rows_to_artwork_df(artwork_rows)

    return df_fabric, df_trim, df_labels, df_artwork


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, help="Full path to PDF")
    ap.add_argument("--head-id", type=int, required=True, help="DesignChartHeadId")
    ap.add_argument("--out-dir", required=False, default=".")
    args = ap.parse_args()

    pdf_path = str(Path(args.pdf).resolve())
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    df_fabric, df_trim, df_labels = build_all_detail_tables_from_pdf(
        pdf_path=pdf_path,
        design_chart_head_id=args.head_id,
    )

    df_fabric.to_excel(out_dir / "designchart_fabric.xlsx", index=False)
    df_trim.to_excel(out_dir / "designchart_trim.xlsx", index=False)
    df_labels.to_excel(out_dir / "designchart_labels.xlsx", index=False)

    print("Done")
    print(f"Fabric rows: {len(df_fabric)}")
    print(f"Trim rows: {len(df_trim)}")
    print(f"Labels rows: {len(df_labels)}")