"""Merge blueprint: friendly ``/merge`` alias for the Merge PDF workspace."""

from __future__ import annotations

from flask import Blueprint

from . import render_tool_workspace

merge_bp = Blueprint("merge", __name__)


@merge_bp.route("/merge")
def merge():
    return render_tool_workspace("merge-pdf", "merge.html")
