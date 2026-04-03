"""
generate_quiz_from_prompt.py
Core quiz generation module using Ollama via direct HTTP API.

Author: Nima Shafie
Rewritten: 2026 — Fixed difficulty enforcement, prompt injection hardening,
           JSON robustness, and subprocess stdout isolation.

Usage (CLI):
    python generate_quiz_from_prompt.py <n_questions> <difficulty> <user_prompt> <question_types_csv>

Returns: JSON to stdout (only the JSON block, nothing else)
"""

import json
import sys
import re
import os
import requests


def get_ollama_config():
    """Read Ollama host and model from environment or config.ini fallback."""
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "")
    if not model:
        try:
            import configparser
            cfg = configparser.ConfigParser()
            cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
            cfg.read(cfg_path)
            model = cfg.get("OLLAMA_DETAILS", "model_name", fallback="gemma3:4b")
        except Exception:
            model = "gemma3:4b"
    return host, model


_INJECTION_PATTERNS = re.compile(
    r"(ignore (previous|above|all) instructions?|"
    r"disregard|forget (everything|all)|"
    r"you are now|act as|pretend (you are|to be)|"
    r"system prompt|override|jailbreak|"
    r"repeat after me|say exactly)",
    re.IGNORECASE,
)
_MAX_PROMPT_LEN = 3000


def sanitize_prompt(text: str) -> str:
    text = text.strip()[:_MAX_PROMPT_LEN]
    text = _INJECTION_PATTERNS.sub("[REMOVED]", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text.strip()


DIFFICULTY_PROFILES = {
    "Easy": {
        "temperature": 0.4,
        "description": (
            "straightforward recall questions suitable for beginners. "
            "Use simple vocabulary. Avoid trick questions. "
            "Wrong options should be clearly incorrect."
        ),
    },
    "Medium": {
        "temperature": 0.6,
        "description": (
            "moderately challenging questions requiring understanding, not just recall. "
            "Distractors should be plausible. Mix conceptual and application questions."
        ),
    },
    "Hard": {
        "temperature": 0.75,
        "description": (
            "advanced questions requiring deep understanding, analysis, or synthesis. "
            "All distractors must be highly plausible. Include edge cases, exceptions, "
            "and nuanced distinctions. Avoid questions answerable by guessing."
        ),
    },
}


def build_prompt(n_questions, difficulty, topic, question_types):
    profile = DIFFICULTY_PROFILES.get(difficulty, DIFFICULTY_PROFILES["Medium"])
    types_str = ", ".join(question_types)

    type_instructions = []
    if "Multiple Choice" in question_types:
        type_instructions.append(
            '- "Multiple Choice": provide exactly 4 options, only one correct. '
            'The "answer" field must exactly match one of the option strings.'
        )
    if "True/False" in question_types:
        type_instructions.append(
            '- "True/False": options must be exactly ["True", "False"]. '
            'The "answer" field must be exactly "True" or "False".'
        )
    if "Fill in the Blanks" in question_types:
        type_instructions.append(
            '- "Fill in the Blanks": the question must contain ___ to mark the blank. '
            '"options" must be an empty array []. "answer" is the word/phrase for the blank.'
        )

    type_detail = "\n".join(type_instructions)

    return f"""You are a professional quiz writer. Generate exactly {n_questions} quiz questions.

TOPIC: {topic}

DIFFICULTY: {difficulty} — {profile['description']}

QUESTION TYPES REQUIRED: {types_str}
Distribute questions as evenly as possible across the requested types.
Group all questions of the same type together.

TYPE-SPECIFIC RULES:
{type_detail}

CRITICAL OUTPUT RULES:
1. Respond with ONLY a valid JSON object. No explanation, no markdown, no code fences.
2. Every question MUST reflect the {difficulty} difficulty level described above.
3. Do NOT repeat questions or use the same wording twice.
4. The "type" field must exactly match one of: {types_str}

JSON FORMAT:
{{
  "quiz": [
    {{
      "question": "Question text here",
      "type": "Multiple Choice",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"
    }}
  ]
}}"""


def call_ollama(prompt, model, host, temperature):
    url = f"{host}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature,
            "num_predict": 4096,
        },
    }
    resp = requests.post(url, json=payload, timeout=180)
    resp.raise_for_status()
    return resp.json().get("response", "")


def extract_quiz_json(raw):
    try:
        data = json.loads(raw)
        if "quiz" in data:
            return data
    except json.JSONDecodeError:
        pass
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    match = re.search(r"(\{[\s\S]*\})", raw)
    if match:
        try:
            data = json.loads(match.group(1))
            if "quiz" in data:
                return data
        except json.JSONDecodeError:
            pass
    return None


TYPE_ALIASES = {
    "multiplechoice": "Multiple Choice",
    "multiple choice": "Multiple Choice",
    "mcq": "Multiple Choice",
    "true/false": "True/False",
    "truefalse": "True/False",
    "true or false": "True/False",
    "fill in the blank": "Fill in the Blanks",
    "fill in the blanks": "Fill in the Blanks",
    "fillintheblank": "Fill in the Blanks",
    "fill-in-the-blank": "Fill in the Blanks",
}


def normalize_question(q):
    if not isinstance(q, dict):
        return None
    question = str(q.get("question", "")).strip()
    raw_type_key = q.get("type", "").strip().lower()
    normalized_type = TYPE_ALIASES.get(raw_type_key, None) or \
                      TYPE_ALIASES.get(raw_type_key.replace(" ", "").replace("-", ""), "Multiple Choice")
    options = q.get("options", [])
    answer = str(q.get("answer", "")).strip()

    if not question or not answer:
        return None

    if normalized_type == "True/False":
        options = ["True", "False"]
        answer = "True" if answer.lower() in ("true", "t", "yes", "1") else "False"
    elif normalized_type == "Fill in the Blanks":
        options = []
        if "___" not in question:
            question = question.rstrip("?") + " (___)"
    elif normalized_type == "Multiple Choice":
        if not isinstance(options, list) or len(options) < 2:
            return None
        options = [str(o).strip() for o in options[:4]]

    return {
        "question": question,
        "type": normalized_type,
        "options": options,
        "answer": answer,
    }


def generate_quiz(number_of_questions=5, difficulty="Medium", user_prompt="", question_types=None):
    if question_types is None:
        question_types = ["Multiple Choice"]

    safe_prompt = sanitize_prompt(user_prompt)
    if not safe_prompt:
        return {"quiz": [], "error": "Empty or invalid prompt after sanitization."}

    host, model = get_ollama_config()
    profile = DIFFICULTY_PROFILES.get(difficulty, DIFFICULTY_PROFILES["Medium"])
    prompt = build_prompt(number_of_questions, difficulty, safe_prompt, question_types)

    try:
        raw = call_ollama(prompt, model, host, profile["temperature"])
    except requests.exceptions.ConnectionError:
        return {"quiz": [], "error": f"Cannot connect to Ollama at {host}. Is it running?"}
    except requests.exceptions.Timeout:
        return {"quiz": [], "error": "Ollama request timed out after 180 seconds."}
    except Exception as e:
        return {"quiz": [], "error": f"Ollama error: {str(e)}"}

    data = extract_quiz_json(raw)
    if not data:
        return {"quiz": [], "error": "Model did not return valid JSON."}

    questions = [normalize_question(q) for q in data.get("quiz", [])]
    questions = [q for q in questions if q is not None]
    return {"quiz": questions}


def main():
    if len(sys.argv) != 5:
        sys.stderr.write(
            "Usage: python generate_quiz_from_prompt.py "
            "<n_questions> <difficulty> <user_prompt> <question_types_csv>\n"
        )
        sys.exit(1)

    n = int(sys.argv[1])
    difficulty = sys.argv[2]
    user_prompt = sys.argv[3]
    question_types = [t.strip() for t in sys.argv[4].split(",") if t.strip()]

    result = generate_quiz(n, difficulty, user_prompt, question_types)
    # ONLY output JSON to stdout — QuizCraft.py regex-parses this
    print(json.dumps(result))


if __name__ == "__main__":
    main()
