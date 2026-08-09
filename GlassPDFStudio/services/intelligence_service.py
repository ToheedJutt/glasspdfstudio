"""Intelligence service: local summarisation, translation and workflows."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import List, Tuple

from .common import (
    ToolError,
    create_text_pdf,
    extract_pdf_text,
    require_files,
    require_pdf,
)


# --------------------------------------------------------------------------- #
# Summarisation
# --------------------------------------------------------------------------- #
def summarize_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Rank sentences by keyword frequency to build a short local summary."""

    require_files(files)
    require_pdf(files[0])
    text = "\n".join(extract_pdf_text(files[0], opts.get("password") or None))
    sentences = split_sentences(text)
    limit = int(opts.get("sentences") or 8)
    summary = rank_sentences(sentences, limit)
    output = output_dir / "summary.pdf"
    create_text_pdf(output, "PDF summary",
                    summary or ["No selectable text found to summarize."])
    return output, f"Generated a {len(summary)} sentence local summary.", []


def split_sentences(text: str) -> List[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", clean)
            if len(sentence.strip()) > 20]


def rank_sentences(sentences: List[str], limit: int) -> List[str]:
    if not sentences:
        return []
    stop = {"the", "and", "for", "that", "with", "this", "from", "are", "was",
            "were", "have", "has", "you", "your", "not", "but"}
    words = re.findall(r"[a-zA-Z]{4,}", " ".join(sentences).lower())
    freq: dict[str, int] = {}
    for word in words:
        if word not in stop:
            freq[word] = freq.get(word, 0) + 1
    scored = []
    for index, sentence in enumerate(sentences):
        score = sum(freq.get(word.lower(), 0)
                    for word in re.findall(r"[a-zA-Z]{4,}", sentence))
        scored.append((score, index, sentence))
    top = sorted(scored, reverse=True)[: max(1, limit)]
    return [item[2] for item in sorted(top, key=lambda row: row[1])]


# --------------------------------------------------------------------------- #
# Translation (offline dictionary fallback)
# --------------------------------------------------------------------------- #
def translate_pdf(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Translate extracted PDF text with a small offline dictionary."""

    require_files(files)
    require_pdf(files[0])
    target = opts.get("target") or "Spanish"
    text = "\n".join(extract_pdf_text(files[0], opts.get("password") or None))
    translated, details = translate_text_local(text, target)
    output = output_dir / "translated_text.pdf"
    create_text_pdf(output, f"Translated text - {target}", [translated])
    return output, f"Created a {target} translation document.", details


def translate_text_local(text: str, target: str) -> Tuple[str, List[str]]:
    dictionaries = {
        "spanish": {
            "hello": "hola", "world": "mundo", "invoice": "factura", "date": "fecha",
            "total": "total", "name": "nombre", "address": "direccion",
            "thank": "gracias", "you": "usted", "page": "pagina",
        },
        "french": {
            "hello": "bonjour", "world": "monde", "invoice": "facture", "date": "date",
            "total": "total", "name": "nom", "address": "adresse", "thank": "merci",
            "you": "vous", "page": "page",
        },
        "urdu": {
            "hello": "salam", "world": "dunya", "invoice": "bill", "date": "tareekh",
            "total": "kul", "name": "naam", "address": "pata", "thank": "shukriya",
            "you": "aap", "page": "safha",
        },
    }
    key = target.strip().lower()
    dictionary = dictionaries.get(key)
    if not dictionary:
        return text, [f"No offline dictionary is configured for {target}. "
                      "The extracted text was packaged as a PDF."]

    def replace(match: re.Match) -> str:
        word = match.group(0)
        lower = word.lower()
        replacement = dictionary.get(lower, word)
        return replacement.capitalize() if word[:1].isupper() else replacement

    translated = re.sub(r"\b[A-Za-z]+\b", replace, text)
    return translated, ["Offline dictionary translation is basic. Connect a "
                        "translation API for production-quality results."]


# --------------------------------------------------------------------------- #
# Workflow orchestration
# --------------------------------------------------------------------------- #
def create_workflow(files: List[Path], opts: dict, output_dir: Path) -> Tuple[Path, str, list]:
    """Run a chain of allowed tools, feeding each output into the next step."""

    # Imported lazily to avoid a circular import at module load time.
    from .compress_service import compress_pdf, repair_pdf
    from .edit_service import page_numbers, rotate_pdf, watermark_pdf
    from .security_service import protect_pdf

    require_files(files)
    current = files[0]
    steps = opts.get("steps") or []
    if not isinstance(steps, list) or not steps:
        raise ToolError("Choose at least one workflow step.")
    details: List[str] = []
    allowed = {
        "compress_pdf": compress_pdf,
        "repair_pdf": repair_pdf,
        "page_numbers": page_numbers,
        "watermark_pdf": watermark_pdf,
        "protect_pdf": protect_pdf,
        "rotate_pdf": rotate_pdf,
    }
    for index, step in enumerate(steps, start=1):
        if step not in allowed:
            raise ToolError(f"Workflow step is not supported locally: {step}")
        step_dir = output_dir / f"step_{index}_{step}"
        step_dir.mkdir()
        step_options = opts.get("stepOptions", {})
        step_opts = {**opts,
                     **(step_options.get(step, {}) if isinstance(step_options, dict) else {})}
        result, message, extra = allowed[step]([current], step_opts, step_dir)
        current = result
        details.append(f"{index}. {message}")
        details.extend(extra)
    final = output_dir / f"workflow_result{current.suffix}"
    shutil.copyfile(current, final)
    return final, "Workflow completed.", details
