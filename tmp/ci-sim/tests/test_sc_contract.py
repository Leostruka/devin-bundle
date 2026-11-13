"""sc_contract — request validation and result envelope for schema v1."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_contract as contract  # noqa: E402


def _req(**over):
    r = {
        "version": 1,
        "request_id": "r1",
        "capability": "process.observe",
        "args": {},
        "deadline_ms": 1000,
    }
    r.update(over)
    return r


def test_response_distinguishes_dispatch_from_verification():
    r = contract.result(ok=True, status="dispatched",
                        request_id="r1", backend="fake")
    assert r["ok"] is True
    assert r["status"] == "dispatched"
    assert "postcondition" in r


def test_process_target_requires_start_time():
    with pytest.raises(ValueError, match="start_time"):
        contract.validate_request({
            "version": 1, "request_id": "r1",
            "capability": "process.observe", "target": {"pid": 12},
            "args": {}, "deadline_ms": 1000,
        })


def test_process_target_requires_pid():
    with pytest.raises(ValueError, match="pid"):
        contract.validate_request(_req(target={"start_time": 99}))


def test_validate_request_returns_normalized_dict():
    r = contract.validate_request(
        _req(target={"pid": 7, "start_time": 99}))
    assert r["version"] == 1
    assert r["target"] == {"pid": 7, "start_time": 99}


def test_rejects_non_dict_request():
    with pytest.raises(ValueError):
        contract.validate_request(["not", "a", "dict"])


def test_rejects_missing_required_key():
    for key in ("version", "request_id", "capability", "args",
                "deadline_ms"):
        r = _req()
        del r[key]
        with pytest.raises(ValueError, match=key):
            contract.validate_request(r)


def test_rejects_unknown_schema_version():
    with pytest.raises(ValueError, match="version"):
        contract.validate_request(_req(version=2))


def test_rejects_non_dict_args():
    with pytest.raises(ValueError, match="args"):
        contract.validate_request(_req(args="rm -rf"))


def test_deadline_ms_bounds():
    for bad in (0, -1, 300001, "1000", 1.5, True):
        with pytest.raises(ValueError, match="deadline_ms"):
            contract.validate_request(_req(deadline_ms=bad))
    contract.validate_request(_req(deadline_ms=1))
    contract.validate_request(_req(deadline_ms=300000))


def test_result_materializes_evidence_defaults():
    r = contract.result(ok=True, status="verified",
                        request_id="r1", backend="fake")
    assert r["evidence"] == {"cursor": None, "spill": None, "dropped": 0}
    assert r["privilege"] == "user"
    assert r["error"] is None


def test_result_carries_evidence_fields():
    r = contract.result(ok=True, status="verified", request_id="r1",
                        backend="fake", cursor="c1", spill="/tmp/x",
                        dropped=3)
    assert r["evidence"] == {"cursor": "c1", "spill": "/tmp/x",
                            "dropped": 3}


def test_untrusted_marks_external_value():
    u = contract.untrusted({"stdout": "log line"})
    assert u["untrusted"] is True
    assert u["value"] == {"stdout": "log line"}


def test_target_helper_requires_ints():
    assert contract.target(7, 99) == {"pid": 7, "start_time": 99}
    for bad_pid, bad_start in ((-1, 0), ("7", 99), (7, "99"), (7, -5),
                               (True, 1)):
        with pytest.raises(ValueError):
            contract.target(bad_pid, bad_start)


def test_target_rejects_extra_keys():
    with pytest.raises(ValueError, match="target"):
        contract.validate_request(
            _req(target={"pid": 7, "start_time": 99, "extra": 1}))


def test_invalid_request_is_typed_valueerror():
    assert issubclass(contract.InvalidRequest, ValueError)
    with pytest.raises(contract.InvalidRequest):
        contract.validate_request(_req(deadline_ms=0))
