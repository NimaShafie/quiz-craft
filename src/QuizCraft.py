"""
QuizCraft.py  —  VERSION 1: Self-Hosted / Personal Setup
AI-powered quiz generator using a local Ollama model.

Author: Nima Shafie

Usage:
    streamlit run src/QuizCraft.py
"""

import json
import sys
import re
import os
import subprocess
import tempfile
import streamlit as st
from fpdf import FPDF

# ─────────────────────────────────────────────────────────────────────────────
# Page config — must be first Streamlit call
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
LOGO_PATH = os.path.join(SCRIPT_DIR, "..", "images", "logo", "quiz-craft-logo.png")
GEN_SCRIPT = os.path.join(SCRIPT_DIR, "generate_quiz_from_prompt.py")

# ─────────────────────────────────────────────────────────────────────────────
# Styling
# ─────────────────────────────────────────────────────────────────────────────
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
# Session state init
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [("quiz_generated", False), ("quiz_data", None), ("last_error", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
# Helper: extract text from uploaded file
# ─────────────────────────────────────────────────────────────────────────────
def extract_text_from_file(uploaded_file) -> str:
    """Extract plain text from TXT or PDF upload."""
    if uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8", errors="replace")[:3000]

    elif uploaded_file.type == "application/pdf":
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(uploaded_file.read()))
            text = " ".join(
                page.extract_text() or "" for page in reader.pages
            )
            return text[:3000]
        except Exception as e:
            st.error(f"Could not read PDF: {e}")
            return ""
    return ""

# ─────────────────────────────────────────────────────────────────────────────
# Helper: call the generation subprocess
# ─────────────────────────────────────────────────────────────────────────────
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
        st.session_state.last_error = "Quiz generation timed out. Try fewer questions or a smaller model."
        return None
    except Exception as e:
        st.session_state.last_error = f"Subprocess error: {e}"
        return None

    if result.returncode != 0 and not result.stdout.strip():
        st.session_state.last_error = result.stderr[:500] or "Unknown subprocess error."
        return None

    # Parse JSON from stdout
    match = re.search(r"(\{[\s\S]*\})", result.stdout)
    if not match:
        st.session_state.last_error = "Model returned no parseable JSON. Check Ollama is running and a model is pulled."
        return None

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        st.session_state.last_error = f"JSON parse error: {e}"
        return None

    if "error" in data:
        st.session_state.last_error = data["error"]
        return None

    if not data.get("quiz"):
        st.session_state.last_error = "Model returned an empty quiz. Try a different topic or model."
        return None

    return data

# ─────────────────────────────────────────────────────────────────────────────
# Helper: format quiz as human-readable text
# ─────────────────────────────────────────────────────────────────────────────
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
                letter = chr(97 + idx)
                out += f"{i}. ({letter}) {answer_clean}\n"
            except ValueError:
                out += f"{i}. {answer}\n"
        elif qtype == "true/false":
            letter = "a" if str(answer).lower() == "true" else "b"
            out += f"{i}. ({letter}) {answer}\n"
        else:
            out += f"{i}. {answer}\n"
    return out

# ─────────────────────────────────────────────────────────────────────────────
# Helper: generate PDF
# ─────────────────────────────────────────────────────────────────────────────
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
st.caption("AI-powered quiz generator — self-hosted with Ollama")

with st.expander("ℹ️ Setup — first time?", expanded=False):
    st.markdown("""
**Requirements:** [Ollama](https://ollama.com) must be running on your machine.

```bash
# 1. Install Ollama (Linux / macOS)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull the recommended model
ollama pull gemma3:4b

# 3. Start Ollama (if not already running)
ollama serve

# 4. Run QuizCraft
streamlit run src/QuizCraft.py
```

Edit `config.ini` to change the model. You can use any model from [ollama.com/search](https://ollama.com/search).
""")

st.markdown("---")

# Input section
uploaded_file = st.file_uploader(
    "📎 Upload a TXT or PDF file",
    type=["txt", "pdf"],
    help="Max ~3000 characters will be used as context.",
)

st.write("<center style='color:#888;padding:4px'>— OR —</center>", unsafe_allow_html=True)

user_prompt = st.text_area(
    "✍️ Enter a topic or paste text",
    height=160,
    max_chars=3500,
    placeholder="e.g. 'World War II causes and effects' or paste any text...",
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

    n_questions = st.slider("Number of Questions", min_value=3, max_value=40, value=10)

    # Validation
    has_input = bool(user_prompt.strip() or uploaded_file)
    has_both = bool(user_prompt.strip() and uploaded_file)
    has_types = bool(question_types)

    disable = not has_input or has_both or not has_types

    if has_both:
        st.warning("⚠️ Please use only one input method — text OR file, not both.")
    elif not has_input:
        st.info("Enter a topic above or upload a file to get started.")
    elif not has_types:
        st.warning("⚠️ Please select at least one question type.")

    submit = st.form_submit_button("🚀 Generate Quiz", disabled=disable, use_container_width=True)

# Generation
if submit:
    st.session_state.quiz_generated = False
    st.session_state.last_error = None

    prompt_text = user_prompt.strip()
    if uploaded_file:
        with st.spinner("Reading file..."):
            prompt_text = extract_text_from_file(uploaded_file)

    if prompt_text:
        with st.status("Generating quiz...", expanded=True) as status:
            st.write(f"🤖 Asking Ollama to create a **{difficulty}** {n_questions}-question quiz...")
            quiz_data = run_generate_quiz(n_questions, difficulty, prompt_text, question_types)

            if quiz_data:
                st.session_state.quiz_data = quiz_data
                st.session_state.quiz_generated = True
                status.update(label="✅ Quiz ready!", state="complete", expanded=False)
                st.toast("Quiz generated! 🎉", icon="🎉")
            else:
                status.update(label="❌ Generation failed", state="error", expanded=False)

if st.session_state.last_error:
    st.error(f"**Error:** {st.session_state.last_error}")

# Results
if st.session_state.quiz_generated and st.session_state.quiz_data:
    st.markdown("---")
    formatted = format_quiz_as_text(st.session_state.quiz_data)
    pdf_bytes = generate_quiz_pdf(formatted)

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
