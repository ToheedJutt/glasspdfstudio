"""Application configuration for GlassPDFStudio.

Centralises every path and tunable constant so the rest of the codebase can
import from one place. Keeping this isolated makes the app factory in
``app.py`` small and keeps the service layer free of filesystem literals.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# --------------------------------------------------------------------------- #
# Filesystem layout
# --------------------------------------------------------------------------- #
BASE_DIR: Path = Path(__file__).resolve().parent

# Long-lived per-job storage (uploads + generated outputs). This mirrors the
# original layout so existing download URLs (``/download/<job>/<file>``) keep
# working without migration.
STORAGE_DIR: Path = BASE_DIR / "storage"
JOBS_DIR: Path = STORAGE_DIR / "jobs"

# Convenience working directories requested by the target architecture. They
# are created on boot even though most tools stream through the per-job dirs.
UPLOADS_DIR: Path = BASE_DIR / "uploads"
OUTPUTS_DIR: Path = BASE_DIR / "outputs"
TEMP_DIR: Path = BASE_DIR / "temp"

# Frontend asset roots.
STATIC_DIR: Path = BASE_DIR / "static"
TEMPLATES_DIR: Path = BASE_DIR / "templates"

# Database file
DATABASE_PATH: Path = BASE_DIR / "glasspdstudio.db"


# --------------------------------------------------------------------------- #
# Runtime settings
# --------------------------------------------------------------------------- #
class Config:
    """Base Flask configuration."""

    # Load from environment variables or use defaults
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "dev-secret-change-me"
    )
    
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")

    # Generous ceiling for large scanned documents (350 MB, unchanged).
    MAX_CONTENT_LENGTH: int = int(
        os.getenv("MAX_CONTENT_LENGTH", 350 * 1024 * 1024)
    )

    # Where the dev server binds. The Windows launcher health-checks this port.
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 5055))

    # Database configuration
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{DATABASE_PATH}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Email configuration
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS: bool = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER: str = os.getenv(
        "MAIL_DEFAULT_SENDER", "noreply@glasspdstudio.com"
    )

    # Application metadata
    APP_NAME: str = os.getenv("APP_NAME", "GlassPDFStudio")
    APP_VERSION: str = os.getenv("APP_VERSION", "2.0.0")

    # Static build tag appended to asset URLs for cache busting.
    ASSET_VERSION: str = "2"

    # OTP settings
    OTP_EXPIRY_SECONDS: int = int(os.getenv("OTP_EXPIRY_SECONDS", 900))
    OTP_LENGTH: int = int(os.getenv("OTP_LENGTH", 6))

    # Conversion used on the pricing page to show PKR -> USD approximations.
    PKR_TO_USD: float = float(os.getenv("PKR_TO_USD", 0.0034))

    # Admin contact
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@glasspdstudio.com")


def ensure_directories() -> None:
    """Create every runtime directory if it does not already exist."""

    for directory in (JOBS_DIR, UPLOADS_DIR, OUTPUTS_DIR, TEMP_DIR):
        directory.mkdir(parents=True, exist_ok=True)

