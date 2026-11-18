"""Desktop entry point for GlassPDF Studio.

Starts the Flask app under waitress on 127.0.0.1:5055 in a background
thread, waits until the engine answers its health probe, then shows the
UI in a native pywebview window. If pywebview is unavailable (or no GUI
backend can start), it falls back to the user's default browser and
keeps the server alive until the process is stopped.

Works both ways:

* unfrozen — ``python desktop.py`` from this folder;
* frozen   — as the PyInstaller entry point (see ``glasspdf.spec``).

Frozen-path shim
----------------
``config.py`` derives every path from ``Path(__file__).parent``. In a
frozen one-folder build that is the bundle's ``_internal`` folder, which
holds the bundled templates/static — correct for reads. But the bundle
may be read-only (macOS app translocation, ``Program Files`` on
Windows), so the *writable* state (job storage, uploads, outputs, temp,
the SQLite database) is redirected to a per-user data directory before
the app is imported. ``routes``/``services`` read those constants from
the ``config`` module at import time, so patching the module attributes
here — before ``import app`` — propagates everywhere. Read-only assets
(templates, static) stay pointed at the bundle.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

HOST = "127.0.0.1"
PORT = int(os.getenv("PORT", "5055"))
HEALTH_URL = f"http://{HOST}:{PORT}/api/health"
APP_URL = f"http://{HOST}:{PORT}"


def _user_data_dir() -> Path:
    """Per-user writable directory for the frozen app's state."""

    if sys.platform == "win32":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "GlassPDFStudio"


def _apply_frozen_shim() -> None:
    """Redirect writable state out of the (possibly read-only) bundle.

    Only runs when frozen. Must run before ``app`` (and therefore
    ``routes``/``services``) is imported.
    """

    if not getattr(sys, "frozen", False):
        return

    import config

    data_dir = _user_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    config.STORAGE_DIR = data_dir / "storage"
    config.JOBS_DIR = config.STORAGE_DIR / "jobs"
    config.UPLOADS_DIR = data_dir / "uploads"
    config.OUTPUTS_DIR = data_dir / "outputs"
    config.TEMP_DIR = data_dir / "temp"
    config.DATABASE_PATH = data_dir / "glasspdstudio.db"

    # Only override the database location when the operator has not
    # configured one explicitly (mirrors config.py's own precedence).
    if not os.getenv("DATABASE_URL"):
        config.Config.SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{config.DATABASE_PATH}"
        )


def _wait_for_health(timeout: float = 60.0) -> bool:
    """Poll the health endpoint until the engine answers or time runs out."""

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=2) as response:
                if response.status == 200:
                    return True
        except Exception:  # noqa: BLE001 - server not up yet, keep polling
            time.sleep(0.25)
    return False


def _serve(flask_app) -> threading.Thread:
    """Run waitress on a daemon thread so the main thread owns the GUI."""

    from waitress import serve

    thread = threading.Thread(
        target=serve,
        kwargs={
            "app": flask_app,
            "host": HOST,
            "port": PORT,
            "threads": 8,
            "_quiet": True,
        },
        name="glasspdf-server",
        daemon=True,
    )
    thread.start()
    return thread


def _open_window() -> bool:
    """Show the UI in a pywebview window. Returns False if that failed."""

    try:
        import webview
    except Exception:  # noqa: BLE001 - pywebview not installed
        return False

    try:
        webview.create_window(
            "GlassPDF Studio",
            APP_URL,
            width=1280,
            height=860,
            min_size=(900, 600),
        )
        webview.start()
        return True
    except Exception:  # noqa: BLE001 - no GUI backend / headless / etc.
        return False


def main() -> int:
    # PyInstaller + Windows: harmless elsewhere, required for frozen
    # multiprocessing support.
    import multiprocessing

    multiprocessing.freeze_support()

    # Make sibling modules importable when run as a plain script from
    # any working directory (a no-op when frozen).
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))

    _apply_frozen_shim()

    from app import app as flask_app

    _serve(flask_app)

    if not _wait_for_health():
        print(f"GlassPDF Studio server did not come up on {APP_URL}", file=sys.stderr)
        return 1

    if not _open_window():
        # Fallback: default browser, then keep the server alive until
        # the user stops the process (Ctrl+C / closing the console).
        webbrowser.open(APP_URL)
        print(f"GlassPDF Studio is running at {APP_URL} — press Ctrl+C to stop.")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
