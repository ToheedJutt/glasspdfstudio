"""Image service: images <-> PDF (scan-to-PDF, JPG-to-PDF, PDF-to-JPG)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageOps

from .common import (
    ToolError,
    make_zip,
    parse_pages,
    read_pdf,
    render_pdf_pages,
    require_files,
    require_pdf,
)


def scan_to_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Assemble images into a single scan-style PDF with optional enhancement."""

    require_files(files)
    image_paths = [file for file in files
                   if file.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp",
                                              ".tif", ".tiff", ".webp"}]
    if not image_paths:
        raise ToolError("Upload JPG, PNG, BMP, TIFF, or WEBP images.")
    processed: List[Image.Image] = []
    enhance = opts.get("enhance") == "true"
    for path in image_paths:
        image = Image.open(path).convert("RGB")
        if enhance:
            image = ImageOps.autocontrast(ImageOps.grayscale(image)).convert("RGB")
        processed.append(image)
    output = output_dir / "scanned.pdf"
    first, rest = processed[0], processed[1:]
    first.save(output, save_all=True, append_images=rest, resolution=150.0)
    for image in processed:
        image.close()
    return output, f"Created a scan-style PDF from {len(image_paths)} image(s).", []


def jpg_to_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Convert images to a PDF (delegates to the shared scan pipeline)."""

    return scan_to_pdf(files, opts, output_dir)


def pdf_to_jpg(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Rasterise PDF pages to JPG images (zipped when more than one page)."""

    require_files(files)
    require_pdf(files[0])
    reader = read_pdf(files[0], opts.get("password") or None)
    pages = parse_pages(opts.get("pages"), len(reader.pages))
    zoom = float(opts.get("scale") or 2)
    output_files = render_pdf_pages(files[0], output_dir, pages=pages,
                                    zoom=max(1, min(4, zoom)), fmt="jpg")
    if len(output_files) == 1:
        return output_files[0], "Rendered one page as JPG.", []
    archive = make_zip(output_files, output_dir / "pdf_pages_as_jpg.zip")
    return archive, f"Rendered {len(output_files)} pages as JPG.", []
