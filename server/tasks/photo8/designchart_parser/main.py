from pathlib import Path

from .parsers import parse_head_from_pdf
from .repositories import (
    make_sql_server_engine,
    replace_fabric_by_head_id,
    replace_trim_by_head_id,
    replace_labels_by_head_id,
    replace_artwork_by_head_id,
    upsert_design_chart_head,
    delete_detail_rows_by_head_id,
    reseed_head_table,
    update_design_chart_head_image,
)
from .services import build_all_detail_tables_from_pdf_v2
from .image_processor import process_pdf_image
from .colorways_extractor import process_colorways


def import_detail_tables_to_sql(
    pdf_path: str,
    design_chart_head_id: int | None = None,
    reseed_id: int | None = None,
    config_path: Path | None = None,
    profile_name: str = "prod_des",
):
    if config_path is None:
        config_path = Path(__file__).parent.parent / "ServerPassword.json"
    
    print(f"[1/8] Connecting to SQL Server...")
    engine = make_sql_server_engine(
        json_path=config_path,
        profile_name=profile_name
    )
    
    if reseed_id is not None:
        print(f"       Reseeding ID to {reseed_id}...")
        reseed_head_table(engine, reseed_id)
    
    print(f"[2/8] Parsing HEAD from PDF...")
    head_data = parse_head_from_pdf(pdf_path)
    print(f"       - Style: {head_data.get('Style', '')}")
    print(f"       - Name: {head_data.get('Name', '')}")
    
    print(f"[3/8] Upserting HEAD to database...")
    head_id, is_update = upsert_design_chart_head(engine, head_data)
    print(f"       - DesignChartHeadId: {head_id}")
    print(f"       - Is update: {is_update}")
    
    print(f"[4/8] Parsing FABRIC/TRIM/LABELS/ARTWORK tables...")
    df_fabric, df_trim, df_labels, df_artwork = build_all_detail_tables_from_pdf_v2(
        pdf_path=pdf_path,
        design_chart_head_id=head_id,
    )
    print(f"       - Fabric rows: {len(df_fabric)}")
    print(f"       - Trim rows: {len(df_trim)}")
    print(f"       - Labels rows: {len(df_labels)}")
    print(f"       - Artwork rows: {len(df_artwork)}")

    if is_update:
        print(f"[5/8] Deleting existing detail rows (same file)...")
        delete_detail_rows_by_head_id(engine, head_id)
    else:
        print(f"[5/8] Skipping delete (new file)...")
    
    print(f"[6/8] Inserting FABRIC data...")
    replace_fabric_by_head_id(engine, head_id, df_fabric)
    
    print(f"[7/8] Inserting TRIM and LABELS data...")
    replace_trim_by_head_id(engine, head_id, df_trim)
    replace_labels_by_head_id(engine, head_id, df_labels)
    
    print(f"[8/8] Inserting ARTWORK data...")
    replace_artwork_by_head_id(engine, head_id, df_artwork)

    style = head_data.get("Style", "")
    if style:
        print(f"[9/9] Processing first page image...")
        image_path = process_pdf_image(pdf_path, style)
        if image_path:
            update_design_chart_head_image(engine, head_id, image_path)
            print(f"       - Image saved: {image_path}")
        else:
            print(f"       - Image processing skipped (failed)")
        
        print(f"[10/10] Extracting Colorways images...")
        colorway_images = process_colorways(pdf_path, style, head_id, engine)
        print(f"       - Colorway images: {len(colorway_images)}")

    return head_id, df_fabric, df_trim, df_labels, df_artwork


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--reseed-id", type=int, default=None, help="Reseed head ID to this value")
    parser.add_argument("--config", type=str, default=None, help="Path to ServerPassword.json")
    parser.add_argument("--profile", type=str, default="prod_des", help="Profile name in config")
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None

    print("=" * 50)
    print("Starting import process...")
    print("=" * 50)

    head_id, df_fabric, df_trim, df_labels, df_artwork = import_detail_tables_to_sql(
        pdf_path=args.pdf,
        reseed_id=args.reseed_id,
        config_path=config_path,
        profile_name=args.profile,
    )