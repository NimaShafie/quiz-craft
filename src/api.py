"""
QuizCraft REST API — FastAPI wrapper around generate_quiz().

Run (from repo root):
    uvicorn api:app --app-dir src --reload --port 8000
    # or:
    python src/api.py

Interactive docs: http://localhost:8000/docs
OpenAPI JSON:     http://localhost:8000/openapi.json

Security env vars (all optional — safe defaults for personal/local use):
    API_KEY          — when set, all endpoints require `X-API-Key: <value>` header
    CORS_ORIGINS     — comma-separated allowed origins, or "*" (default) for open CORS
    HOSTED_MODE      — "true" enables public-facing defaults (rate limiting at 5/hour)
    API_RATE_LIMIT   — slowapi limit string e.g. "10/hour"; overrides HOSTED_MODE default
    UVICORN_RELOAD   — "true" to enable auto-reload (default: false)
    API_PORT         — port to bind (default: 8000)
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests as _requests
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from generate_quiz_from_prompt import generate_quiz, get_backend_config, DIFFICULTY_PROFILES

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
_logger = logging.getLogger("quizcraft.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

# ─────────────────────────────────────────────────────────────────────────────
# Config from environment
# ─────────────────────────────────────────────────────────────────────────────
_cors_raw = os.environ.get("CORS_ORIGINS", "*")
CORS_ORIGINS = (
    [o.strip() for o in _cors_raw.split(",") if o.strip()]
    if _cors_raw != "*"
    else ["*"]
)

_API_KEY_ENV = os.environ.get("API_KEY", "").strip()
_HOSTED_MODE = os.environ.get("HOSTED_MODE", "").lower() in ("true", "1", "yes")
_API_RATE_LIMIT_ENV = os.environ.get("API_RATE_LIMIT", "").strip()
# Explicit API_RATE_LIMIT always wins; fall back to 5/hour when public-facing, else unlimited.
_RATE_LIMIT = _API_RATE_LIMIT_ENV or ("5/hour" if _HOSTED_MODE else "")

# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="QuizCraft API",
    description=(
        "Generate AI-powered quizzes from any topic or text. "
        "Works with Ollama (local), LM Studio, Groq, OpenRouter, Together.ai, "
        "or any OpenAI-compatible LLM. Set `LLM_BACKEND=openai` to switch backends.\n\n"
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

# ─────────────────────────────────────────────────────────────────────────────
# Middleware: CORS
# ─────────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Middleware: security headers
# ─────────────────────────────────────────────────────────────────────────────
class _SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(_SecurityHeadersMiddleware)

# ─────────────────────────────────────────────────────────────────────────────
# Rate limiting (slowapi — optional dep, gates behind API_RATE_LIMIT env var)
# ─────────────────────────────────────────────────────────────────────────────
_limiter = None
if _RATE_LIMIT:
    try:
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.util import get_remote_address
        from slowapi.errors import RateLimitExceeded
        _limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = _limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    except ImportError:
        _logger.warning(
            "API_RATE_LIMIT is set but 'slowapi' is not installed. "
            "Rate limiting is disabled. Install it: pip install slowapi"
        )


def _rate_limit(limit_str: str):
    """Decorator factory — applies slowapi limit when configured, no-op otherwise."""
    def decorator(func):
        if _limiter:
            return _limiter.limit(limit_str)(func)
        return func
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Auth: optional API key
# ─────────────────────────────────────────────────────────────────────────────
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _verify_api_key(key: str | None = Security(_api_key_header)) -> None:
    """No-op when API_KEY env var is unset (personal/local use). Enforces key when set."""
    if not _API_KEY_ENV:
        return
    if key != _API_KEY_ENV:
        raise HTTPException(status_code=403, detail="Invalid or missing API key.")


# ─────────────────────────────────────────────────────────────────────────────
# Metadata
# ─────────────────────────────────────────────────────────────────────────────
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
    backend: str = Field(description="'ollama' or 'openai'")
    backend_url: str = ""
    model: str = ""
    model_available: bool = False
    available_models: list[str] = Field(default=[], description="Pulled models (Ollama only)")
    detail: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="LLM backend health check",
    tags=["Status"],
    dependencies=[Depends(_verify_api_key)],
)
def health():
    """Check whether the configured LLM backend is reachable and the model is available."""
    cfg = get_backend_config()
    try:
        if cfg["type"] == "openai":
            headers = {"Authorization": f"Bearer {cfg['api_key']}"}
            resp = _requests.get(f"{cfg['base_url']}/models", headers=headers, timeout=3)
            if not resp.ok:
                return HealthResponse(
                    status="degraded", backend="openai", backend_url=cfg["base_url"],
                    detail=f"Backend returned HTTP {resp.status_code}",
                )
            return HealthResponse(
                status="ok", backend="openai", backend_url=cfg["base_url"],
                model=cfg["model"], model_available=True,
            )
        else:
            host, model = cfg["host"], cfg["model"]
            resp = _requests.get(f"{host}/api/tags", timeout=3)
            if not resp.ok:
                return HealthResponse(
                    status="degraded", backend="ollama", backend_url=host,
                    detail=f"Ollama returned HTTP {resp.status_code}",
                )
            pulled = [m.get("name", "") for m in resp.json().get("models", [])]
            model_available = any(model in name for name in pulled)
            return HealthResponse(
                status="ok" if model_available else "degraded",
                backend="ollama", backend_url=host,
                model=model, model_available=model_available, available_models=pulled,
                detail="" if model_available else f"Model '{model}' not pulled. Run: ollama pull {model}",
            )
    except Exception as e:
        _logger.exception("Health check failed")
        target = cfg.get("base_url") or cfg.get("host", "")
        return HealthResponse(status="error", backend=cfg["type"], backend_url=target, detail=str(e))


@app.get(
    "/api/v1/models",
    summary="List available models from the LLM backend",
    tags=["Status"],
    dependencies=[Depends(_verify_api_key)],
)
def list_models():
    """Return models available on the backend (Ollama: pulled models; OpenAI-compatible: /v1/models list)."""
    cfg = get_backend_config()
    try:
        if cfg["type"] == "openai":
            headers = {"Authorization": f"Bearer {cfg['api_key']}"}
            resp = _requests.get(f"{cfg['base_url']}/models", headers=headers, timeout=3)
            resp.raise_for_status()
            data = resp.json()
            models = [m.get("id") for m in data.get("data", [])] or data.get("models", [])
            return {"backend": "openai", "models": models}
        else:
            host = cfg["host"]
            resp = _requests.get(f"{host}/api/tags", timeout=3)
            resp.raise_for_status()
            return {"backend": "ollama", "models": [m.get("name") for m in resp.json().get("models", [])]}
    except Exception:
        _logger.exception("list_models failed")
        raise HTTPException(status_code=503, detail="LLM backend is unavailable. Check server logs.")


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
    dependencies=[Depends(_verify_api_key)],
)
@_rate_limit(_RATE_LIMIT or "9999/second")
def generate(req: GenerateRequest, request: Request):
    """
    Generate an AI-powered quiz from a topic or text passage.

    The LLM runs via your configured backend (Ollama, LM Studio, Groq, etc.).
    Local models typically take 15–60 seconds on CPU. Cloud backends (Groq, OpenRouter) respond in seconds.
    """
    result = generate_quiz(
        number_of_questions=req.n_questions,
        difficulty=req.difficulty,
        user_prompt=req.topic,
        question_types=req.question_types,
    )
    if result.get("error"):
        _logger.warning("generate_quiz returned error: %s", result["error"])
        raise HTTPException(status_code=502, detail="Quiz generation failed. Check that your LLM backend is running.")
    if not result.get("quiz"):
        raise HTTPException(
            status_code=502,
            detail="Model returned an empty quiz. Try a different topic or check your LLM backend setup.",
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
    _reload = os.environ.get("UVICORN_RELOAD", "false").lower() in ("true", "1", "yes")
    uvicorn.run(
        "api:app",
        host=os.environ.get("API_HOST", "0.0.0.0"),
        port=int(os.environ.get("API_PORT", "8000")),
        reload=_reload,
        app_dir=os.path.dirname(__file__),
    )


if __name__ == "__main__":
    main()
