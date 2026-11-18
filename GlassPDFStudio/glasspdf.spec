# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the GlassPDF Studio desktop app.

Build (from this folder):
    pyinstaller glasspdf.spec --noconfirm

One-folder mode. Layout of the result:

    dist/GlassPDFStudio/
        GlassPDFStudio(.exe)     <- launcher
        _internal/               <- bundled code + data (sys._MEIPASS)
            templates/           <- Flask templates (config.TEMPLATES_DIR)
            static/              <- CSS/JS + PWA manifest, sw.js, icons
            index.html           <- standalone SPA shell

Path strategy: config.py derives BASE_DIR from Path(__file__).parent,
which PyInstaller sets inside _internal for frozen modules — so the
bundled templates/static resolve with no app-code changes. Writable
state (storage, DB) is redirected to a per-user data dir by the shim in
desktop.py, so nothing here needs to be writable at runtime.

NOTE: the local .env file is deliberately NOT bundled (it can hold
secrets); the frozen app runs on config.py defaults + real env vars.
"""

import os
import sys

from PyInstaller.utils.hooks import collect_data_files

SPECPATH = os.path.dirname(os.path.abspath(SPEC))


def _data(source: str, dest: str):
    return (os.path.join(SPECPATH, source), dest)


datas = [
    _data("templates", "templates"),
    _data("static", "static"),
    _data("index.html", "."),
]

# python-docx / python-pptx load bundled template documents from inside
# their packages at runtime; PyInstaller's default analysis misses them.
datas += collect_data_files("docx")
datas += collect_data_files("pptx")

a = Analysis(
    [os.path.join(SPECPATH, "desktop.py")],
    pathex=[SPECPATH],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GlassPDFStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # Windowed build: no console window on Windows/macOS.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="GlassPDFStudio",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="GlassPDFStudio.app",
        icon=None,
        bundle_identifier="com.glasspdfstudio.app",
        info_plist={
            "CFBundleName": "GlassPDF Studio",
            "CFBundleDisplayName": "GlassPDF Studio",
            "NSHighResolutionCapable": True,
        },
    )
