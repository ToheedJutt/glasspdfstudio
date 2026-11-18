# GlassPDF Studio

**A local-first PDF toolkit with a frosted-glass dashboard — every file stays on your machine.**

GlassPDF Studio is a full PDF utility suite that runs entirely on localhost: a Flask backend and a clean, iOS-style glass interface in the browser. No uploads to third-party servers, no file ever leaves your computer.

![Python](https://img.shields.io/badge/Python-3.12+-blue) ![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey) ![License](https://img.shields.io/badge/License-MIT-green)
**🌐 Project website:** [toheedjutt.github.io/glasspdfstudio](https://toheedjutt.github.io/glasspdfstudio/)
**▶️ Live demo:** [glasspdfstudio.onrender.com](https://glasspdfstudio.onrender.com/)

## Features

**Organize**
- Merge multiple PDFs into one
- Split a PDF by pages or ranges
- Compress PDFs with quality control
- Rotate pages

**Convert**
- PDF → Word, Excel, PowerPoint
- Word / Excel / PowerPoint → PDF (layout-accurate via LibreOffice)
- HTML → PDF
- PDF → PDF/A archivable copy

**Edit & secure**
- Add text and shapes directly onto pages
- Watermark with custom text, position, opacity and color
- Protect with a password, or unlock a protected copy

**Images**
- PDF → JPG (every page rendered)
- JPG → PDF, including a scan-style mode

Accounts with email verification, a tools catalogue, and an AI PDF assistant page are built in.

## Quick start

```bash
git clone https://github.com/ToheedJutt/glasspdfstudio.git
cd glasspdfstudio/GlassPDFStudio
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5055**.

On Windows you can also just run `Start GlassPDFStudio.bat` — it creates the virtual environment, installs dependencies, waits for the health endpoint, and opens the dashboard for you.

Copy `.env.example` to `.env` and set your own `SECRET_KEY` and mail settings before using accounts in production.

## Optional engines

| Engine | Needed for |
|---|---|
| [LibreOffice](https://www.libreoffice.org/) | Layout-accurate Office ↔ PDF conversion |
| [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | Text recognition in scanned documents |

Without them the app still works — it falls back to local text extraction and tells you exactly what is missing.

## Tech stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Mail, Waitress
- **PDF engines:** PyMuPDF, pypdf, ReportLab
- **Documents:** python-docx, openpyxl, python-pptx, Pillow
- **Frontend:** HTML, CSS, JavaScript (glassmorphism UI, no framework)

## Project structure

```
glasspdfstudio/
├── GlassPDFStudio/     # the application
│   ├── app.py          # application factory
│   ├── routes/         # blueprints: one module per tool family + API + auth
│   ├── services/       # the processing engines behind every tool
│   ├── templates/      # Jinja pages
│   └── static/         # CSS / JS / assets
├── SETUP_GUIDE.md
└── README.md
```

## License

MIT — see [LICENSE](LICENSE).
