"""
QuizCraft.py — AI-powered quiz generator using a local Ollama model.

Author: Nima Shafie

Usage:
    streamlit run src/QuizCraft.py
    HOSTED_MODE=true streamlit run src/QuizCraft.py
"""

import json
import sys
import re
import os
import time
import subprocess
import hashlib
import logging
import traceback
import streamlit as st
from fpdf import FPDF
from dataclasses import dataclass, field

# ─────────────────────────────────────────────────────────────────────────────
# Mode + Config
# ─────────────────────────────────────────────────────────────────────────────
HOSTED_MODE = os.environ.get("HOSTED_MODE", "").lower() in ("true", "1", "yes")

MAX_QUESTIONS    = 20   if HOSTED_MODE else 40
MAX_PROMPT_CHARS = 2000 if HOSTED_MODE else 3500
RATE_LIMIT_REQUESTS   = 5
RATE_LIMIT_WINDOW_SEC = 3600
COOLDOWN_SEC          = 15

TOPIC_SUGGESTIONS = [
    "World War II", "Human anatomy", "Python basics", "Climate change",
    "Ancient Rome", "Solar system", "Cell biology", "World geography",
]

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuizCraft — AI Generated Quizzes",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items=None,
)

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH  = os.path.join(SCRIPT_DIR, "..", "images", "logo", "quiz-craft-logo.png")
GEN_SCRIPT = os.path.join(SCRIPT_DIR, "generate_quiz_from_prompt.py")

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
_LOG_DIR = os.path.join(SCRIPT_DIR, "..", "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(_LOG_DIR, "quizcraft.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_logger = logging.getLogger("quizcraft")

# ─────────────────────────────────────────────────────────────────────────────
# Theme CSS
# ─────────────────────────────────────────────────────────────────────────────
_THEME_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp {
    background-color: #0f1923;
    background-image:
        radial-gradient(ellipse at 20% 20%, rgba(201,79,53,0.06) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(100,140,180,0.05) 0%, transparent 50%),
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Ctext x='15' y='45' font-size='28' fill='rgba(255,255,255,0.018)' font-family='Georgia'%3E%3F%3C/text%3E%3Ctext x='65' y='95' font-size='22' fill='rgba(255,255,255,0.015)' font-family='Georgia'%3EA%3C/text%3E%3Ctext x='5' y='110' font-size='18' fill='rgba(255,255,255,0.012)' font-family='Georgia'%3EQ%3C/text%3E%3Ctext x='80' y='30' font-size='20' fill='rgba(255,255,255,0.015)' font-family='Georgia'%3E%E2%9C%93%3C/text%3E%3C/svg%3E");
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

.block-container { padding-top: 1rem !important; max-width: 780px !important; }

/* Logo */
#qc-logo-wrap {
    display: flex; justify-content: center;
    margin: 0.5rem auto -0.5rem auto; width: 190px;
    background: radial-gradient(ellipse at center, rgba(0,0,0,0.55) 30%, transparent 75%);
    border-radius: 50%; padding: 0.8rem;
}
#qc-logo { display: block; width: 150px; filter: drop-shadow(0 4px 20px rgba(220,80,80,0.3)); }

/* Title */
h1 {
    font-family: 'Playfair Display', serif !important;
    font-size: 2.4rem !important; font-weight: 700 !important;
    color: #f0ece4 !important; letter-spacing: -0.5px; margin-bottom: 0 !important;
}

.stCaption p { color: #8fa3b8 !important; font-size: 0.9rem !important; }

hr { border-color: rgba(255,255,255,0.07) !important; margin: 0.8rem 0 1.2rem 0 !important; }

/* Form card */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 16px !important; padding: 1.6rem 1.8rem !important;
    backdrop-filter: blur(8px); box-shadow: 0 8px 40px rgba(0,0,0,0.3);
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1.5px dashed rgba(255,255,255,0.15) !important;
    border-radius: 10px !important; padding: 0.4rem 0.8rem !important;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: rgba(220,130,100,0.5) !important; }

/* Text area */
[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1.5px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important; color: #e8e4dc !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.95rem !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(220,130,100,0.6) !important;
    box-shadow: 0 0 0 3px rgba(220,130,100,0.1) !important;
}

/* OR separator */
.or-sep {
    text-align: center; color: #4a6070; font-size: 0.78rem;
    letter-spacing: 2px; text-transform: uppercase; margin: 0.6rem 0;
}

/* Segmented control */
[data-testid="stSegmentedControl"] {
    background: rgba(255,255,255,0.05) !important;
    border-radius: 8px !important; border: 1px solid rgba(255,255,255,0.08) !important;
}

/* Generate button */
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #c94f35 0%, #e0714f 100%) !important;
    border: none !important; border-radius: 10px !important;
    color: white !important; font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important; font-size: 1rem !important;
    letter-spacing: 0.3px !important; padding: 0.65rem 1.5rem !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
    box-shadow: 0 4px 20px rgba(201,79,53,0.35) !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 28px rgba(201,79,53,0.5) !important;
}
[data-testid="stFormSubmitButton"] button:disabled {
    background: rgba(255,255,255,0.08) !important; box-shadow: none !important;
    transform: none !important; color: rgba(255,255,255,0.3) !important;
}

/* Download buttons */
[data-testid="stDownloadButton"] button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important; color: #c8d8e8 !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: background 0.15s, border-color 0.15s !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(255,255,255,0.25) !important;
}

/* Regular buttons (topic pills, quiz mode) */
[data-testid="stButton"] button {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 20px !important; color: #a0b8cc !important;
    font-size: 0.82rem !important; padding: 0.25rem 0.85rem !important;
    transition: all 0.15s !important;
}
[data-testid="stButton"] button:hover {
    background: rgba(201,79,53,0.15) !important;
    border-color: rgba(201,79,53,0.4) !important;
    color: #e8c4b8 !important;
}

/* Quiz mode answer buttons */
.quiz-btn-correct button {
    background: rgba(76,175,130,0.2) !important;
    border-color: rgba(76,175,130,0.5) !important;
    color: #7dd4aa !important;
}
.quiz-btn-wrong button {
    background: rgba(220,80,80,0.2) !important;
    border-color: rgba(220,80,80,0.5) !important;
    color: #e08888 !important;
}

/* Quiz mode question card */
.quiz-question-card {
    background: rgba(15,25,40,0.7);
    border: 1px solid rgba(201,79,53,0.25);
    border-radius: 14px 14px 0 0;
    padding: 1.2rem 1.6rem 1rem 1.6rem;
    margin: 0.8rem 0 0 0;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 30px rgba(0,0,0,0.4);
}
/* Style the container holding quiz card + answers as one unit */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:has(.quiz-question-card) {
    background: rgba(15,25,40,0.5);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 0 0 1rem 0;
    backdrop-filter: blur(8px);
}
.quiz-q-number {
    font-size: 0.78rem; color: #dc6e50;
    letter-spacing: 1px; text-transform: uppercase;
    margin-bottom: 0.4rem; font-weight: 600;
}
.quiz-q-text {
    font-size: 1.05rem; color: #e8e4dc;
    font-weight: 600; line-height: 1.5;
    margin-bottom: 1rem;
}
.quiz-opt-btn button {
    background: rgba(255,255,255,0.05) !important;
    border: 1.5px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: #c0d0dc !important;
    font-size: 0.92rem !important;
    padding: 0.5rem 1rem !important;
    text-align: left !important;
    transition: all 0.15s !important;
    margin-bottom: 0.3rem !important;
}
.quiz-opt-btn button:hover {
    background: rgba(201,79,53,0.12) !important;
    border-color: rgba(201,79,53,0.4) !important;
    color: #e8c4b0 !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 10px !important;
}
[data-testid="stExpander"] summary { color: #8fa3b8 !important; font-size: 0.9rem !important; }

/* Alerts */
.stAlert { border-radius: 10px !important; border-left-width: 3px !important; font-size: 0.9rem !important; }

/* Status box */
[data-testid="stStatus"] {
    border-radius: 10px !important; background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

/* Multiselect tags */
[data-baseweb="tag"] {
    background: rgba(201,79,53,0.25) !important;
    border-color: rgba(201,79,53,0.4) !important; border-radius: 6px !important;
}

/* Labels */
label, [data-testid="stWidgetLabel"] p {
    color: #a0b4c4 !important; font-size: 0.85rem !important;
    font-weight: 500 !important; letter-spacing: 0.3px !important;
    text-transform: uppercase !important;
}

/* Quiz preview text */
[data-testid="stText"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important; line-height: 1.7 !important; color: #c8d8e0 !important;
}

/* Score display */
.score-display {
    text-align: center; padding: 1.5rem;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px; margin: 1rem 0;
}
.score-number {
    font-family: 'Playfair Display', serif;
    font-size: 3rem; color: #e0714f; font-weight: 700;
}
.score-label { color: #8fa3b8; font-size: 0.9rem; margin-top: 0.3rem; }

/* Quota badge */
.quota-badge { text-align: right; font-size: 0.78rem; margin-top: -10px; margin-bottom: 8px; opacity: 0.85; }

/* Footer */
.qc-footer {
    text-align: center; color: #2a4050; font-size: 0.75rem;
    margin-top: 2.5rem; padding: 1.5rem 0 1rem 0;
    border-top: 1px solid rgba(255,255,255,0.05);
    letter-spacing: 0.3px; line-height: 1.8;
}
.qc-footer a { color: #4a7080; text-decoration: none; }
.qc-footer a:hover { color: #dc6e50; }
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Inject theme + logo
# ─────────────────────────────────────────────────────────────────────────────
import base64 as _b64
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as _f:
        _logo_data = _b64.b64encode(_f.read()).decode()
    st.html(_THEME_CSS + '<div id="qc-logo-wrap"><img id="qc-logo" src="data:image/png;base64,' + _logo_data + '" /></div>')
else:
    st.html(_THEME_CSS)

# ─────────────────────────────────────────────────────────────────────────────
# Rate limiting
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class _IPRecord:
    timestamps: list = field(default_factory=list)
    last_request: float = 0.0

_ip_store: dict = {}

_ABUSE_PATTERNS = re.compile(
    r"(ignore (previous|above|all) instructions?|disregard|forget (everything|all)|"
    r"you are now|act as|pretend (you are|to be)|system prompt|override|jailbreak|"
    r"repeat after me|say exactly)", re.IGNORECASE,
)

def _get_client_ip() -> str:
    try:
        headers = st.context.headers
        for h in ("X-Forwarded-For", "X-Real-Ip"):
            val = headers.get(h, "")
            if val:
                return hashlib.sha256(val.split(",")[0].strip().encode()).hexdigest()[:16]
    except Exception:
        pass
    try:
        ctx = st.runtime.scriptrunner.get_script_run_ctx()
        return hashlib.sha256(ctx.session_id.encode()).hexdigest()[:16]
    except Exception:
        return "unknown"

def check_rate_limit() -> tuple:
    if not HOSTED_MODE: return True, ""
    ip = _get_client_ip(); now = time.time()
    if ip not in _ip_store: _ip_store[ip] = _IPRecord()
    record = _ip_store[ip]
    elapsed = now - record.last_request
    if record.last_request > 0 and elapsed < COOLDOWN_SEC:
        return False, f"Please wait {int(COOLDOWN_SEC - elapsed)}s before generating another quiz."
    record.timestamps = [t for t in record.timestamps if now - t < RATE_LIMIT_WINDOW_SEC]
    if len(record.timestamps) >= RATE_LIMIT_REQUESTS:
        oldest = record.timestamps[0]
        reset_in = int(RATE_LIMIT_WINDOW_SEC - (now - oldest))
        return False, f"Rate limit reached ({RATE_LIMIT_REQUESTS} quizzes/hour). Resets in {reset_in // 60}m {reset_in % 60}s."
    return True, ""

def record_request():
    if not HOSTED_MODE: return
    ip = _get_client_ip(); now = time.time()
    if ip not in _ip_store: _ip_store[ip] = _IPRecord()
    _ip_store[ip].timestamps.append(now)
    _ip_store[ip].last_request = now

def get_remaining_quota() -> tuple:
    if not HOSTED_MODE: return 0, 0
    ip = _get_client_ip(); now = time.time()
    if ip not in _ip_store: return 0, RATE_LIMIT_REQUESTS
    used = len([t for t in _ip_store[ip].timestamps if now - t < RATE_LIMIT_WINDOW_SEC])
    return used, RATE_LIMIT_REQUESTS

def validate_input(text: str) -> tuple:
    text = text.strip()
    if not text: return False, "", "Please enter a topic or paste some text."
    if HOSTED_MODE:
        text = text[:MAX_PROMPT_CHARS]
        if _ABUSE_PATTERNS.search(text):
            return False, "", "Your input contains phrases that look like attempts to misuse the AI. Please enter a genuine quiz topic."
        if len(text.split()) < 2:
            return False, text, "Please enter a more descriptive topic (at least 2 words)."
    return True, text, ""

# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
defaults = {
    "quiz_generated": False, "quiz_data": None, "last_error": None,
    "quiz_mode": False, "current_q": 0, "answers": {}, "show_results": False, "quiz_topic": "",
    "topic_suggestion": "",
}
for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def extract_text_from_file(uploaded_file) -> str:
    if uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8", errors="replace")[:MAX_PROMPT_CHARS]
    elif uploaded_file.type == "application/pdf":
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(uploaded_file.read()))
            return " ".join(page.extract_text() or "" for page in reader.pages)[:MAX_PROMPT_CHARS]
        except Exception as e:
            st.error(f"Could not read PDF: {e}")
            return ""
    return ""

def run_generate_quiz(n_questions, difficulty, user_prompt, question_types) -> dict:
    types_csv = ",".join(question_types)
    try:
        result = subprocess.run(
            [sys.executable, GEN_SCRIPT, str(n_questions), difficulty, user_prompt, types_csv],
            capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        _logger.warning("Timeout n=%s difficulty=%s", n_questions, difficulty)
        st.session_state.last_error = "Quiz generation timed out. Try fewer questions or a smaller model."
        return None
    except Exception as e:
        _logger.error("Subprocess error: %s\n%s", e, traceback.format_exc())
        st.session_state.last_error = "An unexpected error occurred. Please try again."
        return None
    match = re.search(r"(\{[\s\S]*\})", result.stdout)
    if not match:
        st.session_state.last_error = "Model returned no parseable JSON. Check Ollama is running and a model is pulled."
        return None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        _logger.error("JSON parse error: %s", e)
        st.session_state.last_error = "Unexpected response from the model. Please try again."
        return None
    if "error" in data:
        st.session_state.last_error = data["error"]
        return None
    if not data.get("quiz"):
        st.session_state.last_error = "Model returned an empty quiz. Try a different topic or model."
        return None
    return data

def format_quiz_as_text(quiz_data: dict, topic: str = "") -> str:
    import datetime
    divider = "=" * 60
    thin    = "-" * 60
    out = divider + "\n"
    out += "  QUIZCRAFT — AI-Generated Quiz\n"
    if topic:
        out += f"  Topic: {topic}\n"
    out += f"  Generated: {datetime.datetime.now().strftime('%B %d, %Y')}\n"
    out += divider + "\n\n"

    for i, q in enumerate(quiz_data.get("quiz", []), 1):
        qtype = q.get("type", "").strip().lower()
        out += f"{i}.  {q['question']}\n"
        if qtype == "multiple choice":
            for idx, opt in enumerate(q.get("options", []), 1):
                out += f"     {chr(96+idx)})  {opt}\n"
        elif qtype == "true/false":
            out += "     a)  True\n"
            out += "     b)  False\n"
        elif qtype == "fill in the blanks":
            out += "     Answer: ___________________________\n"
        out += "\n"

    out += thin + "\n"
    out += "  ANSWER KEY\n"
    out += thin + "\n"
    for i, q in enumerate(quiz_data.get("quiz", []), 1):
        answer = q.get("answer", "")
        qtype = q.get("type", "").strip().lower()
        if qtype == "multiple choice":
            opts = q.get("options", [])
            answer_clean = answer.split(". ", 1)[-1] if ". " in answer else answer
            try:
                idx = opts.index(answer_clean)
                out += f"  {i}.  ({chr(97+idx)})  {answer_clean}\n"
            except ValueError:
                out += f"  {i}.  {answer}\n"
        elif qtype == "true/false":
            out += f"  {i}.  ({'a' if str(answer).lower() == 'true' else 'b'})  {answer}\n"
        else:
            out += f"  {i}.  {answer}\n"

    out += "\n" + divider + "\n"
    out += "  Created with QuizCraft  |  github.com/NimaShafie/quiz-craft\n"
    out += divider + "\n"
    return out

def generate_quiz_pdf(quiz_data: dict, topic: str = "") -> bytes:
    import datetime
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Header bar
    pdf.set_fill_color(30, 40, 55)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_text_color(240, 200, 170)
    pdf.set_font("Arial", "B", 18)
    pdf.set_xy(10, 6)
    pdf.cell(0, 10, "QuizCraft", ln=False)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(160, 180, 190)
    pdf.set_xy(10, 17)
    label = f"Topic: {topic}  |  " if topic else ""
    pdf.cell(0, 6, f"{label}Generated: {datetime.datetime.now().strftime('%B %d, %Y')}", ln=True)

    pdf.set_text_color(30, 40, 55)
    pdf.ln(8)

    questions = quiz_data.get("quiz", [])
    for i, q in enumerate(questions, 1):
        qtype = q.get("type", "").strip().lower()

        # Question number + text
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(40, 55, 70)
        safe_q = f"{i}.  {q['question']}".encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(0, 7, safe_q)
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(60, 75, 90)

        if qtype == "multiple choice":
            for idx, opt in enumerate(q.get("options", []), 1):
                safe_opt = f"     {chr(96+idx)})  {opt}".encode("latin-1", errors="replace").decode("latin-1")
                pdf.multi_cell(0, 6, safe_opt)
        elif qtype == "true/false":
            pdf.cell(0, 6, "     a)  True", ln=True)
            pdf.cell(0, 6, "     b)  False", ln=True)
        elif qtype == "fill in the blanks":
            pdf.cell(0, 6, "     Answer: ___________________________", ln=True)
        pdf.ln(3)

    # Answer key section
    pdf.ln(4)
    pdf.set_fill_color(245, 240, 235)
    pdf.set_draw_color(200, 160, 130)
    pdf.set_line_width(0.4)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(150, 80, 50)
    pdf.cell(0, 8, "  Answer Key", ln=True, fill=True, border="B")
    pdf.ln(2)

    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(40, 55, 70)
    for i, q in enumerate(questions, 1):
        answer = q.get("answer", "")
        qtype = q.get("type", "").strip().lower()
        if qtype == "multiple choice":
            opts = q.get("options", [])
            answer_clean = answer.split(". ", 1)[-1] if ". " in answer else answer
            try:
                idx = opts.index(answer_clean)
                ans_text = f"  {i}.  ({chr(97+idx)})  {answer_clean}"
            except ValueError:
                ans_text = f"  {i}.  {answer}"
        elif qtype == "true/false":
            ans_text = f"  {i}.  ({'a' if str(answer).lower() == 'true' else 'b'})  {answer}"
        else:
            ans_text = f"  {i}.  {answer}"
        safe_ans = ans_text.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(0, 6, safe_ans)

    # Footer
    pdf.ln(6)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(140, 160, 170)
    pdf.cell(0, 5, "Created with QuizCraft  |  github.com/NimaShafie/quiz-craft", ln=True, align="C")

    return pdf.output(dest="S").encode("latin-1")

# ─────────────────────────────────────────────────────────────────────────────
# UI — Header
# ─────────────────────────────────────────────────────────────────────────────
st.title("QuizCraft")

if HOSTED_MODE:
    st.caption("AI-powered quiz generator — free to use, powered by Ollama")
    used, total = get_remaining_quota()
    remaining = total - used
    color = "#4caf82" if remaining >= 3 else ("#f0a050" if remaining >= 1 else "#e05050")
    st.html(f'<div class="quota-badge" style="color:{color};">{remaining}/{total} generations remaining this hour</div>')
else:
    st.caption("AI-powered quiz generator — self-hosted with Ollama")
    with st.expander("Setup — first time?", expanded=False):
        st.markdown("""
**Requirements:** [Ollama](https://ollama.com) must be running on your machine.
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3:4b
streamlit run src/QuizCraft.py
```
Edit `config.ini` to change the model.
""")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# UI — Topic suggestions
# ─────────────────────────────────────────────────────────────────────────────
st.html('<p style="color:#6a8090;font-size:0.8rem;letter-spacing:0.5px;text-transform:uppercase;margin-bottom:0.4rem;">Quick topics</p>')
_topic_cols = st.columns(4)
for i, _topic in enumerate(TOPIC_SUGGESTIONS):
    with _topic_cols[i % 4]:
        if st.button(_topic, key=f"topic_{i}", use_container_width=True):
            st.session_state.topic_suggestion = _topic
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# UI — Form
# ─────────────────────────────────────────────────────────────────────────────
with st.form(key="quiz_form"):
    uploaded_file = st.file_uploader(
        "Upload a TXT or PDF file", type=["txt", "pdf"],
        help=f"Max ~{MAX_PROMPT_CHARS} characters will be used as context.",
    )
    st.html('<div class="or-sep">— or —</div>')
    user_prompt = st.text_area(
        "Enter a topic or paste text", height=120,
        max_chars=MAX_PROMPT_CHARS,
        value=st.session_state.topic_suggestion,
        placeholder="e.g. 'World War II causes and effects' or paste any text...",
    )
    col1, col2 = st.columns(2, gap="large")
    with col1:
        question_types = st.multiselect(
            "Question Types",
            ["Multiple Choice", "True/False", "Fill in the Blanks"],
            default=["Multiple Choice"],
        )
    with col2:
        difficulty = st.segmented_control("Difficulty", ["Easy", "Medium", "Hard"], default="Medium")

    n_questions = st.slider("Number of Questions", min_value=3, max_value=MAX_QUESTIONS, value=10)

    no_quota  = HOSTED_MODE and get_remaining_quota()[0] >= RATE_LIMIT_REQUESTS
    has_types = bool(question_types)

    if no_quota:
        st.error("You've reached the hourly limit. Please come back later.")
    if not has_types:
        st.warning("Please select at least one question type.")

    submit = st.form_submit_button(
        "Generate Quiz", disabled=(no_quota or not has_types),
        use_container_width=True, type="primary",
    )

# ─────────────────────────────────────────────────────────────────────────────
# Generation
# ─────────────────────────────────────────────────────────────────────────────
if submit:
    st.session_state.quiz_generated = False
    st.session_state.last_error = None
    st.session_state.quiz_mode = False
    st.session_state.current_q = 0
    st.session_state.answers = {}
    st.session_state.show_results = False
    st.session_state.topic_suggestion = ""

    if HOSTED_MODE:
        allowed, rate_msg = check_rate_limit()
        if not allowed:
            st.error(rate_msg)
            st.stop()

    raw_prompt = user_prompt.strip()
    if uploaded_file:
        with st.spinner("Reading file..."):
            raw_prompt = extract_text_from_file(uploaded_file)

    is_valid, safe_prompt, warn_msg = validate_input(raw_prompt)
    if not is_valid:
        st.warning(warn_msg)
        st.stop()

    with st.status("Generating quiz...", expanded=True) as status:
        st.write(f"Generating a **{difficulty}** {n_questions}-question quiz on your topic...")
        st.write("This takes 15-30 seconds on CPU — please wait...")
        st.progress(0.3, text="Sending request to Ollama...")
        quiz_data = run_generate_quiz(n_questions, difficulty, safe_prompt, question_types)
        if quiz_data:
            if HOSTED_MODE:
                record_request()
            st.session_state.quiz_data = quiz_data
            st.session_state.quiz_generated = True
            st.session_state.quiz_topic = safe_prompt[:60]
            status.update(label="Quiz ready!", state="complete", expanded=False)
            st.toast("Quiz ready!")
        else:
            status.update(label="Generation failed", state="error", expanded=False)

if st.session_state.last_error:
    st.error(f"Error: {st.session_state.last_error}")

# ─────────────────────────────────────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.quiz_generated and st.session_state.quiz_data:
    st.markdown("---")
    quiz_data = st.session_state.quiz_data
    questions = quiz_data.get("quiz", [])
    formatted = format_quiz_as_text(quiz_data, topic=st.session_state.get("quiz_topic", ""))

    try:
        pdf_bytes = generate_quiz_pdf(quiz_data, topic=st.session_state.get("quiz_topic", ""))
    except Exception as e:
        _logger.error("PDF error: %s\n%s", e, traceback.format_exc())
        pdf_bytes = None

    # Action row — download + take quiz toggle
    col_pdf, col_txt, col_mode = st.columns([1, 1, 1])
    with col_pdf:
        if pdf_bytes:
            st.download_button("Download PDF", data=pdf_bytes, file_name="quiz.pdf",
                               mime="application/pdf", use_container_width=True)
        else:
            st.warning("PDF unavailable. Use TXT.")
    with col_txt:
        st.download_button("Download TXT", data=formatted, file_name="quiz.txt",
                           mime="text/plain", use_container_width=True)
    with col_mode:
        label = "View Download" if st.session_state.quiz_mode else "Take Quiz"
        if st.button(label, use_container_width=True):
            st.session_state.quiz_mode = not st.session_state.quiz_mode
            st.session_state.current_q = 0
            st.session_state.answers = {}
            st.session_state.show_results = False
            st.rerun()

    # ── Interactive quiz mode ──────────────────────────────────────────────
    if st.session_state.quiz_mode and not st.session_state.show_results:
        mc_questions = [q for q in questions if q.get("type", "").lower() == "multiple choice"]
        tf_questions = [q for q in questions if q.get("type", "").lower() == "true/false"]
        takeable = mc_questions + tf_questions

        if not takeable:
            st.info("Interactive mode requires Multiple Choice or True/False questions.")
        else:
            idx = st.session_state.current_q
            if idx < len(takeable):
                q = takeable[idx]
                progress_val = idx / len(takeable)
                with st.container():
                    # These three lines must be indented to stay inside the container
                    st.html(f'''<div class="quiz-question-card">
                        <div class="quiz-q-number">Question {idx + 1} of {len(takeable)}</div>
                        <div class="quiz-q-text">{q["question"]}</div>
                    </div>''')
                    st.progress(progress_val)
                    st.html('<div style="height:0.5rem"></div>')

                opts = q.get("options", ["True", "False"])
                already_answered = idx in st.session_state.answers
                for opt in opts:
                    if already_answered:
                        correct_answer = q.get("answer", "")
                        answer_clean = correct_answer.split(". ", 1)[-1] if ". " in correct_answer else correct_answer
                        is_correct_opt = opt == answer_clean or opt == correct_answer
                        is_chosen = st.session_state.answers[idx] == opt
                        if is_correct_opt:
                            st.success(f"✓  {opt}")
                        elif is_chosen:
                            st.error(f"✗  {opt}")
                        else:
                            st.html(f'<div style="padding:0.4rem 0.8rem;color:#6a8090;font-size:0.92rem;">{opt}</div>')
                    else:
                        if st.button(opt, key=f"opt_{idx}_{opt}", use_container_width=True):
                            st.session_state.answers[idx] = opt
                            st.rerun()

                if already_answered:
                    st.html('<div style="height:0.4rem"></div>')
                    col_next, _ = st.columns([1, 3])
                    with col_next:
                        next_label = "Finish" if idx + 1 >= len(takeable) else "Next"
                        if st.button(next_label, key="next_q", type="primary"):
                            if idx + 1 >= len(takeable):
                                st.session_state.show_results = True
                            else:
                                st.session_state.current_q += 1
                            st.rerun()

    # ── Score results ──────────────────────────────────────────────────────
    elif st.session_state.quiz_mode and st.session_state.show_results:
        mc_questions = [q for q in questions if q.get("type", "").lower() == "multiple choice"]
        tf_questions = [q for q in questions if q.get("type", "").lower() == "true/false"]
        takeable = mc_questions + tf_questions

        correct = 0
        for i, q in enumerate(takeable):
            chosen = st.session_state.answers.get(i, "")
            correct_answer = q.get("answer", "")
            answer_clean = correct_answer.split(". ", 1)[-1] if ". " in correct_answer else correct_answer
            if chosen == answer_clean or chosen == correct_answer:
                correct += 1

        total_q = len(takeable)
        pct = int((correct / total_q) * 100) if total_q > 0 else 0
        grade = "Excellent!" if pct >= 90 else "Good work!" if pct >= 70 else "Keep practicing!"

        st.html(f'''<div class="score-display">
            <div class="score-number">{correct}/{total_q}</div>
            <div class="score-label">{pct}% — {grade}</div>
        </div>''')

        if st.button("Retake Quiz", use_container_width=False):
            st.session_state.current_q = 0
            st.session_state.answers = {}
            st.session_state.show_results = False
            st.rerun()

    # ── Preview (non-quiz mode) ────────────────────────────────────────────
    else:
        with st.expander("Preview Quiz", expanded=True):
            st.text(formatted)

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.html('''<div class="qc-footer">
    <strong style="color:#4a7080;letter-spacing:1px;">QUIZCRAFT</strong><br>
    Built by <a href="https://github.com/NimaShafie">Nima Shafie</a>
    &nbsp;·&nbsp; Powered by <a href="https://ollama.com">Ollama</a>
    &nbsp;·&nbsp; Built with <a href="https://streamlit.io">Streamlit</a>
    &nbsp;·&nbsp; Model: <a href="https://ollama.com/library/gemma3">gemma3:4b</a><br>
    <span style="color:#1e3040;">Licensed under CC BY-NC-ND 4.0 &nbsp;·&nbsp; Not for commercial use</span>
</div>''')