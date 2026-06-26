"""
test_rate_limiting.py
Unit tests for the rate-limiting logic in quiz_craft.py.
No Streamlit display or real LLM required.

Run with: python -m pytest tests/test_rate_limiting.py -v
"""

import sys
import os
import time
from unittest.mock import MagicMock, patch

# ── Mock heavy optional deps before importing quiz_craft ────────────────────
_streamlit_mock = MagicMock()

# st.columns(n) is called at module level with tuple-unpacking, e.g. col1, col2 = st.columns(2).
# Use side_effect so it returns exactly n MagicMocks regardless of the argument.
def _columns_side_effect(n, *args, **kwargs):
    count = n if isinstance(n, int) else len(n)
    return [MagicMock() for _ in range(count)]

_streamlit_mock.columns.side_effect = _columns_side_effect

# st.cache_data must be a pass-through decorator so cached functions remain callable
# and their return values can be unpacked (e.g. _llm_ok, _llm_detail = _check_llm_health()).
def _cache_data_noop(**_kwargs):
    def decorator(fn):
        # Wrap so the decorated function returns a real 2-tuple on every call.
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception:
                return (False, "mocked-health-check")
        return wrapper
    return decorator

_streamlit_mock.cache_data = _cache_data_noop
_streamlit_mock.cache_data.clear = lambda: None

sys.modules["streamlit"] = _streamlit_mock
sys.modules["fpdf"] = MagicMock()
# Do NOT mock sys.modules["requests"] globally — it contaminates other test modules.
# requests.get is patched locally inside _load_module() instead.


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def _make_ctx(session_id: str = "test-session-abc"):
    ctx = MagicMock()
    ctx.session_id = session_id
    return ctx


def _load_module(hosted_mode: bool = True, trusted_proxy: bool = False):
    """Reimport quiz_craft with the desired HOSTED_MODE / TRUSTED_PROXY env vars."""
    os.environ["HOSTED_MODE"] = "true" if hosted_mode else "false"
    os.environ["TRUSTED_PROXY"] = "true" if trusted_proxy else "false"

    if "quiz_craft" in sys.modules:
        del sys.modules["quiz_craft"]

    # Patch requests.get during import to prevent real LLM health-check network calls.
    _mock_resp = MagicMock()
    _mock_resp.ok = True
    _mock_resp.json.return_value = {"models": [{"name": "test-model"}]}
    with patch("requests.get", return_value=_mock_resp):
        import quiz_craft as qc

    qc._ip_store.clear()
    return qc


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _make_ip_allowed(qc, session_id="sess-001", n_times=0):
    """Pre-populate the ip_store with n_times past requests for session_id."""
    _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx(session_id)
    import hashlib
    ip = hashlib.sha256(session_id.encode()).hexdigest()[:16]
    from dataclasses import dataclass, field as dc_field

    @dataclass
    class _Rec:
        timestamps: list = dc_field(default_factory=list)
        last_request: float = 0.0

    qc._ip_store[ip] = qc._IPRecord()
    now = time.time()
    qc._ip_store[ip].timestamps = [now - 100] * n_times  # old enough to be in window
    return ip


# ─────────────────────────────────────────────────────────────────────────────
# Basic allow / deny
# ─────────────────────────────────────────────────────────────────────────────
class TestCheckRateLimitBasic:
    def test_first_request_allowed(self):
        qc = _load_module(hosted_mode=True)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s1")
        allowed, msg = qc.check_rate_limit()
        assert allowed is True
        assert msg == ""

    def test_non_hosted_always_allowed(self):
        qc = _load_module(hosted_mode=False)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s1")
        allowed, msg = qc.check_rate_limit()
        assert allowed is True

    def test_limit_exceeded_returns_false(self):
        qc = _load_module(hosted_mode=True)
        _make_ip_allowed(qc, "s-limit", n_times=qc.RATE_LIMIT_REQUESTS)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-limit")
        allowed, msg = qc.check_rate_limit()
        assert allowed is False
        assert "Rate limit" in msg

    def test_rate_limit_message_contains_reset_time(self):
        qc = _load_module(hosted_mode=True)
        _make_ip_allowed(qc, "s-msg", n_times=qc.RATE_LIMIT_REQUESTS)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-msg")
        _, msg = qc.check_rate_limit()
        assert "Resets in" in msg or "m" in msg  # "XmYs" format

    def test_one_below_limit_is_allowed(self):
        qc = _load_module(hosted_mode=True)
        _make_ip_allowed(qc, "s-below", n_times=qc.RATE_LIMIT_REQUESTS - 1)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-below")
        allowed, _ = qc.check_rate_limit()
        assert allowed is True


# ─────────────────────────────────────────────────────────────────────────────
# Cooldown
# ─────────────────────────────────────────────────────────────────────────────
class TestCooldown:
    def test_cooldown_blocks_rapid_requests(self):
        qc = _load_module(hosted_mode=True)
        import hashlib
        ip = hashlib.sha256("s-cd".encode()).hexdigest()[:16]
        qc._ip_store[ip] = qc._IPRecord()
        qc._ip_store[ip].last_request = time.time()  # just made a request
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-cd")
        allowed, msg = qc.check_rate_limit()
        assert allowed is False
        assert "wait" in msg.lower() or "Please" in msg

    def test_cooldown_expires(self):
        qc = _load_module(hosted_mode=True)
        import hashlib
        ip = hashlib.sha256("s-exp".encode()).hexdigest()[:16]
        qc._ip_store[ip] = qc._IPRecord()
        qc._ip_store[ip].last_request = time.time() - qc.COOLDOWN_SEC - 1  # expired
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-exp")
        allowed, _ = qc.check_rate_limit()
        assert allowed is True


# ─────────────────────────────────────────────────────────────────────────────
# record_request
# ─────────────────────────────────────────────────────────────────────────────
class TestRecordRequest:
    def test_record_increments_timestamps(self):
        qc = _load_module(hosted_mode=True)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-rec")
        import hashlib
        ip = hashlib.sha256("s-rec".encode()).hexdigest()[:16]
        qc.record_request()
        assert len(qc._ip_store[ip].timestamps) == 1

    def test_record_noop_when_not_hosted(self):
        qc = _load_module(hosted_mode=False)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-noop")
        qc.record_request()
        # Nothing should be in the store
        assert len(qc._ip_store) == 0


# ─────────────────────────────────────────────────────────────────────────────
# get_remaining_quota
# ─────────────────────────────────────────────────────────────────────────────
class TestRemainingQuota:
    def test_fresh_ip_has_full_quota(self):
        qc = _load_module(hosted_mode=True)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-quota")
        used, total = qc.get_remaining_quota()
        assert used == 0
        assert total == qc.RATE_LIMIT_REQUESTS

    def test_used_quota_reflects_records(self):
        qc = _load_module(hosted_mode=True)
        _make_ip_allowed(qc, "s-used", n_times=3)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-used")
        used, total = qc.get_remaining_quota()
        assert used == 3
        assert total == qc.RATE_LIMIT_REQUESTS

    def test_quota_returns_zeros_when_not_hosted(self):
        qc = _load_module(hosted_mode=False)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-nh")
        used, total = qc.get_remaining_quota()
        assert used == 0
        assert total == 0


# ─────────────────────────────────────────────────────────────────────────────
# Expired timestamp cleanup
# ─────────────────────────────────────────────────────────────────────────────
class TestTimestampCleanup:
    def test_old_timestamps_not_counted(self):
        qc = _load_module(hosted_mode=True)
        import hashlib
        ip = hashlib.sha256("s-old".encode()).hexdigest()[:16]
        qc._ip_store[ip] = qc._IPRecord()
        # All timestamps are older than the window
        expired = time.time() - qc.RATE_LIMIT_WINDOW_SEC - 10
        qc._ip_store[ip].timestamps = [expired] * qc.RATE_LIMIT_REQUESTS
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-old")
        allowed, _ = qc.check_rate_limit()
        assert allowed is True

    def test_stale_ip_entries_evicted_when_store_large(self):
        qc = _load_module(hosted_mode=True)
        # Populate store beyond threshold with fully-expired records.
        old_time = time.time() - qc.RATE_LIMIT_WINDOW_SEC - 10
        for i in range(qc._MAX_IP_STORE_SIZE + 5):
            fake_ip = f"fake-ip-{i:05d}"
            qc._ip_store[fake_ip] = qc._IPRecord()
            qc._ip_store[fake_ip].timestamps = [old_time]

        before = len(qc._ip_store)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = _make_ctx("s-evict")
        qc.check_rate_limit()  # triggers cleanup
        after = len(qc._ip_store)
        assert after < before, "Stale entries should have been evicted"


# ─────────────────────────────────────────────────────────────────────────────
# X-Forwarded-For — only trusted when TRUSTED_PROXY=true
# ─────────────────────────────────────────────────────────────────────────────
class TestClientIp:
    def test_session_id_used_when_trusted_proxy_off(self):
        qc = _load_module(hosted_mode=True, trusted_proxy=False)
        ctx = _make_ctx("my-unique-session")
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.return_value = ctx
        ip = qc._get_client_ip()
        import hashlib
        expected = hashlib.sha256("my-unique-session".encode()).hexdigest()[:16]
        assert ip == expected

    def test_x_forwarded_for_used_when_trusted_proxy_on(self):
        qc = _load_module(hosted_mode=True, trusted_proxy=True)
        # Simulate request headers with X-Forwarded-For containing spoofed + real IP.
        headers_mock = {"X-Forwarded-For": "1.2.3.4, 10.0.0.1"}
        _streamlit_mock.context.headers = headers_mock
        ip = qc._get_client_ip()
        import hashlib
        # Should use the LAST IP (10.0.0.1 — the one added by the trusted proxy).
        expected = hashlib.sha256("10.0.0.1".encode()).hexdigest()[:16]
        assert ip == expected

    def test_unknown_fallback_on_exception(self):
        qc = _load_module(hosted_mode=False)
        _streamlit_mock.runtime.scriptrunner.get_script_run_ctx.side_effect = RuntimeError("no ctx")
        ip = qc._get_client_ip()
        assert ip == "unknown"
