import io
from pypdf import PdfReader, PdfWriter

def merge_pdfs(pdf_contents: list[bytes]) -> bytes:
    writer = PdfWriter()
    for content in pdf_contents:
        reader = PdfReader(io.BytesIO(content))
        for page in reader.pages:
            writer.add_page(page)
            
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()

def split_pdf(pdf_bytes: bytes, start_page: int, end_page: int) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    
    total_pages = len(reader.pages)
    # Convert to 0-indexed bounds checking
    start = max(0, start_page - 1)
    end = min(total_pages, end_page)
    
    for idx in range(start, end):
        writer.add_page(reader.pages[idx])
        
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
