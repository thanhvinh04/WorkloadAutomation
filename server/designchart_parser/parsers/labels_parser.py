from __future__ import annotations

from typing import Any

import pandas as pd

from ..config import FIELD_LABELS, LABELS_COLUMNS
from ..core.parser_common import (
    build_label_to_row,
    build_position_cols,
    ensure_dataframe_columns,
    find_colorway_row_and_span,
    is_color_value,
    norm,
    pick_dev_or_vendor,
    pick_first_value,
    read_color_under_position,
)
from ..core.types import TableMeta


def parse_labels_table(df_table: pd.DataFrame, meta: TableMeta) -> list[dict[str, Any]]:
    cols = [c for c in df_table.columns if c.startswith("c")]
    if not cols:
        return []

    position_cols = build_position_cols(df_table)
    if not position_cols:
        return []

    label_to_row = build_label_to_row(df_table)

    def _pick_first(labels: list[str], col: str) -> str:
        return pick_first_value(label_to_row, labels, col)

    color_idx, _span_cols = find_colorway_row_and_span(df_table, cols, max_window=6)
    if color_idx is None:
        return []

    out: list[dict[str, Any]] = []

    for col, position in position_cols:
        internal_code = _pick_first(FIELD_LABELS["internal_code"], col)
        dev_code = pick_dev_or_vendor(
            label_to_row,
            col,
            FIELD_LABELS["dev_code"],
            FIELD_LABELS["vendor_ref_no"],
        )
        vendor_ref_no = _pick_first(FIELD_LABELS["vendor_ref_no"], col)
        vendor = _pick_first(FIELD_LABELS["vendor"], col)
        name = _pick_first(FIELD_LABELS["name_labels"], col)
        type_val = _pick_first(FIELD_LABELS["type"], col)
        location = _pick_first(FIELD_LABELS["location"], col)
        if not location:
            location = position
        placement = _pick_first(FIELD_LABELS["placement"], col)
        if not placement:
            placement = location
        variable = _pick_first(FIELD_LABELS["variable"], col)
        quantity = _pick_first(FIELD_LABELS["quantity"], col)
        special_instructions = _pick_first(FIELD_LABELS["special_instructions"], col)
        size_scale = _pick_first(FIELD_LABELS["size_scale"], col)

        for i in range(color_idx + 1, len(df_table)):
            row_i = df_table.iloc[i]

            color_garment = norm(row_i.get("c0", ""))
            if not is_color_value(color_garment):
                continue

            color_trim = read_color_under_position(row_i, col, cols, join_width=2)
            color_trim = norm(color_trim)
            if not is_color_value(color_trim):
                continue

            out.append({
                "DesignChartHeadId": meta.design_chart_head_id,
                "Position": position,
                "ColorGarment": color_garment,
                "ColorTrim": color_trim,
                "InternalCode": internal_code,
                "DevCode": dev_code,
                "VendorRefNo": vendor_ref_no,
                "Vendor": vendor,
                "Name": name,
                "Type": type_val,
                "Location": location,
                "Placement": placement,
                "Variable": variable,
                "Quantity": quantity,
                "SpecialInstructions": special_instructions,
                "SizeScale": size_scale,
                "Page": meta.page,
            })

    return out


def rows_to_labels_df(rows: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    return ensure_dataframe_columns(df, LABELS_COLUMNS)