"""
QuizCraft REST API — FastAPI wrapper around generate_quiz().

Run (from repo root):
    uvicorn api:app --app-dir src --reload --port 8000
    # or:
    python src/api.py

Interactive docs: http://localhost:8000/docs
OpenAPI JSON:     http://localhost:8000/openapi.json
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests as _requests
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from generate_quiz_from_prompt import generate_quiz, get_ollama_config, DIFFICULTY_PROFILES

# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="QuizCraft API",
    description=(
        "Generate AI-powered quizzes from any topic or text using a local Ollama model. "
        "No API keys required — all inference runs on your machine.\n\n"
        "**Source:** https://github.com/NimaShafie/quiz-craft  \n"
        "**Live demo:** https://quizcraft.shafie.org"
    ),
    version="1.0.0",
    license_info={
        "name": "CC BY-NC-ND 4.0",
        "url": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    },
    contact={"name": "Nima Shafie", "url": "https://github.com/NimaShafie"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

QUESTION_TYPES = ["Multiple Choice", "True/False", "Fill in the Blanks"]
DIFFICULTIES = list(DIFFICULTY_PROFILES.keys())

# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    topic: str = Field(
        ...,
        description="Topic or text to generate questions about. "
                    "Can be a keyword ('World War II'), a sentence, or a full passage pasted from a document.",
        min_length=2,
        max_length=3000,
        examples=["World War II causes and effects"],
    )
    n_questions: int = Field(
        5,
        ge=1,
        le=40,
        description="Number of questions to generate.",
    )
    difficulty: Literal["Easy", "Medium", "Hard"] = Field(
        "Medium",
        description="Quiz difficulty level.",
    )
    question_types: list[Literal["Multiple Choice", "True/False", "Fill in the Blanks"]] = Field(
        ["Multiple Choice"],
        description="Question types to include. At least one required. "
                    "Questions are distributed evenly across chosen types.",
        min_length=1,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "topic": "World War II causes and effects",
                    "n_questions": 5,
                    "difficulty": "Medium",
                    "question_types": ["Multiple Choice", "True/False"],
                }
            ]
        }
    }


class QuizQuestion(BaseModel):
    question: str
    type: str = Field(description="One of: 'Multiple Choice', 'True/False', 'Fill in the Blanks'")
    options: list[str] = Field(description="Answer options. Empty list for Fill in the Blanks.")
    answer: str


class GenerateResponse(BaseModel):
    topic: str
    difficulty: str
    n_questions: int = Field(description="Actual number of questions returned (may differ from requested).")
    quiz: list[QuizQuestion]


class HealthResponse(BaseModel):
    status: str = Field(description="'ok', 'degraded', or 'error'")
    ollama: bool
    ollama_host: str = ""
    model: str = ""
    model_available: bool = False
    available_models: list[str] = []
    detail: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="Ollama health check",
    tags=["Status"],
)
def health():
    """Check whether Ollama is reachable and the configured model is pulled."""
    host, model = get_ollama_config()
    try:
        resp = _requests.get(f"{host}/api/tags", timeout=3)
        if not resp.ok:
            return HealthResponse(
                status="degraded", ollama=False, ollama_host=host,
                detail=f"Ollama returned HTTP {resp.status_code}",
            )
        pulled = [m.get("name", "") for m in resp.json().get("models", [])]
        model_available = any(model in name for name in pulled)
        return HealthResponse(
            status="ok" if model_available else "degraded",
            ollama=True,
            ollama_host=host,
            model=model,
            model_available=model_available,
            available_models=pulled,
            detail="" if model_available else f"Model '{model}' not pulled. Run: ollama pull {model}",
        )
    except Exception as e:
        return HealthResponse(
            status="error", ollama=False, ollama_host=host, detail=str(e),
        )


@app.get(
    "/api/v1/models",
    summary="List pulled Ollama models",
    tags=["Status"],
)
def list_models():
    """Return all models currently pulled on the Ollama server."""
    host, _ = get_ollama_config()
    try:
        resp = _requests.get(f"{host}/api/tags", timeout=3)
        resp.raise_for_status()
        return {"models": [m.get("name") for m in resp.json().get("models", [])]}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Cannot reach Ollama at {host}: {e}")


@app.get(
    "/api/v1/question-types",
    summary="List supported question types",
    tags=["Metadata"],
)
def question_types():
    """Return the question types QuizCraft supports."""
    return {"question_types": QUESTION_TYPES}


@app.get(
    "/api/v1/difficulties",
    summary="List difficulty levels",
    tags=["Metadata"],
)
def difficulties():
    """Return available difficulty levels with their descriptions."""
    return {
        "difficulties": {
            name: profile["description"]
            for name, profile in DIFFICULTY_PROFILES.items()
        }
    }


@app.post(
    "/api/v1/quiz/generate",
    response_model=GenerateResponse,
    summary="Generate a quiz",
    tags=["Quiz"],
)
def generate(req: GenerateRequest):
    """
    Generate an AI-powered quiz from a topic or text passage.

    The LLM runs locally via Ollama — no data leaves your machine.
    Generation typically takes 15–60 seconds on CPU for a 4B parameter model.
    """
    result = generate_quiz(
        number_of_questions=req.n_questions,
        difficulty=req.difficulty,
        user_prompt=req.topic,
        question_types=req.question_types,
    )
    if result.get("error"):
        raise HTTPException(status_code=502, detail=result["error"])
    if not result.get("quiz"):
        raise HTTPException(
            status_code=502,
            detail="Model returned an empty quiz. Try a different topic or check your Ollama setup.",
        )
    return GenerateResponse(
        topic=req.topic[:80],
        difficulty=req.difficulty,
        n_questions=len(result["quiz"]),
        quiz=result["quiz"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, app_dir=os.path.dirname(__file__))


if __name__ == "__main__":
    main()
