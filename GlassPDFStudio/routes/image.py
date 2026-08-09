"""Image blueprint: friendly aliases for the image-oriented tools."""

from __future__ import annotations

from flask import Blueprint

from . import render_tool_workspace

image_bp = Blueprint("image", __name__)


@image_bp.route("/jpg-to-pdf")
def jpg_to_pdf():
    return render_tool_workspace("jpg-to-pdf", "jpg_to_pdf.html")


@image_bp.route("/scan-to-pdf")
def scan_to_pdf():
    return render_tool_workspace("scan-to-pdf")
