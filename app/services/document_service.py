import os
import tempfile

def convert_docx_to_md(docx_bytes: bytes) -> bytes:
    """Convert a DOCX file to Markdown using pypandoc (lazy import)."""
    import pypandoc  # installed in .venv; linter false-positive on global interpreter
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
        tf.write(docx_bytes)
        docx_path = tf.name
    try:
        output = pypandoc.convert_file(docx_path, "markdown")
        return output.encode("utf-8")
    except Exception as e:
        return f"# Converted Document\n\nFallback. Error: {str(e)}".encode("utf-8")
    finally:
        try:
            os.remove(docx_path)
        except Exception:
            pass

def convert_md_to_pdf(md_bytes: bytes) -> bytes:
    """Convert Markdown to PDF using reportlab (pure Python, Windows-compatible)."""
    import io
    from reportlab.lib.pagesizes import A4  # lazy import: .venv only
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    md_text = md_bytes.decode("utf-8", errors="ignore")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    for line in md_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            story.append(Paragraph(stripped[2:], styles["h1"]))
        elif stripped.startswith("## "):
            story.append(Paragraph(stripped[3:], styles["h2"]))
        elif stripped:
            story.append(Paragraph(stripped, styles["Normal"]))
        else:
            story.append(Spacer(1, 12))

    doc.build(story)
    return buf.getvalue()
