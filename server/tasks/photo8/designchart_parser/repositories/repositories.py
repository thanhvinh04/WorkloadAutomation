from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy.engine import Engine

from ..config.config import FABRIC_COLUMNS, TRIM_COLUMNS, LABELS_COLUMNS
from ..core.parser_common import ensure_dataframe_columns
from ..parsers.artwork import ARTWORK_COLUMNS


def _clean_value(v: Any) -> Any:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, str):
        v = v.strip()
        v_upper = v.upper()
        if v_upper in ("NAN", "NONE", "", "NULL") or "NAN" in v_upper:
            return None
        if len(v) > 400:
            v = v[:400]
        return v
    return str(v) if v else None


def _replace_by_head_id(
    engine: Engine,
    table_name: str,
    df: pd.DataFrame,
    design_chart_head_id: int,
    ordered_columns: list[str],
):
    df = ensure_dataframe_columns(df, ordered_columns)

    for col in df.columns:
        df[col] = df[col].apply(_clean_value)

    with engine.begin() as conn:
        conn.exec_driver_sql(
            f"DELETE FROM {table_name} WHERE DesignChartHeadId = ?",
            (design_chart_head_id,),
        )

    if not df.empty:
        df = df.where(pd.notnull(df), None)
        
        success = 0
        failed = 0
        failed_rows = []
        for i, row in df.iterrows():
            try:
                row.to_frame().T.to_sql(
                    name=table_name,
                    con=engine,
                    if_exists="append",
                    index=False,
                )
                success += 1
            except Exception as e:
                failed += 1
                err_msg = str(e)
                if "SQL Server" in err_msg:
                    import re
                    match = re.search(r'\[SQL Server\]([^[]+)', err_msg)
                    if match:
                        err_msg = match.group(1).strip()[:100]
                row_name = str(row.get("Name", "unknown"))[:30] if row.get("Name") else "unknown"
                failed_rows.append({
                    "index": i,
                    "name": row_name,
                    "error": err_msg,
                })
        
        for fr in failed_rows[:10]:
            print(f"  Warning: Failed row {fr['index']}: {fr['name']} - {fr['error']}")
        
        print(f"  Inserted {success} rows, failed {failed} rows")


def replace_fabric_by_head_id(
    engine: Engine,
    design_chart_head_id: int,
    df_fabric: pd.DataFrame,
    table_name: str = "DesignChartFabric",
):
    _replace_by_head_id(
        engine=engine,
        table_name=table_name,
        df=df_fabric,
        design_chart_head_id=design_chart_head_id,
        ordered_columns=FABRIC_COLUMNS,
    )


def replace_trim_by_head_id(
    engine: Engine,
    design_chart_head_id: int,
    df_trim: pd.DataFrame,
    table_name: str = "DesignChartTrim",
):
    _replace_by_head_id(
        engine=engine,
        table_name=table_name,
        df=df_trim,
        design_chart_head_id=design_chart_head_id,
        ordered_columns=TRIM_COLUMNS,
    )


def replace_labels_by_head_id(
    engine: Engine,
    design_chart_head_id: int,
    df_labels: pd.DataFrame,
    table_name: str = "DesignChartLabels",
):
    _replace_by_head_id(
        engine=engine,
        table_name=table_name,
        df=df_labels,
        design_chart_head_id=design_chart_head_id,
        ordered_columns=LABELS_COLUMNS,
    )


def replace_artwork_by_head_id(
    engine: Engine,
    design_chart_head_id: int,
    df_artwork: pd.DataFrame,
    table_name: str = "DesignChartArtWork",
):
    _replace_by_head_id(
        engine=engine,
        table_name=table_name,
        df=df_artwork,
        design_chart_head_id=design_chart_head_id,
        ordered_columns=ARTWORK_COLUMNS,
    )


from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.engine import Engine


VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def vn_now():
    return datetime.now(VN_TZ).replace(tzinfo=None)


def upsert_design_chart_head(
    engine: Engine,
    head_data: dict,
    created_by: str = "PDFToSQL",
    last_updated_by: str = "PDFToSQL",
) -> tuple[int, bool]:
    """
    Logic:
    - If File_name exists -> update Head and return (Id, True)
    - If not exists -> insert new and return (new_Id, False)
    """
    now_vn = vn_now()

    sql_find = text("""
        SELECT TOP 1 Id
        FROM DesignChartHead
        WHERE Style = :style
    """)

    sql_update = text("""
        UPDATE DesignChartHead
        SET
            CustomerId = :CustomerId,
            Style = :Style,
            Name = :Name,
            Season = :Season,
            Year = :Year,
            Brand = :Brand,
            Gender = :Gender,
            Player = :Player,
            Size = :Size,
            TPCreatedBy = :TPCreatedBy,
            SpecBy = :SpecBy,
            CreateDate = :CreateDate,
            Image = :Image,
            LastUpdatedAt = :LastUpdatedAt,
            LastUpdatedBy = :LastUpdatedBy
        WHERE Id = :Id
    """)

    sql_insert = text("""
        INSERT INTO DesignChartHead (
            File_name,
            CustomerId,
            Style,
            Name,
            Season,
            Year,
            Brand,
            Gender,
            Player,
            Size,
            TPCreatedBy,
            SpecBy,
            CreateDate,
            Image,
            CreatedAt,
            CreatedBy,
            LastUpdatedAt,
            LastUpdatedBy
        )
        OUTPUT INSERTED.Id
        VALUES (
            :File_name,
            :CustomerId,
            :Style,
            :Name,
            :Season,
            :Year,
            :Brand,
            :Gender,
            :Player,
            :Size,
            :TPCreatedBy,
            :SpecBy,
            :CreateDate,
            :Image,
            :CreatedAt,
            :CreatedBy,
            :LastUpdatedAt,
            :LastUpdatedBy
        )
    """)

    params = {
        "File_name": head_data.get("File_name"),
        "CustomerId": head_data.get("CustomerId", "HA"),
        "Style": head_data.get("Style", ""),
        "Name": head_data.get("Name", ""),
        "Season": head_data.get("Season", ""),
        "Year": head_data.get("Year", ""),
        "Brand": head_data.get("Brand", ""),
        "Gender": head_data.get("Gender", ""),
        "Player": head_data.get("Player", ""),
        "Size": head_data.get("Size", ""),
        "TPCreatedBy": head_data.get("TPCreatedBy", ""),
        "SpecBy": head_data.get("SpecBy", ""),
        "CreateDate": head_data.get("CreateDate", ""),
        "Image": head_data.get("Image"),
        "CreatedAt": now_vn,
        "CreatedBy": created_by,
        "LastUpdatedAt": now_vn,
        "LastUpdatedBy": last_updated_by,
    }

    with engine.begin() as conn:
        existing_id = conn.execute(
            sql_find,
            {"style": params["Style"]},
        ).scalar()

        if existing_id:
            conn.execute(
                sql_update,
                {
                    **params,
                    "Id": existing_id,
                },
            )
            return int(existing_id), True

        new_id = conn.execute(sql_insert, params).scalar()
        return int(new_id), False


def delete_detail_rows_by_head_id(engine: Engine, design_chart_head_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM DesignChartImage WHERE DesignChartHeadId = :id"),
            {"id": design_chart_head_id},
        )
        conn.execute(
            text("DELETE FROM DesignChartArtWork WHERE DesignChartHeadId = :id"),
            {"id": design_chart_head_id},
        )
        conn.execute(
            text("DELETE FROM DesignChartLabels WHERE DesignChartHeadId = :id"),
            {"id": design_chart_head_id},
        )
        conn.execute(
            text("DELETE FROM DesignChartTrim WHERE DesignChartHeadId = :id"),
            {"id": design_chart_head_id},
        )
        conn.execute(
            text("DELETE FROM DesignChartFabric WHERE DesignChartHeadId = :id"),
            {"id": design_chart_head_id},
        )
        conn.execute(
            text("DELETE FROM DesignChartBOM WHERE DesignChartHeadId = :id"),
            {"id": design_chart_head_id},
        )


def reseed_head_table(engine: Engine, target_id: int = 1) -> None:
    pass


def update_design_chart_head_image(
    engine: Engine,
    design_chart_head_id: int,
    image_path: str,
) -> bool:
    """
    Update the Image field in DesignChartHead.
    
    Args:
        engine: SQLAlchemy engine
        design_chart_head_id: The ID of the DesignChartHead record
        image_path: Path to the image file (local path)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        sql = text("""
            UPDATE DesignChartHead
            SET Image = :image_path, LastUpdatedAt = :LastUpdatedAt
            WHERE Id = :Id
        """)
        
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "image_path": image_path,
                    "LastUpdatedAt": vn_now(),
                    "Id": design_chart_head_id,
                },
            )
        return True
    except Exception as e:
        print(f"       [WARN] Failed to update Image field: {e}")
        return False