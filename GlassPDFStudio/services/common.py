"""Shared helpers and low-level primitives for the PDF service layer.

Everything here is a faithful port of the helpers that lived at the top of the
original ``app.py``. Behaviour is intentionally unchanged: page parsing, PDF
reading/writing, text extraction, ReportLab document builders and the overlay
primitives all produce byte-for-byte equivalent output.
"""

from __future__ import annotations

import html as html_lib
import io
import re
import shutil
import subprocess
import textwrap
import uuid
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

import fitz
from flask import request
from PIL import Image  # noqa: F401  (imported so callers share one Pillow import)
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.utils import secure_filename

from config import JOBS_DIR


class ToolError(Exception):
    """Raised for user-facing, recoverable errors (mapped to HTTP 400)."""


# --------------------------------------------------------------------------- #
# Job + upload management
# --------------------------------------------------------------------------- #
def new_job() -> Tuple[str, Path, Path, Path]:
    """Create a fresh job directory with uploads/ and outputs/ subfolders."""

    job_id = uuid.uuid4().hex
    job_dir = JOBS_DIR / job_id
    upload_dir = job_dir / "uploads"
    output_dir = job_dir / "outputs"
    upload_dir.mkdir(parents=True)
    output_dir.mkdir()
    return job_id, job_dir, upload_dir, output_dir


def save_uploads(upload_dir: Path) -> List[Path]:
    """Persist every uploaded file, sanitising names and avoiding clashes."""

    files = request.files.getlist("files")
    saved: List[Path] = []
    for index, file in enumerate(files):
        if not file or not file.filename:
            continue
        name = secure_filename(file.filename) or f"upload_{index}"
        target = upload_dir / unique_name(upload_dir, name)
        file.save(target)
        saved.append(target)
    return saved


def unique_name(directory: Path, filename: str) -> str:
    """Return a filename that does not collide inside ``directory``."""

    path = directory / filename
    if not path.exists():
        return filename
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = f"{stem}_{counter}{suffix}"
        if not (directory / candidate).exists():
            return candidate
        counter += 1


def require_files(files: List[Path], count: int = 1) -> None:
    """Guard: ensure at least ``count`` files were uploaded."""

    if len(files) < count:
        raise ToolError(f"Upload at least {count} file{'s' if count != 1 else ''}.")


def is_pdf(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


def require_pdf(path: Path) -> None:
    if not is_pdf(path):
        raise ToolError("This tool needs a PDF file.")


# --------------------------------------------------------------------------- #
# PDF reading / writing
# --------------------------------------------------------------------------- #
def read_pdf(path: Path, password: Optional[str] = None) -> PdfReader:
    """Open a (possibly encrypted) PDF with pypdf."""

    reader = PdfReader(str(path), strict=False)
    if reader.is_encrypted:
        if not password:
            raise ToolError("This PDF is encrypted. Enter its password first.")
        status = reader.decrypt(password)
        if status == 0:
            raise ToolError("The password did not unlock this PDF.")
    return reader


def write_pdf(writer: PdfWriter, path: Path) -> Path:
    with path.open("wb") as handle:
        writer.write(handle)
    return path


# --------------------------------------------------------------------------- #
# Page range parsing
# --------------------------------------------------------------------------- #
def parse_pages(spec: Optional[str], total: int) -> List[int]:
    """Parse a page spec ("all", "1-3,5", "last") into 0-based indices."""

    if not spec or spec.strip().lower() in {"all", "*"}:
        return list(range(total))
    selected: List[int] = []
    for part in re.split(r"[,;]\s*", spec.strip()):
        if not part:
            continue
        if "-" in part:
            left, right = [p.strip() for p in part.split("-", 1)]
            start = page_token(left, total)
            end = page_token(right, total)
            step = 1 if start <= end else -1
            selected.extend(range(start, end + step, step))
        else:
            selected.append(page_token(part, total))
    result: List[int] = []
    for item in selected:
        if item < 0 or item >= total:
            raise ToolError(f"Page {item + 1} is outside the document.")
        result.append(item)
    return result


def page_token(token: str, total: int) -> int:
    token = token.strip().lower()
    if token in {"last", "end"}:
        return total - 1
    if not token.isdigit():
        raise ToolError(f"Invalid page token: {token}")
    page = int(token)
    if page < 1:
        raise ToolError("Page numbers start at 1.")
    return page - 1


def parse_range_groups(spec: Optional[str], total: int) -> List[Tuple[str, List[int]]]:
    """Parse a spec into named groups, one per split output file."""

    if not spec or spec.strip().lower() in {"all", "*"}:
        return [(f"page_{i + 1:03d}", [i]) for i in range(total)]
    groups: List[Tuple[str, List[int]]] = []
    for part in re.split(r"[,;]\s*", spec.strip()):
        if not part:
            continue
        pages = parse_pages(part, total)
        label = "pages_" + part.replace("-", "_to_").replace(" ", "")
        groups.append((secure_filename(label) or f"group_{len(groups) + 1}", pages))
    return groups


# --------------------------------------------------------------------------- #
# Archive + API response helpers
# --------------------------------------------------------------------------- #
def make_zip(files: List[Path], zip_path: Path) -> Path:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in files:
            archive.write(item, arcname=item.name)
    return zip_path


def response_for(job_id: str, path: Path, message: str = "",
                 details: Optional[List[str]] = None) -> dict:
    """Shape the success payload returned by ``/api/process``."""

    return {
        "filename": path.name,
        "downloadUrl": f"/download/{job_id}/{path.name}",
        "message": message,
        "details": details or [],
    }


# --------------------------------------------------------------------------- #
# Text extraction + document builders
# --------------------------------------------------------------------------- #
def extract_pdf_text(path: Path, password: Optional[str] = None) -> List[str]:
    """Return the plain text of every page using PyMuPDF."""

    doc = fitz.open(str(path))
    if doc.needs_pass:
        if not password or not doc.authenticate(password):
            raise ToolError("This PDF is encrypted. Enter its password first.")
    pages: List[str] = []
    for page in doc:
        pages.append(page.get_text("text").strip())
    doc.close()
    return pages


def create_text_pdf(path: Path, title: str, blocks: List[str],
                    landscape: bool = False) -> Path:
    """Render a simple, readable text PDF with ReportLab."""

    page_size = (letter[1], letter[0]) if landscape else letter
    doc = SimpleDocTemplate(
        str(path), pagesize=page_size,
        rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42,
    )
    styles = getSampleStyleSheet()
    story: list = [Paragraph(html_lib.escape(title), styles["Title"]), Spacer(1, 12)]
    for index, block in enumerate(blocks):
        text = block.strip() or " "
        for chunk in textwrap.wrap(text, width=110, replace_whitespace=False) or [" "]:
            story.append(Paragraph(html_lib.escape(chunk), styles["BodyText"]))
            story.append(Spacer(1, 4))
        if index != len(blocks) - 1:
            story.append(Spacer(1, 8))
    doc.build(story)
    return path


def create_table_pdf(path: Path, title: str, rows: List[List[str]]) -> Path:
    """Render a tabular PDF (used for spreadsheet + form-field exports)."""

    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=36,
                            leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story: list = [Paragraph(html_lib.escape(title), styles["Title"]), Spacer(1, 12)]
    if rows:
        safe_rows = [[html_lib.escape(str(cell)) for cell in row] for row in rows[:500]]
        table = Table(safe_rows, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#b7c2d0")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eef7")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
                ]
            )
        )
        story.append(table)
    doc.build(story)
    return path


def render_pdf_pages(path: Path, output_dir: Path, pages: Optional[List[int]] = None,
                     zoom: float = 2.0, fmt: str = "jpg") -> List[Path]:
    """Rasterise selected PDF pages to image files via PyMuPDF."""

    doc = fitz.open(str(path))
    selected = pages if pages is not None else list(range(doc.page_count))
    output: List[Path] = []
    for page_index in selected:
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        target = output_dir / f"page_{page_index + 1:03d}.{fmt}"
        pix.save(str(target))
        output.append(target)
    doc.close()
    return output


# --------------------------------------------------------------------------- #
# LibreOffice bridge (optional external engine)
# --------------------------------------------------------------------------- #
def find_soffice() -> Optional[str]:
    """Locate a LibreOffice/soffice binary if one is installed."""

    for command in ("soffice", "libreoffice"):
        found = shutil.which(command)
        if found:
            return found
    return None


def office_to_pdf_with_soffice(path: Path, output_dir: Path) -> Optional[Path]:
    """Convert an Office document to PDF using LibreOffice, if available."""

    soffice = find_soffice()
    if not soffice:
        return None
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir",
         str(output_dir), str(path)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90,
    )
    candidate = output_dir / f"{path.stem}.pdf"
    return candidate if candidate.exists() else None


# --------------------------------------------------------------------------- #
# HTML helpers
# --------------------------------------------------------------------------- #
def html_to_text(raw: str) -> str:
    """Strip HTML down to readable plain text (local fallback renderer)."""

    raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?i)</(p|div|section|article|h[1-6]|li|tr)>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html_lib.unescape(raw)
    return re.sub(r"[ \t]+", " ", raw).strip()


# --------------------------------------------------------------------------- #
# Overlay primitives (watermark / page numbers / signatures)
# --------------------------------------------------------------------------- #
def overlay_page(page, overlay_pdf: PdfReader) -> None:
    page.merge_page(overlay_pdf.pages[0])


def create_text_overlay(width: float, height: float, text: str, opts: dict,
                        page_number: int = 1, total: int = 1) -> PdfReader:
    """Build a single-page overlay PDF containing centred, rotated text."""

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    size = int(opts.get("fontSize") or 42)
    opacity = float(opts.get("opacity") or 0.22)
    color = parse_hex_color(opts.get("color") or "#0f172a", opacity)
    can.setFillColor(color)
    if hasattr(can, "setFillAlpha"):
        can.setFillAlpha(opacity)
    can.setFont("Helvetica-Bold", size)
    label = text.replace("{page}", str(page_number)).replace("{total}", str(total))
    x, y = overlay_position(width, height, opts.get("position") or "center", size)
    angle = float(opts.get("angle") or 0)
    can.saveState()
    can.translate(x, y)
    can.rotate(angle)
    can.drawCentredString(0, 0, label)
    can.restoreState()
    can.save()
    packet.seek(0)
    return PdfReader(packet)


def create_image_overlay(width: float, height: float, image_path: Path,
                         opts: dict) -> PdfReader:
    """Build a single-page overlay PDF containing a scaled image stamp."""

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    scale = float(opts.get("scale") or 0.28)
    image = ImageReader(str(image_path))
    iw, ih = image.getSize()
    target_w = width * scale
    target_h = target_w * ih / iw
    x, y = overlay_position(width, height, opts.get("position") or "bottom-right",
                            target_h)
    can.drawImage(image, x - target_w / 2, y - target_h / 2, target_w, target_h,
                  mask="auto")
    can.save()
    packet.seek(0)
    return PdfReader(packet)


def overlay_position(width: float, height: float, position: str,
                     inset: float) -> Tuple[float, float]:
    """Resolve a named position keyword into (x, y) canvas coordinates."""

    margin = max(36, inset)
    positions = {
        "top-left": (margin, height - margin),
        "top": (width / 2, height - margin),
        "top-right": (width - margin, height - margin),
        "center": (width / 2, height / 2),
        "bottom-left": (margin, margin),
        "bottom": (width / 2, margin),
        "bottom-right": (width - margin, margin),
    }
    return positions.get(position, positions["center"])


def parse_hex_color(value: str, opacity: float) -> Color:
    """Convert a #rrggbb string into a ReportLab Color with alpha."""

    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        value = "0f172a"
    r = int(value[0:2], 16) / 255
    g = int(value[2:4], 16) / 255
    b = int(value[4:6], 16) / 255
    return Color(r, g, b, alpha=opacity)


def hex_to_rgb(value: str) -> Tuple[float, float, float]:
    """Convert a #rrggbb string into a 0..1 RGB tuple for PyMuPDF."""

    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        value = "0f172a"
    return int(value[:2], 16) / 255, int(value[2:4], 16) / 255, int(value[4:], 16) / 255
