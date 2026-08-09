"""Split service: split, remove, extract and reorder PDF pages."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from pypdf import PdfWriter

from .common import (
    ToolError,
    make_zip,
    parse_pages,
    parse_range_groups,
    read_pdf,
    require_files,
    require_pdf,
    write_pdf,
)


def split_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Split a PDF into one file per requested range (zipped if multiple)."""

    require_files(files)
    require_pdf(files[0])
    reader = read_pdf(files[0], opts.get("password") or None)
    groups = parse_range_groups(opts.get("ranges") or "all", len(reader.pages))
    outputs: List[Path] = []
    for label, pages in groups:
        writer = PdfWriter()
        for page_index in pages:
            writer.add_page(reader.pages[page_index])
        target = output_dir / f"{label}.pdf"
        write_pdf(writer, target)
        outputs.append(target)
    if len(outputs) == 1:
        return outputs[0], "Created one split PDF.", []
    archive = make_zip(outputs, output_dir / "split_pdfs.zip")
    return archive, f"Created {len(outputs)} split PDFs.", []


def remove_pages(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Delete the specified pages and keep the rest."""

    require_files(files)
    require_pdf(files[0])
    reader = read_pdf(files[0], opts.get("password") or None)
    remove = set(parse_pages(opts.get("pages"), len(reader.pages)))
    writer = PdfWriter()
    for index, page in enumerate(reader.pages):
        if index not in remove:
            writer.add_page(page)
    if not writer.pages:
        raise ToolError("Removing those pages would leave an empty PDF.")
    output = output_dir / "pages_removed.pdf"
    write_pdf(writer, output)
    return output, f"Removed {len(remove)} page(s).", []


def extract_pages(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Keep only the specified pages in a new document."""

    require_files(files)
    require_pdf(files[0])
    reader = read_pdf(files[0], opts.get("password") or None)
    pages = parse_pages(opts.get("pages"), len(reader.pages))
    writer = PdfWriter()
    for page_index in pages:
        writer.add_page(reader.pages[page_index])
    output = output_dir / "extracted_pages.pdf"
    write_pdf(writer, output)
    return output, f"Extracted {len(pages)} page(s).", []


def organize_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Reorder pages according to the requested sequence."""

    require_files(files)
    require_pdf(files[0])
    reader = read_pdf(files[0], opts.get("password") or None)
    order = parse_pages(opts.get("order"), len(reader.pages))
    writer = PdfWriter()
    for page_index in order:
        writer.add_page(reader.pages[page_index])
    output = output_dir / "organized.pdf"
    write_pdf(writer, output)
    return output, f"Organized {len(order)} page(s).", []
