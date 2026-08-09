"""Compress blueprint: friendly ``/compress`` alias for Compress PDF."""

from __future__ import annotations

from flask import Blueprint

from . import render_tool_workspace

compress_bp = Blueprint("compress", __name__)


@compress_bp.route("/compress")
def compress():
    return render_tool_workspace("compress-pdf", "compress.html")
