from __future__ import annotations

import json
import os
import urllib.parse
import warnings
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Any, Dict, Optional, Tuple

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

warnings.filterwarnings("ignore")

# =========================================================
# CONFIG
# =========================================================

# Your original delimiter used upstream
SEP = " | "
NEWLINE_COLS = ["description", "COLOR"]

# Main tables
FABRIC_TABLE = "dbo.Fabric"
TRIM_TABLE = "dbo.TrimAndLabels"

# Log tables (for previous version)
FABRIC_LOG_TABLE = "dbo.Fabric_Log"
FABRIC_LOG_TIME_COL = "ActionTime"
TRIM_LOG_TABLE = "dbo.TrimAndLabels_Log"
TRIM_LOG_TIME_COL = "LogTime"

# Batch bucket in minutes (you asked to widen to 2 minutes)
BATCH_BUCKET_MINUTES = 2

# Google Sheet
SPREADSHEET_ID = "1HVERYwjbyLroIpJY28-p9RNKz4Q6SyZEYamiP0rLhcY"
FABRIC_SHEET_NAME = "Fabric"
TRIM_SHEET_NAME = "Trim"   # giờ chỉ chứa TRIM
LABELS_SHEET_NAME = "Labels"          # sheet mới, chứa LABELS đã transform

# Sheet layout
META_ROW = 1
HEADER_ROW = 2
DATA_START_ROW = 3

BASE_DIR = Path(__file__).resolve().parent

GSERVICE_ACCOUNT_JSON = os.environ.get(
    "HADDAD_GS_SERVICE_JSON",
    str(BASE_DIR / "Account_LS_EHD_MANAGEMENT.json"),
)
SQL_CONFIG_PATH = os.environ.get(
    "HADDAD_SQL_CONFIG",
    str(BASE_DIR / "ServerPassword.json"),
)

# =========================================================
# HARD-CODE TEST FILES (YOU CAN EDIT)
# =========================================================
TEST_FILE_NAMES = [
    # Put exact file_name values (usually PDF file names) that exist in SQL
    # Example:
    # "ABC_001.pdf",
]

# =========================================================
# SQL HELPERS
# =========================================================

def read_sql_config(path: str, profile: str = "ERP_Import") -> tuple[str, str, str, str]:
    with open(path, "r", encoding="utf-8") as f:
        p = json.load(f)["profiles"][profile]
    return p["server"], p["database"], p["user"], p["password"]


def create_engine_sqlserver(server: str, database: str, user: str, password: str) -> Engine:
    conn_str = (
        "DRIVER=ODBC Driver 18 for SQL Server;"
        f"SERVER={server};DATABASE={database};UID={user};PWD={password};TrustServerCertificate=yes;"
    )
    return create_engine(f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}")


def read_sql_table(engine: Engine, full_table: str) -> pd.DataFrame:
    schema, table = full_table.split(".", 1)
    # Keep your original ordering (works if cols exist)
    q = text(f"SELECT * FROM {schema}.{table} ORDER BY file_name, matched_groups, page")
    return pd.read_sql(q, engine)


def _sql_ident(name: str) -> str:
    return "[" + name.replace("]", "]]") + "]"


def _bucket_time_expr_nmin(time_col: str, bucket_minutes: int) -> str:
    """
    Buckets datetime2 into N-minute windows (floor).
    Example N=2:
      DATEADD(minute, (DATEDIFF(minute,0,t)/2)*2, 0)
    """
    n = int(bucket_minutes)
    return f"DATEADD(minute, (DATEDIFF(minute, 0, {_sql_ident(time_col)}) / {n}) * {n}, 0)"


def fetch_prev_version_from_log(
    engine: Engine,
    log_table: str,
    time_col: str,
    file_name: str,
    data_cols: List[str],
    bucket_minutes: int = 2,
) -> pd.DataFrame:
    """
    Returns rows of the PREVIOUS batch (BatchRank = 2) for one file_name from *_Log table,
    where batch is grouped by N-minute buckets.
    """
    bt = _bucket_time_expr_nmin(time_col, bucket_minutes)
    select_cols = ", ".join(_sql_ident(c) for c in data_cols)

    sql = text(f"""
    WITH L AS (
        SELECT
            {select_cols},
            {bt} AS BatchTime
        FROM {log_table}
        WHERE {_sql_ident("file_name")} = :fn
    ),
    R AS (
        SELECT
            *,
            DENSE_RANK() OVER (ORDER BY BatchTime DESC) AS BatchRank
        FROM L
    )
    SELECT {select_cols}
    FROM R
    WHERE BatchRank = 2
    """)

    df = pd.read_sql(sql, engine, params={"fn": str(file_name)})
    # Ensure columns exist
    for c in data_cols:
        if c not in df.columns:
            df[c] = None
    return df[data_cols].copy()


# =========================================================
# DESIGNCHART IMAGE LOOKUP
# =========================================================

def lookup_colorway_image(
    engine: Engine,
    style: str,
    color_garment: str,
) -> str:
    """
    Lookup DesignChartImage by Style + partial ColorGarment match.
    
    Logic:
    - Query DesignChartImage where DesignChartHead.Style matches
    - Try exact match first
    - Try with FRONT_ prefix (prioritize)
    - Try with BACK_ prefix
    - Return Image URL or ""
    """
    if not style or not color_garment:
        return ""
    
    color_garment = str(color_garment).strip().upper()
    
    try:
        sql = text("""
            SELECT di.Image
            FROM DesignChartImage di
            INNER JOIN DesignChartHead dh ON di.DesignChartHeadId = dh.Id
            WHERE dh.Style = :style
            ORDER BY 
                CASE 
                    WHEN di.ColorGarment LIKE :exact_match THEN 1
                    WHEN di.ColorGarment LIKE :front_match THEN 2
                    WHEN di.ColorGarment LIKE :back_match THEN 3
                    ELSE 4
                END
        """)
        
        exact = color_garment
        front = f"FRONT%{color_garment}%"
        back = f"BACK%{color_garment}%"
        
        with engine.begin() as conn:
            result = conn.execute(sql, {
                "style": style,
                "exact_match": exact,
                "front_match": front,
                "back_match": back,
            }).fetchone()
        
        if result:
            return result[0] or ""
        
    except Exception as e:
        pass
    
    return ""


def add_image_column_to_labels(
    engine: Engine,
    df_labels: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add Image column to Labels dataframe by looking up DesignChartImage.
    """
    if df_labels.empty:
        return df_labels
    
    df_labels = df_labels.copy()
    df_labels["Image"] = ""
    
    for idx, row in df_labels.iterrows():
        style = row.get("Style", "")
        color_garment = row.get("Color Garment", "")
        
        if style and color_garment:
            image_url = lookup_colorway_image(engine, style, color_garment)
            df_labels.at[idx, "Image"] = image_url
    
    return df_labels


# =========================================================
# GOOGLE SHEETS HELPERS
# =========================================================

def get_gspread_client(service_account_json_path: str) -> gspread.Client:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(service_account_json_path, scopes=scopes)
    return gspread.authorize(creds)


def ensure_worksheet(sh: gspread.Spreadsheet, title: str, rows: int = 2000, cols: int = 60) -> gspread.Worksheet:
    try:
        return sh.worksheet(title)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=title, rows=str(rows), cols=str(cols))


def update_last_load_time(ws: gspread.Worksheet) -> None:
    ts = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S ICT")
    ws.update("A1:B1", [["Last load", ts]], value_input_option="RAW")
    
# ===== MARK: SHEET LASTUPDATEDAT HELPERS START =====
def get_push_timestamp_str() -> str:
    return datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S ICT")


def append_last_updated_at(df: pd.DataFrame, ts: str) -> pd.DataFrame:
    df = df.copy()
    df["LastUpdatedAt"] = ts
    return df
# ===== MARK: SHEET LASTUPDATEDAT HELPERS END =====


def get_header(ws: gspread.Worksheet) -> List[str]:
    row = ws.row_values(HEADER_ROW)
    return [c.strip() for c in row] if row else []


def write_header_if_needed(ws: gspread.Worksheet, cols: List[str]) -> None:
    # ensure meta row exists
    if not ws.get_all_values():
        update_last_load_time(ws)

    existing = get_header(ws)
    if existing != cols:
        ws.update(f"A{HEADER_ROW}", [cols], value_input_option="RAW")


def df_to_rows_for_sheet(df: pd.DataFrame, cols: List[str]) -> List[List[Any]]:
    df2 = df.copy()
    for c in cols:
        if c not in df2.columns:
            df2[c] = ""
    df2 = df2[cols].fillna("")
    # Convert to Python scalars (strings usually)
    rows: List[List[Any]] = []
    for _, r in df2.iterrows():
        row = []
        for c in cols:
            v = r[c]
            if v is None or (isinstance(v, float) and pd.isna(v)):
                v = ""
            row.append(v)
        rows.append(row)
    return rows


def convert_sep_to_newline_for_trim_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep same behavior as your original: only for rows where matched_groups contains 'TRIM'
    convert ' | ' into '\n' for description and COLOR.
    """
    if df.empty or "matched_groups" not in df.columns:
        return df
    df = df.copy()
    mask_trim = df["matched_groups"].astype(str).str.upper().str.contains("TRIM", na=False)
    for col in NEWLINE_COLS:
        if col in df.columns:
            s = df.loc[mask_trim, col].astype(str)
            s = s.str.replace(SEP, "\n", regex=False)
            df.loc[mask_trim, col] = s
    return df

# =========================================================
# BUILD LABELS -> Trim sheet
# =========================================================

def build_labels_trim_sheet(df_trim: pd.DataFrame) -> pd.DataFrame:
    """
    Build sheet 'Trim' from rows where matched_groups = LABELS.

    Output columns:
      file_name
      Style
      Position
      Code
      Color Garment
      Color Trim
      Variable
      page

    Rules:
    - only matched_groups = LABELS
    - Style = STYLE_NO (fallback Style)
    - Position = POSITION
    - Code = description before first '+'
    - If type contains 'Heat Transfer':
        Color Garment = COLOR before first '|'
        Color Trim = trim color column
      else:
        Color Garment = ''
        Color Trim = ''
    - For non-Heat Transfer: keep 1 row per file_name + Style + Position + Code + page
    - For Heat Transfer: keep distinct rows by color as well
    """

    out_cols = [
        "file_name",
        "Style",
        "Position",
        "Code",
        "Color Garment",
        "Color Trim",
        "Variable",
        "page",
    ]

    if df_trim.empty or "matched_groups" not in df_trim.columns:
        return pd.DataFrame(columns=out_cols)

    df = df_trim.copy()
    df = df[df["matched_groups"].astype(str).str.upper().str.strip() == "LABELS"].copy()

    if df.empty:
        return pd.DataFrame(columns=out_cols)

    style_col = pick_first_existing_col(df, ["STYLE_NO", "Style", "STYLE"])
    position_col = pick_first_existing_col(df, ["POSITION", "Position", "POS"])
    desc_col = pick_first_existing_col(df, ["description", "DESCRIPTION"])
    color_col = pick_first_existing_col(df, ["COLOR", "GARMENT_COLOR", "COLOR_RAW", "GARMENT_COLOR_RAW"])
    color_trim_col = pick_first_existing_col(df, ["Color Trim", "COLOR_TRIM", "TRIM_COLOR", "COLORTRIM"])
    variable_col = pick_first_existing_col(df, ["Variable", "VARIABLE"])
    type_col = pick_first_existing_col(df, ["type", "Type", "TYPE"])
    page_col = pick_first_existing_col(df, ["page", "PAGE"])

    out = pd.DataFrame(index=df.index)

    out["file_name"] = df["file_name"] if "file_name" in df.columns else ""
    out["Style"] = df[style_col] if style_col else ""
    out["Position"] = df[position_col] if position_col else ""
    out["page"] = df[page_col] if page_col else ""

    if desc_col:
        desc = df[desc_col].fillna("").astype(str)
        typeheat = (
            df[type_col].fillna("").astype(str)
            if type_col
            else pd.Series("", index=df.index)
        )
        out["Code"] = desc.str.split("+", n=1).str[0].str.strip()
        is_heat_transfer = typeheat.str.contains("Heat Transfer", case=False, na=False)
    else:
        out["Code"] = ""
        is_heat_transfer = pd.Series(False, index=df.index)

    out["Color Garment"] = ""
    if color_col:
        out.loc[is_heat_transfer, "Color Garment"] = (
            df.loc[is_heat_transfer, color_col]
            .fillna("")
            .astype(str)
            .str.split("|", n=1)
            .str[0]
            .str.strip()
        )

    out["Color Trim"] = ""
    if color_trim_col:
        out.loc[is_heat_transfer, "Color Trim"] = (
            df.loc[is_heat_transfer, color_trim_col]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    if variable_col:
        out["Variable"] = df[variable_col].fillna("").astype(str)
    else:
        out["Variable"] = ""

    out = out[out_cols]

    # Deduplicate:
    # - Heat Transfer: keep distinct by colors
    # - Non-Heat Transfer: keep 1 row by Position + Code (+ file/style/page)
    mask_ht = is_heat_transfer.reindex(out.index, fill_value=False)

    out_ht = out[mask_ht].drop_duplicates(
        subset=[
            "file_name",
            "Style",
            "Position",
            "Code",
            "Color Garment",
            "Color Trim",
            "page",
        ]
    )

    out_non_ht = out[~mask_ht].drop_duplicates(
        subset=[
            "file_name",
            "Style",
            "Position",
            "Code",
            "page",
        ]
    )

    out_final = pd.concat([out_ht, out_non_ht], ignore_index=True)

    return out_final

# =========================================================
# DELETE rows by file_name (block delete)
# =========================================================

def find_row_blocks_by_file(ws: gspread.Worksheet, file_names: List[str], file_col_name: str = "file_name"):
    file_set = {str(x).strip() for x in file_names if x}
    header = get_header(ws)
    if not header or file_col_name not in header:
        return []

    file_col_idx = header.index(file_col_name) + 1  # 1-based
    col_values = ws.col_values(file_col_idx)

    rows = []
    for r, v in enumerate(col_values, start=1):
        if r < DATA_START_ROW:
            continue
        fn = (v or "").strip()
        if fn in file_set:
            rows.append(r)

    if not rows:
        return []

    rows.sort()
    blocks = []
    s = e = rows[0]
    for rr in rows[1:]:
        if rr == e + 1:
            e = rr
        else:
            blocks.append((s, e))
            s = e = rr
    blocks.append((s, e))
    return blocks


def delete_rows_blocks(ws: gspread.Worksheet, blocks):
    if not blocks:
        return 0
    sheet_id = ws.id
    reqs = []
    for s, e in sorted(blocks, key=lambda x: x[0], reverse=True):
        reqs.append({
            "deleteDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": s - 1,
                    "endIndex": e,  # end exclusive in API
                }
            }
        })
    ws.spreadsheet.batch_update({"requests": reqs})
    return sum(e - s + 1 for s, e in blocks)


def delete_rows_by_file_names(ws: gspread.Worksheet, file_names: List[str], file_col_name: str = "file_name") -> int:
    blocks = find_row_blocks_by_file(ws, file_names, file_col_name)
    return delete_rows_blocks(ws, blocks)

def filter_trim_rows_only(df_trim: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only rows where matched_groups contains TRIM.
    Used for sheet 'TrimAndLabels' after business rule changed:
    this sheet should no longer contain LABELS rows.
    """
    if df_trim.empty or "matched_groups" not in df_trim.columns:
        return df_trim.copy()

    df = df_trim.copy()
    mask_trim = df["matched_groups"].astype(str).str.upper().str.contains("TRIM", na=False)
    return df[mask_trim].copy()

# =========================================================
# ROW-BY-ROW KEY (your new definition)
# key = file_name + page + matched_groups + POSITION + STYLE_NO + top_right_text + color_trim + color_garment
# =========================================================

def _norm_val(v: Any, upper: bool = False) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).strip()
    # optional: collapse multiple spaces
    s = " ".join(s.split())
    return s.upper() if upper else s


def pick_first_existing_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    return None


def build_primary_key_series(
    df: pd.DataFrame,
    *,
    style_col: str,
    pos_col: str,
    page_col: str,
    grp_col: str,
    top_right_col: str,
    color_trim_col: str,
    color_garment_col: str,
    fashion_color_col: Optional[str] = None,  # NEW
) -> pd.Series:
    """
    Key = file_name + page + matched_groups + POSITION + STYLE_NO + top_right_text
          + color_trim + color_garment (+ fashion_color if provided)
    """

    # ensure all needed columns exist
    need = ["file_name", page_col, grp_col, pos_col, style_col, top_right_col, color_trim_col, color_garment_col]
    if fashion_color_col:
        need.append(fashion_color_col)

    d = df.copy()
    for c in need:
        if c not in d.columns:
            d[c] = ""

    # normalize for stable join
    fn = d["file_name"].apply(lambda x: _norm_val(x, upper=False))
    page = d[page_col].apply(lambda x: _norm_val(x, upper=False))
    grp = d[grp_col].apply(lambda x: _norm_val(x, upper=True))
    pos = d[pos_col].apply(lambda x: _norm_val(x, upper=True))
    style = d[style_col].apply(lambda x: _norm_val(x, upper=True))
    tr = d[top_right_col].apply(lambda x: _norm_val(x, upper=False))

    # colors: uppercase to stabilize
    ctrim = d[color_trim_col].apply(lambda x: _norm_val(x, upper=True))
    cgar = d[color_garment_col].apply(lambda x: _norm_val(x, upper=True))

    key = (fn + "||" + page + "||" + grp + "||" + pos + "||" + style + "||" + tr + "||" + ctrim + "||" + cgar)

    if fashion_color_col:
        cfashion = d[fashion_color_col].apply(lambda x: _norm_val(x, upper=True))
        key = key + "||" + cfashion

    return key


def get_key_columns_mapping_for_table(df: pd.DataFrame, table_kind: str) -> Dict[str, Optional[str]]:
    """
    Decide which actual columns map to the canonical fields for key building.

    Returns dict with:
      style_col, pos_col, page_col, grp_col, top_right_col,
      color_trim_col, color_garment_col,
      fashion_color_col (only for fabric; else None)
    """

    # stable ones
    style_col = pick_first_existing_col(df, ["STYLE_NO", "STYLE", "STYLE_NO_RAW"])
    pos_col = pick_first_existing_col(df, ["POSITION", "Position", "POS"])
    grp_col = pick_first_existing_col(df, ["matched_groups", "MATCHED_GROUPS", "group"])
    page_col = pick_first_existing_col(df, ["page", "PAGE"])
    top_right_col = pick_first_existing_col(df, ["top_right_text", "TOP_RIGHT_TEXT", "topRightText"])

    # fallbacks (ensure not None)
    if not style_col:
        style_col = "STYLE_NO"
    if not pos_col:
        pos_col = "POSITION"
    if not grp_col:
        grp_col = "matched_groups"
    if not page_col:
        page_col = "page"
    if not top_right_col:
        top_right_col = "top_right_text"

    fashion_color_col: Optional[str] = None

    if table_kind.lower() == "fabric":
        # garment color (prefer raw garment color)
        color_garment_col = pick_first_existing_col(
            df,
            ["GARMENT_COLOR_RAW", "COLOR_RAW", "GARMENT_COLOR", "COLOR", "FASHION_COLOR", "COLOR_NAME"],
        )

        # trim-ish color in fabric (adjust if you have a dedicated trim color column)
        color_trim_col = pick_first_existing_col(
            df,
            ["COLOR_TRIM", "TRIM_COLOR", "COLOR", "COLOR_RAW"],
        )

        # NEW: fashion color for key (only in fabric)
        fashion_color_col = pick_first_existing_col(
            df,
            ["FASHION_COLOR", "FASHIONCOLOUR", "FASHION_COLOR_RAW"],
        )

    else:
        # TrimAndLabels:
        color_trim_col = pick_first_existing_col(df, ["COLOR_TRIM", "TRIM_COLOR", "COLORTRIM"])
        color_garment_col = pick_first_existing_col(df, ["COLOR", "GARMENT_COLOR_RAW", "COLOR_RAW", "GARMENT_COLOR"])
        fashion_color_col = None

    # fallback to virtual empty columns if missing
    if not color_trim_col:
        color_trim_col = "__COLOR_TRIM_EMPTY__"
        df[color_trim_col] = ""
    if not color_garment_col:
        color_garment_col = "__COLOR_GAR_EMPTY__"
        df[color_garment_col] = ""

    # NOTE: if fashion_color_col is None -> do not add to key
    return {
        "style_col": style_col,
        "pos_col": pos_col,
        "page_col": page_col,
        "grp_col": grp_col,
        "top_right_col": top_right_col,
        "color_trim_col": color_trim_col,
        "color_garment_col": color_garment_col,
        "fashion_color_col": fashion_color_col,  # NEW
    }


# =========================================================
# DIFF + BOLD formatting (row-by-row using your composite key)
# =========================================================

def build_old_lookup_by_key(
    old_df: pd.DataFrame,
    key_series: pd.Series,
    all_cols: List[str],
) -> Dict[str, List[Dict[str, str]]]:
    """
    key -> list of row dicts (stringified)
    list is to handle duplicates (rare but possible).
    """
    lookup: Dict[str, List[Dict[str, str]]] = {}
    if old_df.empty:
        return lookup

    old_df2 = old_df.copy()
    for c in all_cols:
        if c not in old_df2.columns:
            old_df2[c] = ""

    for i, k in enumerate(key_series.tolist()):
        row = old_df2.iloc[i].to_dict()
        row_s = {col: ("" if pd.isna(v) else str(v)) for col, v in row.items()}
        lookup.setdefault(k, []).append(row_s)
    return lookup


def pop_old_row(lookup: Dict[str, List[Dict[str, str]]], k: str) -> Optional[Dict[str, str]]:
    rows = lookup.get(k)
    if not rows:
        return None
    return rows.pop(0)


def diff_cols_to_bold(old_row: Optional[Dict[str, str]], new_row: Dict[str, str], all_cols: List[str]) -> List[int]:
    # If no matching old row => bold entire row (insert)
    if old_row is None:
        return list(range(len(all_cols)))

    out = []
    for idx, col in enumerate(all_cols):
        ov = old_row.get(col, "")
        nv = new_row.get(col, "")
        if ov != nv:
            out.append(idx)
    return out


def apply_bold_cells(ws: gspread.Worksheet, start_row_1based: int, bold_map: Dict[int, List[int]]):
    """
    bold_map: new_row_offset(0..) -> list of 0-based col indexes to bold
    """
    if not bold_map:
        return

    sheet_id = ws.id
    requests = []

    for row_off, cols0 in bold_map.items():
        r1 = start_row_1based + row_off  # 1-based row number on sheet
        cols_sorted = sorted(set(cols0))
        if not cols_sorted:
            continue

        # group contiguous columns to reduce requests
        blocks: List[Tuple[int, int]] = []
        s = e = cols_sorted[0]
        for c in cols_sorted[1:]:
            if c == e + 1:
                e = c
            else:
                blocks.append((s, e))
                s = e = c
        blocks.append((s, e))

        for c0, c1 in blocks:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": r1 - 1,
                        "endRowIndex": r1,
                        "startColumnIndex": c0,
                        "endColumnIndex": c1 + 1,
                    },
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                    "fields": "userEnteredFormat.textFormat.bold",
                }
            })

    if requests:
        ws.spreadsheet.batch_update({"requests": requests})


def get_last_used_row(ws: gspread.Worksheet) -> int:
    vals = ws.get_all_values()
    return max(len(vals), HEADER_ROW)


def append_per_file_and_bold_changes_row_by_row(
    engine: Engine,
    ws: gspread.Worksheet,
    df_new_all: pd.DataFrame,
    file_names: List[str],
    all_cols: List[str],
    log_table: str,
    log_time_col: str,
    table_kind: str,  # "fabric" or "trim"
    bucket_minutes: int = 2,
) -> int:
    """
    For each file_name:
      - Load previous batch rows from log
      - Build composite key for old and new using your definition
      - Match row-by-row via key
      - Append new rows
      - Bold changed cells vs old row; bold entire row if inserted (no old match)

    Returns appended row count.
    """
    appended = 0
    last_row = get_last_used_row(ws)

    if df_new_all.empty:
        return 0

    df_new_all = df_new_all.copy()
    for c in all_cols:
        if c not in df_new_all.columns:
            df_new_all[c] = ""

    # Decide column mapping for key building (based on df columns)
    mapping = get_key_columns_mapping_for_table(df_new_all, table_kind)

    for fn in file_names:
        fn_norm = str(fn).strip()
        df_new = df_new_all[df_new_all["file_name"].astype(str).str.strip() == fn_norm].copy()
        if df_new.empty:
            continue

        # pull previous version from log
        df_old = fetch_prev_version_from_log(
            engine=engine,
            log_table=log_table,
            time_col=log_time_col,
            file_name=fn_norm,
            data_cols=[c for c in all_cols if c != "LastUpdatedAt"],
            bucket_minutes=bucket_minutes,
        )

        # build keys
        # note: get_key_columns_mapping_for_table may have added virtual empty columns in df_new_all;
        # ensure df_old has them too (so key function works consistently).
        for virtual in ["__COLOR_TRIM_EMPTY__", "__COLOR_GAR_EMPTY__"]:
            if virtual in df_new.columns and virtual not in df_old.columns:
                df_old[virtual] = ""

        new_keys = build_primary_key_series(
            df_new,
            style_col=mapping["style_col"],
            pos_col=mapping["pos_col"],
            page_col=mapping["page_col"],
            grp_col=mapping["grp_col"],
            top_right_col=mapping["top_right_col"],
            color_trim_col=mapping["color_trim_col"],
            color_garment_col=mapping["color_garment_col"],
        )

        old_keys = build_primary_key_series(
            df_old,
            style_col=mapping["style_col"],
            pos_col=mapping["pos_col"],
            page_col=mapping["page_col"],
            grp_col=mapping["grp_col"],
            top_right_col=mapping["top_right_col"],
            color_trim_col=mapping["color_trim_col"],
            color_garment_col=mapping["color_garment_col"],
        ) if not df_old.empty else pd.Series([], dtype=str)

        old_lookup = build_old_lookup_by_key(df_old, old_keys, all_cols)

        # Prepare rows to append
        df_new = df_new.reindex(columns=all_cols)
        rows_new = df_to_rows_for_sheet(df_new, all_cols)
        if not rows_new:
            continue

        start_row_for_append = last_row + 1
        ws.append_rows(rows_new, value_input_option="RAW")

        # Build bold map for appended rows
        bold_map: Dict[int, List[int]] = {}
        for i, (k, row_vals) in enumerate(zip(new_keys.tolist(), rows_new)):
            new_row_dict = {all_cols[j]: ("" if row_vals[j] is None else str(row_vals[j])) for j in range(len(all_cols))}
            old_row = pop_old_row(old_lookup, k)
            cols_to_bold = diff_cols_to_bold(old_row, new_row_dict, all_cols)
            if cols_to_bold:
                bold_map[i] = cols_to_bold

        apply_bold_cells(ws, start_row_for_append, bold_map)

        appended += len(rows_new)
        last_row += len(rows_new)

    return appended


# =========================================================
# MAIN SYNC (REPLACE mode + row-by-row highlight)
# =========================================================

def sync_sql_to_google_sheet_replace_files(
    engine: Engine,
    engine_prod: Engine,
    spreadsheet_id: str,
    service_account_json_path: str,
    file_names_to_replace: List[str],
    fabric_table: str = FABRIC_TABLE,
    trim_table: str = TRIM_TABLE,
    fabric_sheet_name: str = FABRIC_SHEET_NAME,
    trim_sheet_name: str = TRIM_SHEET_NAME,
    file_col: str = "file_name",
) -> None:
    file_names_to_replace = sorted(list({(x or "").strip() for x in file_names_to_replace if x}))
    if not file_names_to_replace:
        print("No file names to replace.")
        return

    # 1) Read SQL main tables
    df_fabric = read_sql_table(engine, fabric_table)
    df_trim_raw = read_sql_table(engine, trim_table)

    # 2) Keep same original text formatting behavior first
    df_trim_raw = convert_sep_to_newline_for_trim_rows(df_trim_raw)

    df_trim_only = filter_trim_rows_only(df_trim_raw)
    df_labels_trim = build_labels_trim_sheet(df_trim_raw)

    # 4) Connect to Google Sheet
    gc = get_gspread_client(service_account_json_path)
    sh = gc.open_by_key(spreadsheet_id)

    ws_fabric = ensure_worksheet(sh, fabric_sheet_name)
    ws_trim = ensure_worksheet(sh, trim_sheet_name)
    ws_labels_trim = ensure_worksheet(sh, LABELS_SHEET_NAME)

    # 5) Headers
    fabric_cols = list(df_fabric.columns) if not df_fabric.empty else [file_col]
    trim_cols = list(df_trim_only.columns) if not df_trim_only.empty else [file_col]
    labels_trim_cols = [
        "file_name",
        "Style",
        "Color Garment",
        "Color Trim",
        "Variable",
        "Position",
        "Code",
        "page",
        "Image",
    ]

    # ===== MARK: APPEND LASTUPDATEDAT COLUMN START =====
    if "LastUpdatedAt" not in fabric_cols:
        fabric_cols.append("LastUpdatedAt")
    if "LastUpdatedAt" not in trim_cols:
        trim_cols.append("LastUpdatedAt")
    if "LastUpdatedAt" not in labels_trim_cols:
        labels_trim_cols.append("LastUpdatedAt")
    # ===== MARK: APPEND LASTUPDATEDAT COLUMN END =====

    if file_col not in fabric_cols:
        fabric_cols = [file_col] + fabric_cols
    if file_col not in trim_cols:
        trim_cols = [file_col] + trim_cols

    write_header_if_needed(ws_fabric, fabric_cols)
    write_header_if_needed(ws_trim, trim_cols)
    write_header_if_needed(ws_labels_trim, labels_trim_cols)

    # 6) DELETE existing sheet rows for these file_names
    del_f = delete_rows_by_file_names(ws_fabric, file_names_to_replace, file_col_name=file_col)
    del_t = delete_rows_by_file_names(ws_trim, file_names_to_replace, file_col_name=file_col)
    del_lt = delete_rows_by_file_names(ws_labels_trim, file_names_to_replace, file_col_name=file_col)
    print(f"Deleted rows: Fabric={del_f}, Trim={del_t}, Labels={del_lt}")

    # 7) Filter SQL rows for these file_names
    df_f = (
        df_fabric[df_fabric[file_col].astype(str).str.strip().isin(file_names_to_replace)].copy()
        if not df_fabric.empty else pd.DataFrame(columns=fabric_cols)
    )

    df_t = (
        df_trim_only[df_trim_only[file_col].astype(str).str.strip().isin(file_names_to_replace)].copy()
        if not df_trim_only.empty else pd.DataFrame(columns=trim_cols)
    )

    df_lt = (
        df_labels_trim[df_labels_trim[file_col].astype(str).str.strip().isin(file_names_to_replace)].copy()
        if not df_labels_trim.empty else pd.DataFrame(columns=labels_trim_cols)
    )
    
    # ===== MARK: FILL LASTUPDATEDAT FOR ALL SHEETS START =====
    push_ts = get_push_timestamp_str()

    if not df_f.empty:
        df_f = append_last_updated_at(df_f, push_ts)

    if not df_t.empty:
        df_t = append_last_updated_at(df_t, push_ts)

    if not df_lt.empty:
        df_lt = append_last_updated_at(df_lt, push_ts)
    # ===== MARK: FILL LASTUPDATEDAT FOR ALL SHEETS END =====
    
    # ===== MARK: TRIM SHEET SORT START =====
    if not df_lt.empty:
        if "page" in df_lt.columns:
            df_lt["page"] = pd.to_numeric(df_lt["page"], errors="coerce")

        sort_cols_lt = [c for c in ["file_name", "page", "Position", "Code"] if c in df_lt.columns]
        if sort_cols_lt:
            df_lt = df_lt.sort_values(by=sort_cols_lt, kind="stable")
    # ===== MARK: TRIM SHEET SORT END =====

    # 8b) Add Image column to Labels by looking up DesignChartImage
    if not df_lt.empty:
        df_lt = add_image_column_to_labels(engine_prod, df_lt)

    # 8) Append per file + bold changes row-by-row for Fabric / TrimAndLabels(TRIM only)
    appended_f = 0
    appended_t = 0

    if not df_f.empty:
        appended_f = append_per_file_and_bold_changes_row_by_row(
            engine=engine,
            ws=ws_fabric,
            df_new_all=df_f,
            file_names=file_names_to_replace,
            all_cols=fabric_cols,
            log_table=FABRIC_LOG_TABLE,
            log_time_col=FABRIC_LOG_TIME_COL,
            table_kind="fabric",
            bucket_minutes=BATCH_BUCKET_MINUTES,
        )
        print(f"  - Fabric: appended {appended_f} row(s) + bolded changes")

    if not df_t.empty:
        appended_t = append_per_file_and_bold_changes_row_by_row(
            engine=engine,
            ws=ws_trim,
            df_new_all=df_t,
            file_names=file_names_to_replace,
            all_cols=trim_cols,
            log_table=TRIM_LOG_TABLE,
            log_time_col=TRIM_LOG_TIME_COL,
            table_kind="trim",
            bucket_minutes=BATCH_BUCKET_MINUTES,
        )
        print(f"  - Trim: appended {appended_t} row(s) + bolded changes")

    # 9) Append sheet Trim (LABELS transformed)
    #    No row-by-row bold here because this is a derived business view, not raw table sync.
    appended_lt = 0
    if not df_lt.empty:
        rows_lt = df_to_rows_for_sheet(df_lt, labels_trim_cols)
        if rows_lt:
            ws_labels_trim.append_rows(rows_lt, value_input_option="RAW")
            appended_lt = len(rows_lt)
            print(f"  - Labels: appended {appended_lt} row(s)")

    # 10) Update last load time
    update_last_load_time(ws_fabric)
    update_last_load_time(ws_trim)
    update_last_load_time(ws_labels_trim)

    print("Done (REPLACE mode + 3 sheets: Fabric, Trim, Labels).")

# =========================================================
# ENTRYPOINT
# =========================================================
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=False)
    args = ap.parse_args()

    # ==========================================
    # HARD CODE TEST FILES (optional)
    # ==========================================
    TEST_FILE_NAMES = [
        # "NKG-CFP879-S-2027_02_27_2026_05_57.pdf"
    ]

    if TEST_FILE_NAMES:
        file_names = TEST_FILE_NAMES
        print("Using HARDCODED files:", file_names)

    elif args.input_dir:
        # lấy file từ folder giống script cũ
        from pathlib import Path

        folder = Path(args.input_dir)
        pdfs = sorted([p.name for p in folder.glob("*.pdf")])

        file_names = pdfs
        print("Using input-dir files:", file_names)

    else:
        raise SystemExit("Provide --input-dir or set TEST_FILE_NAMES.")

    server, database, user, password = read_sql_config(SQL_CONFIG_PATH)
    engine = create_engine_sqlserver(server, database, user, password)

    server_prod, database_prod, user_prod, password_prod = read_sql_config(SQL_CONFIG_PATH, "prod_des")
    engine_prod = create_engine_sqlserver(server_prod, database_prod, user_prod, password_prod)

    sync_sql_to_google_sheet_replace_files(
        engine=engine,
        engine_prod=engine_prod,
        spreadsheet_id=SPREADSHEET_ID,
        service_account_json_path=GSERVICE_ACCOUNT_JSON,
        file_names_to_replace=file_names,
    )