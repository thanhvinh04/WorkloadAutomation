from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pdfplumber
from minio import Minio
from minio.error import S3Error


CORNER_THRESHOLD = 0.15
MIN_IMAGE_AREA = 50000
RESOLUTION = 200

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


def _upload_image_to_s3(pil_image, style: str) -> Optional[str]:
    """
    Upload PIL Image directly to S3 and return public URL.
    """
    import io
    
    try:
        client = _get_s3_client()
        
        if not client.bucket_exists(S3_BUCKET):
            print(f"       [WARN] S3 bucket does not exist: {S3_BUCKET}")
            return None
        
        filename = f"{style}.png"
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
        print(f"       [INFO] Uploaded to S3: {url}")
        
        return url
    
    except S3Error as e:
        print(f"       [WARN] S3Error: {e}")
        return None
    except Exception as e:
        print(f"       [WARN] Failed to upload to S3: {e}")
        return None


def _fallback_upload_s3(pdf_path: str, style: str, page) -> Optional[str]:
    """
    Fallback: render full first page and upload to S3.
    """
    try:
        img = page.to_image(resolution=150)
        pil_image = img.original
        
        return _upload_image_to_s3(pil_image, style)
    except Exception as e:
        print(f"       [WARN] Fallback also failed: {e}")
        return None


def is_in_corner(center_x: float, center_y: float) -> bool:
    in_top_left = center_x < CORNER_THRESHOLD and center_y < CORNER_THRESHOLD
    in_top_right = center_x > (1 - CORNER_THRESHOLD) and center_y < CORNER_THRESHOLD
    in_bottom_left = center_x < CORNER_THRESHOLD and center_y > (1 - CORNER_THRESHOLD)
    in_bottom_right = center_x > (1 - CORNER_THRESHOLD) and center_y > (1 - CORNER_THRESHOLD)
    return in_top_left or in_top_right or in_bottom_left or in_bottom_right


def crop_first_page_to_image(
    pdf_path: str,
    style: str,
    upload_to_s3: bool = True,
) -> Optional[str]:
    """
    Extract the main image from the first page of PDF.
    
    Algorithm:
    1. Get all embedded images from first page
    2. Filter out corner/logo images (4 corners + small)
    3. Select the largest remaining image
    4. Crop to PIL Image
    5. Upload directly to S3 (no local save)
    6. Return S3 URL
    
    Args:
        pdf_path: Path to the PDF file
        style: Style name to use for the output filename
        upload_to_s3: Whether to upload to S3 (default True)
    
    Returns:
        S3 URL, or None if failed
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                print(f"       [WARN] PDF has no pages: {pdf_path}")
                return None
            
            page = pdf.pages[0]
            width = page.width
            height = page.height
            
            images = page.images
            if not images:
                print(f"       [WARN] No embedded images found in first page")
                return _fallback_upload_s3(pdf_path, style, page)
            
            valid_images = []
            for img in images:
                x0 = float(img.get("x0", 0))
                top = float(img.get("top", 0))
                x1 = float(img.get("x1", 0))
                bottom = float(img.get("bottom", 0))
                
                area = (x1 - x0) * (bottom - top)
                if area < MIN_IMAGE_AREA:
                    continue
                
                center_x = ((x0 + x1) / 2) / width
                center_y = ((top + bottom) / 2) / height
                
                if is_in_corner(center_x, center_y):
                    continue
                
                valid_images.append({
                    "img": img,
                    "area": area,
                    "x0": x0,
                    "top": top,
                    "x1": x1,
                    "bottom": bottom,
                })
            
            if not valid_images:
                print(f"       [WARN] No valid main image found (all in corners or too small)")
                return _fallback_upload_s3(pdf_path, style, page)
            
            selected = max(valid_images, key=lambda x: x["area"])
            x0 = selected["x0"]
            top = selected["top"]
            x1 = selected["x1"]
            bottom = selected["bottom"]
            
            page_render = page.to_image(resolution=RESOLUTION)
            pil_image = page_render.original
            
            scale = RESOLUTION / 72.0
            left_px = int(x0 * scale)
            top_px = int(top * scale)
            right_px = int(x1 * scale)
            bottom_px = int(bottom * scale)
            
            left_px = max(0, left_px)
            top_px = max(0, top_px)
            right_px = min(pil_image.width, right_px)
            bottom_px = min(pil_image.height, bottom_px)
            
            cropped = pil_image.crop((left_px, top_px, right_px, bottom_px))
            
            return _upload_image_to_s3(cropped, style)
    
    except Exception as e:
        print(f"       [WARN] Failed to extract image: {e}")
        return None


def process_pdf_image(pdf_path: str, style: str) -> Optional[str]:
    """
    Process first page of PDF, upload to S3, return URL.
    
    Args:
        pdf_path: Path to PDF file
        style: Style name extracted from PDF
    
    Returns:
        S3 URL, or None on failure
    """
    if not os.path.exists(pdf_path):
        print(f"       [WARN] PDF not found: {pdf_path}")
        return None
    
    return crop_first_page_to_image(pdf_path, style, upload_to_s3=True)