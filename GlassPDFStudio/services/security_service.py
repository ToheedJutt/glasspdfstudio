"""Security service: unlock, protect, sign, redact and compare PDFs."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import List, Tuple

import fitz
import re
from pypdf import PdfWriter

from .common import (
    ToolError,
    create_text_pdf,
    extract_pdf_text,
    hex_to_rgb,
    read_pdf,
    require_files,
    require_pdf,
    write_pdf,
)
from .edit_service import watermark_pdf


def unlock_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Write a decrypted copy of a password-protected PDF."""

    require_files(files)
    require_pdf(files[0])
    reader = read_pdf(files[0], opts.get("password") or None)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    output = output_dir / "unlocked.pdf"
    write_pdf(writer, output)
    return output, "Created an unlocked copy.", []


def protect_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Encrypt a PDF with a user-supplied password."""

    require_files(files)
    require_pdf(files[0])
    password = opts.get("newPassword") or opts.get("password")
    if not password:
        raise ToolError("Enter a password for the protected PDF.")
    reader = read_pdf(files[0], opts.get("sourcePassword") or None)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    output = output_dir / "protected.pdf"
    write_pdf(writer, output)
    return output, "Encrypted the PDF with a password.", []


def sign_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Stamp a signature onto the PDF (reuses the watermark pipeline)."""

    require_files(files)
    require_pdf(files[0])
    opts = {**opts,
            "position": opts.get("position") or "bottom-right",
            "fontSize": opts.get("fontSize") or 24,
            "opacity": opts.get("opacity") or 0.92}
    opts["text"] = opts.get("text") or "Signed"
    return watermark_pdf(files, opts, output_dir)


def redact_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Permanently black out every occurrence of the requested terms."""

    require_files(files)
    require_pdf(files[0])
    terms = [term.strip() for term in re.split(r"[,;\n]", opts.get("terms") or "")
             if term.strip()]
    if not terms:
        raise ToolError("Enter at least one word or phrase to redact.")
    doc = fitz.open(str(files[0]))
    if doc.needs_pass:
        password = opts.get("password") or ""
        if not doc.authenticate(password):
            raise ToolError("The password did not unlock this PDF.")
    count = 0
    fill = hex_to_rgb(opts.get("fill") or "#050505")
    for page in doc:
        for term in terms:
            for rect in page.search_for(term):
                page.add_redact_annot(rect, fill=fill)
                count += 1
        if count:
            page.apply_redactions()
    output = output_dir / "redacted.pdf"
    doc.save(str(output), garbage=4, deflate=True)
    doc.close()
    return output, f"Applied {count} redaction mark(s).", []


def compare_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Produce a unified-diff report between two PDFs' extracted text."""

    require_files(files, 2)
    for file in files[:2]:
        require_pdf(file)
    left = "\n".join(extract_pdf_text(files[0], opts.get("password") or None)).splitlines()
    right = "\n".join(extract_pdf_text(files[1], opts.get("password") or None)).splitlines()
    diff = list(difflib.unified_diff(left, right, fromfile=files[0].name,
                                     tofile=files[1].name, lineterm=""))
    output = output_dir / "comparison_report.pdf"
    create_text_pdf(output, "PDF comparison", diff or ["No text differences found."])
    return output, f"Compared documents and found {len(diff)} diff line(s).", []
