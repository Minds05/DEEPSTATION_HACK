"""
PDF Reader Utility
Extracts raw text from a PDF file using PyMuPDF (fitz) as primary,
with pdfplumber as fallback for complex layouts.
"""
import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF given as raw bytes.
    Tries PyMuPDF first, falls back to pdfplumber.
    Returns a single cleaned string.
    """
    try:
        return _extract_with_pymupdf(pdf_bytes)
    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed: {e}. Trying pdfplumber...")
        try:
            return _extract_with_pdfplumber(pdf_bytes)
        except Exception as e2:
            logger.error(f"pdfplumber extraction also failed: {e2}")
            raise RuntimeError("Could not extract text from PDF using any available method.") from e2


def _extract_with_pymupdf(pdf_bytes: bytes) -> str:
    """Primary extractor — fast and accurate for standard PDFs."""
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")  # plain text, preserves layout
        if text.strip():
            pages_text.append(text.strip())

    doc.close()

    if not pages_text:
        raise ValueError("PyMuPDF extracted zero text from document.")

    full_text = "\n\n--- PAGE BREAK ---\n\n".join(pages_text)
    return _clean_text(full_text)


def _extract_with_pdfplumber(pdf_bytes: bytes) -> str:
    """Fallback extractor — better for multi-column and table-heavy PDFs."""
    import pdfplumber

    pages_text = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(text.strip())

    if not pages_text:
        raise ValueError("pdfplumber extracted zero text from document.")

    return _clean_text("\n\n".join(pages_text))


def _clean_text(text: str) -> str:
    """Remove excessive whitespace while preserving meaningful line breaks."""
    import re
    # Collapse 3+ newlines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove null bytes and control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Strip trailing whitespace per line
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()
