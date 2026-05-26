"""
test_api.py
Integration tests for the QuizCraft FastAPI REST API.
No real LLM backend required — generate_quiz and get_backend_config are mocked.

Run with: python -m pytest tests/test_api.py -v
"""

import sys
import os
import json
from unittest.mock import MagicMock, patch

# Mock streamlit and fpdf before any imports
sys.modules.setdefault("streamlit", MagicMock())
sys.modules.setdefault("fpdf", MagicMock())

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Clear API_KEY so auth is disabled by default in tests
os.environ.pop("API_KEY", None)
os.environ.pop("API_RATE_LIMIT", None)

from fastapi.testclient import TestClient

_MOCK_QUIZ = {
    "quiz": [
        {
            "question": "What is photosynthesis?",
            "type": "Multiple Choice",
            "options": ["A", "B", "C", "D"],
            "answer": "A",
        }
    ]
}

_MOCK_BACKEND_CFG = {"type": "ollama", "host": "http://localhost:11434", "model": "test-model"}


@pytest.fixture()
def client():
    """Fresh TestClient with generate_quiz and get_backend_config mocked."""
    with patch("generate_quiz_from_prompt.get_backend_config", return_value=_MOCK_BACKEND_CFG):
        import api as api_module
        with TestClient(api_module.app, raise_server_exceptions=True) as c:
            yield c


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/health
# ─────────────────────────────────────────────────────────────────────────────
class TestHealth:
    def test_returns_200(self, client):
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                ok=True,
                json=lambda: {"models": [{"name": "test-model"}]},
            )
            resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_response_has_required_fields(self, client):
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                ok=True,
                json=lambda: {"models": [{"name": "test-model"}]},
            )
            resp = client.get("/api/v1/health")
        body = resp.json()
        for field in ("status", "backend", "backend_url", "model", "model_available"):
            assert field in body, f"Missing field: {field}"

    def test_returns_error_when_backend_unreachable(self, client):
        import requests as req_mod
        with patch("requests.get", side_effect=req_mod.exceptions.ConnectionError("refused")):
            resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "error"


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/models
# ─────────────────────────────────────────────────────────────────────────────
class TestModels:
    def test_returns_200(self, client):
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                ok=True,
                json=lambda: {"models": [{"name": "test-model"}]},
            )
            mock_get.return_value.raise_for_status = lambda: None
            resp = client.get("/api/v1/models")
        assert resp.status_code == 200

    def test_response_has_backend_and_models(self, client):
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                ok=True,
                json=lambda: {"models": [{"name": "qwen3:4b"}]},
            )
            mock_get.return_value.raise_for_status = lambda: None
            resp = client.get("/api/v1/models")
        body = resp.json()
        assert "backend" in body
        assert "models" in body

    def test_returns_503_when_backend_down(self, client):
        import requests as req_mod
        with patch("requests.get", side_effect=req_mod.exceptions.ConnectionError):
            resp = client.get("/api/v1/models")
        assert resp.status_code == 503
        # Must NOT expose internal URL in error detail
        assert "localhost" not in resp.json().get("detail", "")


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/question-types and /api/v1/difficulties
# ─────────────────────────────────────────────────────────────────────────────
class TestMetadata:
    def test_question_types_no_auth(self, client):
        resp = client.get("/api/v1/question-types")
        assert resp.status_code == 200
        assert "question_types" in resp.json()

    def test_difficulties_no_auth(self, client):
        resp = client.get("/api/v1/difficulties")
        assert resp.status_code == 200
        assert "difficulties" in resp.json()

    def test_difficulties_has_three_levels(self, client):
        body = client.get("/api/v1/difficulties").json()
        assert len(body["difficulties"]) == 3


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/quiz/generate
# ─────────────────────────────────────────────────────────────────────────────
class TestGenerate:
    _payload = {
        "topic": "World War II",
        "n_questions": 1,
        "difficulty": "Medium",
        "question_types": ["Multiple Choice"],
    }

    def test_happy_path(self, client):
        with patch("api.generate_quiz", return_value=_MOCK_QUIZ):
            resp = client.post("/api/v1/quiz/generate", json=self._payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "quiz" in body
        assert len(body["quiz"]) == 1

    def test_response_shape(self, client):
        with patch("api.generate_quiz", return_value=_MOCK_QUIZ):
            resp = client.post("/api/v1/quiz/generate", json=self._payload)
        body = resp.json()
        for field in ("topic", "difficulty", "n_questions", "quiz"):
            assert field in body

    def test_topic_too_short_returns_422(self, client):
        resp = client.post("/api/v1/quiz/generate", json={**self._payload, "topic": "a"})
        assert resp.status_code == 422

    def test_n_questions_zero_returns_422(self, client):
        resp = client.post("/api/v1/quiz/generate", json={**self._payload, "n_questions": 0})
        assert resp.status_code == 422

    def test_n_questions_too_high_returns_422(self, client):
        resp = client.post("/api/v1/quiz/generate", json={**self._payload, "n_questions": 41})
        assert resp.status_code == 422

    def test_invalid_difficulty_returns_422(self, client):
        resp = client.post("/api/v1/quiz/generate", json={**self._payload, "difficulty": "Extreme"})
        assert resp.status_code == 422

    def test_llm_error_returns_502(self, client):
        with patch("api.generate_quiz", return_value={"quiz": [], "error": "timeout"}):
            resp = client.post("/api/v1/quiz/generate", json=self._payload)
        assert resp.status_code == 502
        # Internal LLM error detail should NOT be forwarded verbatim
        assert "timeout" not in resp.json().get("detail", "")

    def test_empty_quiz_returns_502(self, client):
        with patch("api.generate_quiz", return_value={"quiz": []}):
            resp = client.post("/api/v1/quiz/generate", json=self._payload)
        assert resp.status_code == 502

    def test_whitespace_only_topic_returns_error(self, client):
        # "  " has length 2 so passes Pydantic min_length; generate_quiz rejects it as empty.
        with patch("api.generate_quiz", return_value={"quiz": [], "error": "Empty or invalid prompt after sanitization."}):
            resp = client.post("/api/v1/quiz/generate", json={**self._payload, "topic": "  "})
        assert resp.status_code == 502


# ─────────────────────────────────────────────────────────────────────────────
# API key authentication
# ─────────────────────────────────────────────────────────────────────────────
class TestApiKeyAuth:
    _payload = {
        "topic": "Biology",
        "n_questions": 1,
        "difficulty": "Easy",
        "question_types": ["True/False"],
    }

    def test_no_key_required_when_env_unset(self, client):
        """Default: API_KEY not set → no auth required."""
        with patch("api.generate_quiz", return_value=_MOCK_QUIZ):
            resp = client.post("/api/v1/quiz/generate", json=self._payload)
        assert resp.status_code == 200

    def test_correct_key_allows_access(self):
        os.environ["API_KEY"] = "test-secret"
        try:
            import importlib
            import api as api_module
            importlib.reload(api_module)
            with TestClient(api_module.app) as c:
                with patch("api.generate_quiz", return_value=_MOCK_QUIZ):
                    resp = c.post(
                        "/api/v1/quiz/generate",
                        json=self._payload,
                        headers={"X-API-Key": "test-secret"},
                    )
            assert resp.status_code == 200
        finally:
            del os.environ["API_KEY"]

    def test_wrong_key_returns_403(self):
        os.environ["API_KEY"] = "test-secret"
        try:
            import importlib
            import api as api_module
            importlib.reload(api_module)
            with TestClient(api_module.app) as c:
                resp = c.post(
                    "/api/v1/quiz/generate",
                    json=self._payload,
                    headers={"X-API-Key": "wrong-key"},
                )
            assert resp.status_code == 403
        finally:
            del os.environ["API_KEY"]

    def test_missing_key_returns_403(self):
        os.environ["API_KEY"] = "test-secret"
        try:
            import importlib
            import api as api_module
            importlib.reload(api_module)
            with TestClient(api_module.app) as c:
                resp = c.post("/api/v1/quiz/generate", json=self._payload)
            assert resp.status_code == 403
        finally:
            del os.environ["API_KEY"]


# ─────────────────────────────────────────────────────────────────────────────
# Security headers
# ─────────────────────────────────────────────────────────────────────────────
class TestSecurityHeaders:
    def test_x_content_type_options(self, client):
        resp = client.get("/api/v1/question-types")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        resp = client.get("/api/v1/question-types")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy(self, client):
        resp = client.get("/api/v1/question-types")
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


# ─────────────────────────────────────────────────────────────────────────────
# Rate limiting — HOSTED_MODE coupling
# ─────────────────────────────────────────────────────────────────────────────
class TestHostedModeRateLimiting:
    def _reload_api(self):
        import importlib
        import api as api_module
        importlib.reload(api_module)
        return api_module

    def test_no_rate_limit_when_hosted_mode_off(self):
        """HOSTED_MODE unset and API_RATE_LIMIT unset → rate limiting disabled."""
        os.environ.pop("HOSTED_MODE", None)
        os.environ.pop("API_RATE_LIMIT", None)
        api_module = self._reload_api()
        assert api_module._RATE_LIMIT == ""

    def test_default_rate_limit_when_hosted_mode_on(self):
        """HOSTED_MODE=true and API_RATE_LIMIT unset → default 5/hour."""
        os.environ["HOSTED_MODE"] = "true"
        os.environ.pop("API_RATE_LIMIT", None)
        try:
            api_module = self._reload_api()
            assert api_module._RATE_LIMIT == "5/hour"
        finally:
            del os.environ["HOSTED_MODE"]

    def test_explicit_rate_limit_overrides_hosted_mode(self):
        """API_RATE_LIMIT set explicitly overrides the HOSTED_MODE default."""
        os.environ["HOSTED_MODE"] = "true"
        os.environ["API_RATE_LIMIT"] = "10/minute"
        try:
            api_module = self._reload_api()
            assert api_module._RATE_LIMIT == "10/minute"
        finally:
            del os.environ["HOSTED_MODE"]
            del os.environ["API_RATE_LIMIT"]
