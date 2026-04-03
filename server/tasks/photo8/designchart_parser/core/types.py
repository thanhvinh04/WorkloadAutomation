from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TableMeta:
    page: int
    table_index: int
    style_number: str
    matched_groups: str
    top_right_text: str
    file_name: str
    design_chart_head_id: int