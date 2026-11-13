"""Durable session event log prototype tests."""
import importlib.util
import os
import tempfile

BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_spec = importlib.util.spec_from_file_location(
    "context_pressure",
    os.path.join(BUNDLE_ROOT, "scripts", "context-pressure.py"),
)
cp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cp)


def test_log_and_replay_events():
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".jsonl") as f:
        path = f.name
    try:
        cp.log_event("action", {"idempotency_key": "a1", "task": "read spec"}, log_path=path)
        cp.log_event("action", {"idempotency_key": "a2", "task": "run tests"}, log_path=path)
        events = cp.replay_events(path)
        assert len(events) == 2
        assert events[0]["event_type"] == "action"
    finally:
        os.unlink(path)


def test_resume_state_deduplicates_events():
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".jsonl") as f:
        path = f.name
    try:
        cp.log_event("action", {"idempotency_key": "a1", "task": "read"}, log_path=path)
        cp.log_event("action", {"idempotency_key": "a1", "task": "read"}, log_path=path)
        state = cp.resume_state(path)
        assert len(state["events"]) == 1
        assert "a1" in state["completed_keys"]
    finally:
        os.unlink(path)


def test_constraints_survive_interruption():
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".jsonl") as f:
        path = f.name
    try:
        cp.log_event("constraint", {"idempotency_key": "c1", "constraints": ["no_push_without_auth"]}, log_path=path)
        cp.log_event("action", {"idempotency_key": "a1", "task": "audit"}, log_path=path)
        state = cp.resume_state(path)
        assert "no_push_without_auth" in state["constraints"]
        assert len(state["events"]) == 2
    finally:
        os.unlink(path)
