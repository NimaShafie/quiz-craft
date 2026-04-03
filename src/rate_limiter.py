"""
rate_limiter.py — Version 2: Hosted deployment security module.
Author: Nima Shafie

Provides:
- Per-IP rate limiting (in-memory, resets on server restart)
- Input validation and length caps
- Abuse pattern detection (too-long prompts, suspicious tokens)
- Session token tracking to prevent parallel abuse

This is a lightweight in-process store — no Redis required.
For production scale, swap _store for a Redis/SQLite backend.
"""

import hashlib
import time
import re
import streamlit as st
from collections import defaultdict
from dataclasses import dataclass, field
from typing import ClassVar


# ─────────────────────────────────────────────────────────────────────────────
# Config — tune these for your deployment
# ─────────────────────────────────────────────────────────────────────────────

RATE_LIMIT_REQUESTS   = 5      # max quiz generations per window
RATE_LIMIT_WINDOW_SEC = 3600   # rolling window in seconds (1 hour)
MAX_QUESTIONS_HOSTED  = 20     # cap questions for hosted version
MAX_PROMPT_CHARS      = 2000   # tighter cap for hosted
COOLDOWN_SEC          = 15     # minimum seconds between requests

# Phrases that suggest someone is trying to abuse the LLM
_ABUSE_PATTERNS = re.compile(
    r"(ignore (previous|above|all) instructions?|"
    r"disregard|forget (everything|all)|"
    r"you are now|act as (an?|the)\s+\w+|pretend (you are|to be)|"
    r"system prompt|override (the )?(system|instructions?)|"
    r"jailbreak|DAN mode|developer mode|"
    r"write me (a |an )?(story|essay|poem|code|script)|"
    r"translate (this|the following)|"
    r"summarize|explain|help me (write|code|build)|"
    r"what is (your|the) (system prompt|context)|"
    r"repeat after me|say exactly|output your (prompt|instructions?))",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# In-memory store (shared across Streamlit reruns via st.session_state cache)
# We use a module-level dict so it persists across user sessions on the server.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class _IPRecord:
    timestamps: list = field(default_factory=list)
    last_request: float = 0.0
    total_lifetime: int = 0


# Module-level store — survives streamlit reruns within the same server process
_ip_store: dict[str, _IPRecord] = {}


def _get_client_ip() -> str:
    """
    Best-effort client IP extraction from Streamlit headers.
    Works behind nginx with X-Forwarded-For.
    Falls back to a hashed session id if headers are unavailable.
    """
    try:
        # Streamlit >= 1.31 exposes request headers
        headers = st.context.headers
        forwarded_for = headers.get("X-Forwarded-For", "")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
            return hashlib.sha256(ip.encode()).hexdigest()[:16]
        real_ip = headers.get("X-Real-Ip", "")
        if real_ip:
            return hashlib.sha256(real_ip.encode()).hexdigest()[:16]
    except Exception:
        pass

    # Fallback: use a stable hash of session id
    session_id = st.runtime.scriptrunner.get_script_run_ctx().session_id
    return hashlib.sha256(session_id.encode()).hexdigest()[:16]


def check_rate_limit() -> tuple[bool, str]:
    """
    Returns (allowed: bool, message: str).
    Call this before every quiz generation attempt.
    """
    ip = _get_client_ip()
    now = time.time()

    if ip not in _ip_store:
        _ip_store[ip] = _IPRecord()

    record = _ip_store[ip]

    # Enforce cooldown between requests
    elapsed_since_last = now - record.last_request
    if record.last_request > 0 and elapsed_since_last < COOLDOWN_SEC:
        remaining = int(COOLDOWN_SEC - elapsed_since_last)
        return False, f"Please wait {remaining}s before generating another quiz."

    # Prune timestamps outside the rolling window
    record.timestamps = [t for t in record.timestamps if now - t < RATE_LIMIT_WINDOW_SEC]

    if len(record.timestamps) >= RATE_LIMIT_REQUESTS:
        oldest = record.timestamps[0]
        reset_in = int(RATE_LIMIT_WINDOW_SEC - (now - oldest))
        mins = reset_in // 60
        secs = reset_in % 60
        return False, (
            f"Rate limit reached ({RATE_LIMIT_REQUESTS} quizzes per hour). "
            f"Resets in {mins}m {secs}s."
        )

    return True, ""


def record_request():
    """Call this after a successful quiz generation to log the request."""
    ip = _get_client_ip()
    now = time.time()
    if ip not in _ip_store:
        _ip_store[ip] = _IPRecord()
    record = _ip_store[ip]
    record.timestamps.append(now)
    record.last_request = now
    record.total_lifetime += 1


def get_remaining_quota() -> tuple[int, int]:
    """Returns (used, total) for the current IP in this window."""
    ip = _get_client_ip()
    now = time.time()
    if ip not in _ip_store:
        return 0, RATE_LIMIT_REQUESTS
    record = _ip_store[ip]
    used = len([t for t in record.timestamps if now - t < RATE_LIMIT_WINDOW_SEC])
    return used, RATE_LIMIT_REQUESTS


# ─────────────────────────────────────────────────────────────────────────────
# Input validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_and_sanitize_input(text: str) -> tuple[bool, str, str]:
    """
    Returns (is_valid: bool, sanitized_text: str, warning_msg: str).
    """
    text = text.strip()

    if not text:
        return False, "", "Please enter a topic or paste some text."

    if len(text) > MAX_PROMPT_CHARS:
        text = text[:MAX_PROMPT_CHARS]

    # Detect abuse patterns
    if _ABUSE_PATTERNS.search(text):
        return False, "", (
            "Your input contains phrases that look like attempts to misuse the AI. "
            "Please enter a genuine quiz topic."
        )

    # Strip control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"[^\S\n]+", " ", text)

    if len(text.split()) < 2:
        return False, text, "Please enter a more descriptive topic (at least 2 words)."

    return True, text, ""
