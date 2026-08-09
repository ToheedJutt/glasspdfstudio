"""Watermark blueprint: friendly ``/watermark`` alias for Watermark PDF."""

from __future__ import annotations

from flask import Blueprint

from . import render_tool_workspace

watermark_bp = Blueprint("watermark", __name__)


@watermark_bp.route("/watermark")
def watermark():
    return render_tool_workspace("watermark-pdf", "watermark.html")
