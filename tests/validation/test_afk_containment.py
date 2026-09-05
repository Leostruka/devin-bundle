"""AFK containment preflight tests."""
import importlib.util
import os

BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_spec = importlib.util.spec_from_file_location(
    "afk_containment",
    os.path.join(BUNDLE_ROOT, "scripts", "afk_containment.py"),
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


def test_preflight_allows_local_work_with_worktree_only():
    result = ac.preflight(require_worktree=False)
    assert result["verdict"] == "allow"
    assert result["exposure"]["git_worktree"] is True
    assert result["checks"]["git worktree"] is True


def test_preflight_fails_closed_for_untrusted_filesystem():
    result = ac.preflight(require_filesystem_sandbox=True)
    # No sandbox is available in the test environment, so it must fail closed.
    assert result["verdict"] == "stop"
    assert result["failed"]
    assert "filesystem sandbox" in result["failed"]


def test_preflight_fails_closed_for_untrusted_network():
    result = ac.preflight(require_network_sandbox=True)
    assert result["verdict"] == "stop"
    assert "network sandbox" in result["failed"]


def test_evaluate_trust_allows_local_source():
    result = ac.evaluate_trust("local")
    assert result["verdict"] == "allow"
    assert result["sandbox_required"] is False


def test_evaluate_trust_stops_for_unknown_source():
    result = ac.evaluate_trust("external")
    assert result["verdict"] == "stop"
    assert result["sandbox_required"] is True


def test_evaluate_trust_allows_signed_and_sandboxed():
    result = ac.evaluate_trust("external", signed_by="ci", approved_sandboxes={"ci"})
    assert result["verdict"] == "allow"
    assert result["sandbox_required"] is True
