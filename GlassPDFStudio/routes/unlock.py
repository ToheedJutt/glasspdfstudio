"""Unlock blueprint: friendly ``/unlock`` alias for Unlock PDF."""

from __future__ import annotations

from flask import Blueprint

from . import render_tool_workspace

unlock_bp = Blueprint("unlock", __name__)


@unlock_bp.route("/unlock")
def unlock():
    return render_tool_workspace("unlock-pdf", "unlock.html")
