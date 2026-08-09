"""Optimize service: compress, repair, OCR and PDF/A normalisation."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import fitz
from pypdf import PdfWriter

from .common import (
    ToolError,
    create_text_pdf,
    read_pdf,
    require_files,
    require_pdf,
    write_pdf,
)


def compress_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Rewrite the PDF with garbage collection + deflate to shrink it."""

    require_files(files)
    require_pdf(files[0])
    output = output_dir / "compressed.pdf"
    source_size = files[0].stat().st_size
    doc = fitz.open(str(files[0]))
    if doc.needs_pass:
        password = opts.get("password") or ""
        if not doc.authenticate(password):
            raise ToolError("The password did not unlock this PDF.")
    doc.save(str(output), garbage=4, deflate=True, clean=True)
    doc.close()
    target_size = output.stat().st_size
    change = source_size - target_size
    percent = (change / source_size * 100) if source_size else 0
    message = (f"Compressed PDF by {percent:.1f}%." if change > 0
               else "Optimized and cleaned the PDF structure.")
    return output, message, []


def repair_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Rebuild a damaged PDF, falling back to a pypdf page copy."""

    require_files(files)
    output = output_dir / "repaired.pdf"
    try:
        doc = fitz.open(str(files[0]))
        if doc.needs_pass:
            password = opts.get("password") or ""
            if not doc.authenticate(password):
                raise ToolError("The password did not unlock this PDF.")
        doc.save(str(output), garbage=4, deflate=True, clean=True)
        doc.close()
    except Exception:
        reader = read_pdf(files[0], opts.get("password") or None)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        write_pdf(writer, output)
    return output, "Rebuilt the PDF structure into a clean file.", []


def ocr_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Extract selectable text, using Tesseract OCR when it is available."""

    require_files(files)
    require_pdf(files[0])
    language = opts.get("language") or "eng"
    details: List[str] = []
    pages: List[str] = []
    doc = fitz.open(str(files[0]))
    if doc.needs_pass:
        password = opts.get("password") or ""
        if not doc.authenticate(password):
            raise ToolError("The password did not unlock this PDF.")
    tesseract_available = shutil.which("tesseract") is not None
    for page in doc:
        text = page.get_text("text").strip()
        if not text and tesseract_available and hasattr(page, "get_textpage_ocr"):
            try:
                text_page = page.get_textpage_ocr(language=language, dpi=200, full=True)
                text = page.get_text("text", textpage=text_page).strip()
            except Exception as exc:
                details.append(f"OCR fallback failed on page {page.number + 1}: {exc}")
        pages.append(text or "[No selectable text found on this page.]")
    doc.close()
    if not tesseract_available:
        details.append("Install Tesseract OCR for real scanned-image OCR. "
                       "Existing selectable text was extracted locally.")
    output = output_dir / "ocr_text.pdf"
    create_text_pdf(output, "OCR text", pages)
    return output, "Generated an OCR text PDF.", details


def pdf_to_pdfa(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Produce a normalised, archivable copy of the PDF."""

    require_files(files)
    require_pdf(files[0])
    output = output_dir / "archivable_copy.pdf"
    doc = fitz.open(str(files[0]))
    metadata = doc.metadata or {}
    metadata["producer"] = "GlassPDF Studio local archivable copy"
    metadata["creationDate"] = (metadata.get("creationDate")
                                or datetime.utcnow().strftime("D:%Y%m%d%H%M%SZ"))
    doc.set_metadata(metadata)
    doc.save(str(output), garbage=4, deflate=True, clean=True)
    doc.close()
    details = ["This is a normalized archivable PDF copy. Full PDF/A validation "
               "requires Ghostscript or a PDF/A validator."]
    return output, "Created an archivable PDF copy.", details
