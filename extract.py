"""Text extraction from uploaded resume files (PDF / DOCX)."""
from __future__ import annotations

import io

from pypdf import PdfReader
from docx import Document

PDF_TYPE = "application/pdf"
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ALLOWED_TYPES = {PDF_TYPE, DOCX_TYPE}


def extract_text(content: bytes, content_type: str, filename: str = "") -> str:
    """Return the plain text of a resume given its raw bytes and content type."""
    name = (filename or "").lower()
    if content_type == PDF_TYPE or name.endswith(".pdf"):
        return _extract_pdf(content)
    if content_type == DOCX_TYPE or name.endswith(".docx"):
        return _extract_docx(content)
    raise ValueError("Unsupported file type — only PDF or DOCX are accepted")


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _extract_docx(content: bytes) -> str:
    document = Document(io.BytesIO(content))
    return "\n".join(p.text for p in document.paragraphs).strip()
