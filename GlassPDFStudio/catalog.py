"""Tool catalogue: the single source of truth for GlassPDFStudio.

Every PDF tool is described once here and consumed in three places:

* the Flask page routes (to render a dedicated workspace per tool),
* the Jinja templates (grid cards, hero shortcuts, tool headers), and
* the browser (serialised to JSON so ``app.js`` can drive the upload form).

The ``options`` schema for each tool is a faithful port of the legacy
frontend definitions, which means the ``/api/process`` contract and every
backend handler continue to behave exactly as before.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# --------------------------------------------------------------------------- #
# Category metadata (label + accent colour used across the UI)
# --------------------------------------------------------------------------- #
CATEGORIES: List[Dict[str, str]] = [
    {"id": "Organize PDF", "label": "Organize", "accent": "#6366f1"},
    {"id": "Optimize PDF", "label": "Optimize", "accent": "#10b981"},
    {"id": "Convert PDF", "label": "Convert", "accent": "#8b5cf6"},
    {"id": "Edit PDF", "label": "Edit", "accent": "#f59e0b"},
    {"id": "PDF Security", "label": "Security", "accent": "#f43f5e"},
    {"id": "PDF Intelligence", "label": "AI & Smart", "accent": "#06b6d4"},
]


# --------------------------------------------------------------------------- #
# Reusable option fragments
# --------------------------------------------------------------------------- #
_PASSWORD = {"name": "password", "label": "PDF password", "type": "password",
             "placeholder": "Optional"}


def _tool(**kwargs: Any) -> Dict[str, Any]:
    """Normalise a tool definition with sensible defaults."""

    kwargs.setdefault("multiple", False)
    kwargs.setdefault("minFiles", 0 if kwargs.get("optionalFiles") else 1)
    kwargs.setdefault("optionalFiles", False)
    kwargs.setdefault("options", [])
    kwargs.setdefault("accept", ".pdf,application/pdf")
    # Derive a URL slug from the tool id (merge_pdf -> merge-pdf).
    kwargs.setdefault("slug", kwargs["id"].replace("_", "-"))
    return kwargs


# --------------------------------------------------------------------------- #
# The catalogue (33 tools across six categories)
# --------------------------------------------------------------------------- #
TOOLS: List[Dict[str, Any]] = [
    # ------------------------- Organize PDF -------------------------------- #
    _tool(
        id="merge_pdf", name="Merge PDF", category="Organize PDF", icon="merge",
        description="Combine multiple PDFs into one continuous document in the order you choose.",
        multiple=True, minFiles=2, options=[_PASSWORD],
    ),
    _tool(
        id="split_pdf", name="Split PDF", category="Organize PDF", icon="split",
        description="Break one PDF into separate files or custom page ranges in seconds.",
        options=[{"name": "ranges", "label": "Ranges", "type": "text",
                  "placeholder": "all or 1-3,5"}, _PASSWORD],
    ),
    _tool(
        id="remove_pages", name="Delete Pages", category="Organize PDF", icon="remove",
        description="Remove unwanted pages from your PDF and keep everything else intact.",
        options=[{"name": "pages", "label": "Pages", "type": "text",
                  "placeholder": "2,4-6"}, _PASSWORD],
    ),
    _tool(
        id="extract_pages", name="Extract Pages", category="Organize PDF", icon="extract",
        description="Pull selected pages out of a PDF into a brand new document.",
        options=[{"name": "pages", "label": "Pages", "type": "text",
                  "placeholder": "1,3-5"}, _PASSWORD],
    ),
    _tool(
        id="organize_pdf", name="Organize PDF", category="Organize PDF", icon="organize",
        description="Reorder, rearrange and reshuffle the pages of your PDF exactly how you need.",
        options=[{"name": "order", "label": "Page order", "type": "text",
                  "placeholder": "3,1,2,4-last"}, _PASSWORD],
    ),
    _tool(
        id="scan_to_pdf", name="Scan to PDF", category="Organize PDF", icon="scan",
        description="Turn photos of documents into a clean, scan-style PDF with optional enhancement.",
        accept=".jpg,.jpeg,.png,.bmp,.tif,.tiff,.webp,image/*", multiple=True,
        options=[{"name": "enhance", "label": "Enhance scans", "type": "select",
                  "options": [["false", "Off"], ["true", "On"]]}],
    ),

    # ------------------------- Optimize PDF -------------------------------- #
    _tool(
        id="compress_pdf", name="Compress PDF", category="Optimize PDF", icon="compress",
        description="Shrink PDF file size while keeping the best possible quality.",
        options=[_PASSWORD],
    ),
    _tool(
        id="repair_pdf", name="Repair PDF", category="Optimize PDF", icon="repair",
        description="Rebuild a damaged or corrupted PDF into a clean, readable file.",
        options=[_PASSWORD],
    ),
    _tool(
        id="ocr_pdf", name="OCR PDF", category="Optimize PDF", icon="ocr",
        description="Recognise text in scanned PDFs and make it searchable and selectable.",
        options=[{"name": "language", "label": "Language code", "type": "text",
                  "value": "eng"}, _PASSWORD],
    ),

    # ------------------------- Convert PDF -------------------------------- #
    _tool(
        id="jpg_to_pdf", name="JPG to PDF", category="Convert PDF", icon="image",
        description="Convert JPG, PNG and other images into a single polished PDF.",
        accept=".jpg,.jpeg,.png,.bmp,.tif,.tiff,.webp,image/*", multiple=True,
        options=[{"name": "enhance", "label": "Enhance images", "type": "select",
                  "options": [["false", "Off"], ["true", "On"]]}],
    ),
    _tool(
        id="word_to_pdf", name="Word to PDF", category="Convert PDF", icon="doc",
        description="Convert Word documents to pixel-perfect PDFs ready to share.",
        accept=".docx,.doc,application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ),
    _tool(
        id="powerpoint_to_pdf", name="PowerPoint to PDF", category="Convert PDF", icon="slides",
        description="Turn PowerPoint presentations into portable, print-ready PDFs.",
        accept=".pptx,.ppt,application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ),
    _tool(
        id="excel_to_pdf", name="Excel to PDF", category="Convert PDF", icon="sheet",
        description="Export Excel spreadsheets to clean PDF documents in a click.",
        accept=".xlsx,.xlsm,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ),
    _tool(
        id="html_to_pdf", name="HTML to PDF", category="Convert PDF", icon="html",
        description="Capture a web page or raw HTML and save it as a tidy PDF.",
        accept=".html,.htm,text/html", optionalFiles=True,
        options=[{"name": "url", "label": "URL", "type": "url",
                  "placeholder": "https://example.com"},
                 {"name": "html", "label": "HTML", "type": "textarea",
                  "placeholder": "<h1>Document</h1>", "full": True}],
    ),
    _tool(
        id="pdf_to_jpg", name="PDF to JPG", category="Convert PDF", icon="image",
        description="Render every page of a PDF into high-quality JPG images.",
        options=[{"name": "pages", "label": "Pages", "type": "text",
                  "placeholder": "all or 1-3"},
                 {"name": "scale", "label": "Scale", "type": "select",
                  "options": [["1", "Standard"], ["2", "Sharp"], ["3", "Retina"],
                              ["4", "Ultra"]]}, _PASSWORD],
    ),
    _tool(
        id="pdf_to_word", name="PDF to Word", category="Convert PDF", icon="doc",
        description="Convert PDF text into an editable Microsoft Word document.",
        options=[_PASSWORD],
    ),
    _tool(
        id="pdf_to_powerpoint", name="PDF to PowerPoint", category="Convert PDF", icon="slides",
        description="Transform PDF pages into editable PowerPoint slides.",
        options=[_PASSWORD],
    ),
    _tool(
        id="pdf_to_excel", name="PDF to Excel", category="Convert PDF", icon="sheet",
        description="Extract tables and text from a PDF straight into Excel.",
        options=[_PASSWORD],
    ),
    _tool(
        id="pdf_to_pdfa", name="PDF to PDF/A", category="Convert PDF", icon="archive",
        description="Create an archivable PDF/A-style copy for long-term storage.",
        options=[_PASSWORD],
    ),

    # ------------------------- Edit PDF ----------------------------------- #
    _tool(
        id="rotate_pdf", name="Rotate PDF", category="Edit PDF", icon="rotate",
        description="Rotate one page or the whole PDF to the correct orientation.",
        options=[{"name": "angle", "label": "Angle", "type": "select",
                  "options": [["90", "90"], ["180", "180"], ["270", "270"]]},
                 {"name": "pages", "label": "Pages", "type": "text",
                  "placeholder": "all or 1,3"}, _PASSWORD],
    ),
    _tool(
        id="page_numbers", name="Add Page Numbers", category="Edit PDF", icon="number",
        description="Insert customisable page numbers anywhere on your document.",
        options=[{"name": "pattern", "label": "Pattern", "type": "text",
                  "value": "{page} / {total}"},
                 {"name": "position", "label": "Position", "type": "select",
                  "options": [["bottom", "Bottom"], ["top", "Top"],
                              ["bottom-right", "Bottom right"],
                              ["bottom-left", "Bottom left"]]},
                 {"name": "fontSize", "label": "Size", "type": "number", "value": "12"},
                 {"name": "pages", "label": "Pages", "type": "text", "placeholder": "all"}],
    ),
    _tool(
        id="watermark_pdf", name="Watermark PDF", category="Edit PDF", icon="watermark",
        description="Stamp text or an image watermark across your PDF pages.",
        accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*", multiple=True,
        options=[{"name": "text", "label": "Text", "type": "text", "value": "WATERMARK"},
                 {"name": "position", "label": "Position", "type": "select",
                  "options": [["center", "Center"], ["top", "Top"], ["bottom", "Bottom"],
                              ["bottom-right", "Bottom right"], ["bottom-left", "Bottom left"]]},
                 {"name": "angle", "label": "Angle", "type": "number", "value": "-30"},
                 {"name": "fontSize", "label": "Size", "type": "number", "value": "42"},
                 {"name": "opacity", "label": "Opacity", "type": "number", "value": "0.22",
                  "step": "0.05"},
                 {"name": "color", "label": "Color", "type": "color", "value": "#0f172a"}],
    ),
    _tool(
        id="crop_pdf", name="Crop PDF", category="Edit PDF", icon="crop",
        description="Trim margins and whitespace to focus on the content that matters.",
        options=[{"name": "margin", "label": "Margin points", "type": "number", "value": "24"},
                 _PASSWORD],
    ),
    _tool(
        id="edit_pdf", name="Edit PDF", category="Edit PDF", icon="edit",
        description="Add text and shapes directly onto any page of your PDF.",
        options=[{"name": "text", "label": "Text", "type": "text", "value": "New text"},
                 {"name": "pages", "label": "Pages", "type": "text", "placeholder": "1"},
                 {"name": "x", "label": "X", "type": "number", "value": "72"},
                 {"name": "y", "label": "Y", "type": "number", "value": "72"},
                 {"name": "fontSize", "label": "Size", "type": "number", "value": "16"},
                 {"name": "color", "label": "Color", "type": "color", "value": "#0f172a"},
                 {"name": "rectangle", "label": "Rectangle", "type": "select",
                  "options": [["false", "Off"], ["true", "On"]]}],
    ),
    _tool(
        id="pdf_forms", name="PDF Forms", category="Edit PDF", icon="form",
        description="Detect, fill or generate interactive PDF form fields.",
        optionalFiles=True,
        options=[{"name": "fields", "label": "Fields JSON", "type": "textarea",
                  "placeholder": '{"name":"Ali"}', "full": True}, _PASSWORD],
    ),

    # ------------------------- PDF Security ------------------------------- #
    _tool(
        id="unlock_pdf", name="Unlock PDF", category="PDF Security", icon="unlock",
        description="Remove passwords and restrictions from a PDF you own.",
        options=[{"name": "password", "label": "Current password", "type": "password",
                  "placeholder": "Required for encrypted PDFs"}],
    ),
    _tool(
        id="protect_pdf", name="Protect PDF", category="PDF Security", icon="lock",
        description="Encrypt your PDF with a strong password to keep it private.",
        options=[{"name": "newPassword", "label": "New password", "type": "password",
                  "placeholder": "Required"},
                 {"name": "sourcePassword", "label": "Current password", "type": "password",
                  "placeholder": "Optional"}],
    ),
    _tool(
        id="sign_pdf", name="Sign PDF", category="PDF Security", icon="sign",
        description="Add a text signature or stamp to finalise your document.",
        accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*", multiple=True,
        options=[{"name": "text", "label": "Signature text", "type": "text", "value": "Signed"},
                 {"name": "position", "label": "Position", "type": "select",
                  "options": [["bottom-right", "Bottom right"], ["bottom-left", "Bottom left"],
                              ["center", "Center"]]},
                 {"name": "fontSize", "label": "Size", "type": "number", "value": "24"}],
    ),
    _tool(
        id="redact_pdf", name="Redact PDF", category="PDF Security", icon="redact",
        description="Permanently black out sensitive words and phrases in your PDF.",
        options=[{"name": "terms", "label": "Terms", "type": "textarea",
                  "placeholder": "secret\naccount number", "full": True},
                 {"name": "fill", "label": "Fill", "type": "color", "value": "#050505"},
                 _PASSWORD],
    ),
    _tool(
        id="compare_pdf", name="Compare PDF", category="PDF Security", icon="compare",
        description="See exactly what changed between two versions of a document.",
        multiple=True, minFiles=2, options=[_PASSWORD],
    ),

    # ------------------------- PDF Intelligence --------------------------- #
    _tool(
        id="ai_summarizer", name="AI Summarizer", category="PDF Intelligence", icon="brain",
        description="Generate a concise summary of any PDF using local intelligence.",
        options=[{"name": "sentences", "label": "Sentences", "type": "number", "value": "8"},
                 _PASSWORD],
    ),
    _tool(
        id="translate_pdf", name="Translate PDF", category="PDF Intelligence", icon="translate",
        description="Produce a translated copy of your PDF into another language.",
        options=[{"name": "target", "label": "Target", "type": "select",
                  "options": [["Spanish", "Spanish"], ["French", "French"],
                              ["Urdu", "Urdu"], ["German", "German"]]}, _PASSWORD],
    ),
    _tool(
        id="create_workflow", name="PDF Workflow", category="PDF Intelligence", icon="workflow",
        description="Chain several tools together and run them as one automated pipeline.",
        options=[{"name": "steps", "label": "Workflow steps", "type": "checklist",
                  "options": [["compress_pdf", "Compress"], ["repair_pdf", "Repair"],
                              ["page_numbers", "Page numbers"], ["watermark_pdf", "Watermark"],
                              ["protect_pdf", "Protect"], ["rotate_pdf", "Rotate"]]},
                 {"name": "text", "label": "Watermark / label text", "type": "text",
                  "placeholder": "Optional"},
                 {"name": "newPassword", "label": "Protect password", "type": "password",
                  "placeholder": "For protect step"}],
    ),
]


# --------------------------------------------------------------------------- #
# SVG icon path library (24x24 viewBox). Shared by server + client rendering.
# --------------------------------------------------------------------------- #
ICON_PATHS: Dict[str, str] = {
    "merge": "M8 7h8m-8 5h8m-8 5h8M4 5v14m16-14v14",
    "split": "M12 3v18M5 7h5m-5 5h5m-5 5h5m4-10h5m-5 5h5m-5 5h5",
    "remove": "M6 7h12M9 7v12m6-12v12M8 7l1-3h6l1 3",
    "extract": "M12 3v12m0 0 4-4m-4 4-4-4M5 21h14",
    "organize": "M4 8h16M4 16h16M8 4v8m8 0v8",
    "scan": "M4 7V5h16v2M4 17v2h16v-2M7 12h10",
    "compress": "M8 3v6H3m13-6v6h5M8 21v-6H3m13 6v-6h5",
    "repair": "M14 7 17 4l3 3-3 3m-2-1-6 6M5 19l4-1 9-9-3-3-9 9-1 4Z",
    "ocr": "M5 5h14v14H5zM8 9h8M8 13h5M8 17h7",
    "image": "M5 5h14v14H5zM8 16l3-3 2 2 3-4 3 5M9 9h.1",
    "doc": "M7 3h7l4 4v14H7zM14 3v5h5M9 13h6M9 17h6",
    "slides": "M4 5h16v11H4zM8 21h8M12 16v5",
    "sheet": "M5 4h14v16H5zM5 9h14M10 4v16M15 4v16M5 14h14",
    "html": "M8 9 4 12l4 3m8-6 4 3-4 3M14 7l-4 10",
    "archive": "M4 7h16v13H4zM4 7l2-4h12l2 4M9 11h6",
    "rotate": "M4 12a8 8 0 1 0 3-6M4 5v7h7",
    "number": "M8 7h8M8 12h8M8 17h8M5 7h.1M5 12h.1M5 17h.1",
    "watermark": "M4 18 18 4M7 7h10v10H7z",
    "crop": "M7 3v14h14M3 7h14v14",
    "edit": "M4 20h4L19 9l-4-4L4 16zM13 7l4 4",
    "form": "M6 3h12v18H6zM9 8h6M9 12h6M9 16h3",
    "unlock": "M7 11h10v9H7zM9 11V8a3 3 0 0 1 5.7-1.3",
    "lock": "M7 11h10v9H7zM9 11V8a3 3 0 0 1 6 0v3",
    "sign": "M4 18c4 0 4-8 7-8 2 0 1 5 3 5 1 0 2-2 3-2 1 0 1 2 3 2M4 21h16",
    "redact": "M5 6h14M5 12h14M5 18h14M8 5v14m8-14v14",
    "compare": "M4 5h7v14H4zM13 5h7v14h-7zM7 9h1m0 4h1m7-4h1m0 4h1",
    "brain": "M9 5a3 3 0 0 0-3 3 3 3 0 0 0 0 6 3 3 0 0 0 3 3m6-12a3 3 0 0 1 3 3 3 3 0 0 1 0 6 3 3 0 0 1-3 3M9 5v14m6-14v14",
    "translate": "M4 5h9M9 5c-.4 4-2 7-5 9m3-5c1 2 3 4 6 5M15 19l4-10 4 10m-6.5-3h5",
    "workflow": "M5 7h5v5H5zM14 12h5v5h-5zM10 9h4m-2 0v5",
    "upload": "M12 17V4m0 0-5 5m5-5 5 5M5 20h14",
    "play": "M8 5v14l11-7z",
    "reset": "M4 12a8 8 0 1 0 3-6M4 5v7h7",
    "spark": "M12 3l1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7z",
    "download": "M12 4v12m0 0 4-4m-4 4-4-4M5 20h14",
    "close": "M18 6 6 18M6 6l12 12",
    "search": "m21 21-4.3-4.3M10.8 18a7.2 7.2 0 1 1 0-14.4 7.2 7.2 0 0 1 0 14.4Z",
    "check": "M4 12l5 5L20 6",
    "shield": "M12 3l7 3v6c0 4-3 7-7 8-4-1-7-4-7-8V6z",
    "bolt": "M13 3 4 14h6l-1 7 9-11h-6z",
    "cloud": "M7 18a4 4 0 0 1 0-8 5 5 0 0 1 9.6-1.3A3.5 3.5 0 0 1 18 18z",
    "gift": "M4 11h16v9H4zM4 8h16v3H4zM12 8V5m0 3c-2 0-4-1-4-2s2-1 4 1c2-2 4-2 4-1s-2 2-4 2",
    "offline": "M3 3l18 18M8 18a4 4 0 0 1 0-8M16.5 8.6A5 5 0 0 0 7 7",
    "star": "M12 3l2.9 6 6.6.6-5 4.3 1.5 6.5L12 17l-5.9 3.4L7.6 14l-5-4.3 6.6-.6z",
    "menu": "M4 7h16M4 12h16M4 17h16",
    "arrow": "M5 12h14m0 0-6-6m6 6-6 6",
    "sun": "M12 5V3m0 18v-2m7-7h2M3 12h2m12.7-6.7 1.4-1.4M4.9 19.1l1.4-1.4m0-11.4L4.9 4.9m14.2 14.2-1.4-1.4M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z",
    "moon": "M20 14A8 8 0 1 1 10 4a6 6 0 0 0 10 10Z",
    "mail": "M4 6h16v12H4zM4 7l8 6 8-6",
    "phone": "M6 3h4l1 5-3 2a11 11 0 0 0 6 6l2-3 5 1v4a1 1 0 0 1-1 1A17 17 0 0 1 5 4a1 1 0 0 1 1-1Z",
}


def get_tool(tool_id: str) -> Optional[Dict[str, Any]]:
    """Return a tool definition by id, or ``None`` if it does not exist."""

    return next((tool for tool in TOOLS if tool["id"] == tool_id), None)


def get_tool_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Return a tool definition by its URL slug."""

    return next((tool for tool in TOOLS if tool["slug"] == slug), None)


def tools_by_category(category: str) -> List[Dict[str, Any]]:
    """Return every tool belonging to a category."""

    return [tool for tool in TOOLS if tool["category"] == category]


# Tools featured on the landing hero / primary grid, in display order.
FEATURED_TOOL_IDS: List[str] = [
    "merge_pdf", "split_pdf", "compress_pdf", "pdf_to_word", "word_to_pdf",
    "pdf_to_jpg", "jpg_to_pdf", "ocr_pdf", "rotate_pdf", "repair_pdf",
    "unlock_pdf", "protect_pdf", "watermark_pdf", "remove_pages",
    "extract_pages", "crop_pdf", "page_numbers", "organize_pdf",
]
