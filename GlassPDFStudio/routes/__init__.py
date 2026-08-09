"""Route package: blueprint registration and shared page helpers.

The UI links to the canonical ``/tools/<slug>`` URL for every one of the 33
tools (see ``tools`` blueprint), which guarantees each tool has a working page.
The dedicated blueprint modules requested by the architecture
(``merge``, ``split`` ...) provide friendly short-URL aliases that render the
exact same workspace.
"""

from __future__ import annotations

from typing import Optional

from flask import Flask, abort, render_template

from catalog import get_tool_by_slug


def render_tool_workspace(slug: str, template: str = "tool.html"):
    """Render a tool workspace page for the tool identified by ``slug``.

    ``template`` lets the dedicated blueprints point at their own named
    template (e.g. ``merge.html``) while sharing this lookup + 404 logic.
    """

    tool = get_tool_by_slug(slug)
    if tool is None:
        abort(404)
    return render_template(template, tool=tool)


def register_blueprints(app: Flask) -> None:
    """Import and register every blueprint on the Flask app."""

    from .api import api_bp
    from .home import home_bp
    from .tools import tools_bp
    from .merge import merge_bp
    from .split import split_bp
    from .compress import compress_bp
    from .convert import convert_bp
    from .protect import protect_bp
    from .unlock import unlock_bp
    from .rotate import rotate_bp
    from .watermark import watermark_bp
    from .image import image_bp
    from .auth import auth_bp

    for blueprint in (
        api_bp, home_bp, tools_bp, merge_bp, split_bp, compress_bp, convert_bp,
        protect_bp, unlock_bp, rotate_bp, watermark_bp, image_bp, auth_bp,
    ):
        app.register_blueprint(blueprint)
