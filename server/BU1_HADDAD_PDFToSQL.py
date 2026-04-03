from __future__ import annotations

import os
import re
import json
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import pdfplumber
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# optional camelot
try:
    import camelot  # type: ignore
    HAVE_CAMELOT = True
except Exception:
    HAVE_CAMELOT = False


# =========================================================
# 1) DB CONFIG + ENGINE
# =========================================================
def read_config(path: str) -> tuple[str, str, str, str]:
    with open(path, "r", encoding="utf-8") as f:
        p = json.load(f)["profiles"]["ERP_Import"]
    return p["server"], p["database"], p["user"], p["password"]


def create_engine_sqlserver(server: str, database: str, user: str, password: str) -> Engine:
    conn_str = (
        "DRIVER=ODBC Driver 18 for SQL Server;"
        f"SERVER={server};DATABASE={database};UID={user};PWD={password};TrustServerCertificate=yes;"
    )
    return create_engine(f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}")


# =========================================================
# 2) Helpers
# =========================================================
def sanitize_sheet_name(name: str) -> str:
    name = re.sub(r"[:\\/?*\[\]]", "_", name).strip()
    return (name or "sheet")[:31]


def norm(s):
    if s is None:
        return ""
    if isinstance(s, float) and pd.isna(s):
        return ""
    return re.sub(r"\s+", " ", str(s)).strip().replace("•", "")


def get_joined_cell(row_series, cols_to_join):
    parts = [norm(row_series.get(c, "")) for c in cols_to_join]
    parts = [p for p in parts if p]
    return norm(" ".join(parts))


def read_color_under_position(row_i, col, all_cols, join_width=2):
    """
    Đọc cell theo đúng position column `col`, nếu bị split sang cột kế bên thì ghép.
    """
    try:
        j = all_cols.index(col)
    except ValueError:
        return norm(row_i.get(col, ""))

    span = all_cols[j : j + join_width]
    return get_joined_cell(row_i, span)


def extract_top_right_text(page, x_min_ratio=0.60, y_max_ratio=0.25) -> str:
    W, H = page.width, page.height
    x0 = W * x_min_ratio
    y1 = H * y_max_ratio
    try:
        cropped = page.crop((x0, 0, W, y1))
        text_ = cropped.extract_text() or ""
        return re.sub(r"\s+", " ", text_).strip()
    except Exception:
        words = page.extract_words() or []
        tr = [w for w in words if w.get("x0", 0) >= x0 and w.get("top", 1e9) <= y1]
        tr.sort(key=lambda w: (round(w.get("top", 0), 1), w.get("x0", 0)))
        return re.sub(r"\s+", " ", " ".join(w["text"] for w in tr)).strip()


def extract_top_left_first_line(page, x_max_ratio=0.55, y_max_ratio=0.20, line_tol=2.5) -> str:
    W, H = page.width, page.height
    x1 = W * x_max_ratio
    y1 = H * y_max_ratio

    words = page.extract_words() or []
    if not words:
        return ""

    cand = [w for w in words if w.get("x0", 1e9) <= x1 and w.get("top", 1e9) <= y1]
    if not cand:
        return ""

    cand.sort(key=lambda w: (w.get("top", 1e9), w.get("x0", 1e9)))
    first_top = cand[0].get("top", 0)

    first_line = [w for w in cand if abs(w.get("top", 0) - first_top) <= line_tol]
    first_line.sort(key=lambda w: w.get("x0", 1e9))

    text_ = " ".join(w["text"] for w in first_line if w.get("text"))
    return re.sub(r"\s+", " ", text_).strip()


def is_valid_table_df(df: pd.DataFrame, min_rows=2, min_cols=2, min_nonempty_cells=4) -> bool:
    if df is None or df.empty:
        return False
    if df.shape[0] < min_rows or df.shape[1] < min_cols:
        return False

    nonempty = 0
    for r in range(df.shape[0]):
        for c in range(df.shape[1]):
            v = df.iat[r, c]
            if v is None:
                continue
            if isinstance(v, str):
                v = re.sub(r"\s+", " ", v).strip()
                if not v:
                    continue
            nonempty += 1
    return nonempty >= min_nonempty_cells


def detect_tables_on_page(pdf_path: str, page_idx_1based: int, page) -> Tuple[bool, str, List[pd.DataFrame]]:
    # 1) Camelot lattice
    if HAVE_CAMELOT:
        try:
            tables = camelot.read_pdf(pdf_path, pages=str(page_idx_1based), flavor="lattice")
            dfs: List[pd.DataFrame] = []
            if tables and len(tables) > 0:
                for t in tables:
                    df = t.df.copy().replace({"": None})
                    if is_valid_table_df(df):
                        dfs.append(df)
                if dfs:
                    return True, "camelot", dfs
        except Exception:
            pass

    # 2) pdfplumber fallback
    try:
        tbls = page.extract_tables() or []
        dfs2: List[pd.DataFrame] = []
        for tbl in tbls:
            df = pd.DataFrame(tbl).replace({"": None})
            if is_valid_table_df(df):
                dfs2.append(df)
        if dfs2:
            return True, "pdfplumber", dfs2
    except Exception:
        pass

    return False, "none", []


def find_keywords_in_text(text_: str, keywords: List[str]) -> Tuple[bool, str]:
    if not text_:
        return False, ""
    hits = []
    for kw in keywords:
        if re.search(kw, text_, flags=re.IGNORECASE):
            hits.append(kw)
    return (len(hits) > 0), ", ".join(hits)


def df_to_wide_rows(df: pd.DataFrame, page: int, table_index: int, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    ncols = df.shape[1]
    for r in range(df.shape[0]):
        row_dict: Dict[str, Any] = {"page": page, "table_index": table_index, "row": r, **meta}
        for c in range(ncols):
            v = df.iat[r, c]
            if isinstance(v, str):
                v = re.sub(r"\s+", " ", v).strip()
            row_dict[f"c{c}"] = v if v not in ("", None) else None
        out.append(row_dict)
    return out

def pick_dev_or_vendor(label_to_row, col):
    dev = pick_first_value(label_to_row, ["DEV CODE", "DEV_CODE", "DEV"], col)
    if dev:
        return dev
    return pick_first_value(label_to_row, ["VENDOR REF NO", "VENDOR REF", "VENDOR"], col)

# =========================================================
# 3) PDF -> (detect + tables_wide) IN MEMORY
# =========================================================
def pdf_to_detect_and_tables_wide(
    pdf_path: str,
    filter_groups: List[Dict[str, Any]],
    x_min_ratio=0.60,
    y_max_ratio=0.25,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    detect_rows: List[Dict[str, Any]] = []
    tables_wide_rows: List[Dict[str, Any]] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            top_right_text = extract_top_right_text(page, x_min_ratio=x_min_ratio, y_max_ratio=y_max_ratio)
            top_left_first_line = extract_top_left_first_line(page, x_max_ratio=0.55, y_max_ratio=0.20)

            has_table, method, dfs = detect_tables_on_page(pdf_path, page_idx, page)

            matched_groups: List[Tuple[str, str]] = []
            for g in filter_groups:
                group_name = sanitize_sheet_name(str(g.get("sheet", "group")))
                keywords = g.get("keywords", []) or []
                matched, matched_kws = find_keywords_in_text(top_right_text, keywords)
                if matched:
                    matched_groups.append((group_name, matched_kws))

            if matched_groups and has_table:
                detect_row = {
                    "page": page_idx,
                    "top_left_first_line": top_left_first_line,
                    "top_right_text": top_right_text,
                    "table_method": method,
                    "tables_found": len(dfs),
                    "matched_groups": ", ".join(g for g, _ in matched_groups),
                    "matched_keywords": " | ".join(f"{g}: {kws}" for g, kws in matched_groups),
                }
                detect_rows.append(detect_row)

                meta = {
                    "matched_groups": detect_row["matched_groups"],
                    "matched_keywords": detect_row["matched_keywords"],
                    "top_left_first_line": top_left_first_line,
                    "top_right_text": top_right_text,
                    "table_method": method,
                }

                for t_i, df in enumerate(dfs, start=1):
                    tables_wide_rows.extend(df_to_wide_rows(df, page_idx, t_i, meta))

    return pd.DataFrame(detect_rows), pd.DataFrame(tables_wide_rows)


# =========================================================
# 4) Parser: COLORWAYS row finder
# =========================================================
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


def split_color(s: str) -> tuple[str, str]:
    """
    Fabric rule: 3 ký tự đầu là code, phần còn lại là name
    """
    s = norm(s)
    code = s[:3].strip()
    name = s[3:].strip()
    name = re.sub(r"^[\-\–\—\s]+", "", name).strip()
    return code, name


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


# =========================================================
# 5) Parse TRIM/LABELS
#    - Zip merge ONLY for TRIM group
#    - Use separator " | " instead of newline (SQL-safe)
# =========================================================
def pick_value(label_to_row, label, col):
    if label not in label_to_row:
        return ""
    v = label_to_row[label].get(col, "")
    return norm(v)


def pick_first_value(label_to_row, labels, col):
    for lb in labels:
        key = lb.upper()
        if key in label_to_row:
            return norm(label_to_row[key].get(col, ""))
    return ""


def join_trim_description(internal_code: str, position: str, name: str) -> str:
    parts = [p for p in [norm(internal_code), norm(position), norm(name)] if p]
    return " + ".join(parts)

def parse_one_table_to_trim_rows(df_table: pd.DataFrame, meta: dict) -> list[dict]:
    SEP = " | "  # store in SQL, convert back to newline when writing to Google Sheet if needed

    cols = [c for c in df_table.columns if re.fullmatch(r"c\d+", c)]
    if not cols:
        return []

    # 1) Position row = first row
    header = df_table.iloc[0].to_dict()
    position_cols = []
    for c in cols:
        if c == "c0":
            continue
        pos = norm(header.get(c))
        if pos:
            position_cols.append((c, pos))
    if not position_cols:
        return []

    # 2) Map label rows (c0 is label)
    label_to_row = {}
    for i in range(len(df_table)):
        label = norm(df_table.iloc[i].get("c0", ""))
        if label:
            label_to_row[label.upper()] = df_table.iloc[i]

    # 3) Find COLORWAY(S)
    color_idx, _span_cols = find_colorway_row_and_span(df_table, cols, max_window=6)
    if color_idx is None:
        return []

    out: list[dict] = []
    skip_cols: set[str] = set()

    for col, position in position_cols:
        if col in skip_cols:
            continue

        internal_code = pick_value(label_to_row, "INTERNAL CODE", col)
        name = pick_first_value(label_to_row, ["NAME", "ITEM NAME", "TRIM NAME", "DESCRIPTION"], col)
        variable = pick_first_value(label_to_row, ["VARIABLE", "VAR"], col)
        type_val = pick_first_value(label_to_row, ["TYPE", "Type"], col)

        item_desc = pick_first_value(
            label_to_row,
            ["LOCATION/PLACEMENT", "LOCATION / PLACEMENT", "LOCATION", "PLACEMENT"],
            col
        )
        if not item_desc:
            item_desc = position

        vendor_ref = pick_value(label_to_row, "VENDOR REF NO", col)
        desc = join_trim_description(internal_code, position, " ".join([p for p in [vendor_ref, name] if p]))

        for i in range(color_idx + 1, len(df_table)):
            row_i = df_table.iloc[i]

            # garment color from c0
            color_garment = norm(row_i.get("c0", ""))
            if not is_color_value(color_garment):
                continue

            # trim/label color under current position column
            trim_cell = read_color_under_position(row_i, col, cols, join_width=2)
            trim_cell = norm(trim_cell)

            if not is_color_value(trim_cell):
                continue

            color_combined = SEP.join([x for x in [color_garment, trim_cell] if x])

            out.append({
                "SUPPLIER": "",
                "STYLE_NO": meta.get("style_number", ""),
                "POSITION": position,
                "description": desc,
                "ITEM DESCRIPTION": item_desc,
                "COLOR": color_combined,
                "color TRIM": trim_cell,
                "VARIABLE": variable,
                "TYPE": type_val,
                "DEL": "",
                "date approved": "",
                "Status2": "",
                "page": meta.get("page"),
                "matched_groups": meta.get("matched_groups", ""),
                "top_right_text": meta.get("top_right_text", ""),
            })

    return out

# =========================================================
# 6) Parse FABRIC
# =========================================================
def parse_one_table_to_fabric_rows(df_table: pd.DataFrame, meta: dict) -> list[dict]:
    """
    NEW FABRIC RULE (2026-02)

    Output per (GARMENT_COLOR row under COLORWAYS) x (POSITION column):
      - VENDOR_CODE: blank
      - STYLE_NO: meta["style_number"]
      - GARMENT_COLOR_RAW: c0 (left column)
      - COLOR: first 3 chars of GARMENT_COLOR_RAW
      - FASHION_COLOR: GARMENT_COLOR_RAW without first 3 chars, strip leading " - " if any
      - POSITION: header value for that column
      - INTERNAL_CODE / DEV_CODE / FABRIC_NAME / CONTENT / WEIGHT: from label rows (c0 as label)
      - MATERIAL_CODE: "FB-" + INTERNAL_CODE
      - DESCRIPTION: "Dev code, Name, Content, Weight"
      - COLOR_NAME: cell under current POSITION column (row under COLORWAYS)
      - DEADLINE_APPROVE / EX_FACT: blank
    """
    cols = [c for c in df_table.columns if re.fullmatch(r"c\d+", c)]
    if not cols:
        return []

    # 1) Header row -> positions
    header = df_table.iloc[0].to_dict()
    position_cols: list[tuple[str, str]] = []
    for c in cols:
        if c == "c0":
            continue
        pos = norm(header.get(c))
        if pos:
            position_cols.append((c, pos))
    if not position_cols:
        return []

    # 2) Map label rows (c0 is label)
    label_to_row: dict[str, Any] = {}
    for i in range(len(df_table)):
        label = norm(df_table.iloc[i].get("c0", ""))
        if label:
            label_to_row[label.upper()] = df_table.iloc[i]

    # helper: label variants (vendor PDFs hay viết khác nhau)
    def _pick_first(labels: list[str], col: str) -> str:
        return pick_first_value(label_to_row, labels, col)

    # 3) Find COLORWAY(S) row
    color_idx, _span_cols = find_colorway_row_and_span(df_table, cols, max_window=6)
    if color_idx is None:
        return []

    out: list[dict] = []

    # 4) Iterate rows under COLORWAYS
    for i in range(color_idx + 1, len(df_table)):
        row_i = df_table.iloc[i]

        garment_raw = norm(row_i.get("c0", ""))
        if not is_color_value(garment_raw):
            continue

        garment_code = norm(garment_raw[:3])
        fashion_color = norm(garment_raw[3:])
        fashion_color = re.sub(r"^[\-\–\—\s]+", "", fashion_color).strip()  # strip leading " - "

        for col, position in position_cols:
            color_name = read_color_under_position(row_i, col, cols, join_width=2)
            color_name = norm(color_name)
            if not color_name:
                continue

            internal_code = _pick_first(["INTERNAL CODE", "INTERNAL_CODE", "INTERNAL"], col)
            dev_code = pick_dev_or_vendor(label_to_row, col)

            fabric_name = _pick_first(["NAME", "ITEM NAME", "FABRIC NAME", "DESCRIPTION"], col)
            content = _pick_first(["CONTENT", "FABRIC CONTENT", "COMPOSITION"], col)
            weight = _pick_first(["WEIGHT", "WT", "FABRIC WEIGHT"], col)

            material_code = f"FB-{internal_code}" if internal_code else ""

            # Description: Dev code, Name, Content, Weight (comma-separated)
            desc_parts = [p for p in [dev_code, fabric_name, content, weight] if norm(p)]
            description = ", ".join(desc_parts)

            out.append({
                "VENDOR_CODE": "",
                "STYLE_NO": meta.get("style_number", ""),

                "GARMENT_COLOR_RAW": garment_raw,
                "COLOR": garment_code,
                "FASHION_COLOR": fashion_color,

                "POSITION": position,

                "INTERNAL_CODE": internal_code,
                "MATERIAL_CODE": material_code,

                "DEV_CODE": dev_code,
                "FABRIC_NAME": fabric_name,
                "CONTENT": content,
                "WEIGHT": weight,
                "DESCRIPTION": description,

                "COLOR_NAME": color_name,

                "DEADLINE_APPROVE": "",
                "EX_FACT": "",

                "page": meta.get("page"),
                "matched_groups": meta.get("matched_groups", ""),
                "top_right_text": meta.get("top_right_text", ""),
            })

    return out


# =========================================================
# 7) Build 2 DataFrames từ PDF (Fabric + TrimAndLabels)
# =========================================================
def build_fabric_and_trimlabels_from_pdf(pdf_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    FILTER_GROUPS = [
        {"sheet": "FABRIC", "keywords": [r"\bfabric\b"]},
        {"sheet": "TRIM", "keywords": [r"\btrim\b"]},
        {"sheet": "LABELS", "keywords": [r"\bLabels & packaging\b"]},
    ]

    df_detect, df_wide = pdf_to_detect_and_tables_wide(pdf_path, FILTER_GROUPS)

    if df_detect.empty or df_wide.empty:
        return pd.DataFrame(), pd.DataFrame()

    # map page -> style number (top_left_first_line)
    page_to_style = (
        df_detect.drop_duplicates(subset=["page"])
        .set_index("page")["top_left_first_line"]
        .fillna("")
        .astype(str)
        .to_dict()
    )

    out_fabric: list[dict] = []
    out_trimlabels: list[dict] = []

    for (page, table_index), g in df_wide.groupby(["page", "table_index"], sort=True):
        g = g.sort_values("row")
        page_int = int(page)

        meta = {
            "page": page_int,
            "table_index": int(table_index),
            "style_number": page_to_style.get(page_int, ""),
            "matched_groups": str(g["matched_groups"].iloc[0]) if "matched_groups" in g.columns else "",
            "top_right_text": str(g["top_right_text"].iloc[0]) if "top_right_text" in g.columns else "",
        }

        matched_groups = meta["matched_groups"].upper()

        if "FABRIC" in matched_groups:
            out_fabric.extend(parse_one_table_to_fabric_rows(g, meta))
        if ("TRIM" in matched_groups) or ("LABELS" in matched_groups):
            out_trimlabels.extend(parse_one_table_to_trim_rows(g, meta))

    df_fabric = pd.DataFrame(out_fabric)
    df_trimlabels = pd.DataFrame(out_trimlabels)
    return df_fabric, df_trimlabels


# =========================================================
# 8) SQL: create table + fix columns + delete-by-file + insert
# =========================================================
def _safe_ident(name: str) -> str:
    name = str(name).strip()
    name = re.sub(r"[^0-9a-zA-Z_]+", "_", name)
    return name if name else "col_1"


COLUMN_RENAME_MAP = {
    "STYLE#": "STYLE_NO",
    "STYLE_NUMBER": "STYLE_NO",
    "STYLE": "STYLE_NO",

    "ITEM DESCRIPTION": "ITEM_DESCRIPTION",
    "color TRIM": "COLOR_TRIM",
    "date approved": "DATE_APPROVED",
}


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns=COLUMN_RENAME_MAP)
    return df


def normalize_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    new_cols = [_safe_ident(c) for c in df.columns]
    seen = {}
    final = []
    for c in new_cols:
        seen[c] = seen.get(c, 0) + 1
        final.append(c if seen[c] == 1 else f"{c}_{seen[c]}")
    df.columns = final
    return df


def ensure_schema(engine: Engine, schema: str) -> None:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema or ""):
        raise ValueError(f"Invalid schema name: {schema!r}")

    with engine.begin() as conn:
        conn.execute(text(f"""
            IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = '{schema}')
            BEGIN
                EXEC('CREATE SCHEMA [{schema}]');
            END
        """))


FABRIC_SCHEMA = {
    # ===== NEW FABRIC STRUCTURE (2026-02) =====
    "file_name": "NVARCHAR(255) NOT NULL",

    # Business fields
    "VENDOR_CODE": "NVARCHAR(50) NULL",                 # always blank for now
    "STYLE_NO": "NVARCHAR(100) NULL",
    "GARMENT_COLOR_RAW": "NVARCHAR(200) NULL",          # left column (c0) garment color text
    "COLOR": "NVARCHAR(20) NULL",                       # 3-char garment color code
    "FASHION_COLOR": "NVARCHAR(200) NULL",              # garment color name (garment raw without first 3 chars, strip leading ' - ')
    "POSITION": "NVARCHAR(200) NULL",

    "INTERNAL_CODE": "NVARCHAR(100) NULL",
    "MATERIAL_CODE": "NVARCHAR(120) NULL",              # FB-<INTERNAL_CODE>

    "DEV_CODE": "NVARCHAR(100) NULL",
    "FABRIC_NAME": "NVARCHAR(300) NULL",
    "CONTENT": "NVARCHAR(800) NULL",
    "WEIGHT": "NVARCHAR(120) NULL",
    "DESCRIPTION": "NVARCHAR(1200) NULL",               # "Dev code, Name, Content, Weight"

    "COLOR_NAME": "NVARCHAR(300) NULL",                 # value under Position column

    "DEADLINE_APPROVE": "NVARCHAR(50) NULL",            # blank
    "EX_FACT": "NVARCHAR(50) NULL",                     # blank

    # Meta
    "page": "INT NULL",
    "matched_groups": "NVARCHAR(200) NULL",
    "top_right_text": "NVARCHAR(500) NULL",
}

TRIM_SCHEMA = {
    "file_name": "NVARCHAR(255) NOT NULL",
    "SUPPLIER": "NVARCHAR(200) NULL",
    "STYLE_NO": "NVARCHAR(100) NULL",
    "description": "NVARCHAR(500) NULL",
    "ITEM_DESCRIPTION": "NVARCHAR(300) NULL",
    "COLOR": "NVARCHAR(1000) NULL", # "A | B | C"
    "COLOR_TRIM": "NVARCHAR(100) NULL",
    "VARIABLE": "NVARCHAR(255) NULL",
    "TYPE": "NVARCHAR(255) NULL",
    "DEL": "NVARCHAR(50) NULL",
    "DATE_APPROVED": "NVARCHAR(50) NULL",
    "Status2": "NVARCHAR(50) NULL",
    "page": "INT NULL",
    "matched_groups": "NVARCHAR(200) NULL",
    "top_right_text": "NVARCHAR(500) NULL",
}


def ensure_table_structure(engine: Engine, full_table_name: str, schema_def: dict, strict_drop_extra: bool = False):
    schema, table = full_table_name.split(".", 1)
    ensure_schema(engine, schema)

    cols_sql = ",\n        ".join([f"[{c}] {t}" for c, t in schema_def.items()])

    with engine.begin() as conn:
        conn.execute(text(f"""
            IF OBJECT_ID('{schema}.{table}', 'U') IS NULL
            BEGIN
                CREATE TABLE {schema}.{table} (
                    {cols_sql}
                );
                CREATE INDEX IX_{table}_file_name ON {schema}.{table} (file_name);
            END
        """))

        conn.execute(text(f"""
            IF COL_LENGTH('{schema}.{table}', 'STYLE_NO') IS NULL
               AND COL_LENGTH('{schema}.{table}', 'STYLE_') IS NOT NULL
            BEGIN
                EXEC sp_rename '{schema}.{table}.STYLE_', 'STYLE_NO', 'COLUMN';
            END
        """))

        for col, coltype in schema_def.items():
            conn.execute(text(f"""
                IF COL_LENGTH('{schema}.{table}', '{col}') IS NULL
                BEGIN
                    ALTER TABLE {schema}.{table} ADD [{col}] {coltype};
                END
            """))

        if strict_drop_extra:
            rows = conn.execute(text(f"""
                SELECT c.name
                FROM sys.columns c
                JOIN sys.objects o ON c.object_id = o.object_id
                JOIN sys.schemas s ON o.schema_id = s.schema_id
                WHERE o.type='U' AND o.name = :table AND s.name = :schema
            """), {"table": table, "schema": schema}).fetchall()

            existing_cols = {r[0] for r in rows}
            wanted_cols = set(schema_def.keys())
            extras = sorted(existing_cols - wanted_cols)

            for c in extras:
                conn.execute(text(f"ALTER TABLE {schema}.{table} DROP COLUMN [{c}];"))




# =========================================================
# 8A) POST-PROCESS RULES (apply on final DataFrame before SQL)
# =========================================================
_AS_LABEL_RE = re.compile(r"\bAS\s*LABELS?\b", re.I)
_SEP = " | "

_FIX_DESC_KEYS = [
    "CARE LABEL + UNIVERSAL CARE LABEL",
    'WARNING LABELS + "KEEP AWAY FROM FIRE" WARNING LBL',
    "HANGTAG LOOP + HTL-001 HANGTAG LOOP",
    "SWIFT TACK LOOPS + SWIFT TACK LOOP",
]

# ===== MARK: NEW TRIM MERGE HELPERS START =====
_SPECIAL_INTERNAL_CODES = {"T0345", "T0586", "T0330", "T2041", "T0673", "T0340", "T4080"}

def _extract_internal_code_from_description(desc: Any) -> str:
    """
    description format hiện tại:
      INTERNAL_CODE + POSITION + VENDOR/NAME
    => lấy phần đầu tiên làm internal code
    """
    parts = [p.strip() for p in str(desc or "").split("+")]
    if parts:
        return norm(parts[0]).upper()
    return ""

def _merge_pipe_unique(values: list[Any]) -> str:
    """
    Gộp unique values theo thứ tự xuất hiện, ngăn cách bằng ' | '
    """
    out = []
    seen = set()
    for v in values:
        s = norm(v)
        if not s:
            continue
        # hỗ trợ nếu bản thân cell đã chứa sẵn ' | '
        parts = [norm(x) for x in str(s).split(" | ")]
        for p in parts:
            if p and p not in seen:
                seen.add(p)
                out.append(p)
    return " | ".join(out)
# ===== MARK: NEW TRIM MERGE HELPERS END =====

def _norm_key(s: Any) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", str(s or "").upper()).strip()

def _is_as_label(s: Any) -> bool:
    return bool(_AS_LABEL_RE.search(str(s or "")))

def _extract_position_from_description(desc: Any) -> str:
    """Try to extract POSITION from normal 'internal + position + name' description."""
    parts = [p.strip() for p in str(desc or "").split("+")]
    if len(parts) >= 2:
        return norm(parts[1])
    return ""

def _zipper_prefix_from_position(pos: Any) -> str:
    """Return zipper grouping prefix based on POSITION.

    New rule: remove the trailing keyword (ZIPPER TEETH/TAPE/PULL) and keep the
    left part (prefix). Zipper rows are merged ONLY when this prefix matches.
    Normalization: UPPER + collapse whitespace + strip.
    """
    s = norm(pos)
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s).strip().upper()
    for kw in ("ZIPPER TEETH", "ZIPPER TAPE", "ZIPPER PULL"):
        if kw in s:
            return s.split(kw, 1)[0].strip()
    return ""


def post_process_trimlabels_before_sql(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    df = df.copy()
    df["file_name"] = file_name

    is_trim_page = df["matched_groups"].astype(str).str.contains("TRIM", case=False, na=False)
    is_labels_page = df["matched_groups"].astype(str).str.contains("LABELS", case=False, na=False)

    # RULE OLD #1 -> TRIM only
    if "COLOR_TRIM" in df.columns and "description" in df.columns:
        desc_norm = df["description"].apply(_norm_key)
        key_norms = [_norm_key(k) for k in _FIX_DESC_KEYS]

        mask_fix = is_trim_page & desc_norm.apply(lambda d: any(k in d for k in key_norms))
        fix_df = df[mask_fix]

        drop_idx: list[int] = []
        for _, g in fix_df.groupby(["file_name", "STYLE_NO", "description"], dropna=False):
            if g["COLOR_TRIM"].apply(_is_as_label).all() and len(g) > 1:
                drop_idx.extend(g.index[1:].tolist())
        if drop_idx:
            df = df.drop(index=drop_idx)

    # RULE OLD #2 -> TRIM only
    if {"COLOR_TRIM", "description", "matched_groups"}.issubset(df.columns):
        is_hangtag = df["description"].str.contains("HANGTAG", case=False, na=False)
        is_as = df["COLOR_TRIM"].apply(_is_as_label)

        mask_hp = is_hangtag & is_trim_page & is_as
        hp_df = df[mask_hp].copy()
        if not hp_df.empty:
            hp_df["_pos"] = hp_df["POSITION"] if "POSITION" in hp_df.columns else hp_df["description"].apply(_extract_position_from_description)
            drop_idx: list[int] = []
            for _, g in hp_df.groupby(["file_name", "STYLE_NO", "_pos"], dropna=False):
                if len(g) > 1:
                    drop_idx.extend(g.index[1:].tolist())
            if drop_idx:
                df = df.drop(index=drop_idx)

    # -----------------------------
    # RULE NEW #2 (AND condition):
    # Hangtag (description contains HANGTAG) AND Packing page
    # If COLOR_TRIM is AS LABEL, within same POSITION (same column) -> keep 1 row, no merge
    # Packing detection: matched_groups contains LABELS (Labels & packaging pages)
    # -----------------------------
    if {"COLOR_TRIM", "description", "matched_groups"}.issubset(df.columns):
        is_hangtag = df["description"].str.contains("HANGTAG", case=False, na=False)
        is_trim_page = df["matched_groups"].str.contains("TRIM", case=False, na=False)
        is_as = df["COLOR_TRIM"].apply(_is_as_label)

        mask_hp = is_hangtag & is_trim_page & is_as

        hp_df = df[mask_hp].copy()
        if not hp_df.empty:
            hp_df["_pos"] = hp_df["POSITION"] if "POSITION" in hp_df.columns else hp_df["description"].apply(_extract_position_from_description)
            drop_idx: list[int] = []
            for _, g in hp_df.groupby(["file_name", "STYLE_NO", "_pos"], dropna=False):
                if len(g) > 1:
                    drop_idx.extend(g.index[1:].tolist())
            if drop_idx:
                df = df.drop(index=drop_idx)

    # -----------------------------
    # ZIPPER (UPDATED RULE):
    # - Parse step outputs RAW rows only (no zipper merge at parse time).
    # - Here (right before SQL) we merge zipper components across pages/tables.
    # - Merge key is: (file_name, STYLE_NO, garment_color, POSITION_PREFIX)
    #   where POSITION_PREFIX = text BEFORE 'ZIPPER TEETH/TAPE/PULL' in POSITION.
    # - After prefix matches, we keep the OLD behavior inside that group:
    #   require TEETH + TAPE + at least 1 PULL to create 1 merged row per garment color.
    # -----------------------------
    if {"matched_groups", "COLOR", "COLOR_TRIM", "ITEM_DESCRIPTION"}.issubset(df.columns):
        trim_df = df[df["matched_groups"].str.contains("TRIM", case=False, na=False)].copy()
        if not trim_df.empty:
            # Prefer dedicated POSITION column (added in parse). Fallback to extracting from description for backward-compat.
            if "POSITION" in trim_df.columns:
                trim_df["_pos_u"] = trim_df["POSITION"].apply(lambda x: re.sub(r"\s+", " ", norm(x)).strip().upper())
            else:
                trim_df["_pos_u"] = trim_df["description"].apply(_extract_position_from_description).apply(
                    lambda x: re.sub(r"\s+", " ", norm(x)).strip().upper()
                )

            trim_df["_zip_prefix"] = trim_df["_pos_u"].apply(_zipper_prefix_from_position)

            # Any zipper components at all?
            teeth_rows = trim_df[trim_df["_pos_u"].str.contains("ZIPPER TEETH", na=False)]
            tape_rows  = trim_df[trim_df["_pos_u"].str.contains("ZIPPER TAPE", na=False)]
            pull_rows  = trim_df[trim_df["_pos_u"].str.contains("ZIPPER PULL", na=False)]

            if not teeth_rows.empty and not tape_rows.empty and not pull_rows.empty:
                # group by STYLE_NO to avoid mixing different styles inside a file
                # group by STYLE_NO to avoid mixing different styles inside a file
                for style_no, g_style in trim_df.groupby("STYLE_NO", dropna=False):
                    g_style = g_style.copy()

                    # ===== MARK: SINGLE ZIPPER DETECTION START =====
                    # RULE:
                    # - Không đếm số dòng
                    # - Đếm DISTINCT POSITION của từng component trong cùng STYLE
                    # - Nếu:
                    #     + ZIPPER TEETH có đúng 1 DISTINCT POSITION
                    #     + ZIPPER TAPE  có đúng 1 DISTINCT POSITION
                    #     + ZIPPER PULL  có đúng 1 DISTINCT POSITION
                    #   => coi là chỉ có 1 bộ zipper duy nhất trong STYLE
                    #   => bỏ qua prefix, merge luôn toàn bộ trong STYLE đó
                    # - Nếu bất kỳ component nào có > 1 DISTINCT POSITION
                    #   => coi là có nhiều bộ zipper
                    #   => giữ logic cũ: merge theo prefix

                    g_teeth_all = g_style[g_style["_pos_u"].str.contains("ZIPPER TEETH", na=False)].copy()
                    g_tape_all  = g_style[g_style["_pos_u"].str.contains("ZIPPER TAPE", na=False)].copy()
                    g_pull_all  = g_style[g_style["_pos_u"].str.contains("ZIPPER PULL", na=False)].copy()

                    def _distinct_pos_set(_df: pd.DataFrame) -> set[str]:
                        if _df.empty:
                            return set()
                        return set(
                            _df["_pos_u"]
                            .fillna("")
                            .astype(str)
                            .map(lambda x: re.sub(r"\s+", " ", x).strip().upper())
                            .tolist()
                        )

                    teeth_pos = _distinct_pos_set(g_teeth_all)
                    tape_pos  = _distinct_pos_set(g_tape_all)
                    pull_pos  = _distinct_pos_set(g_pull_all)

                    has_zipper_set = bool(teeth_pos) and bool(tape_pos) and bool(pull_pos)

                    is_single_zipper = (
                        has_zipper_set
                        and len(teeth_pos) == 1
                        and len(tape_pos) == 1
                        and len(pull_pos) == 1
                    )

                    if is_single_zipper:
                        # Ignore prefix completely
                        group_iter = [("GLOBAL", g_style)]
                    else:
                        # Keep existing behavior: split by zipper prefix
                        group_iter = g_style.groupby("_zip_prefix", dropna=False)
                    # ===== MARK: SINGLE ZIPPER DETECTION END =====

                    for prefix, g_pref in group_iter:
                        prefix = norm(prefix).strip().upper()
                        prefix = prefix or "GLOBAL"

                        g_teeth = g_pref[g_pref["_pos_u"].str.contains("ZIPPER TEETH", na=False)]
                        g_tape  = g_pref[g_pref["_pos_u"].str.contains("ZIPPER TAPE", na=False)]
                        g_pull  = g_pref[g_pref["_pos_u"].str.contains("ZIPPER PULL", na=False)]

                        if g_teeth.empty or g_tape.empty or g_pull.empty:
                            continue
                        
                        # helper: parse garment/trim from COLOR "garment | trim"
                        def _split_color(color_val: Any) -> tuple[str, str]:
                            parts = [p.strip() for p in str(color_val or "").split(_SEP)]
                            if len(parts) >= 2:
                                return norm(parts[0]), norm(parts[1])
                            return norm(parts[0]) if parts else "", ""

                        # OLD behavior, but scoped by (STYLE_NO, prefix)
                        tape_by_garment: dict[str, tuple[str, str]] = {}
                        for _, r in g_tape.iterrows():
                            garment, trim = _split_color(r.get("COLOR"))
                            if garment and trim:
                                tape_by_garment[garment] = (trim, r.get("description", ""))

                        pulls_by_garment: dict[str, list[tuple[str, str]]] = {}
                        for _, r in g_pull.iterrows():
                            garment, trim = _split_color(r.get("COLOR"))
                            if garment and trim:
                                pulls_by_garment.setdefault(garment, []).append((trim, r.get("description", "")))

                        teeth_by_garment: dict[str, tuple[str, str]] = {}
                        for _, r in g_teeth.iterrows():
                            garment, _trim = _split_color(r.get("COLOR"))
                            if garment:
                                teeth_by_garment[garment] = (r.get("ITEM_DESCRIPTION", ""), r.get("description", ""))

                        new_rows: list[dict[str, Any]] = []
                        merged_garments: set[str] = set()

                        for garment, (item_desc, desc_teeth) in teeth_by_garment.items():
                            if garment not in tape_by_garment or garment not in pulls_by_garment:
                                continue

                            tape_trim, desc_tape = tape_by_garment[garment]
                            pull_trims = [t for t, _d in pulls_by_garment.get(garment, [])]
                            pull_descs = [_d for _t, _d in pulls_by_garment.get(garment, [])]

                            merged_desc = _SEP.join([d for d in [desc_teeth, desc_tape, *pull_descs] if norm(d)])
                            merged_color = _SEP.join([x for x in [garment, tape_trim, *pull_trims] if norm(x)])

                            new_rows.append({
                                "SUPPLIER": "",
                                "STYLE_NO": style_no,
                                "POSITION": "ZIPPER" if prefix == "GLOBAL" else f"{prefix} ZIPPER",
                                "description": merged_desc,
                                "ITEM_DESCRIPTION": item_desc or "zipper teeth",
                                "COLOR": merged_color,
                                "COLOR_TRIM": tape_trim,
                                "DEL": "",
                                "DATE_APPROVED": "",
                                "Status2": "",
                                "page": None,  # merged across pages/tables
                                "matched_groups": "TRIM",
                                "top_right_text": "",
                                "file_name": file_name,
                            })
                            merged_garments.add(garment)

                        if new_rows and merged_garments:
                            # Drop ONLY original component rows inside this STYLE_NO + PREFIX + GARMENT set
                            g_zip = g_pref[g_pref["_pos_u"].str.contains(r"ZIPPER (TEETH|TAPE|PULL)", na=False, regex=True)].copy()
                            if not g_zip.empty:
                                g_zip["_garment"], g_zip["_trim"] = zip(*g_zip["COLOR"].apply(_split_color))
                                idx_to_drop = g_zip[g_zip["_garment"].isin(merged_garments)].index.tolist()
                                if idx_to_drop:
                                    df = df.drop(index=idx_to_drop, errors="ignore")

                            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    # ===== MARK: RULE NEW #3 - MERGE SPECIAL INTERNAL CODES START =====
    # Rule:
    # - TRIM only
    # - Nếu Internal Code (lấy từ đầu description) thuộc 1 trong list đặc biệt
    #   {T0345, T0586, T0330, T2041, T0673, T0340, T4080}
    # - Gộp thành 1 dòng duy nhất trong cùng file_name + STYLE_NO
    # - COLOR để trống
    # - COLOR_TRIM gộp unique, cách nhau bởi " | "
    if {"matched_groups", "description", "STYLE_NO"}.issubset(df.columns):
        trim_df = df[df["matched_groups"].astype(str).str.contains("TRIM", case=False, na=False)].copy()
        if not trim_df.empty:
            trim_df["_internal_code"] = trim_df["description"].apply(_extract_internal_code_from_description)
            special_df = trim_df[trim_df["_internal_code"].isin(_SPECIAL_INTERNAL_CODES)].copy()

            if not special_df.empty:
                new_rows = []
                idx_to_drop = []

                for (file_name_g, style_no, internal_code), g in special_df.groupby(["file_name", "STYLE_NO", "_internal_code"], dropna=False):
                    idx_to_drop.extend(g.index.tolist())

                    merged_color_trim = _merge_pipe_unique(g["COLOR_TRIM"].tolist()) if "COLOR_TRIM" in g.columns else ""
                    merged_desc = _merge_pipe_unique(g["description"].tolist())
                    merged_item_desc = _merge_pipe_unique(g["ITEM_DESCRIPTION"].tolist()) if "ITEM_DESCRIPTION" in g.columns else ""
                    merged_variable = _merge_pipe_unique(g["VARIABLE"].tolist()) if "VARIABLE" in g.columns else ""
                    merged_type = _merge_pipe_unique(g["TYPE"].tolist()) if "TYPE" in g.columns else ""

                    new_rows.append({
                        "SUPPLIER": "",
                        "STYLE_NO": style_no,
                        "POSITION": "SPECIAL TRIM",
                        "description": merged_desc,
                        "ITEM_DESCRIPTION": merged_item_desc,
                        "COLOR": "",  # theo rule mới: để trống
                        "COLOR_TRIM": merged_color_trim,
                        "VARIABLE": merged_variable,
                        "TYPE": merged_type,
                        "DEL": "",
                        "DATE_APPROVED": "",
                        "Status2": "",
                        "page": None,
                        "matched_groups": "TRIM",
                        "top_right_text": "",
                        "file_name": file_name_g,
                    })

                if idx_to_drop:
                    df = df.drop(index=idx_to_drop, errors="ignore")

                if new_rows:
                    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    # ===== MARK: RULE NEW #3 - MERGE SPECIAL INTERNAL CODES END =====

    # ===== MARK: RULE NEW #4 - MERGE SWOOTH + SNAP START =====
    # Rule:
    # - TRIM only
    # - Các dòng có POSITION chứa 'SWOOTH' hoặc 'SNAP'
    # - Gộp giống zipper nhưng KHÔNG xét prefix
    # - Tức là trong cùng file_name + STYLE_NO + garment_color:
    #     + gom các row SWOOTH/SNAP lại thành 1 row
    #     + COLOR = garment | trim1 | trim2 | ...
    #     + COLOR_TRIM = trim1 | trim2 | ...
    if {"matched_groups", "POSITION", "COLOR", "STYLE_NO"}.issubset(df.columns):
        trim_df = df[df["matched_groups"].astype(str).str.contains("TRIM", case=False, na=False)].copy()
        if not trim_df.empty:
            ss_df = trim_df[
                trim_df["POSITION"].astype(str).str.contains(r"SWOOTH|SNAP", case=False, na=False, regex=True)
            ].copy()

            if not ss_df.empty:
                def _split_color(color_val: Any) -> tuple[str, str]:
                    parts = [p.strip() for p in str(color_val or "").split(" | ")]
                    if len(parts) >= 2:
                        return norm(parts[0]), norm(parts[1])
                    return norm(parts[0]) if parts else "", ""

                ss_df["_garment"], ss_df["_trim"] = zip(*ss_df["COLOR"].apply(_split_color))

                new_rows = []
                idx_to_drop = []

                for (file_name_g, style_no, garment), g in ss_df.groupby(["file_name", "STYLE_NO", "_garment"], dropna=False):
                    garment = norm(garment)
                    if not garment:
                        continue

                    idx_to_drop.extend(g.index.tolist())

                    merged_desc = _merge_pipe_unique(g["description"].tolist())
                    merged_item_desc = _merge_pipe_unique(g["ITEM_DESCRIPTION"].tolist()) if "ITEM_DESCRIPTION" in g.columns else ""
                    merged_color_trim = _merge_pipe_unique(g["_trim"].tolist())
                    merged_variable = _merge_pipe_unique(g["VARIABLE"].tolist()) if "VARIABLE" in g.columns else ""
                    merged_type = _merge_pipe_unique(g["TYPE"].tolist()) if "TYPE" in g.columns else ""

                    merged_color = " | ".join([x for x in [garment, merged_color_trim] if norm(x)])

                    new_rows.append({
                        "SUPPLIER": "",
                        "STYLE_NO": style_no,
                        "POSITION": "SWOOTH | SNAP",
                        "description": merged_desc,
                        "ITEM_DESCRIPTION": merged_item_desc,
                        "COLOR": merged_color,
                        "COLOR_TRIM": merged_color_trim,
                        "VARIABLE": merged_variable,
                        "TYPE": merged_type,
                        "DEL": "",
                        "DATE_APPROVED": "",
                        "Status2": "",
                        "page": None,
                        "matched_groups": "TRIM",
                        "top_right_text": "",
                        "file_name": file_name_g,
                    })

                if idx_to_drop:
                    df = df.drop(index=idx_to_drop, errors="ignore")

                if new_rows:
                    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    # ===== MARK: RULE NEW #4 - MERGE SWOOTH + SNAP END =====

    return df


def delete_then_append_by_file(
    engine: Engine,
    df: pd.DataFrame,
    full_table_name: str,
    pdf_path: str,
    file_col: str = "file_name",
) -> None:
    schema, table = full_table_name.split(".", 1)
    file_name = os.path.basename(pdf_path)

    df = pd.DataFrame() if df is None else df.copy()

    # 1) standardize column names
    df = standardize_columns(df)

    
    # 1.5) ensure file_name early (needed for post-rules grouping)
    df[file_col] = file_name

    # 1.6) POST-RULES: only for TrimAndLabels (keep PDF reading unchanged)
    if not full_table_name.lower().endswith(".fabric"):
        df = post_process_trimlabels_before_sql(df, file_name)
# 2) ensure schema and table structure
    if full_table_name.lower().endswith(".fabric"):
        ensure_table_structure(engine, full_table_name, FABRIC_SCHEMA, strict_drop_extra=False)
    else:
        ensure_table_structure(engine, full_table_name, TRIM_SCHEMA, strict_drop_extra=False)

    # 3) normalize column names (safe SQL col names)
    df = normalize_df_columns(df)

    # 4) ensure file_name
    df[file_col] = file_name

    # 5) delete by file_name then insert
    with engine.begin() as conn:
        conn.execute(
            text(f"DELETE FROM {schema}.{table} WHERE [{file_col}] = :fn"),
            {"fn": file_name},
        )

    if not df.empty:
        df.to_sql(
            name=table,
            con=engine,
            schema=schema,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=100,
        )


def load_pdf_to_sql(
    engine: Engine,
    pdf_path: str,
    fabric_table: str = "dbo.Fabric",
    trimlabels_table: str = "dbo.TrimAndLabels",
    file_col: str = "file_name",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df_fabric, df_trimlabels = build_fabric_and_trimlabels_from_pdf(pdf_path)

    delete_then_append_by_file(engine, df_fabric, fabric_table, pdf_path, file_col=file_col)
    delete_then_append_by_file(engine, df_trimlabels, trimlabels_table, pdf_path, file_col=file_col)

    return df_fabric, df_trimlabels


# =========================================================
# 9) RUN: scan new PDFs not in SQL then load
# =========================================================
def get_loaded_file_names(engine: Engine, fabric_table="dbo.Fabric", trim_table="dbo.TrimAndLabels", file_col="file_name") -> set[str]:
    f_schema, f_table = fabric_table.split(".", 1)
    t_schema, t_table = trim_table.split(".", 1)

    sql = text(f"""
        SELECT DISTINCT [{file_col}] AS fn FROM {f_schema}.{f_table}
        UNION
        SELECT DISTINCT [{file_col}] AS fn FROM {t_schema}.{t_table}
    """)

    with engine.begin() as conn:
        rows = conn.execute(sql).fetchall()

    return {r[0] for r in rows if r[0]}


def scan_new_pdfs_not_in_sql(
    engine: Engine,
    folder_path: str,
    fabric_table="dbo.Fabric",
    trim_table="dbo.TrimAndLabels",
    file_col="file_name",
    recursive: bool = False,
) -> list[str]:
    loaded = get_loaded_file_names(engine, fabric_table, trim_table, file_col)

    folder = Path(folder_path)
    pdf_paths = folder.rglob("*.pdf") if recursive else folder.glob("*.pdf")

    new_files: list[str] = []
    for p in pdf_paths:
        fn = p.name
        if fn not in loaded:
            new_files.append(str(p))

    return sorted(new_files)


def load_new_pdfs_in_folder(
    engine: Engine,
    folder_path: str,
    recursive: bool = False,
    fabric_table="dbo.Fabric",
    trim_table="dbo.TrimAndLabels",
    file_col="file_name",
):
    new_pdfs = scan_new_pdfs_not_in_sql(
        engine,
        folder_path,
        fabric_table=fabric_table,
        trim_table=trim_table,
        file_col=file_col,
        recursive=recursive,
    )

    print(f"Found {len(new_pdfs)} new PDF(s) to load.")
    for pdf_path in new_pdfs:
        print("Loading:", pdf_path)
        load_pdf_to_sql(
            engine,
            pdf_path,
            fabric_table=fabric_table,
            trimlabels_table=trim_table,
            file_col=file_col,
        )

    return new_pdfs


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True, help="Folder contains uploaded PDFs (from API)")
    ap.add_argument("--recursive", action="store_true")
    args = ap.parse_args()

    BASE_DIR = Path(__file__).resolve().parent
    CONFIG_PATH = BASE_DIR / "ServerPassword.json"

    server, database, user, password = read_config(CONFIG_PATH)
    engine = create_engine_sqlserver(server, database, user, password)

    folder = Path(args.input_dir)
    pdf_paths = folder.rglob("*.pdf") if args.recursive else folder.glob("*.pdf")
    pdf_paths = sorted([str(p) for p in pdf_paths])

    print(f"Found {len(pdf_paths)} PDF(s) in input-dir to load (REPLACE mode).")
    for pdf_path in pdf_paths:
        print("Loading (delete+append):", pdf_path)
        load_pdf_to_sql(
            engine,
            pdf_path,
            fabric_table="dbo.Fabric",
            trimlabels_table="dbo.TrimAndLabels",
            file_col="file_name",
        )

# if __name__ == "__main__":
#     import argparse
#     from pathlib import Path

#     # =========================
#     # DEBUG QUICK SWITCH
#     # - Set to a full file path string to load only 1 PDF
#     # - Set to None to use --input-dir like normal
#     # =========================
#     DEBUG_SINGLE_FILE = r"C:\Users\ADMIN\Downloads\NKG-CFP879-S-2027_02_27_2026_05_57.pdf"
#     # DEBUG_SINGLE_FILE = None                 # <- bật lại mode folder

#     ap = argparse.ArgumentParser()
#     ap.add_argument("--input-dir", required=(DEBUG_SINGLE_FILE is None),
#                     help="Folder contains uploaded PDFs (from API)")
#     ap.add_argument("--recursive", action="store_true")
#     args = ap.parse_args()

#     BASE_DIR = Path(__file__).resolve().parent
#     CONFIG_PATH = BASE_DIR / "ServerPassword.json"

#     server, database, user, password = read_config(CONFIG_PATH)
#     engine = create_engine_sqlserver(server, database, user, password)

#     # Build pdf_paths
#     if DEBUG_SINGLE_FILE is not None:
#         pdf_paths = [DEBUG_SINGLE_FILE]
#     else:
#         folder = Path(args.input_dir)
#         pdf_paths = folder.rglob("*.pdf") if args.recursive else folder.glob("*.pdf")
#         pdf_paths = sorted([str(p) for p in pdf_paths])

#     print(f"Found {len(pdf_paths)} PDF(s) to load (REPLACE mode).")
#     for pdf_path in pdf_paths:
#         print("Loading (delete+append):", pdf_path)
#         load_pdf_to_sql(
#             engine,
#             pdf_path,
#             fabric_table="dbo.Fabric",
#             trimlabels_table="dbo.TrimAndLabels",
#             file_col="file_name",
#         )
