"""
PDF utility functions for rental agreement analysis.
Extracts text from PDF documents for legal analysis.
"""
import io
from typing import Optional
import pdfplumber
import PyPDF2


def extract_text_pdfplumber(pdf_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber (better for structured PDFs)."""
    text_parts = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        return ""
    return "\n".join(text_parts)


def extract_text_pypdf2(pdf_bytes: bytes) -> str:
    """Extract text from PDF using PyPDF2 (fallback)."""
    text_parts = []
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    except Exception as e:
        return ""
    return "\n".join(text_parts)


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF with fallback strategy.
    Tries pdfplumber first, falls back to PyPDF2.
    """
    text = extract_text_pdfplumber(pdf_bytes)
    if not text.strip():
        text = extract_text_pypdf2(pdf_bytes)
    return text.strip()


def get_pdf_metadata(pdf_bytes: bytes) -> dict:
    """Extract metadata from PDF (author, creation date, etc.)."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        meta = reader.metadata or {}
        return {
            "author": meta.get("/Author", None),
            "creator": meta.get("/Creator", None),
            "created": str(meta.get("/CreationDate", None)),
            "pages": len(reader.pages),
        }
    except Exception:
        return {}
