"""
QuizCraft_hosted.py  —  VERSION 2: Hosted / Public Deployment
AI-powered quiz generator with rate limiting and abuse prevention.

Author: Nima Shafie

Usage:
    streamlit run src/QuizCraft_hosted.py
"""

import json
import sys
import re
import os
import subprocess
import io
import streamlit as st
from fpdf import FPDF
from rate_limiter import (
    check_rate_limit,
    record_request,
    get_remaining_quota,
    validate_and_sanitize_input,
    MAX_QUESTIONS_HOSTED,
)

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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH  = os.path.join(SCRIPT_DIR, "..", "images", "logo", "quiz-craft-logo.png")
GEN_SCRIPT = os.path.join(SCRIPT_DIR, "generate_quiz_from_prompt.py")

import base64 as _b64
_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "logo", "quiz-craft-logo.png")
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as _f:
        _logo_data = _b64.b64encode(_f.read()).decode()
    st.html("""<style>
.stAlert { border-radius: 8px; }
#qc-logo { display: block; margin: -2rem auto -1rem auto; width: 150px; }
</style>
<div><img id="qc-logo" src="data:image/png;base64,""" + _logo_data + """" /></div>""")
else:
    st.html("""<style>.stAlert { border-radius: 8px; }</style>""")



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
        return uploaded_file.read().decode("utf-8", errors="replace")[:2000]
    elif uploaded_file.type == "application/pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(uploaded_file.read()))
            text = " ".join(page.extract_text() or "" for page in reader.pages)
            return text[:2000]
        except Exception as e:
            st.error(f"Could not read PDF: {e}")
            return ""
    return ""


def run_generate_quiz(n_questions, difficulty, user_prompt, question_types) -> dict | None:
    types_csv = ",".join(question_types)
    try:
        result = subprocess.run(
            [sys.executable, GEN_SCRIPT,
             str(n_questions), difficulty, user_prompt, types_csv],
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        st.session_state.last_error = "Quiz generation timed out. Please try again."
        return None
    except Exception as e:
        st.session_state.last_error = f"Internal error: {e}"
        return None

    match = re.search(r"(\{[\s\S]*\})", result.stdout)
    if not match:
        st.session_state.last_error = "Service temporarily unavailable. Please try again shortly."
        return None

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        st.session_state.last_error = "Unexpected response from AI. Please try again."
        return None

    if "error" in data:
        st.session_state.last_error = data["error"]
        return None

    if not data.get("quiz"):
        st.session_state.last_error = "Could not generate quiz for this topic. Try a different one."
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
            out += "   (Fill in the blank)\n"
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
        pdf.multi_cell(0, 8, line)
    return pdf.output(dest="S").encode("latin1")


# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
st.title("QuizCraft 🧠📚❓")
st.caption("AI-powered quiz generator — free to use, powered by Ollama")

# Quota display
used, total = get_remaining_quota()
remaining = total - used
quota_color = "green" if remaining >= 3 else ("orange" if remaining >= 1 else "red")
st.html(f"""
<div style="text-align:right; font-size:0.82em; color:{quota_color}; margin-top:-12px; margin-bottom:8px;">
  🎟️ {remaining}/{total} quiz generations remaining this hour
</div>
""")

st.markdown("---")

# Input
uploaded_file = st.file_uploader(
    "📎 Upload a TXT or PDF file",
    type=["txt", "pdf"],
    help="Max ~2000 characters will be used.",
)

st.write("<center style='color:#888;padding:4px'>— OR —</center>", unsafe_allow_html=True)

user_prompt = st.text_area(
    "✍️ Enter a topic or paste text",
    height=140,
    max_chars=2000,
    placeholder="e.g. 'The French Revolution' or 'Python programming basics'...",
)

# Form
with st.form(key="quiz_form"):
    col1, col2 = st.columns(2, gap="large")

    with col1:
        question_types = st.multiselect(
            "Question Types",
            ["Multiple Choice", "True/False", "Fill in the Blanks"],
            default=["Multiple Choice"],
        )

    with col2:
        difficulty = st.segmented_control(
            "Difficulty",
            ["Easy", "Medium", "Hard"],
            default="Medium",
        )

    n_questions = st.slider(
        "Number of Questions",
        min_value=3,
        max_value=MAX_QUESTIONS_HOSTED,
        value=10,
        help=f"Maximum {MAX_QUESTIONS_HOSTED} questions on the hosted version.",
    )

    has_input = bool(user_prompt.strip() or uploaded_file)
    has_both  = bool(user_prompt.strip() and uploaded_file)
    has_types = bool(question_types)

    if has_both:
        st.warning("⚠️ Please use only one input method.")
    elif not has_input:
        st.info("Enter a topic above or upload a file to get started.")
    elif not has_types:
        st.warning("⚠️ Select at least one question type.")

    disable = not has_input or has_both or not has_types or remaining <= 0
    if remaining <= 0:
        st.error("🚫 You've reached the hourly limit. Please come back later.")

    submit = st.form_submit_button(
        "🚀 Generate Quiz",
        disabled=disable,
        use_container_width=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Generation with rate limit check
# ─────────────────────────────────────────────────────────────────────────────
if submit:
    st.session_state.quiz_generated = False
    st.session_state.last_error = None

    # 1. Check rate limit
    allowed, rate_msg = check_rate_limit()
    if not allowed:
        st.error(f"🚫 {rate_msg}")
        st.stop()

    # 2. Resolve input
    raw_prompt = user_prompt.strip()
    if uploaded_file:
        with st.spinner("Reading file..."):
            raw_prompt = extract_text_from_file(uploaded_file)

    # 3. Validate + sanitize
    is_valid, safe_prompt, warn_msg = validate_and_sanitize_input(raw_prompt)
    if not is_valid:
        st.warning(f"⚠️ {warn_msg}")
        st.stop()

    # 4. Generate
    with st.status("Generating quiz...", expanded=True) as status:
        st.write(f"🤖 Creating a **{difficulty}** {n_questions}-question quiz on your topic...")
        quiz_data = run_generate_quiz(n_questions, difficulty, safe_prompt, question_types)

        if quiz_data:
            record_request()  # Log the request after confirmed success
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
    pdf_bytes  = generate_quiz_pdf(formatted)

    col_pdf, col_txt = st.columns(2)
    with col_pdf:
        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_bytes,
            file_name="quiz.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with col_txt:
        st.download_button(
            label="⬇️ Download TXT",
            data=formatted,
            file_name="quiz.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with st.expander("📋 Preview Quiz", expanded=True):
        st.text(formatted)

# Footer
st.markdown("---")
st.caption("QuizCraft — Powered by [Ollama](https://ollama.com) · Built by Nima Shafie")
