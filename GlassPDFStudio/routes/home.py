"""Home blueprint: landing page, all-tools, AI, pricing, contact + errors."""

from __future__ import annotations

from flask import Blueprint, render_template, send_from_directory

from catalog import (
    CATEGORIES,
    FEATURED_TOOL_IDS,
    TOOLS,
    get_tool,
    tools_by_category,
)
from config import Config, STATIC_DIR
from flask import session, request, redirect, flash
from services.user_service import (
    start_trial, is_trial_active, trial_end_date,
    is_ip_device_blocked_from_trial, get_accessible_tools
)

home_bp = Blueprint("home", __name__)


def _get_ip_address() -> str:
    """Extract user's IP address from request, handling proxies."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or "unknown"


def _get_device_id() -> str:
    """Generate a simple device fingerprint from User-Agent and IP."""
    import hashlib
    user_agent = request.headers.get('User-Agent', 'unknown')
    ip = _get_ip_address()
    fingerprint = f"{ip}:{user_agent}"
    return hashlib.md5(fingerprint.encode()).hexdigest()[:16]


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
    """Full catalogue grouped by category with live search + filters."""
    user = session.get("user")
    accessible_tools_ids = get_accessible_tools(user)
    
    # Filter tools based on user tier if necessary
    if accessible_tools_ids is not None:  # None means all tools (trial users)
        filtered_tools = [t for t in TOOLS if t["id"] in accessible_tools_ids]
    else:
        filtered_tools = TOOLS
    
    # Also filter tools_by_category
    filtered_by_category = {}
    for category in CATEGORIES:
        cat_tools = tools_by_category(category["id"])
        if accessible_tools_ids is not None:
            cat_tools = [t for t in cat_tools if t["id"] in accessible_tools_ids]
        filtered_by_category[category["id"]] = cat_tools

    return render_template(
        "all_tools.html",
        categories=CATEGORIES,
        tools_by_category=filtered_by_category,
        tools=filtered_tools,
        user_tier="trial" if user and is_trial_active(user) else "free",
    )


@home_bp.route("/ai-pdf")
def ai_pdf():
    """Dedicated page for the AI / intelligence tools."""

    ai_tools = tools_by_category("PDF Intelligence")
    return render_template("ai_pdf.html", ai_tools=ai_tools)


@home_bp.route("/pricing")
def pricing():
    """Pricing tiers (all tools are free; this showcases the SaaS framing)."""

    # Project-specific pricing shown in PKR with USD approximations.
    monthly_pkr = 500
    original_pkr = 1199
    full_pkr = 15000
    user = session.get("user")
    trial_active = False
    trial_ends = None
    trial_eligible = True
    
    if user:
        trial_active = is_trial_active(user)
        te = trial_end_date(user)
        if te:
            import datetime
            trial_ends = datetime.datetime.fromtimestamp(te)
        # User is not eligible if already used trial or has active trial
        if trial_active or trial_ends:
            trial_eligible = False
    
    # Check if this IP/device is blocked from claiming another trial
    ip_addr = _get_ip_address()
    device_id = _get_device_id()
    if is_ip_device_blocked_from_trial(ip_addr, device_id):
        trial_eligible = False

    return render_template(
        "pricing.html",
        monthly_pkr=monthly_pkr,
        original_pkr=original_pkr,
        full_pkr=full_pkr,
        pkr_to_usd=Config.PKR_TO_USD,
        current_user=user,
        trial_active=trial_active,
        trial_ends=trial_ends,
        trial_eligible=trial_eligible,
    )


@home_bp.route("/billing/start_trial", methods=("POST",))
def billing_start_trial():
    from routes.auth import url_for
    user = session.get("user")
    if not user:
        flash("Please sign in to start your trial.", "error")
        return redirect(url_for("auth.login"))
    
    # Check IP/device eligibility
    ip_addr = _get_ip_address()
    device_id = _get_device_id()
    
    if is_ip_device_blocked_from_trial(ip_addr, device_id):
        flash("You are not eligible for trial. This device/IP has already claimed a free trial.", "error")
        return redirect(url_for("home.pricing"))
    
    # Check if user already has active or expired trial
    if is_trial_active(user) or trial_end_date(user):
        flash("You are not eligible for trial. You have already used your free trial.", "error")
        return redirect(url_for("home.pricing"))
    
    ok = start_trial(user, ip_addr, device_id)
    if ok:
        flash("Trial started — enjoy 1 month free. We'll remind you before renewal.", "success")
    else:
        flash("Could not start trial. Contact support.", "error")
    return redirect(url_for("home.pricing"))


@home_bp.route("/contact")
def contact():
    """Static contact page with a message form and company details."""

    return render_template("contact.html")
