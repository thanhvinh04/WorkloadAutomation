from __future__ import annotations

import os
import io
from pathlib import Path
from typing import Optional

import pdfplumber
from sqlalchemy import text
from sqlalchemy.engine import Engine
from minio import Minio
from minio.error import S3Error


OUTPUT_DIR = Path(__file__).parent / "output_images"

COLORWAYS_KEYWORD = "COLORWAYS"
COLORWAYS_SEARCH_REGION = (0.5, 0.0, 1.0, 0.15)
TEXT_ABOVE_IMAGE_MAX_DISTANCE = 50
MIN_COLORWAY_IMAGE_AREA = 5000

S3_BUCKET = "fileserver-lk"
S3_PREFIX = "DesignChartImage/"
S3_ENDPOINT = "objstore1584api.superdata.vn"
S3_ACCESS_KEY = "pkR4fkf3OMTRjLjseA0k"
S3_SECRET_KEY = "GHxm0g6s87MoLmx2eGlni1x22gkh9FUVOAUJfPt7"
S3_SECURE = True
S3_PUBLIC_BASE = f"https://{S3_ENDPOINT}"


def _get_s3_client() -> Minio:
    return Minio(
        endpoint=S3_ENDPOINT,
        access_key=S3_ACCESS_KEY,
        secret_key=S3_SECRET_KEY,
        secure=S3_SECURE,
    )


def _upload_image_to_s3(pil_image, style: str, color_garment: str) -> Optional[str]:
    """
    Upload PIL Image to S3 and return public URL.
    """
    try:
        client = _get_s3_client()
        
        if not client.bucket_exists(S3_BUCKET):
            print(f"       [WARN] S3 bucket does not exist: {S3_BUCKET}")
            return None
        
        safe_name = "".join(c for c in color_garment if c.isalnum() or c in (" ", "-", "_")).strip()
        safe_name = safe_name[:50]
        
        filename = f"{style}_{safe_name}.png"
        object_name = f"{S3_PREFIX}{filename}"
        
        image_data = io.BytesIO()
        pil_image.save(image_data, format="PNG")
        image_data.seek(0)
        
        client.put_object(
            bucket_name=S3_BUCKET,
            object_name=object_name,
            data=image_data,
            length=image_data.getbuffer().nbytes,
            content_type="image/png",
        )
        
        url = f"{S3_PUBLIC_BASE}/{S3_BUCKET}/{object_name}"
        
        return url
    
    except S3Error as e:
        print(f"       [WARN] S3Error: {e}")
        return None
    except Exception as e:
        print(f"       [WARN] Failed to upload to S3: {e}")
        return None


def _save_to_database(engine: Engine, image_data: list[dict]) -> bool:
    """
    Save colorway images to DesignChartImage table.
    
    Table structure:
    - Id (auto)
    - DesignChartHeadId (int)
    - ColorGarment (string)
    - Image (string - URL)
    - Page (int, nullable)
    - CreatedAt (datetime2)
    - CreatedBy (string)
    - LastUpdatedAt (datetime2, nullable)
    - LastUpdatedBy (string, nullable)
    """
    from datetime import datetime
    
    try:
        head_id = image_data[0]["design_chart_head_id"] if image_data else None
        
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM DesignChartImage WHERE DesignChartHeadId = :head_id"),
                {"head_id": head_id},
            )
        
        now = datetime.now()
        
        sql_insert = text("""
            INSERT INTO DesignChartImage 
                (DesignChartHeadId, ColorGarment, Image, Page, CreatedAt, CreatedBy, LastUpdatedAt, LastUpdatedBy)
            VALUES 
                (:head_id, :color_garment, :image_url, :page, :created_at, :created_by, :updated_at, :updated_by)
        """)
        
        with engine.begin() as conn:
            for i, data in enumerate(image_data):
                conn.execute(
                    sql_insert,
                    {
                        "head_id": data["design_chart_head_id"],
                        "color_garment": data["color_garment"],
                        "image_url": data["s3_url"],
                        "page": data.get("page_index", 0) + 1,
                        "created_at": now,
                        "created_by": "PDFToSQL",
                        "updated_at": now,
                        "updated_by": "PDFToSQL",
                    },
                )
        
        print(f"       [INFO] Inserted {len(image_data)} rows to DesignChartImage")
        return True
    
    except Exception as e:
        print(f"       [WARN] Failed to insert to DesignChartImage: {e}")
        return False


def find_colorways_pages(pdf_path: str) -> list[int]:
    """
    Find pages with 'Colorways' keyword in top-right corner.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        List of page indices (0-based) that contain Colorways
    """
    colorways_pages = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages):
            w, h = page.width, page.height
            x0 = w * COLORWAYS_SEARCH_REGION[0]
            top = h * COLORWAYS_SEARCH_REGION[1]
            x1 = w * COLORWAYS_SEARCH_REGION[2]
            bottom = h * COLORWAYS_SEARCH_REGION[3]
            
            region = page.crop((x0, top, x1, bottom))
            text_content = region.extract_text() or ""
            
            if COLORWAYS_KEYWORD in text_content.upper():
                colorways_pages.append(idx)
    
    return colorways_pages


def extract_text_above_image(page, img_bbox: tuple) -> Optional[str]:
    """
    Extract text that appears above an image.
    
    Args:
        page: pdfplumber page object
        img_bbox: (x0, top, x1, bottom) tuple
    
    Returns:
        Text found above the image, or None
    """
    x0, top, x1, bottom = img_bbox
    
    search_region_top = max(0, top - TEXT_ABOVE_IMAGE_MAX_DISTANCE)
    search_region = page.crop((x0, search_region_top, x1, top))
    
    words = search_region.extract_words() or []
    
    if not words:
        return None
    
    lines = []
    current_line = []
    current_y = None
    
    for w in sorted(words, key=lambda x: x["top"]):
        if current_y is None:
            current_y = w["top"]
            current_line.append(w["text"])
        elif abs(w["top"] - current_y) <= 5:
            current_line.append(w["text"])
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [w["text"]]
            current_y = w["top"]
    
    if current_line:
        lines.append(" ".join(current_line))
    
    if lines:
        return lines[-1].strip()
    
    return None


def extract_colorway_images_from_page(
    page,
    design_chart_head_id: int,
) -> list[dict]:
    """
    Extract images and their color garment names from a page.
    
    Args:
        page: pdfplumber page object
        design_chart_head_id: ID for mapping
    
    Returns:
        List of dicts with keys: color_garment, image_data, x0 (for sorting)
    """
    results = []
    
    images = page.images
    if not images:
        return results
    
    for img in images:
        x0 = float(img.get("x0", 0))
        top = float(img.get("top", 0))
        x1 = float(img.get("x1", 0))
        bottom = float(img.get("bottom", 0))
        
        area = (x1 - x0) * (bottom - top)
        if area < MIN_COLORWAY_IMAGE_AREA:
            continue
        
        img_bbox = (x0, top, x1, bottom)
        
        color_garment = extract_text_above_image(page, img_bbox)
        
        if color_garment:
            results.append({
                "color_garment": color_garment,
                "x0": x0,
                "top": top,
                "x1": x1,
                "bottom": bottom,
                "design_chart_head_id": design_chart_head_id,
            })
    
    return results


def crop_image_from_page(page, bbox: tuple, resolution: int = 200):
    """
    Crop image from page at given resolution.
    
    Args:
        page: pdfplumber page object
        bbox: (x0, top, x1, bottom)
        resolution: DPI for rendering
    
    Returns:
        PIL Image object
    """
    x0, top, x1, bottom = bbox
    
    page_render = page.to_image(resolution=resolution)
    pil_image = page_render.original
    
    scale = resolution / 72.0
    left_px = int(x0 * scale)
    top_px = int(top * scale)
    right_px = int(x1 * scale)
    bottom_px = int(bottom * scale)
    
    left_px = max(0, left_px)
    top_px = max(0, top_px)
    right_px = min(pil_image.width, right_px)
    bottom_px = min(pil_image.height, bottom_px)
    
    return pil_image.crop((left_px, top_px, right_px, bottom_px))


def save_colorway_images(
    pdf_path: str,
    style: str,
    colorway_data: list[dict],
) -> list[dict]:
    """
    Save colorway images to S3.
    
    Args:
        pdf_path: Path to PDF file
        style: Style name for folder naming
        colorway_data: List of dicts with color_garment and image bbox
    
    Returns:
        List of dicts with color_garment and s3_url
    """
    saved_images = []
    seen_colors = set()
    
    with pdfplumber.open(pdf_path) as pdf:
        for data in colorway_data:
            color_garment = data["color_garment"]
            
            if color_garment.upper() in seen_colors:
                continue
            
            seen_colors.add(color_garment.upper())
            
            page_idx = data.get("page_index", 0)
            if page_idx >= len(pdf.pages):
                continue
            
            page = pdf.pages[page_idx]
            bbox = (data["x0"], data["top"], data["x1"], data["bottom"])
            
            try:
                pil_image = crop_image_from_page(page, bbox)
                
                s3_url = _upload_image_to_s3(pil_image, style, color_garment)
                
                if s3_url:
                    saved_images.append({
                        "color_garment": color_garment,
                        "s3_url": s3_url,
                        "design_chart_head_id": data["design_chart_head_id"],
                    })
                    print(f"       [INFO] Uploaded colorway image: {s3_url}")
                else:
                    print(f"       [WARN] Failed to upload: {color_garment}")
                
            except Exception as e:
                print(f"       [WARN] Failed to process image for {color_garment}: {e}")
    
    return saved_images


def extract_colorways_from_pdf(
    pdf_path: str,
    style: str,
    design_chart_head_id: int,
) -> list[dict]:
    """
    Main function to extract colorway images from PDF.
    
    Args:
        pdf_path: Path to PDF file
        style: Style name
        design_chart_head_id: DesignChartHead ID
    
    Returns:
        List of saved image data dicts
    """
    print(f"       [INFO] Searching for Colorways pages...")
    
    colorways_pages = find_colorways_pages(pdf_path)
    if not colorways_pages:
        print(f"       [WARN] No Colorways pages found")
        return []
    
    print(f"       [INFO] Found {len(colorways_pages)} Colorways page(s)")
    
    all_colorway_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx in colorways_pages:
            page = pdf.pages[page_idx]
            
            colorway_data = extract_colorway_images_from_page(
                page,
                design_chart_head_id,
            )
            
            for data in colorway_data:
                data["page_index"] = page_idx
            
            all_colorway_data.extend(colorway_data)
    
    if not all_colorway_data:
        print(f"       [WARN] No colorway images with text found")
        return []
    
    print(f"       [INFO] Found {len(all_colorway_data)} colorway image(s)")
    
    saved_images = save_colorway_images(pdf_path, style, all_colorway_data)
    
    return saved_images


def process_colorways(
    pdf_path: str,
    style: str,
    design_chart_head_id: int,
    engine: Engine,
) -> list[dict]:
    """
    Process colorways from PDF: extract images, upload to S3, save to DB.
    
    Args:
        pdf_path: Path to PDF file
        style: Style name
        design_chart_head_id: DesignChartHead ID
        engine: SQLAlchemy engine
    
    Returns:
        List of image data with S3 URLs
    """
    saved_images = extract_colorways_from_pdf(pdf_path, style, design_chart_head_id)
    
    if saved_images:
        _save_to_database(engine, saved_images)
    
    return saved_images