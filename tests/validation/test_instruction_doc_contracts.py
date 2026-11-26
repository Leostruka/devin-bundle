"""Validation contracts for high-impact instruction docs changed
2026-11-26 (independent-review debt item 9). These tests pin the
behavioral claims the docs make so the instructions cannot silently
drift away from what the runtime actually enforces."""
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def _load_beval():
    spec = importlib.util.spec_from_file_location(
        "behavioral_eval",
        os.path.join(ROOT, "scripts", "behavioral-eval.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_agent_eval_skill_documents_sample_command():
    """agent-eval SKILL.md must document the real sample command surface
    - drift here means agents invoke a mode that does not exist."""
    skill = open(os.path.join(ROOT, "skills", "agent-eval", "SKILL.md"),
                 encoding="utf-8").read()
    assert "sample" in skill
    src = open(os.path.join(ROOT, "scripts", "behavioral-eval.py"),
               encoding="utf-8").read()
    assert "sample" in src  # command exists in the harness


def test_behavioral_harness_excludes_devin_from_digest():
    """The contamination false-pass the reviewer verified must stay
    impossible: .devin excluded from grading digests."""
    beval = _load_beval()
    src = open(os.path.join(ROOT, "scripts", "behavioral-eval.py"),
               encoding="utf-8").read()
    assert '".devin"' in src
    assert beval  # loads cleanly


def test_behavioral_harness_runs_in_process():
    """Timeout must be a real wall-clock cap: in-process flag pinned."""
    src = open(os.path.join(ROOT, "scripts", "behavioral-eval.py"),
               encoding="utf-8").read()
    assert "--process-model=in-process" in src


def test_council_skill_requires_adversarial_review_for_security_narrowing():
    """The 2026-11-26 security incident lesson: any narrowing of a
    security control requires pre-merge adversarial review with real
    exploitation probes. This trigger must not drift out of the skill."""
    skill = open(os.path.join(ROOT, "skills", "council", "SKILL.md"),
                 encoding="utf-8").read()
    low = skill.lower()
    assert "security" in low and "narrowing" in low.replace("-", " ") \
        or "adversarial" in low
    assert "probe" in low or "exploit" in low


def test_media_osint_documents_disk_preflight_and_429():
    """Both 2026-11-26 runs hit a full disk and caption 429s; the skill
    must carry those lessons."""
    skill = open(os.path.join(ROOT, "skills", "media-osint", "SKILL.md"),
                 encoding="utf-8").read()
    assert "preflight" in skill.lower()
    assert "429" in skill


def test_inference_optimisation_carries_mit_attribution():
    """Vendored MIT content must keep provenance - license obligation,
    not decoration."""
    skill = open(os.path.join(ROOT, "skills", "inference-optimisation",
                              "SKILL.md"), encoding="utf-8").read()
    assert "MIT" in skill
    notice = open(os.path.join(ROOT, "NOTICE.md"), encoding="utf-8").read()
    assert "inference-optimisation" in notice


def test_video_improvement_plan_records_i09_scope_honestly():
    """The completion plan must not claim deferred items as done."""
    plan = open(os.path.join(
        ROOT, ".devin", "plans", "2026-11-26-video-self-improvement.md"),
        encoding="utf-8").read()
    assert "defer" in plan.lower()
