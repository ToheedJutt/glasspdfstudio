"""Service layer for GlassPDFStudio.

Each PDF capability lives in a focused module (``merge_service``,
``split_service`` and friends). ``TOOL_HANDLERS`` maps the public tool id used
by the ``/api/process`` endpoint to the callable that implements it, exactly
mirroring the original monolithic dispatch table so the API contract is
unchanged.
"""

from __future__ import annotations

from typing import Callable, Dict

from .common import ToolError  # re-exported for convenience
from .compress_service import (
    compress_pdf,
    ocr_pdf,
    pdf_to_pdfa,
    repair_pdf,
)
from .convert_service import (
    excel_to_pdf,
    html_to_pdf,
    pdf_to_excel,
    pdf_to_powerpoint,
    pdf_to_word,
    powerpoint_to_pdf,
    word_to_pdf,
)
from .edit_service import (
    crop_pdf,
    edit_pdf,
    page_numbers,
    pdf_forms,
    rotate_pdf,
    watermark_pdf,
)
from .image_service import jpg_to_pdf, pdf_to_jpg, scan_to_pdf
from .intelligence_service import create_workflow, summarize_pdf, translate_pdf
from .merge_service import merge_pdf
from .security_service import (
    compare_pdf,
    protect_pdf,
    redact_pdf,
    sign_pdf,
    unlock_pdf,
)
from .split_service import (
    extract_pages,
    organize_pdf,
    remove_pages,
    split_pdf,
)


# Public dispatch table consumed by routes/api.py. Keys are the exact tool ids
# expected by the frontend; the mapping is a faithful port of the original.
TOOL_HANDLERS: Dict[str, Callable] = {
    "merge_pdf": merge_pdf,
    "split_pdf": split_pdf,
    "compress_pdf": compress_pdf,
    "pdf_to_word": pdf_to_word,
    "pdf_to_powerpoint": pdf_to_powerpoint,
    "pdf_to_excel": pdf_to_excel,
    "word_to_pdf": word_to_pdf,
    "powerpoint_to_pdf": powerpoint_to_pdf,
    "excel_to_pdf": excel_to_pdf,
    "edit_pdf": edit_pdf,
    "pdf_to_jpg": pdf_to_jpg,
    "jpg_to_pdf": jpg_to_pdf,
    "sign_pdf": sign_pdf,
    "watermark_pdf": watermark_pdf,
    "rotate_pdf": rotate_pdf,
    "html_to_pdf": html_to_pdf,
    "unlock_pdf": unlock_pdf,
    "protect_pdf": protect_pdf,
    "organize_pdf": organize_pdf,
    "pdf_to_pdfa": pdf_to_pdfa,
    "repair_pdf": repair_pdf,
    "page_numbers": page_numbers,
    "scan_to_pdf": scan_to_pdf,
    "ocr_pdf": ocr_pdf,
    "compare_pdf": compare_pdf,
    "redact_pdf": redact_pdf,
    "crop_pdf": crop_pdf,
    "remove_pages": remove_pages,
    "extract_pages": extract_pages,
    "pdf_forms": pdf_forms,
    "ai_summarizer": summarize_pdf,
    "translate_pdf": translate_pdf,
    "create_workflow": create_workflow,
}

__all__ = ["TOOL_HANDLERS", "ToolError"]
