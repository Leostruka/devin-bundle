"""Reproducoes locais da auditoria; fixtures sinteticas, sem rede ou inferencia real."""
import argparse
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
AI = ROOT / "extensions" / "ai-tools"
BASH = shutil.which("bash") or "bash"
sys.path.insert(0, str(AI))


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fixture(directory):
    root = Path(directory)
    entries = []
    for i, data in enumerate((b"synthetic A", b"synthetic B")):
        path = root / f"input{i}.txt"
        path.write_bytes(data)
        entries.append({"id": f"case-{i}", "path": path.name,
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "split": "heldout", "source": "synthetic"})
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    return manifest


def reads():
    results = []
    for name, path, args in (
        ("audit_dom", "extensions/computer-use/cu_dom_picker.py",
         ["--snapshot", "-", "--goal", "synthetic"]),
        ("audit_scrape_dom", "extensions/scrape-tools/dom_elements.py", ["-"]),
    ):
        module = load(name, path)
        seen = []

        class Input:
            def read(self, size=-1):
                seen.append(size)
                raise RuntimeError("audit sentinel: read intercepted")

        with patch.object(sys, "stdin", Input()), contextlib.redirect_stdout(io.StringIO()):
            try:
                module.main(args)
            except RuntimeError:
                pass
        results.append({"module": path, "read_sizes": seen,
                        "unbounded": -1 in seen})
    return {"defect_confirmed": all(x["unbounded"] for x in results),
            "observed": results}


def tpu():
    module = load("audit_tpu", "extensions/ai-tools/vllm_tpu_runner.py")
    hb = load("heldout_batch", "extensions/ai-tools/heldout_batch.py")

    class LLM:
        def __init__(self, **kwargs):
            pass

        def generate(self, prompts, params):
            return []

    fake = types.SimpleNamespace(LLM=LLM, SamplingParams=lambda **kw: kw)
    with tempfile.TemporaryDirectory(prefix="bundle-audit-") as directory:
        entries = hb.load_manifest(fixture(directory))
        with patch.object(module, "check_tpu", return_value={"ok": True}), \
                patch.dict(sys.modules, {"vllm": fake}):
            result = module.run_tpu_batch(entries, "synthetic-model")
    confirmed = result["ok"] and result["manifest_entries"] == 2 \
        and len(result["results"]) == 0
    return {"defect_confirmed": confirmed, "simulated_backend": True,
            "observed": result, "real_tpu_tested": False}


def clobber():
    hb = load("heldout_batch", "extensions/ai-tools/heldout_batch.py")
    ba = load("bitnet_adapter", "extensions/ai-tools/bitnet_adapter.py")
    with tempfile.TemporaryDirectory(prefix="bundle-audit-") as directory:
        manifest = fixture(directory)
        before = manifest.read_bytes()
        binary = Path(directory) / "synthetic.exe"
        model = Path(directory) / "synthetic.gguf"
        binary.write_bytes(b"synthetic")
        model.write_bytes(b"synthetic")
        argv = ["heldout_batch.py", "--manifest", str(manifest),
                "--binary", str(binary), "--model", str(model),
                "--out", str(manifest)]
        with patch.object(sys, "argv", argv), \
                patch.object(ba, "run", return_value={"ok": True, "output": "synthetic"}), \
                contextlib.redirect_stdout(io.StringIO()):
            try:
                hb.main()
            except SystemExit as exc:
                code = exc.code
        after = manifest.read_bytes()
        keys = sorted(json.loads(after))
    return {"defect_confirmed": before != after and "entries" not in keys,
            "simulated_backend": True, "temporary_manifest_only": True,
            "observed": {"exit_code": code, "manifest_overwritten": before != after,
                         "keys_after": keys}}


def response():
    module = runpy.run_path(str(ROOT / "scripts/compact-gate.py"))
    states = {}
    for field in ("tool_response", "tool_output"):
        state = {"digest": {}}
        payload = {"hook_event_name": "PostToolUse", "tool_name": "exec",
                   "tool_input": {}, field: "Traceback: synthetic error"}
        module["_update_digest"](state, payload, module["DEFAULTS"])
        states[field] = len(state["digest"].get("errors", []))
    return {"defect_confirmed": states == {"tool_response": 0, "tool_output": 1},
            "observed_error_counts": states}


def boundary():
    source = (ROOT / "scripts/compact-gate.py").read_text(encoding="utf-8")
    imports = [{"module": alias.name, "line": node.lineno}
               for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Import)
               for alias in node.names if alias.name in ("decision_contract", "laya_client")]
    return {"defect_confirmed": len(imports) == 2,
            "evidence_type": "static_source", "observed": imports,
            "contract": ".devin/ARCHITECTURE_MANIFEST.md:59-61"}


def protocol():
    fake = types.SimpleNamespace(
        app=types.SimpleNamespace(version_string="audit-stub"),
        context=types.SimpleNamespace(scene=None))
    with patch.dict(sys.modules, {"bpy": fake}):
        module = load("audit_blender_server", "extensions/blender-operator/blender_server.py")
    try:
        module._handle(json.loads("[]"))
        error = None
    except Exception as exc:
        error = type(exc).__name__
    return {"defect_confirmed": error == "AttributeError", "simulated_bpy": True,
            "network_used": False, "observed": {"exception": error,
            "valid_ping_ok": module._handle({"op": "ping"})["ok"]}}


def hashes():
    results = []
    with tempfile.TemporaryDirectory(prefix="bundle-audit-") as directory:
        normal, spaced = Path(directory) / "normal", Path(directory) / "spaced"
        normal.mkdir()
        spaced.mkdir()
        (normal / "asset.txt").write_text("synthetic", encoding="utf-8")
        (spaced / "asset name.txt").write_text("synthetic", encoding="utf-8")
        for file, function in (("install.sh", "dir_hash"),
                               ("install.sh", "dir_hash_ext"),
                               ("export.sh", "dir_hash")):
            source = (ROOT / file).read_text(encoding="utf-8")
            match = re.search(r"(?ms)^" + function + r"\(\) \{\n.*?^\}", source)
            script = "set -euo pipefail\n" + match.group(0) + \
                '\nhash="$(' + function + ' "$1")"\nprintf "%s\\n" "$hash"\n'
            codes, errors = [], []
            for path in (normal, spaced):
                result = subprocess.run([BASH, "-s", "--", path.as_posix()],
                                        input=script.encode("utf-8"), capture_output=True,
                                        timeout=15, shell=False)
                codes.append(result.returncode)
                errors.append(result.stderr.decode("utf-8", errors="replace")[:300])
            results.append({"file": file, "function": function,
                            "normal_exit": codes[0], "space_exit": codes[1],
                            "normal_stderr": errors[0], "space_stderr": errors[1]})
    return {"defect_confirmed": all(r["normal_exit"] == 0 and r["space_exit"] != 0
                                   for r in results), "observed": results}


def ci_mask():
    source = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    masked = [line.strip() for line in source.splitlines()
              if "git diff --check" in line and "|| true" in line]
    if not masked:
        return {"defect_confirmed": False,
                "evidence_type": "static_source",
                "observed": "no 'git diff --check ... || true' in ci.yml"}
    result = subprocess.run([BASH, "-s"], input=b"false || true\n",
                            capture_output=True, timeout=10, shell=False)
    return {"defect_confirmed": result.returncode == 0,
            "evidence_type": "static_source_and_shell_control",
            "observed_source": masked[0],
            "simulated_failure_masked_exit": result.returncode}


CASES = {"reads": reads, "tpu": tpu, "clobber": clobber,
         "response": response, "boundary": boundary, "protocol": protocol,
         "hashes": hashes, "ci-mask": ci_mask}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=["all", *CASES])
    args = parser.parse_args()
    chosen = CASES if args.case == "all" else {args.case: CASES[args.case]}
    results = {name: run() for name, run in chosen.items()}
    print(json.dumps(results, indent=2, ensure_ascii=True))
    return 0 if all(r["defect_confirmed"] for r in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
