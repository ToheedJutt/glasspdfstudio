"""Convert service: Office <-> PDF conversions in both directions.

Where LibreOffice is installed it is used for layout-accurate conversion;
otherwise each function falls back to a local text/image renderer so the tool
still produces a usable file. This mirrors the original behaviour exactly.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple
from urllib.request import Request, urlopen

from docx import Document
from openpyxl import Workbook, load_workbook
from pptx import Presentation
from pptx.util import Inches

from .common import (
    ToolError,
    create_table_pdf,
    create_text_pdf,
    extract_pdf_text,
    html_to_text,
    office_to_pdf_with_soffice,
    render_pdf_pages,
    require_files,
    require_pdf,
)


# --------------------------------------------------------------------------- #
# Office -> PDF
# --------------------------------------------------------------------------- #
def word_to_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Convert a Word document to PDF (LibreOffice or local text fallback)."""

    require_files(files)
    converted = office_to_pdf_with_soffice(files[0], output_dir)
    if converted:
        converted.rename(output_dir / "word_to_pdf.pdf")
        return output_dir / "word_to_pdf.pdf", "Converted with LibreOffice.", []
    if files[0].suffix.lower() != ".docx":
        raise ToolError("DOC conversion needs LibreOffice. DOCX can be converted "
                        "with the local fallback.")
    document = Document(str(files[0]))
    blocks: List[str] = []
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            blocks.append(paragraph.text)
    for table in document.tables:
        for row in table.rows:
            blocks.append(" | ".join(cell.text.strip() for cell in row.cells))
    output = output_dir / "word_to_pdf.pdf"
    create_text_pdf(output, "Word document", blocks or [" "])
    return output, "Converted DOCX text to PDF with the local renderer.", []


def powerpoint_to_pdf(files: List[Path], opts: dict,
                      output_dir: Path) -> Tuple[Path, str, list]:
    """Convert a PowerPoint deck to PDF (LibreOffice or local text fallback)."""

    require_files(files)
    converted = office_to_pdf_with_soffice(files[0], output_dir)
    if converted:
        converted.rename(output_dir / "powerpoint_to_pdf.pdf")
        return output_dir / "powerpoint_to_pdf.pdf", "Converted with LibreOffice.", []
    if files[0].suffix.lower() != ".pptx":
        raise ToolError("PPT conversion needs LibreOffice. PPTX text can be "
                        "converted with the local fallback.")
    presentation = Presentation(str(files[0]))
    blocks: List[str] = []
    for index, slide in enumerate(presentation.slides, start=1):
        blocks.append(f"Slide {index}")
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                blocks.append(shape.text.strip())
        blocks.append("")
    output = output_dir / "powerpoint_to_pdf.pdf"
    create_text_pdf(output, "PowerPoint deck", blocks or [" "], landscape=True)
    return output, "Converted PPTX text to PDF with the local renderer.", []


def excel_to_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Convert an Excel workbook to PDF (LibreOffice or local table fallback)."""

    require_files(files)
    converted = office_to_pdf_with_soffice(files[0], output_dir)
    if converted:
        converted.rename(output_dir / "excel_to_pdf.pdf")
        return output_dir / "excel_to_pdf.pdf", "Converted with LibreOffice.", []
    if files[0].suffix.lower() not in {".xlsx", ".xlsm"}:
        raise ToolError("XLS conversion needs LibreOffice. XLSX can be converted "
                        "with the local fallback.")
    workbook = load_workbook(str(files[0]), data_only=True)
    rows: List[List[str]] = [["Sheet", "Row", "Values"]]
    for worksheet in workbook.worksheets:
        for row_index, row in enumerate(worksheet.iter_rows(values_only=True), start=1):
            values = ["" if value is None else str(value) for value in row]
            if any(values):
                rows.append([worksheet.title, str(row_index), " | ".join(values)])
    output = output_dir / "excel_to_pdf.pdf"
    create_table_pdf(output, "Excel workbook", rows)
    return output, "Converted workbook values to PDF with the local renderer.", []


def html_to_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Convert raw HTML, an uploaded HTML file, or a fetched URL into a PDF."""

    details: List[str] = []
    raw_html = opts.get("html") or ""
    source_url = (opts.get("url") or "").strip()
    if source_url:
        try:
            req = Request(source_url, headers={"User-Agent": "GlassPDFStudio/1.0"})
            with urlopen(req, timeout=20) as response:
                raw_html = response.read().decode("utf-8", errors="replace")
        except Exception as exc:
            raise ToolError(f"Could not fetch URL: {exc}") from exc
    elif files:
        raw_html = files[0].read_text(encoding="utf-8", errors="replace")
    if not raw_html:
        raise ToolError("Provide HTML text, a URL, or an HTML file.")
    text = html_to_text(raw_html)
    details.append("Local fallback renders readable text. Install wkhtmltopdf or "
                   "LibreOffice for full browser layout rendering.")
    output = output_dir / "html_to_pdf.pdf"
    create_text_pdf(output, "HTML to PDF", [text])
    return output, "Converted HTML content to PDF.", details


# --------------------------------------------------------------------------- #
# PDF -> Office
# --------------------------------------------------------------------------- #
def pdf_to_word(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Extract selectable PDF text into an editable DOCX file."""

    require_files(files)
    require_pdf(files[0])
    pages = extract_pdf_text(files[0], opts.get("password") or None)
    document = Document()
    document.add_heading("PDF to Word", 0)
    for index, page_text in enumerate(pages, start=1):
        document.add_heading(f"Page {index}", level=1)
        for line in page_text.splitlines():
            document.add_paragraph(line)
    output = output_dir / "pdf_to_word.docx"
    document.save(str(output))
    return output, "Converted selectable PDF text to DOCX.", []


def pdf_to_powerpoint(files: List[Path], opts: dict,
                      output_dir: Path) -> Tuple[Path, str, list]:
    """Render each PDF page as a full-bleed image on a PowerPoint slide."""

    require_files(files)
    require_pdf(files[0])
    images = render_pdf_pages(files[0], output_dir, zoom=2.0, fmt="png")
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    blank = presentation.slide_layouts[6]
    for image in images:
        slide = presentation.slides.add_slide(blank)
        slide.shapes.add_picture(str(image), 0, 0, width=presentation.slide_width,
                                 height=presentation.slide_height)
    output = output_dir / "pdf_to_powerpoint.pptx"
    presentation.save(str(output))
    return output, f"Converted {len(images)} PDF page(s) to PowerPoint slides.", []


def pdf_to_excel(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Split PDF text into whitespace-delimited cells across sheets."""

    require_files(files)
    require_pdf(files[0])
    pages = extract_pdf_text(files[0], opts.get("password") or None)
    workbook = Workbook()
    workbook.remove(workbook.active)
    for index, text in enumerate(pages, start=1):
        sheet = workbook.create_sheet(title=f"Page {index}")
        for row_index, line in enumerate(text.splitlines(), start=1):
            cells = [cell for cell in re.split(r"\s{2,}|\t", line.strip()) if cell != ""]
            if not cells:
                continue
            for col_index, value in enumerate(cells, start=1):
                sheet.cell(row=row_index, column=col_index, value=value)
    output = output_dir / "pdf_to_excel.xlsx"
    workbook.save(str(output))
    return output, "Extracted text rows into an Excel workbook.", []
