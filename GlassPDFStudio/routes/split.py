"""Split blueprint: friendly ``/split`` alias for the Split PDF workspace."""

from __future__ import annotations

from flask import Blueprint

from . import render_tool_workspace

split_bp = Blueprint("split", __name__)


@split_bp.route("/split")
def split():
    return render_tool_workspace("split-pdf", "split.html")
