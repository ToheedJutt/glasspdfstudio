"""Core API blueprint: the processing engine behind every tool.

This preserves the original public contract exactly:

* ``POST /api/process``  -> run a tool over uploaded files + JSON options
* ``GET  /download/<job>/<file>`` -> stream a generated output as attachment
* ``GET  /api/health``   -> engine + optional-dependency status

Keeping these routes byte-compatible means the frontend (and the Windows
launcher's health probe) works without any migration.
"""

from __future__ import annotations

import json
import shutil
import subprocess

from flask import Blueprint, jsonify, request, send_from_directory, session
from werkzeug.utils import secure_filename

from config import JOBS_DIR, Config
from services import TOOL_HANDLERS, ToolError
from services.common import find_soffice, new_job, response_for, save_uploads

api_bp = Blueprint("api", __name__)


def _record_activity(tool_id: str, files, output, job_id: str) -> None:
    """Save this job to the signed-in member's file history.

    Best-effort by design: history is a member perk, and recording it
    must never break the tool the user actually came for.
    """
    try:
        user = session.get("user")
        if not user:
            return
        first = output[0] if isinstance(output, (list, tuple)) else output
        from services.user_service import record_activity

        record_activity(
            email=user,
            tool=tool_id,
            input_names=[f.name for f in files],
            output_name=first.name,
            job_id=job_id,
            output_size=first.stat().st_size if first.exists() else 0,
        )
    except Exception:  # noqa: BLE001 - never let bookkeeping break a tool
        pass


def _get_options() -> dict:
    """Parse the ``options`` form field as a JSON object (or empty dict)."""

    raw = request.form.get("options") or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolError("Options are not valid JSON.") from exc
    return data if isinstance(data, dict) else {}


@api_bp.route("/api/process", methods=["POST"])
def process_tool():
    """Dispatch an uploaded job to its tool handler and return a JSON result."""

    job_id, _job_dir, upload_dir, output_dir = new_job()
    try:
        tool_id = request.form.get("tool") or ""
        if tool_id not in TOOL_HANDLERS:
            raise ToolError("Unknown tool.")
        files = save_uploads(upload_dir)
        opts = _get_options()
        output, message, details = TOOL_HANDLERS[tool_id](files, opts, output_dir)
        _record_activity(tool_id, files, output, job_id)
        return jsonify({"ok": True, **response_for(job_id, output, message, details)})
    except ToolError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except subprocess.CalledProcessError as exc:
        error = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else str(exc)
        return jsonify({"ok": False, "error": error}), 500
    except Exception as exc:  # noqa: BLE001 - surface any engine error to the client
        return jsonify({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), 500


@api_bp.route("/download/<job_id>/<filename>")
def download(job_id: str, filename: str):
    """Serve a generated output file as a download attachment."""

    safe_job = secure_filename(job_id)
    safe_name = secure_filename(filename)
    directory = JOBS_DIR / safe_job / "outputs"
    return send_from_directory(directory, safe_name, as_attachment=True)


@api_bp.route("/api/health")
def health():
    """Report engine readiness and which optional engines are installed."""

    return jsonify(
        {
            "ok": True,
            "soffice": bool(find_soffice()),
            "tesseract": bool(shutil.which("tesseract")),
            "version": Config.APP_VERSION,
        }
    )
