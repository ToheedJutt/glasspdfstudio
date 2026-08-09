"""Merge service: combine multiple PDFs into a single document."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from pypdf import PdfWriter

from .common import read_pdf, require_files, require_pdf, write_pdf


def merge_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Concatenate every uploaded PDF, in order, into ``merged.pdf``."""

    require_files(files, 2)
    writer = PdfWriter()
    password = opts.get("password") or None
    count = 0
    for file in files:
        require_pdf(file)
        reader = read_pdf(file, password)
        for page in reader.pages:
            writer.add_page(page)
            count += 1
    output = output_dir / "merged.pdf"
    write_pdf(writer, output)
    return output, f"Merged {len(files)} PDFs into {count} pages.", []
