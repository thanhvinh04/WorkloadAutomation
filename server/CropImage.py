import fitz  # pymupdf
import io
import os
from PIL import Image

pdf_path = r"D:\S27\NKB-DTM494-H-2026_10_28_2025_11_40_20_AM\NKB-DTM494-H-2026_10_28_2025_11_40.pdf"
output_dir = r"C:\Users\ADMIN\Downloads\Image"

os.makedirs(output_dir, exist_ok=True)

pdf = fitz.open(pdf_path)

# Chống lưu trùng cùng 1 ảnh xuất hiện nhiều lần trong PDF
saved_xrefs = set()

# Ngưỡng lọc ảnh nhỏ / logo
MIN_WIDTH = 30
MIN_HEIGHT = 30
MIN_AREA = 30* 30

for page_index in range(len(pdf)):
    page = pdf[page_index]
    page_number = page_index + 1

    images = page.get_images(full=True)

    for img_index, img in enumerate(images):
        xref = img[0]

        # Bỏ qua nếu ảnh này đã được lưu trước đó
        if xref in saved_xrefs:
            continue

        base_image = pdf.extract_image(xref)
        image_bytes = base_image["image"]
        ext = base_image["ext"]  # giữ định dạng gốc: png, jpeg, jpx, ...
        width = base_image["width"]
        height = base_image["height"]

        # Lọc ảnh nhỏ / logo
        if width < MIN_WIDTH or height < MIN_HEIGHT or (width * height) < MIN_AREA:
            print(f"Skip small image: page={page_number}, img={img_index}, size={width}x{height}")
            continue

        # Đặt tên file kèm số trang
        output_path = os.path.join(
            output_dir,
            f"page_{page_number}_image_{img_index}_{width}x{height}.{ext}"
        )

        # Lưu ảnh gốc, không recompress
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        saved_xrefs.add(xref)
        print(f"Saved: {output_path}")