"""Rotate blueprint: friendly ``/rotate`` alias for Rotate PDF."""

from __future__ import annotations

from flask import Blueprint

from . import render_tool_workspace

rotate_bp = Blueprint("rotate", __name__)


@rotate_bp.route("/rotate")
def rotate():
    return render_tool_workspace("rotate-pdf", "rotate.html")
