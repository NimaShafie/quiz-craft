"""
QuizCraft.py — AI-powered quiz generator using a local Ollama model.

Author: Nima Shafie

Usage:
    # Self-hosted (no restrictions):
    streamlit run src/QuizCraft.py

    # Hosted mode (rate limiting + abuse protection):
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
# Mode detection
# ─────────────────────────────────────────────────────────────────────────────
HOSTED_MODE = os.environ.get("HOSTED_MODE", "").lower() in ("true", "1", "yes")

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
MAX_QUESTIONS    = 20   if HOSTED_MODE else 40
MAX_PROMPT_CHARS = 2000 if HOSTED_MODE else 3500

RATE_LIMIT_REQUESTS   = 5
RATE_LIMIT_WINDOW_SEC = 3600
COOLDOWN_SEC          = 15

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
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(_LOG_DIR, "quizcraft.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_logger = logging.getLogger("quizcraft")

# ─────────────────────────────────────────────────────────────────────────────
# Styling + Logo + Theme
# ─────────────────────────────────────────────────────────────────────────────
import base64 as _b64
_logo_path = os.path.join(SCRIPT_DIR, "..", "images", "logo", "quiz-craft-logo.png")

_THEME_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── Page background ── */
.stApp {
    background: linear-gradient(160deg, #0f1923 0%, #1a2535 60%, #0f1923 100%);
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Main content area ── */
.block-container {
    padding-top: 1rem !important;
    max-width: 780px !important;
}

/* ── Logo ── */
#qc-logo {
    display: block;
    margin: -2rem auto -1rem auto;
    width: 150px;
    filter: drop-shadow(0 4px 24px rgba(220,80,80,0.25));
}

/* ── Title ── */
h1 {
    font-family: 'Playfair Display', serif !important;
    font-size: 2.6rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #f5f0e8 30%, #e8927c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
    margin-bottom: 0 !important;
}

/* ── Caption / subtitle ── */
.stCaption p {
    color: #8fa3b8 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.3px;
}

/* ── Divider ── */
hr {
    border-color: rgba(255,255,255,0.07) !important;
    margin: 0.8rem 0 1.2rem 0 !important;
}

/* ── Form card ── */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 16px !important;
    padding: 1.6rem 1.8rem !important;
    backdrop-filter: blur(8px);
    box-shadow: 0 8px 40px rgba(0,0,0,0.3);
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1.5px dashed rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    padding: 0.4rem 0.8rem !important;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(220,130,100,0.5) !important;
}

/* ── Text area ── */
[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1.5px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e8e4dc !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(220,130,100,0.6) !important;
    box-shadow: 0 0 0 3px rgba(220,130,100,0.1) !important;
}

/* ── OR separator ── */
.or-sep {
    text-align: center;
    color: #4a6070;
    font-size: 0.78rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 0.6rem 0;
    position: relative;
}

/* ── Segmented control (difficulty) ── */
[data-testid="stSegmentedControl"] {
    background: rgba(255,255,255,0.05) !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

/* ── Slider ── */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background: #dc6e50 !important;
    border-color: #dc6e50 !important;
}

/* ── Generate button ── */
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #c94f35 0%, #e0714f 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 1rem !important;
    letter-spacing: 0.3px !important;
    padding: 0.65rem 1.5rem !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
    box-shadow: 0 4px 20px rgba(201,79,53,0.35) !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 28px rgba(201,79,53,0.5) !important;
}
[data-testid="stFormSubmitButton"] button:disabled {
    background: rgba(255,255,255,0.08) !important;
    box-shadow: none !important;
    transform: none !important;
    color: rgba(255,255,255,0.3) !important;
}

/* ── Download buttons ── */
[data-testid="stDownloadButton"] button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: #c8d8e8 !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: background 0.15s, border-color 0.15s !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(255,255,255,0.25) !important;
}

/* ── Expander (setup + preview) ── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary {
    color: #8fa3b8 !important;
    font-size: 0.9rem !important;
}

/* ── Alerts ── */
.stAlert {
    border-radius: 10px !important;
    border-left-width: 3px !important;
    font-size: 0.9rem !important;
}

/* ── Status box ── */
[data-testid="stStatus"] {
    border-radius: 10px !important;
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

/* ── Multiselect tags ── */
[data-baseweb="tag"] {
    background: rgba(201,79,53,0.25) !important;
    border-color: rgba(201,79,53,0.4) !important;
    border-radius: 6px !important;
}

/* ── Labels ── */
label, .stSelectbox label, [data-testid="stWidgetLabel"] p {
    color: #a0b4c4 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.3px !important;
    text-transform: uppercase !important;
}

/* ── Quiz preview text ── */
[data-testid="stText"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    line-height: 1.7 !important;
    color: #c8d8e0 !important;
}

/* ── Quota badge ── */
.quota-badge {
    text-align: right;
    font-size: 0.78rem;
    margin-top: -10px;
    margin-bottom: 8px;
    opacity: 0.85;
}

/* ── Footer ── */
.qc-footer {
    text-align: center;
    color: #3a5060;
    font-size: 0.75rem;
    margin-top: 2rem;
    letter-spacing: 0.3px;
}
.qc-footer a { color: #5a8090; text-decoration: none; }
</style>
"""

if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as _f:
        _logo_data = _b64.b64encode(_f.read()).decode()
    st.html(_THEME_CSS + '<div><img id="qc-logo" src="data:image/png;base64,' + _logo_data + '" /></div>')
else:
    st.html(_THEME_CSS)

# ─────────────────────────────────────────────────────────────────────────────
# Rate limiting (hosted mode only)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class _IPRecord:
    timestamps: list = field(default_factory=list)
    last_request: float = 0.0

_ip_store: dict = {}

_ABUSE_PATTERNS = re.compile(
    r"(ignore (previous|above|all) instructions?|"
    r"disregard|forget (everything|all)|"
    r"you are now|act as|pretend (you are|to be)|"
    r"system prompt|override|jailbreak|"
    r"repeat after me|say exactly)",
    re.IGNORECASE,
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
    if not HOSTED_MODE:
        return True, ""
    ip = _get_client_ip()
    now = time.time()
    if ip not in _ip_store:
        _ip_store[ip] = _IPRecord()
    record = _ip_store[ip]
    elapsed = now - record.last_request
    if record.last_request > 0 and elapsed < COOLDOWN_SEC:
        return False, f"Please wait {int(COOLDOWN_SEC - elapsed)}s before generating another quiz."
    record.timestamps = [t for t in record.timestamps if now - t < RATE_LIMIT_WINDOW_SEC]
    if len(record.timestamps) >= RATE_LIMIT_REQUESTS:
        oldest = record.timestamps[0]
        reset_in = int(RATE_LIMIT_WINDOW_SEC - (now - oldest))
        return False, (f"Rate limit reached ({RATE_LIMIT_REQUESTS} quizzes/hour). "
                       f"Resets in {reset_in // 60}m {reset_in % 60}s.")
    return True, ""

def record_request():
    if not HOSTED_MODE:
        return
    ip = _get_client_ip()
    now = time.time()
    if ip not in _ip_store:
        _ip_store[ip] = _IPRecord()
    _ip_store[ip].timestamps.append(now)
    _ip_store[ip].last_request = now

def get_remaining_quota() -> tuple:
    if not HOSTED_MODE:
        return 0, 0
    ip = _get_client_ip()
    now = time.time()
    if ip not in _ip_store:
        return 0, RATE_LIMIT_REQUESTS
    used = len([t for t in _ip_store[ip].timestamps if now - t < RATE_LIMIT_WINDOW_SEC])
    return used, RATE_LIMIT_REQUESTS

def validate_input(text: str) -> tuple:
    text = text.strip()
    if not text:
        return False, "", "Please enter a topic or paste some text."
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
for key, default in [("quiz_generated", False), ("quiz_data", None), ("last_error", None)]:
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
            text = " ".join(page.extract_text() or "" for page in reader.pages)
            return text[:MAX_PROMPT_CHARS]
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
        _logger.warning("Quiz generation timed out (n=%s, difficulty=%s)", n_questions, difficulty)
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

def format_quiz_as_text(quiz_data: dict) -> str:
    out = ""
    for i, q in enumerate(quiz_data.get("quiz", []), 1):
        out += f"{i}. {q['question']}\n"
        qtype = q.get("type", "").strip().lower()
        if qtype == "multiple choice":
            for idx, opt in enumerate(q.get("options", []), 1):
                out += f"   {chr(96+idx)}. {opt}\n"
        elif qtype == "true/false":
            out += "   a. True\n   b. False\n"
        elif qtype == "fill in the blanks":
            out += "   (Write your answer on the blank)\n"
        out += "\n"
    out += "\n─── Answer Key ───\n"
    for i, q in enumerate(quiz_data.get("quiz", []), 1):
        answer = q.get("answer", "")
        qtype = q.get("type", "").strip().lower()
        if qtype == "multiple choice":
            opts = q.get("options", [])
            answer_clean = answer.split(". ", 1)[-1] if ". " in answer else answer
            try:
                idx = opts.index(answer_clean)
                out += f"{i}. ({chr(97+idx)}) {answer_clean}\n"
            except ValueError:
                out += f"{i}. {answer}\n"
        elif qtype == "true/false":
            letter = "a" if str(answer).lower() == "true" else "b"
            out += f"{i}. ({letter}) {answer}\n"
        else:
            out += f"{i}. {answer}\n"
    return out

def generate_quiz_pdf(quiz_text: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in quiz_text.split("\n"):
        safe_line = line.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(0, 8, safe_line)
    return bytes(pdf.output())

# ─────────────────────────────────────────────────────────────────────────────
# UI — Header
# ─────────────────────────────────────────────────────────────────────────────
st.title("QuizCraft 🧠📚❓")

if HOSTED_MODE:
    st.caption("AI-powered quiz generator — free to use, powered by Ollama")
    used, total = get_remaining_quota()
    remaining = total - used
    color = "#4caf82" if remaining >= 3 else ("#f0a050" if remaining >= 1 else "#e05050")
    st.html(f'<div class="quota-badge" style="color:{color};">🎟️ {remaining}/{total} generations remaining this hour</div>')
else:
    st.caption("AI-powered quiz generator — self-hosted with Ollama")
    with st.expander("ℹ️ Setup — first time?", expanded=False):
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
# UI — Form
# ─────────────────────────────────────────────────────────────────────────────
with st.form(key="quiz_form"):
    uploaded_file = st.file_uploader(
        "📎 Upload a TXT or PDF file",
        type=["txt", "pdf"],
        help=f"Max ~{MAX_PROMPT_CHARS} characters will be used as context.",
    )

    st.html('<div class="or-sep">— or —</div>')

    user_prompt = st.text_area(
        "✍️ Enter a topic or paste text",
        height=140,
        max_chars=MAX_PROMPT_CHARS,
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
        difficulty = st.segmented_control(
            "Difficulty", ["Easy", "Medium", "Hard"], default="Medium",
        )

    n_questions = st.slider(
        "Number of Questions", min_value=3, max_value=MAX_QUESTIONS, value=10,
    )

    no_quota  = HOSTED_MODE and get_remaining_quota()[0] >= RATE_LIMIT_REQUESTS
    has_types = bool(question_types)

    if no_quota:
        st.error("🚫 You've reached the hourly limit. Please come back later.")
    if not has_types:
        st.warning("⚠️ Please select at least one question type.")

    submit = st.form_submit_button(
        "🚀 Generate Quiz",
        disabled=(no_quota or not has_types),
        use_container_width=True,
        type="primary",
    )

# ─────────────────────────────────────────────────────────────────────────────
# Generation
# ─────────────────────────────────────────────────────────────────────────────
if submit:
    st.session_state.quiz_generated = False
    st.session_state.last_error = None

    if HOSTED_MODE:
        allowed, rate_msg = check_rate_limit()
        if not allowed:
            st.error(f"🚫 {rate_msg}")
            st.stop()

    raw_prompt = user_prompt.strip()
    if uploaded_file:
        with st.spinner("Reading file..."):
            raw_prompt = extract_text_from_file(uploaded_file)

    is_valid, safe_prompt, warn_msg = validate_input(raw_prompt)
    if not is_valid:
        st.warning(f"⚠️ {warn_msg}")
        st.stop()

    with st.status("Generating quiz...", expanded=True) as status:
        st.write(f"🤖 Generating a **{difficulty}** {n_questions}-question quiz on your topic...")
        st.write("⏳ This takes 15-30 seconds on CPU — please wait...")
        st.progress(0.3, text="Sending request to Ollama...")
        quiz_data = run_generate_quiz(n_questions, difficulty, safe_prompt, question_types)
        if quiz_data:
            if HOSTED_MODE:
                record_request()
            st.session_state.quiz_data = quiz_data
            st.session_state.quiz_generated = True
            status.update(label="✅ Quiz ready!", state="complete", expanded=False)
            st.toast("Quiz generated! 🎉", icon="🎉")
        else:
            status.update(label="❌ Generation failed", state="error", expanded=False)

if st.session_state.last_error:
    st.error(f"**Error:** {st.session_state.last_error}")

# ─────────────────────────────────────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.quiz_generated and st.session_state.quiz_data:
    st.markdown("---")
    formatted = format_quiz_as_text(st.session_state.quiz_data)
    try:
        pdf_bytes = generate_quiz_pdf(formatted)
    except Exception as e:
        _logger.error("PDF generation error: %s\n%s", e, traceback.format_exc())
        pdf_bytes = None

    col_pdf, col_txt = st.columns(2)
    with col_pdf:
        if pdf_bytes:
            st.download_button(
                label="⬇️ Download PDF", data=pdf_bytes,
                file_name="quiz.pdf", mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.warning("⚠️ PDF export unavailable. Use TXT instead.")
    with col_txt:
        st.download_button(
            label="⬇️ Download TXT", data=formatted,
            file_name="quiz.txt", mime="text/plain",
            use_container_width=True,
        )
    with st.expander("📋 Preview Quiz", expanded=True):
        st.text(formatted)

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
if HOSTED_MODE:
    st.html('<div class="qc-footer">QuizCraft · Powered by <a href="https://ollama.com">Ollama</a> · Built by Nima Shafie</div>')