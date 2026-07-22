import io
from PIL import Image

def load_image(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes))

def export_image(image: Image.Image, format_str: str = "PNG", quality: int = 85) -> bytes:
    output = io.BytesIO()
    # Handle RGBA to RGB conversion for JPEG format saving
    if format_str.upper() in ("JPEG", "JPG") and image.mode == "RGBA":
        image = image.convert("RGB")
    image.save(output, format=format_str.upper(), quality=quality)
    return output.getvalue()

def compress_image(image_bytes: bytes, quality: int = 70) -> bytes:
    img = load_image(image_bytes)
    return export_image(img, format_str=img.format or "JPEG", quality=quality)

def resize_image(image_bytes: bytes, width: int, height: int) -> bytes:
    img = load_image(image_bytes)
    resized = img.resize((width, height), Image.Resampling.LANCZOS)
    return export_image(resized, format_str=img.format or "PNG")

def crop_image(image_bytes: bytes, left: int, top: int, right: int, bottom: int) -> bytes:
    img = load_image(image_bytes)
    cropped = img.crop((left, top, right, bottom))
    return export_image(cropped, format_str=img.format or "PNG")

def grayscale_image(image_bytes: bytes) -> bytes:
    img = load_image(image_bytes)
    gray = img.convert("L")
    return export_image(gray, format_str=img.format or "PNG")

def convert_image_format(image_bytes: bytes, target_format: str) -> bytes:
    img = load_image(image_bytes)
    return export_image(img, format_str=target_format)
