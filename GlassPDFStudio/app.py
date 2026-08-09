"""GlassPDFStudio application factory.

Creates the Flask app, wires configuration, registers every blueprint, exposes
the tool catalogue to Jinja, and defines the 404 handler. Run directly
(``python app.py``) to start the dev server on the port the launcher probes.
"""

from __future__ import annotations

import json

from flask import Flask, render_template

from catalog import CATEGORIES, ICON_PATHS, TOOLS
from config import STATIC_DIR, TEMPLATES_DIR, Config, ensure_directories
from models import db
from services.mail_service import mail
from routes import register_blueprints


def create_app() -> Flask:
    """Build and configure the GlassPDFStudio Flask application."""

    ensure_directories()

    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        static_url_path="/static",
        template_folder=str(TEMPLATES_DIR),
    )
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    register_blueprints(app)
    _register_template_context(app)
    _register_error_handlers(app)
    _register_response_headers(app)

    return app


def _register_template_context(app: Flask) -> None:
    """Expose the catalogue + helpers to every Jinja template."""

    @app.context_processor
    def inject_globals() -> dict:
        return {
            "APP_NAME": Config.APP_NAME,
            "APP_VERSION": Config.APP_VERSION,
            "ASSET_VERSION": Config.ASSET_VERSION,
            "ALL_TOOLS": TOOLS,
            "CATEGORIES": CATEGORIES,
            "ICON_PATHS": ICON_PATHS,
            # Serialised once so client scripts can hydrate without an API call.
            "TOOLS_JSON": json.dumps(TOOLS),
            "ICONS_JSON": json.dumps(ICON_PATHS),
        }

    @app.template_filter("svg_icon")
    def svg_icon(name: str) -> str:
        """Render a named icon as an inline SVG string."""

        path = ICON_PATHS.get(name, ICON_PATHS["doc"])
        return (
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true"><path d="{path}"/></svg>'
        )


def _register_error_handlers(app: Flask) -> None:
    """Friendly, on-brand error pages."""

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404


def _register_response_headers(app: Flask) -> None:
    """Preserve the permissive CORS headers from the original app."""

    @app.after_request
    def add_local_file_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response


# Module-level app so ``flask run`` and WSGI servers can discover it.
app = create_app()


if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
