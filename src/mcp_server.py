"""
QuizCraft MCP Server

Exposes quiz generation as MCP tools so Claude Code, Claude Desktop,
and any MCP-compatible AI agent can generate quizzes programmatically.

Run (from repo root):
    python src/mcp_server.py

Claude Desktop / Claude Code config (mcp_config.json):
    {
      "mcpServers": {
        "quizcraft": {
          "command": "python",
          "args": ["src/mcp_server.py"],
          "cwd": "/path/to/quiz-craft"
        }
      }
    }

Requirements:
    pip install mcp>=1.0.0
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import requests
from mcp.server.fastmcp import FastMCP

from generate_quiz_from_prompt import generate_quiz, get_backend_config, DIFFICULTY_PROFILES

# ─────────────────────────────────────────────────────────────────────────────
# Server
# ─────────────────────────────────────────────────────────────────────────────
mcp = FastMCP(
    "QuizCraft",
    description=(
        "Generate AI-powered quizzes from any topic or text. "
        "Works with Ollama (local), LM Studio, Groq, OpenRouter, Together.ai, or any OpenAI-compatible LLM. "
        "Source: https://github.com/NimaShafie/quiz-craft"
    ),
)

# ─────────────────────────────────────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────────────────────────────────────
@mcp.tool()
def generate_quiz_tool(
    topic: str,
    n_questions: int = 5,
    difficulty: str = "Medium",
    question_types: list[str] | None = None,
) -> str:
    """
    Generate a quiz from a topic or text passage.

    Args:
        topic: The subject to quiz on. Can be a keyword (e.g. 'Photosynthesis'),
               a sentence, or a full text passage pasted from a document.
        n_questions: How many questions to generate (1–40). Default: 5.
        difficulty: One of 'Easy', 'Medium', 'Hard'. Default: 'Medium'.
        question_types: List of types to include. Any combination of:
                        'Multiple Choice', 'True/False', 'Fill in the Blanks'.
                        Default: ['Multiple Choice'].

    Returns:
        JSON string with a 'quiz' array. Each item has:
          - question (str)
          - type (str): 'Multiple Choice' | 'True/False' | 'Fill in the Blanks'
          - options (list[str]): answer choices (empty for Fill in the Blanks)
          - answer (str): correct answer
    """
    if question_types is None:
        question_types = ["Multiple Choice"]

    if difficulty not in DIFFICULTY_PROFILES:
        difficulty = "Medium"

    n_questions = max(1, min(40, int(n_questions)))

    valid_types = {"Multiple Choice", "True/False", "Fill in the Blanks"}
    question_types = [t for t in question_types if t in valid_types] or ["Multiple Choice"]

    result = generate_quiz(
        number_of_questions=n_questions,
        difficulty=difficulty,
        user_prompt=topic,
        question_types=question_types,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def check_llm_health() -> str:
    """
    Check whether the configured LLM backend is reachable and the model is available.

    Returns:
        JSON string with:
          - status: 'ok' | 'model_not_pulled' | 'error'
          - backend: 'ollama' | 'openai'
          - backend_url (str)
          - model (str): configured model name
          - model_available (bool)
          - available_models (list[str]): models found on the server (Ollama only)
    """
    cfg = get_backend_config()
    try:
        if cfg["type"] == "openai":
            headers = {"Authorization": f"Bearer {cfg['api_key']}"}
            resp = requests.get(f"{cfg['base_url']}/models", headers=headers, timeout=3)
            if not resp.ok:
                return json.dumps({
                    "status": "error",
                    "backend": "openai",
                    "backend_url": cfg["base_url"],
                    "detail": f"HTTP {resp.status_code}",
                })
            return json.dumps({
                "status": "ok",
                "backend": "openai",
                "backend_url": cfg["base_url"],
                "model": cfg["model"],
                "model_available": True,
            }, indent=2)
        else:
            host, model = cfg["host"], cfg["model"]
            resp = requests.get(f"{host}/api/tags", timeout=3)
            if not resp.ok:
                return json.dumps({
                    "status": "error",
                    "backend": "ollama",
                    "backend_url": host,
                    "detail": f"HTTP {resp.status_code}",
                })
            pulled = [m.get("name", "") for m in resp.json().get("models", [])]
            model_available = any(model in name for name in pulled)
            return json.dumps({
                "status": "ok" if model_available else "model_not_pulled",
                "backend": "ollama",
                "backend_url": host,
                "model": model,
                "model_available": model_available,
                "available_models": pulled,
                "hint": "" if model_available else f"Run: ollama pull {model}",
            }, indent=2)
    except Exception as e:
        target = cfg.get("base_url") or cfg.get("host", "")
        return json.dumps({
            "status": "error",
            "backend": cfg["type"],
            "backend_url": target,
            "detail": str(e),
        })


@mcp.tool()
def list_question_types() -> str:
    """
    Return the question types supported by QuizCraft.

    Returns:
        JSON string listing available question types.
    """
    return json.dumps({
        "question_types": [
            {
                "name": "Multiple Choice",
                "description": "4 options, one correct answer. Good for knowledge testing.",
            },
            {
                "name": "True/False",
                "description": "Binary True/False questions. Good for fact verification.",
            },
            {
                "name": "Fill in the Blanks",
                "description": "Question contains ___ to mark a blank the user must fill in.",
            },
        ]
    }, indent=2)


@mcp.tool()
def list_difficulties() -> str:
    """
    Return the difficulty levels QuizCraft supports with their descriptions.

    Returns:
        JSON string with difficulty names and what each level means.
    """
    return json.dumps({
        "difficulties": {
            name: profile["description"]
            for name, profile in DIFFICULTY_PROFILES.items()
        }
    }, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    mcp.run()


if __name__ == "__main__":
    main()
