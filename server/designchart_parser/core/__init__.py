# designchart_parser.core
from .types import TableMeta
from .parser_common import (
    norm,
    is_color_value,
    build_label_to_row,
    build_position_cols,
    pick_first_value,
    pick_dev_or_vendor,
    ensure_dataframe_columns,
)
from .pdf_core import pdf_to_detect_and_tables_wide
