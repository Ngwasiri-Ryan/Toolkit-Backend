import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader, PdfWriter
from app.main import app

client = TestClient(app)

def create_mock_image(format_str="PNG") -> bytes:
    img = Image.new("RGB", (100, 100), color="red")
    out = io.BytesIO()
    img.save(out, format=format_str)
    return out.getvalue()

def create_mock_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

def test_image_compress_and_resize():
    img_data = create_mock_image("JPEG")
    # Test Compress
    response = client.post("/api/v1/images/compress?quality=50", files={"file": ("test.jpg", img_data, "image/jpeg")})
    assert response.status_code == 200
    
    # Test Resize
    response = client.post("/api/v1/images/resize?width=50&height=50", files={"file": ("test.png", img_data, "image/png")})
    assert response.status_code == 200
    resized_img = Image.open(io.BytesIO(response.content))
    assert resized_img.size == (50, 50)

def test_pdf_merge_and_split():
    pdf1 = create_mock_pdf()
    pdf2 = create_mock_pdf()
    
    # Test Merge
    response = client.post(
        "/api/v1/documents/merge-pdf", 
        files=[("files", ("1.pdf", pdf1, "application/pdf")), ("files", ("2.pdf", pdf2, "application/pdf"))]
    )
    assert response.status_code == 200
    merged_pdf = PdfReader(io.BytesIO(response.content))
    assert len(merged_pdf.pages) == 2

    # Test Split
    response = client.post("/api/v1/documents/split-pdf?start_page=1&end_page=1", files={"file": ("merged.pdf", response.content, "application/pdf")})
    assert response.status_code == 200
    split_pdf = PdfReader(io.BytesIO(response.content))
    assert len(split_pdf.pages) == 1

def test_developer_utilities():
    # Base64 Encode
    response = client.post("/api/v1/utilities/base64/encode", json="Hello")
    assert response.status_code == 200
    assert response.json()["encoded"] == "SGVsbG8="

    # Base64 Decode
    response = client.post("/api/v1/utilities/base64/decode", json="SGVsbG8=")
    assert response.status_code == 200
    assert response.json()["decoded"] == "Hello"

    # Hashing
    response = client.post("/api/v1/utilities/hash?algo=md5", json="Hello")
    assert response.status_code == 200
    assert "hash" in response.json()

    # QR Code
    response = client.get("/api/v1/utilities/qr-generate?text=hello")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
