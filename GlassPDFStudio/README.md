# GlassPDF Studio

Local PDF utility dashboard with a frosted iOS-style interface and Flask backend.

## Run

```powershell
cd "D:\Useful Tools Created By me\GlassPDFStudio"
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5055` after the backend starts.

The easiest launcher is:

```powershell
.\Start GlassPDFStudio.bat
```

The launcher creates `.venv` with Python 3.13 if it is missing, installs `requirements.txt` when packages are not available, waits for the Flask health endpoint, and then opens the dashboard.

## Notes

Most PDF operations run locally through PyMuPDF, pypdf, ReportLab, Pillow, python-docx, openpyxl, and python-pptx.

Office layout-accurate conversion needs LibreOffice. Scanned-image OCR needs Tesseract. The app still provides local text fallbacks and precise messages when those engines are missing.
