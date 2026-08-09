"""Edit service: watermark, rotate, page numbers, crop, text edits and forms."""

from __future__ import annotations

import fitz
import json
from pathlib import Path
from typing import List, Tuple

from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet  # noqa: F401 (parity import)
from reportlab.pdfgen import canvas

from .common import (
    ToolError,
    create_image_overlay,
    create_table_pdf,
    create_text_overlay,
    hex_to_rgb,
    overlay_page,
    parse_pages,
    read_pdf,
    require_files,
    require_pdf,
    write_pdf,
)


def watermark_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Stamp a text or image watermark onto the selected pages."""

    require_files(files)
    require_pdf(files[0])
    reader = read_pdf(files[0], opts.get("password") or None)
    writer = PdfWriter()
    text = opts.get("text") or "WATERMARK"
    pages = set(parse_pages(opts.get("pages"), len(reader.pages)))
    image_file = next((file for file in files[1:]
                       if file.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}), None)
    for index, page in enumerate(reader.pages):
        if index in pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            overlay = (create_image_overlay(width, height, image_file, opts)
                       if image_file else create_text_overlay(width, height, text, opts))
            overlay_page(page, overlay)
        writer.add_page(page)
    output = output_dir / "watermarked.pdf"
    write_pdf(writer, output)
    return output, "Applied watermark.", []


def rotate_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Rotate the selected pages by a multiple of 90 degrees."""

    require_files(files)
    require_pdf(files[0])
    reader = read_pdf(files[0], opts.get("password") or None)
    pages = set(parse_pages(opts.get("pages"), len(reader.pages)))
    angle = int(opts.get("angle") or 90)
    if angle % 90 != 0:
        raise ToolError("Rotation angle must be 90, 180, or 270.")
    writer = PdfWriter()
    for index, page in enumerate(reader.pages):
        if index in pages:
            page.rotate(angle)
        writer.add_page(page)
    output = output_dir / "rotated.pdf"
    write_pdf(writer, output)
    return output, f"Rotated {len(pages)} page(s).", []


def page_numbers(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Overlay a customisable page-number pattern on each selected page."""

    require_files(files)
    require_pdf(files[0])
    reader = read_pdf(files[0], opts.get("password") or None)
    writer = PdfWriter()
    pages = set(parse_pages(opts.get("pages"), len(reader.pages)))
    pattern = opts.get("pattern") or "{page}"
    merged = 0
    for index, page in enumerate(reader.pages):
        if index in pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            overlay = create_text_overlay(
                width, height, pattern,
                {
                    "fontSize": opts.get("fontSize") or 12,
                    "opacity": opts.get("opacity") or 0.9,
                    "color": opts.get("color") or "#0f172a",
                    "position": opts.get("position") or "bottom",
                    "angle": 0,
                },
                page_number=index + 1,
                total=len(reader.pages),
            )
            overlay_page(page, overlay)
            merged += 1
        writer.add_page(page)
    output = output_dir / "page_numbers.pdf"
    write_pdf(writer, output)
    return output, f"Added page numbers to {merged} page(s).", []


def crop_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Trim page margins by adjusting each page's crop box."""

    require_files(files)
    require_pdf(files[0])
    reader = read_pdf(files[0], opts.get("password") or None)
    margins = {
        "left": float(opts.get("left") or opts.get("margin") or 24),
        "right": float(opts.get("right") or opts.get("margin") or 24),
        "top": float(opts.get("top") or opts.get("margin") or 24),
        "bottom": float(opts.get("bottom") or opts.get("margin") or 24),
    }
    writer = PdfWriter()
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        page.cropbox.lower_left = (margins["left"], margins["bottom"])
        page.cropbox.upper_right = (
            max(margins["left"] + 1, width - margins["right"]),
            max(margins["bottom"] + 1, height - margins["top"]),
        )
        writer.add_page(page)
    output = output_dir / "cropped.pdf"
    write_pdf(writer, output)
    return output, "Cropped page margins.", []


def edit_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Insert text (and an optional bounding rectangle) onto pages."""

    require_files(files)
    require_pdf(files[0])
    doc = fitz.open(str(files[0]))
    if doc.needs_pass:
        password = opts.get("password") or ""
        if not doc.authenticate(password):
            raise ToolError("The password did not unlock this PDF.")
    text = opts.get("text") or "New text"
    pages = parse_pages(opts.get("pages"), doc.page_count)
    font_size = float(opts.get("fontSize") or 16)
    color = hex_to_rgb(opts.get("color") or "#0f172a")
    x = float(opts.get("x") or 72)
    y = float(opts.get("y") or 72)
    for index in pages:
        page = doc[index]
        page.insert_text((x, y), text, fontsize=font_size, color=color)
        if opts.get("rectangle") == "true":
            page.draw_rect(fitz.Rect(x - 8, y - font_size - 8, x + 220, y + 12),
                           color=color, width=1.1)
    output = output_dir / "edited.pdf"
    doc.save(str(output), garbage=4, deflate=True)
    doc.close()
    return output, f"Added content to {len(pages)} page(s).", []


def pdf_forms(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Detect, fill, or generate PDF form fields depending on inputs."""

    fields_data = parse_json_object(opts.get("fields") or "{}")
    if not files:
        output = output_dir / "fillable_form.pdf"
        create_basic_form(output)
        return output, "Created a basic fillable PDF form.", []
    require_pdf(files[0])
    reader = read_pdf(files[0], opts.get("password") or None)
    fields = reader.get_fields() or {}
    if not fields_data:
        rows = [["Field name", "Current value"]]
        for name, data in fields.items():
            rows.append([name, str(data.get("/V", ""))])
        output = output_dir / "form_fields.pdf"
        create_table_pdf(output, "Detected PDF form fields",
                         rows if len(rows) > 1 else [["No fields found", ""]])
        return output, "Detected form fields.", []
    writer = PdfWriter()
    writer.append(reader)
    for page in writer.pages:
        writer.update_page_form_field_values(page, fields_data)
    if "/AcroForm" in reader.trailer["/Root"]:
        writer._root_object.update(
            {NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]})
        writer._root_object["/AcroForm"].update(
            {NameObject("/NeedAppearances"): BooleanObject(True)})
    output = output_dir / "filled_form.pdf"
    write_pdf(writer, output)
    return output, f"Filled {len(fields_data)} form field(s).", []


def parse_json_object(raw: str) -> dict:
    """Parse a JSON object of string values, raising a friendly ToolError."""

    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolError("Field values must be a JSON object.") from exc
    if not isinstance(value, dict):
        raise ToolError("Field values must be a JSON object.")
    return {str(key): str(val) for key, val in value.items()}


def create_basic_form(path: Path) -> Path:
    """Generate a simple, ready-to-fill PDF form from scratch."""

    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 720, "Fillable PDF Form")
    fields = [("name", "Name", 660), ("email", "Email", 600),
              ("date", "Date", 540), ("notes", "Notes", 480)]
    c.setFont("Helvetica", 10)
    form = getattr(c, "acroform", None)
    for name, label, y in fields:
        c.drawString(72, y + 24, label)
        if form:
            form.textfield(name=name, tooltip=label, x=72, y=y, width=360, height=22,
                           borderStyle="underlined", forceBorder=True)
        else:
            c.roundRect(72, y, 360, 24, 4)
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(80, y + 8, name)
            c.setFont("Helvetica", 10)
    c.save()
    return path
