from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

import pandas as pd
import pdfplumber

try:
    import camelot  # type: ignore
    HAVE_CAMELOT = True
except Exception:
    HAVE_CAMELOT = False


def norm(v: Any) -> str:
    if v is None:
        return ""
    s = str(v)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def sanitize_sheet_name(s: str) -> str:
    s = norm(s).upper()
    s = re.sub(r"[^A-Z0-9_]+", "_", s)
    return s.strip("_") or "GROUP"


def extract_top_right_text(page, x_min_ratio=0.60, y_max_ratio=0.25, line_tol=3) -> str:
    width = float(page.width)
    height = float(page.height)

    x_min = width * x_min_ratio
    y_max = height * y_max_ratio

    words = page.extract_words() or []
    cand = []
    for w in words:
        x0 = float(w.get("x0", 0))
        top = float(w.get("top", 0))
        if x0 >= x_min and top <= y_max:
            cand.append(w)

    if not cand:
        return ""

    cand.sort(key=lambda w: (w.get("top", 1e9), w.get("x0", 1e9)))

    all_lines = []
    current_top = None
    current_line = []
    
    for w in cand:
        top = w.get("top", 0)
        if current_top is None:
            current_top = top
            current_line = [w]
        elif abs(top - current_top) <= line_tol:
            current_line.append(w)
        else:
            current_line.sort(key=lambda w: w.get("x0", 1e9))
            line_text = " ".join(w["text"] for w in current_line if w.get("text"))
            if line_text:
                all_lines.append(line_text)
            current_top = top
            current_line = [w]
    
    if current_line:
        current_line.sort(key=lambda w: w.get("x0", 1e9))
        line_text = " ".join(w["text"] for w in current_line if w.get("text"))
        if line_text:
            all_lines.append(line_text)

    return " | ".join(all_lines[:2])


def extract_top_left_first_line(page, x_max_ratio=0.55, y_max_ratio=0.20, line_tol=3) -> str:
    width = float(page.width)
    height = float(page.height)

    x_max = width * x_max_ratio
    y_max = height * y_max_ratio

    words = page.extract_words() or []
    cand = []
    for w in words:
        x0 = float(w.get("x0", 0))
        top = float(w.get("top", 0))
        if x0 <= x_max and top <= y_max:
            cand.append(w)

    if not cand:
        return ""

    cand.sort(key=lambda w: (w.get("top", 1e9), w.get("x0", 1e9)))
    first_top = cand[0].get("top", 0)

    first_line = [w for w in cand if abs(float(w.get("top", 0)) - float(first_top)) <= line_tol]
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


def find_keywords_in_page(page, keywords: List[str]) -> Tuple[bool, str]:
    text = page.extract_text() or ""
    return find_keywords_in_text(text, keywords)


def df_to_wide_rows(df: pd.DataFrame, page: int, table_index: int, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    ncols = df.shape[1]

    for r in range(df.shape[0]):
        row_dict: Dict[str, Any] = {
            "page": page,
            "table_index": table_index,
            "row": r,
            **meta,
        }
        for c in range(ncols):
            v = df.iat[r, c]
            if isinstance(v, str):
                v = re.sub(r"\s+", " ", v).strip()
            row_dict[f"c{c}"] = v if v not in ("", None) else None
        out.append(row_dict)

    return out


def pdf_to_detect_and_tables_wide(
    pdf_path: str,
    filter_groups: List[Dict[str, Any]],
    x_min_ratio=0.60,
    y_max_ratio=0.50,
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