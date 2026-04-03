"""
generate_quiz_on_file.py
File-based quiz generation using Ollama (no llama-index required).

Author: Nima Shafie
Rewritten: 2026 — Replaced llama-index RAG pipeline with direct text
extraction + Ollama HTTP API. Keeps the same public interface.

Usage:
    from generate_quiz_on_file import generate_quiz_from_file
    result = generate_quiz_from_file(
        file_path="./data/my_doc.pdf",
        difficulty="Hard",
        number_of_questions=10,
        question_types=["Multiple Choice", "True/False"],
    )

NOTE: For most use cases QuizCraft.py handles file ingestion directly via
pypdf in the UI. This module exists for headless / scripted use.
"""

import io
import os
import sys
import json
import requests

# Re-use shared helpers from generate_quiz_from_prompt
sys.path.insert(0, os.path.dirname(__file__))
from generate_quiz_from_prompt import (
    get_ollama_config,
    sanitize_prompt,
    build_prompt,
    call_ollama,
    extract_quiz_json,
    normalize_question,
    DIFFICULTY_PROFILES,
)


# ─────────────────────────────────────────────────────────────────────────────
# Text extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str, max_chars: int = 6000) -> str:
    """Extract plain text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        pages_text = [page.extract_text() or "" for page in reader.pages]
        return " ".join(pages_text)[:max_chars]
    except ImportError:
        raise RuntimeError("pypdf is required: pip install pypdf")
    except Exception as e:
        raise RuntimeError(f"Could not read PDF '{file_path}': {e}")


def extract_text_from_txt(file_path: str, max_chars: int = 6000) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()[:max_chars]


def extract_text(file_path: str, max_chars: int = 6000) -> str:
    """Auto-detect file type and extract text."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path, max_chars)
    elif ext in (".txt", ".md", ".rst"):
        return extract_text_from_txt(file_path, max_chars)
    else:
        # Try plain text as fallback
        try:
            return extract_text_from_txt(file_path, max_chars)
        except Exception:
            raise RuntimeError(
                f"Unsupported file type '{ext}'. Supported: .pdf, .txt, .md"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_quiz_from_file(
    file_path: str,
    difficulty: str = "Medium",
    number_of_questions: int = 10,
    question_types: list[str] | None = None,
    focus_prompt: str = "",
) -> dict:
    """
    Generate a quiz from a file.

    Args:
        file_path:          Path to .pdf or .txt file.
        difficulty:         "Easy", "Medium", or "Hard".
        number_of_questions: How many questions to generate.
        question_types:     List of types; default ["Multiple Choice"].
        focus_prompt:       Optional extra instruction, e.g. "Focus on Chapter 3".

    Returns:
        {"quiz": [...]} or {"quiz": [], "error": "..."} on failure.
    """
    if question_types is None:
        question_types = ["Multiple Choice"]

    # Extract file text
    try:
        file_text = extract_text(file_path)
    except RuntimeError as e:
        return {"quiz": [], "error": str(e)}

    if not file_text.strip():
        return {"quiz": [], "error": f"No text could be extracted from '{file_path}'."}

    # Build the base topic string
    topic = f"the following document content:\n\n{file_text}"
    if focus_prompt.strip():
        clean_focus = sanitize_prompt(focus_prompt)
        if clean_focus:
            topic += f"\n\nAdditional focus: {clean_focus}"

    # Delegate to the same generation pipeline
    host, model = get_ollama_config()
    profile = DIFFICULTY_PROFILES.get(difficulty, DIFFICULTY_PROFILES["Medium"])
    prompt = build_prompt(number_of_questions, difficulty, topic, question_types)

    try:
        raw = call_ollama(prompt, model, host, profile["temperature"])
    except requests.exceptions.ConnectionError:
        return {"quiz": [], "error": f"Cannot connect to Ollama at {host}. Is it running?"}
    except requests.exceptions.Timeout:
        return {"quiz": [], "error": "Ollama request timed out."}
    except Exception as e:
        return {"quiz": [], "error": f"Ollama error: {str(e)}"}

    data = extract_quiz_json(raw)
    if not data:
        return {"quiz": [], "error": "Model did not return valid JSON."}

    questions = [normalize_question(q) for q in data.get("quiz", [])]
    questions = [q for q in questions if q is not None]
    return {"quiz": questions}


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate a quiz from a PDF or text file using Ollama."
    )
    parser.add_argument("file", help="Path to .pdf or .txt file")
    parser.add_argument("--difficulty", default="Medium",
                        choices=["Easy", "Medium", "Hard"])
    parser.add_argument("--questions", type=int, default=10)
    parser.add_argument("--types", default="Multiple Choice",
                        help="Comma-separated: 'Multiple Choice,True/False,Fill in the Blanks'")
    parser.add_argument("--focus", default="",
                        help="Optional focus instruction")
    args = parser.parse_args()

    types = [t.strip() for t in args.types.split(",") if t.strip()]
    result = generate_quiz_from_file(
        args.file, args.difficulty, args.questions, types, args.focus
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
