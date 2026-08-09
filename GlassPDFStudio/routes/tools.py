"""Tools blueprint: canonical ``/tools/<slug>`` workspace for every tool.

Some tools have a hand-crafted template (merge, split, ...) listed in the
target architecture; the rest fall back to the generic ``tool.html``. Either
way every tool in the catalogue resolves to a working, styled page.
"""

from __future__ import annotations

from flask import Blueprint

from . import render_tool_workspace

tools_bp = Blueprint("tools", __name__)


# Slugs that ship a bespoke template. Everything else uses tool.html.
TEMPLATE_OVERRIDES = {
    "merge-pdf": "merge.html",
    "split-pdf": "split.html",
    "compress-pdf": "compress.html",
    "pdf-to-word": "pdf_to_word.html",
    "word-to-pdf": "word_to_pdf.html",
    "pdf-to-jpg": "pdf_to_jpg.html",
    "jpg-to-pdf": "jpg_to_pdf.html",
    "rotate-pdf": "rotate.html",
    "unlock-pdf": "unlock.html",
    "protect-pdf": "protect.html",
    "watermark-pdf": "watermark.html",
}


@tools_bp.route("/tools/<slug>")
def page(slug: str):
    """Render the workspace for ``slug`` using its bespoke or generic template."""

    template = TEMPLATE_OVERRIDES.get(slug, "tool.html")
    return render_tool_workspace(slug, template)
