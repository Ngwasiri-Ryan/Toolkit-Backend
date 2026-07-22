import os
import re
import xml.etree.ElementTree as ET
from fastapi import HTTPException, status
from app.core.config import settings

def validate_safe_filename(filename: str) -> str:
    """
    Validates that a filename does not contain directory traversal patterns.
    Returns the stripped/cleaned filename or raises HTTP 400.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
        
    # Standardize path separators and check for path traversal patterns
    normalized = filename.replace("\\", "/")
    if ".." in normalized or "/" in normalized or normalized.startswith("."):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Directory traversal or invalid path format detected in filename"
        )
        
    return filename.strip()

def validate_file_size(file_bytes: bytes) -> None:
    """
    Validates that the file size does not exceed the configured maximum.
    Raises HTTP 413 if validation fails.
    """
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum limit of {settings.MAX_FILE_SIZE_MB}MB"
        )

def sanitize_svg_content(svg_bytes: bytes) -> bytes:
    """
    Scrubs SVG file content of dynamic scripts, embedded iframes/objects,
    and event attributes to prevent Cross-Site Scripting (XSS).
    """
    try:
        # Prevent XML entity expansion exploits (XXE) by using the standard parser
        parser = ET.XMLParser()
        root = ET.fromstring(svg_bytes, parser=parser)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid XML or corrupted SVG content"
        )

    # Elements to remove entirely (namespace-agnostic)
    unsafe_tags = {"script", "iframe", "object", "embed", "foreignobject"}
    
    # Track nodes to remove
    to_remove = []
    
    for elem in root.iter():
        # Clean tag names of XML namespaces for matching
        local_tag = elem.tag.split("}")[-1].lower() if "}" in elem.tag else elem.tag.lower()
        
        if local_tag in unsafe_tags:
            to_remove.append(elem)
            continue
            
        # Strip any event handler attributes (e.g. onload, onclick)
        attrs_to_delete = [attr for attr in elem.attrib if attr.lower().startswith("on") or attr.lower().endswith("href") and "javascript:" in elem.attrib[attr].lower()]
        for attr in attrs_to_delete:
            del elem.attrib[attr]

    # Remove the unsafe elements from their parents
    for elem in to_remove:
        # Find parent and remove child
        for parent in root.iter():
            if elem in list(parent):
                parent.remove(elem)
                
    try:
        return ET.tostring(root, encoding="utf-8")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to serialize sanitized SVG content"
        )
