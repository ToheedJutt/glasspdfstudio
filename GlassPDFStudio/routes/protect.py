"""Protect blueprint: friendly ``/protect`` alias for Protect PDF."""

from __future__ import annotations

from flask import Blueprint

from . import render_tool_workspace

protect_bp = Blueprint("protect", __name__)


@protect_bp.route("/protect")
def protect():
    return render_tool_workspace("protect-pdf", "protect.html")
