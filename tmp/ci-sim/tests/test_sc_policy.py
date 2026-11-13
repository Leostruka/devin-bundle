"""sc_policy — deny-wins classification and one-shot request-bound tokens."""
import json
import os
import stat
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_contract as contract  # noqa: E402
import sc_policy as policy  # noqa: E402


def request(capability, args, target=None):
    value = {
        "version": 1, "request_id": "r1", "capability": capability,
        "args": args, "deadline_ms": 1000, "policy": {"dry_run": False},
    }
    if target is not None:
        value["target"] = target
    return value


def test_deny_wins_over_confirmation():
    req = request("file.delete", {"path": "x"})
    assert policy.classify(req)["decision"] == "deny"


def test_confirmation_is_bound_to_exact_request(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    original = request("process.cancel", {}, {"pid": 10, "start_time": 20})
    token = policy.issue_confirmation(original)["confirmation_id"]
    changed = request("process.cancel", {}, {"pid": 11, "start_time": 20})
    assert policy.consume_confirmation(changed, token)["ok"] is False


def test_confirmation_is_single_use(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {}, {"pid": 10, "start_time": 20})
    token = policy.issue_confirmation(req)["confirmation_id"]
    assert policy.consume_confirmation(req, token)["ok"] is True
    assert policy.consume_confirmation(req, token)["ok"] is False


def test_classify_decision_shapes():
    assert policy.classify(request("capabilities", {})) == {
        "decision": "allow", "reason": "capability_allowed"}
    assert policy.classify(request("process.exec", {})) == {
        "decision": "confirm", "reason": "confirmation_required"}
    assert policy.classify(request("file.delete", {})) == {
        "decision": "deny", "reason": "capability_denied"}
    assert policy.classify(request("no.such", {})) == {
        "decision": "deny", "reason": "unknown_capability"}


def test_deny_wins_with_overlapping_sets(monkeypatch):
    monkeypatch.setattr(policy, "DENY", {"x.op"})
    monkeypatch.setattr(policy, "CONFIRM", {"x.op", "process.cancel"})
    monkeypatch.setattr(policy, "ALLOW", {"x.op"})
    assert policy.classify(request("x.op", {}))["decision"] == "deny"
    monkeypatch.setattr(policy, "DENY", set())
    assert policy.classify(
        request("process.cancel", {}))["decision"] == "confirm"
    monkeypatch.setattr(policy, "CONFIRM", set())
    assert policy.classify(
        request("process.cancel", {}))["decision"] == "deny"


def test_dry_run_never_authorizes_mutation():
    req = request("process.exec", {})
    req["policy"]["dry_run"] = True
    assert policy.classify(req)["decision"] == "confirm"


def test_policy_schema_validation():
    contract.validate_request(request("capabilities", {}))
    bad = request("capabilities", {})
    bad["policy"]["extra"] = 1
    with pytest.raises(contract.InvalidRequest, match="policy"):
        contract.validate_request(bad)
    bad = request("capabilities", {})
    bad["policy"]["dry_run"] = "yes"
    with pytest.raises(contract.InvalidRequest, match="dry_run"):
        contract.validate_request(bad)
    bad = request("capabilities", {})
    bad["policy"]["confirmation_id"] = 42
    with pytest.raises(contract.InvalidRequest,
                       match="confirmation_id"):
        contract.validate_request(bad)
    ok = request("capabilities", {})
    ok["policy"]["confirmation_id"] = "a" * 64
    contract.validate_request(ok)
    bad = request("capabilities", {})
    bad["policy"] = "nope"
    with pytest.raises(contract.InvalidRequest, match="policy"):
        contract.validate_request(bad)


def test_digest_binds_everything_except_confirmation_id(tmp_path,
                                                        monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {"grace": 2},
                  {"pid": 10, "start_time": 20})
    base = policy.request_digest(req)
    issued = policy.issue_confirmation(req)
    with_id = request("process.cancel", {"grace": 2},
                      {"pid": 10, "start_time": 20})
    with_id["policy"]["confirmation_id"] = issued["confirmation_id"]
    assert policy.request_digest(with_id) == base
    for mutate in (
            lambda r: r.update(request_id="r2"),
            lambda r: r.update(capability="process.exec"),
            lambda r: r["target"].update(pid=11),
            lambda r: r["args"].update(grace=5),
            lambda r: r.update(deadline_ms=2000),
            lambda r: r["policy"].update(dry_run=True)):
        changed = request("process.cancel", {"grace": 2},
                          {"pid": 10, "start_time": 20})
        mutate(changed)
        assert policy.request_digest(changed) != base


def test_issue_confirmation_validates_request(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    bad = request("process.cancel", {})
    del bad["deadline_ms"]
    with pytest.raises(contract.InvalidRequest):
        policy.issue_confirmation(bad)


def test_ttl_bounds(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    for bad in (True, 0, -1, 121, "5", 1.5):
        with pytest.raises(contract.InvalidRequest):
            policy.issue_confirmation(req, ttl_s=bad)
    policy.issue_confirmation(req, ttl_s=1)
    policy.issue_confirmation(req, ttl_s=120)


def test_token_format_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    for bad in ("../x", "..\\x", "a" * 63, "a" * 65, "A" * 64,
                "a" * 32 + "/..", "", None):
        r = policy.consume_confirmation(req, bad)
        assert r["ok"] is False
        assert r["reason"] == "unknown_confirmation"


def test_consume_unknown_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    r = policy.consume_confirmation(req, "f" * 64)
    assert r == {"ok": False, "reason": "unknown_confirmation"}


def test_metadata_contains_no_raw_request(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {"secretish": "v"},
                  {"pid": 10, "start_time": 20})
    token = policy.issue_confirmation(req)["confirmation_id"]
    meta = json.loads((tmp_path / f"{token}.json").read_text())
    assert set(meta) == {"digest", "created_at", "expires_at"}
    assert meta["digest"] == policy.request_digest(req)
    assert "args" not in meta and "target" not in meta
    assert "capability" not in meta


def test_token_file_owner_only_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    token = policy.issue_confirmation(req)["confirmation_id"]
    mode = stat.S_IMODE((tmp_path / f"{token}.json").stat().st_mode)
    if os.name == "posix":
        assert mode == 0o600


def test_consume_expired_deletes_token(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    token = policy.issue_confirmation(req, ttl_s=60)[
        "confirmation_id"]
    path = tmp_path / f"{token}.json"
    meta = json.loads(path.read_text())
    meta["created_at"] = time.time() - 61
    meta["expires_at"] = time.time() - 1
    path.write_text(json.dumps(meta))
    r = policy.consume_confirmation(req, token)
    assert r == {"ok": False, "reason": "expired"}
    assert not path.exists()


def test_consume_mismatch_deletes_token(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    token = policy.issue_confirmation(req)["confirmation_id"]
    changed = request("process.cancel", {"different": True})
    r = policy.consume_confirmation(changed, token)
    assert r == {"ok": False, "reason": "request_mismatch"}
    assert not (tmp_path / f"{token}.json").exists()


def test_malformed_metadata_fails_closed_and_consumes(tmp_path,
                                                    monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    token = policy.issue_confirmation(req)["confirmation_id"]
    path = tmp_path / f"{token}.json"
    path.write_text("not json {")
    r = policy.consume_confirmation(req, token)
    assert r["ok"] is False
    assert not path.exists()
    assert list(tmp_path.iterdir()) == []


def test_consume_is_atomic_single_use(tmp_path, monkeypatch):
    """Two racing consumers: exactly one may succeed."""
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    token = policy.issue_confirmation(req)["confirmation_id"]
    barrier = threading.Barrier(2)
    real_replace = os.replace

    def synced_replace(src, dst):
        if Path(src).name == f"{token}.json":
            barrier.wait(timeout=10)
        return real_replace(src, dst)

    monkeypatch.setattr(policy.os, "replace", synced_replace)
    results = []
    threads = [
        threading.Thread(
            target=lambda: results.append(
                policy.consume_confirmation(req, token)["ok"]))
        for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(15)
    assert not any(t.is_alive() for t in threads)
    assert sorted(results) == [False, True]


def test_consume_retries_transient_claimed_read(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    token = policy.issue_confirmation(req)["confirmation_id"]
    real_read = Path.read_text
    calls = {"n": 0}

    def flaky_read(self, *args, **kwargs):
        if self.name.startswith(".consume-"):
            calls["n"] += 1
            if calls["n"] <= 2:
                raise PermissionError("transient lock")
        return real_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", flaky_read)
    r = policy.consume_confirmation(req, token)
    assert r == {"ok": True, "reason": "confirmed"}
    assert calls["n"] == 3
    assert list(tmp_path.iterdir()) == []


def test_consume_persistent_claimed_read_failure_fails_closed(
        tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    token = policy.issue_confirmation(req)["confirmation_id"]
    real_read = Path.read_text

    def dead_read(self, *args, **kwargs):
        if self.name.startswith(".consume-"):
            raise PermissionError("locked forever")
        return real_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", dead_read)
    r = policy.consume_confirmation(req, token)
    assert r == {"ok": False, "reason": "unknown_confirmation"}
    assert list(tmp_path.iterdir()) == []


def test_consume_invalid_utf8_metadata_fails_closed(tmp_path,
                                                    monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    token = policy.issue_confirmation(req)["confirmation_id"]
    (tmp_path / f"{token}.json").write_bytes(b"\xff\xfe\x00bad")
    r = policy.consume_confirmation(req, token)
    assert r == {"ok": False, "reason": "unknown_confirmation"}
    assert list(tmp_path.iterdir()) == []


def test_consume_deeply_nested_json_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    token = policy.issue_confirmation(req)["confirmation_id"]
    (tmp_path / f"{token}.json").write_text("[" * 100000)
    r = policy.consume_confirmation(req, token)
    assert r == {"ok": False, "reason": "unknown_confirmation"}
    assert list(tmp_path.iterdir()) == []


def test_consume_unlink_failure_never_succeeds(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    token = policy.issue_confirmation(req)["confirmation_id"]

    def boom(self, *args, **kwargs):
        raise OSError("unlink blocked")

    monkeypatch.setattr(Path, "unlink", boom)
    r = policy.consume_confirmation(req, token)
    assert r == {"ok": False, "reason": "unknown_confirmation"}


def test_issue_confirmation_rejects_non_confirm(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    for cap in ("file.delete", "no.such", "capabilities"):
        with pytest.raises(contract.InvalidRequest,
                           match="confirmation"):
            policy.issue_confirmation(request(cap, {}))
    assert list(tmp_path.iterdir()) == []


def test_consume_rejects_malformed_metadata_fields(tmp_path,
                                                  monkeypatch):
    monkeypatch.setattr(policy, "STATE_DIR", tmp_path)
    req = request("process.cancel", {})
    now = time.time()
    good = {"digest": policy.request_digest(req),
            "created_at": now, "expires_at": now + 60}
    cases = [
        {k: v for k, v in good.items() if k != "digest"},
        {**good, "extra": 1},
        {**good, "digest": 123},
        {**good, "created_at": True},
        {**good, "expires_at": False},
        {**good, "created_at": float("nan")},
        {**good, "expires_at": float("inf")},
        {**good, "created_at": now + 60, "expires_at": now},
        {**good, "expires_at": now + 121},
        {**good, "created_at": "x"},
        ["not", "a", "dict"],
    ]
    for meta in cases:
        token = policy.issue_confirmation(req)["confirmation_id"]
        path = tmp_path / f"{token}.json"
        path.write_text(json.dumps(meta))
        r = policy.consume_confirmation(req, token)
        assert r == {"ok": False, "reason": "unknown_confirmation"}, meta
        assert not path.exists()
