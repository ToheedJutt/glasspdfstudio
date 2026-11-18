"""Home blueprint: landing page, all-tools, AI, contact + errors."""

from __future__ import annotations

from flask import Blueprint, render_template, send_from_directory

from catalog import (
    CATEGORIES,
    FEATURED_TOOL_IDS,
    TOOLS,
    get_tool,
    tools_by_category,
)
from config import STATIC_DIR
home_bp = Blueprint("home", __name__)


def _featured_tools():
    """Resolve the featured tool ids into full tool dicts, preserving order."""

    return [get_tool(tool_id) for tool_id in FEATURED_TOOL_IDS if get_tool(tool_id)]


@home_bp.route("/")
def index():
    """Premium landing page with hero, featured grid and feature highlights."""

    return render_template(
        "index.html",
        featured_tools=_featured_tools(),
        categories=CATEGORIES,
        tools_by_category={c["id"]: tools_by_category(c["id"]) for c in CATEGORIES},
    )


@home_bp.route("/sw.js")
def service_worker():
    """Serve the PWA service worker from the site root.

    The file lives in static/, but a worker registered from /static/sw.js
    could only control pages under /static/ — serving it at /sw.js gives
    it scope over the whole site. Sent uncached so updates roll out.
    """

    response = send_from_directory(STATIC_DIR, "sw.js", mimetype="application/javascript")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@home_bp.route("/tools")
def all_tools():
    """Full catalogue grouped by category with live search + filters.

    Every tool is free for everyone — no tiers, no gating.
    """

    return render_template(
        "all_tools.html",
        categories=CATEGORIES,
        tools_by_category={c["id"]: tools_by_category(c["id"]) for c in CATEGORIES},
        tools=TOOLS,
    )


@home_bp.route("/ai-pdf")
def ai_pdf():
    """Dedicated page for the AI / intelligence tools."""

    ai_tools = tools_by_category("PDF Intelligence")
    return render_template("ai_pdf.html", ai_tools=ai_tools)


@home_bp.route("/contact")
def contact():
    """Static contact page with a message form and company details."""

    return render_template("contact.html")
