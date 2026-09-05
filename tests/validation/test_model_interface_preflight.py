"""Model interface tool preflight tests."""
import importlib.util
import os

BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_spec = importlib.util.spec_from_file_location(
    "validate_tool_args",
    os.path.join(BUNDLE_ROOT, "scripts", "validate-tool-args.py"),
)
vt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vt)


def test_full_funnel_passes():
    call = {"tool_name": "exec", "tool_input": {"command": "python --version"}}
    result = vt.preflight_tool_call(call)
    assert result["verdict"] == "pass"
    assert result["stage"] == "observed"


def test_adapter_rejects_valid_emitted_call():
    call = {"tool_name": "exec", "tool_input": {"command": ""}}
    result = vt.preflight_tool_call(call)
    assert result["verdict"] == "fail"
    assert result["stage"] == "parsed"
    assert result["reason"].startswith("adapter")


def test_executor_failure_attributed_to_executor():
    call = {"tool_name": "exec", "tool_input": {"command": "echo hi"}}
    result = vt.preflight_tool_call(call, adapter_valid=True, executor_valid=False, observer_valid=True)
    assert result["verdict"] == "fail"
    assert result["stage"] == "executed"


def test_observer_failure_attributed_to_observer():
    call = {"tool_name": "exec", "tool_input": {"command": "echo hi"}}
    result = vt.preflight_tool_call(call, adapter_valid=True, executor_valid=True, observer_valid=False)
    assert result["verdict"] == "fail"
    assert result["stage"] == "observed"


def test_no_emission_attributed_to_model():
    result = vt.preflight_tool_call(None)
    assert result["verdict"] == "fail"
    assert result["stage"] == "emitted"


def test_classify_interface_failure_labels():
    assert vt.classify_interface_failure({"verdict": "pass"}) == "ok"
    assert vt.classify_interface_failure({"verdict": "fail", "stage": "parsed"}) == "parsed"
    assert vt.classify_interface_failure({"verdict": "fail", "stage": "emitted"}) == "model-emission"
