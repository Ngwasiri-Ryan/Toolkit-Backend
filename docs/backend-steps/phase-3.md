# Phase 3: Synchronous Processing Services

## 1. Overview
Phase 3 implements fast synchronous processing operations (<5s response times) directly in-process, covering image manipulation, PDF document merging/splitting, developer utilities, and styled QR Code generation.

---

## 2. Implemented Services & Endpoints

### 2.1 Image Processing (`app/routers/images.py` & `app/services/image_service.py`)
- **Compress & Resize**: Uses Pillow to optimize JPEG/PNG quality and perform dimension scaling.
- **Format Conversion**: Instant conversion between PNG, JPEG, WEBP, and BMP.

### 2.2 PDF Document Manipulation (`app/routers/documents.py` & `app/services/pdf_service.py`)
- **PDF Merge**: Combines multiple PDF file uploads into a single compiled document using `pypdf`.
- **PDF Split**: Extracts individual pages or custom ranges into downloadable PDF files.

### 2.3 Developer Utilities (`app/routers/general.py` & `app/services/utility_service.py`)
- Base64 encoder/decoder, JSON formatter/validator, CSV-to-JSON converter, Datetime/Epoch timestamp converter, and color code converter (HEX <-> RGB <-> HSL).

### 2.4 Styled QR Code Generator (`app/services/qr_service.py`)
- Generates high-resolution vector and raster QR codes with custom foreground/background colors and error correction level H.

---

## 3. Verification & Tests (`app/tests/test_phase3.py`)
- `test_image_compress_and_resize`: Tests Pillow compression and pixel dimension scaling.
- `test_pdf_merge_and_split`: Verifies `pypdf` page parsing and compilation.
- `test_developer_utilities`: Validates JSON formatting and Base64 routines.
