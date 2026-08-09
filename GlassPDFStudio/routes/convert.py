"""Convert blueprint: friendly aliases for the document conversion tools.

Covers both PDF->Office and Office->PDF plus HTML->PDF, each mapping to a
bespoke or generic workspace template.
"""

from __future__ import annotations

from flask import Blueprint

from . import render_tool_workspace

convert_bp = Blueprint("convert", __name__)


@convert_bp.route("/pdf-to-word")
def pdf_to_word():
    return render_tool_workspace("pdf-to-word", "pdf_to_word.html")


@convert_bp.route("/word-to-pdf")
def word_to_pdf():
    return render_tool_workspace("word-to-pdf", "word_to_pdf.html")


@convert_bp.route("/pdf-to-jpg")
def pdf_to_jpg():
    return render_tool_workspace("pdf-to-jpg", "pdf_to_jpg.html")


@convert_bp.route("/pdf-to-powerpoint")
def pdf_to_powerpoint():
    return render_tool_workspace("pdf-to-powerpoint")


@convert_bp.route("/pdf-to-excel")
def pdf_to_excel():
    return render_tool_workspace("pdf-to-excel")


@convert_bp.route("/powerpoint-to-pdf")
def powerpoint_to_pdf():
    return render_tool_workspace("powerpoint-to-pdf")


@convert_bp.route("/excel-to-pdf")
def excel_to_pdf():
    return render_tool_workspace("excel-to-pdf")


@convert_bp.route("/html-to-pdf")
def html_to_pdf():
    return render_tool_workspace("html-to-pdf")


@convert_bp.route("/pdf-to-pdfa")
def pdf_to_pdfa():
    return render_tool_workspace("pdf-to-pdfa")
