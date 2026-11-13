"""Envelope contract v2 coverage guard (#593, hardened #601).

Every agent-facing wrapper listed in .devin/docs/CLI-CONTRACT.md must
emit api_version=2 plus meta.answered_by provenance on its JSON
responses. Each wrapper is probed in a real subprocess on a safe,
side-effect-free invocation; the parsed stdout must carry the markers.
Static text checks cannot see runtime breakage (e.g. a manifest that
parses but is not a dict), so this is the authoritative guard.

When adding a new wrapper, extend PROBES and the contract doc.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_VERSION = json.loads(
    (ROOT / "manifest.json").read_text(encoding="utf-8"))["version"]

# (wrapper path, argv that yields a JSON envelope without side effects,
#  expected answered_by.wrapper)
PROBES = [
    ("extensions/agent-reach/wrapper.py", [], "agent-reach"),
    ("extensions/voicebox/wrapper.py", [], "voicebox"),
    ("extensions/hyperframes/wrapper.py", [], "hyperframes"),
    ("extensions/gcal/wrapper.py", [], "gcal"),
    ("extensions/offsec-tools/wrapper.py", ["capabilities"], "offsec-tools"),
    ("extensions/rea-ops/wrapper.py", ["capabilities"], "rea-ops"),
    ("extensions/rz-ops/wrapper.py", ["capabilities"], "rz-ops"),
    ("extensions/stock-footage/fetch.py",
     ["search", "--query", "contract-probe"], "stock-footage"),
    ("extensions/blender-operator/wrapper.py", ["status"],
     "blender-operator"),
    ("extensions/comfyui-operator/wrapper.py", ["status"],
     "comfyui-operator"),
    ("extensions/laya-tools/laya_cli.py", ["--self-test"], "laya-tools"),
    # wave-5 utility CLIs (#604): SSRF-denied URL, missing-dep, missing
    # file, and binary-missing paths all emit JSON offline.
    ("extensions/scrape-tools/scrape.py",
     ["http://127.0.0.1/", "--css", "x"], "scrape-tools"),
    ("extensions/scrape-tools/parse.py",
     ["manifest.json", "--css", "x"], "scrape-tools"),
    ("extensions/scrape-tools/dom_elements.py",
     ["nonexistent.json"], "scrape-tools"),
    ("extensions/asr/bootstrap.py", ["--model", "bad!"], "asr"),
    ("extensions/asr/transcribe.py", ["manifest.json"], "asr"),
    # --envelope is opt-in: result envelope when index exists, stamped
    # missing-index JSON otherwise - deterministic contract either way.
    ("extensions/code-graph/query.py",
     [".", "files", "zzz-probe", "--envelope"], "code-graph"),
    # wave-6 computer-use (#604): the 8 skill-invoked entry CLIs plus
    # cu_motion's shared JsonParser error path all emit stamped JSON on
    # dependency-free paths (binding lookup, usage error, doctor report).
    ("extensions/computer-use/terminal.py", ["info"], "computer-use"),
    ("extensions/computer-use/screenshot.py", [], "computer-use"),
    ("extensions/computer-use/mouse.py", [], "computer-use"),
    ("extensions/computer-use/type_text.py", [], "computer-use"),
    ("extensions/computer-use/record.py", [], "computer-use"),
    ("extensions/computer-use/profile.py", ["bogus"], "computer-use"),
    ("extensions/computer-use/env.py", ["doctor"], "computer-use"),
    ("extensions/computer-use/browser.py", ["status"], "computer-use"),
    # __main__-only utility CLIs (wave-7 sweep of the same extension):
    # daemon-absent error path is deterministic on any host.
    ("extensions/computer-use/cu_events.py", ["drain"], "computer-use"),
    # wave-8 skill-referenced extension CLIs (#604): every argv below is
    # an offline deterministic path - usage error, missing input, or a
    # self-test/validate mode. jxl_bootstrap is excluded from probes
    # (its only JSON path performs a toolchain install); the static
    # marker check still covers it.
    ("extensions/ai-tools/abliterator.py", [], "ai-tools"),
    ("extensions/ai-tools/adapter_expand.py", ["--self-test"], "ai-tools"),
    ("extensions/ai-tools/bitnet_adapter.py", ["--self-test"], "ai-tools"),
    ("extensions/ai-tools/dory_sweep.py",
     ["--cases", "nope", "--loops", "1"], "ai-tools"),
    ("extensions/ai-tools/heldout_batch.py",
     ["--manifest", "nope"], "ai-tools"),
    ("extensions/ai-tools/offload_plan.py",
     ["--backend", "bitnet.cpp"], "ai-tools"),
    ("extensions/ai-tools/prompt_compiler.py", [], "ai-tools"),
    ("extensions/ai-tools/vllm_tpu_runner.py",
     ["--check-only"], "ai-tools"),
    ("extensions/ai-tools/weight_patch.py", [], "ai-tools"),
    ("extensions/media-tools/ascii_mancer.py", [], "media-tools"),
    ("extensions/media-tools/grainrad.py", [], "media-tools"),
    ("extensions/media-tools/jxl.py",
     ["identify", "nope"], "media-tools"),
    ("extensions/media-tools/playblast_ingest.py",
     ["nope.mp4"], "media-tools"),
    ("extensions/media-tools/update_tooooools_db.py",
     ["--dry-run"], "media-tools"),
    ("extensions/remotion-render/composite.py",
     ["-o", "probe-x.out", "a.png", "b.png"], "remotion-render"),
    ("extensions/remotion-render/plan_check.py", [], "remotion-render"),
    ("extensions/remotion-render/render.py",
     ["--workdir", "nope", "plan.json"], "remotion-render"),
    ("extensions/design-intelligence/design_lint.py",
     ["nonexistent", "--json"], "design-intelligence"),
    ("extensions/design-intelligence/look_ledger.py",
     ["compare", "nope", "nope2"], "design-intelligence"),
    ("extensions/design-intelligence/validate_csv.py",
     ["--json"], "design-intelligence"),
    ("extensions/image-forensics/eval_set.py",
     ["--real", "nope", "--synth", "nope"], "image-forensics"),
    ("extensions/image-forensics/metadata.py", [], "image-forensics"),
    ("extensions/image-forensics/verdict.py",
     ["nope"], "image-forensics"),
    # wave-9 remaining extension emitters + graph-query (#604): doctor
    # reports, missing-input errors, resume/diff on absent state - all
    # offline deterministic.
    ("extensions/laya-compactor/compact.py",
     ["-o", "probe-x.out", "nope"], "laya-compactor"),
    ("extensions/ppisp-prep/photo_qc.py", ["nope"], "ppisp-prep"),
    ("extensions/ppisp-prep/ppisp_runner.py", ["doctor"], "ppisp-prep"),
    ("extensions/mesh-utils/meshops.py", ["doctor"], "mesh-utils"),
    ("extensions/api-bridge/bridge.py", ["doctor"], "api-bridge"),
    ("extensions/diagram-tools/plantuml_renderer.py",
     ["--self-test"], "diagram-tools"),
    ("extensions/craft-bridge/bridge.py", ["doctor"], "craft-bridge"),
    ("extensions/craft-bridge/scene_manifest.py",
     ["nope"], "craft-bridge"),
    ("extensions/harness-tree/ns.py",
     ["resume", "nonexistent"], "harness-tree"),
    ("extensions/harness-tree/tree.py",
     ["diff", "nope", "nope2"], "harness-tree"),
    ("scripts/graph-query.py", ["probe-test"], "graph-query"),
    # wave-10 (#604): laya-tools sub-tools, missed ext files, and
    # skill-referenced non-hook scripts. All offline deterministic.
    ("extensions/laya-tools/fit_calibration.py",
     ["--manifest", "nope"], "laya-tools"),
    ("extensions/laya-tools/layad.py", [], "laya-tools"),
    ("extensions/laya-tools/capture_eval.py",
     ["--draft", "nope", "--config", "x", "--out", "x"], "laya-tools"),
    ("extensions/laya-tools/doc_coverage.py",
     ["--changed", "x", "--map", "nope"], "laya-tools"),
    ("extensions/laya-tools/eval_decisions.py",
     ["--manifest", "nope", "--mode", "evaluate", "--out", "x"],
     "laya-tools"),
    ("extensions/laya-tools/explore.py",
     ["--keywords", "x", "--question", "q"], "laya-tools"),
    ("extensions/laya-tools/filebool.py",
     ["--glob", "nope", "--question", "q"], "laya-tools"),
    ("extensions/laya-tools/laya_worker.py", [], "laya-tools"),
    ("extensions/laya-tools/review_gate.py", [], "laya-tools"),
    ("extensions/laya-tools/bootstrap.py", ["--dry-run"], "laya-tools"),
    ("extensions/blender-operator/camera_blocking.py",
     ["--out", "probe-x.out"], "blender-operator"),
    ("extensions/code-graph/detect_changes.py", [], "code-graph"),
    ("scripts/check-tools.py", ["--json"], "check-tools"),
    ("scripts/context-budget.py", ["--json"], "context-budget"),
    ("scripts/decision-queue.py", ["--pending"], "decision-queue"),
    ("scripts/done-evaluator.py", [], "done-evaluator"),
    ("scripts/focus.py", ["report", "--json"], "focus"),
    ("scripts/install-ledger.py", ["reconcile"], "install-ledger"),
    ("scripts/dep-audit.py", [], "dep-audit"),
    ("scripts/spec-consistency.py", ["nonexistent"], "spec-consistency"),
    ("scripts/subagent-trace.py", [], "subagent-trace"),
    # wave-11 (#604): last dict-JSON emitters in scripts/. Remaining
    # unstamped prints are hook-protocol output or bare arrays.
    ("scripts/roadmap-board.py", ["--json"], "roadmap-board"),
    ("scripts/ship-metrics.py", ["report"], "ship-metrics"),
    ("scripts/rules-coverage.py", ["nonexistent"], "rules-coverage"),
]

# Keys that could turn a probe into a real network call.
PROBE_ENV = {k: v for k, v in os.environ.items()
             if k not in ("PEXELS_API_KEY", "PIXABAY_API_KEY")}


def test_all_listed_wrappers_exist():
    missing = [w for w, _, _ in PROBES if not (ROOT / w).is_file()]
    assert not missing, f"wrapper paths missing: {missing}"


def test_wrappers_emit_api_version_and_provenance():
    """Static marker check - cheap smoke; the subprocess probes below
    are the authoritative runtime guard. Files that stamp via a shared
    helper (st_common.emit/_emit) don't carry the literals themselves."""
    markers = ('"api_version"', "'api_version'", "_bundle_version",
               "_stamp(", "st_common.emit(", "_emit(")
    for rel, _, _ in PROBES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert any(m in text for m in markers), \
            f"{rel}: no contract v2 stamp site found"


@pytest.mark.parametrize("rel,argv,wrapper", PROBES,
                         ids=[w for _, _, w in PROBES])
def test_wrapper_emits_contract_v2(rel, argv, wrapper):
    proc = subprocess.run(
        [sys.executable, str(ROOT / rel)] + argv,
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=90, env=PROBE_ENV, cwd=str(ROOT))
    payload = json.loads(proc.stdout)
    assert payload.get("api_version") == 2, \
        f"{wrapper}: api_version={payload.get('api_version')!r}"
    answered = payload.get("meta", {}).get("answered_by", {})
    assert answered.get("wrapper") == wrapper, \
        f"{wrapper}: answered_by.wrapper={answered.get('wrapper')!r}"
    assert answered.get("bundle") == MANIFEST_VERSION, \
        f"{wrapper}: answered_by.bundle={answered.get('bundle')!r} " \
        f"(manifest {MANIFEST_VERSION})"


# Files whose JSON stdout must route through the stamp. Derived from
# PROBES plus emit-only siblings that share the same _dumps funnel.
def _stamped_files():
    import glob
    out = set(rel for rel, _, _ in PROBES)
    out.add("skills/context-hygiene/scripts/fold_store.py")
    for rel in list(out):
        d = os.path.dirname(rel)
        if d.startswith("extensions/"):
            out.update(glob.glob(os.path.join(d, "*.py"),
                                 root_dir=str(ROOT)))
    return sorted(out)


@pytest.mark.parametrize("rel", _stamped_files(),
                         ids=[os.path.basename(r) for r in _stamped_files()])
def test_no_unstamped_stdout_pattern(rel):
    """Guard the two bypass classes found in review: direct
    `print(json.dumps(...))` and assign-then-print `x=json.dumps();
    print(x)`. Both must route through `_dumps`/`_stamp`."""
    import ast
    src = (ROOT / rel).read_text(encoding="utf-8")
    if "_BUNDLE_VERSION_CACHE" not in src:
        pytest.skip(f"{rel}: not a stamped emitter")
    tree = ast.parse(src)
    assigns = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, ast.Call) \
                and isinstance(node.value.func, ast.Attribute) \
                and node.value.func.attr == "dumps":
            assigns[node.targets[0].id] = node.lineno
        if isinstance(node, ast.Call) and isinstance(
                node.func, ast.Name) and node.func.id == "print":
            for a in node.args:
                if isinstance(a, ast.Call) and isinstance(
                        a.func, ast.Attribute) and a.func.attr == "dumps":
                    pytest.fail(
                        f"{rel}:{a.lineno} print(json.dumps(...)) bypasses "
                        "_dumps funnel")
                if isinstance(a, ast.Name) and a.id in assigns:
                    pytest.fail(
                        f"{rel}:{a.lineno} print({a.id}) of json.dumps "
                        f"assigned at :{assigns[a.id]} bypasses _dumps")


def test_fold_store_save_emits_contract_v2(tmp_path):
    """fold_store save needs stdin + FOLD_STORE_DIR (writes a record
    file) so it can't ride the shared PROBES runner."""
    env = dict(PROBE_ENV, FOLD_STORE_DIR=str(tmp_path))
    proc = subprocess.run(
        [sys.executable,
         str(ROOT / "skills/context-hygiene/scripts/fold_store.py"),
         "save", "probe", "--summary", "p"],
        input="x", capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=30, env=env, cwd=str(ROOT))
    payload = json.loads(proc.stdout)
    assert payload.get("api_version") == 2
    answered = payload.get("meta", {}).get("answered_by", {})
    assert answered.get("wrapper") == "fold_store"
    assert answered.get("bundle") == MANIFEST_VERSION
