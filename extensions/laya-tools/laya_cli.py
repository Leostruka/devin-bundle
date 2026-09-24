#!/usr/bin/env python3
"""laya_cli — agent-friendly CLI over the `laya` decision engine.

Wraps laya's Router (auto language/script routing across the english,
multilingual and typed-decisions checkpoints) and the built-in question
presets. Emits pure JSON on stdout; never prints anything else.

  laya_cli.py predict --state '{"body": "refund me"}' --preset triage
  laya_cli.py predict --state-file s.json --questions-file q.json
  laya_cli.py predict --state-file s.json --questions-file q.json --model multilingual
  laya_cli.py --check-questions q.json       # schema validation, no deps
  laya_cli.py --list-presets                 # no deps
  laya_cli.py --self-test                    # offline asserts, no deps

Deps (torch/transformers/laya) are lazy — only `predict` imports them.
First predict downloads ~1GB of weights from Hugging Face.
"""
import argparse
import json
import os
import sys
from pathlib import Path

PRESETS = ["triage", "email", "guard", "moderation", "router"]
MODELS = ["auto", "english", "multilingual", "typed-decisions"]
QTYPES = {"choice", "score", "noul"}


def emit(obj, code=0):
    print(json.dumps(obj, indent=2, ensure_ascii=False))
    sys.exit(code)


def load_json_arg(inline, file_arg, name):
    if inline:
        try:
            return json.loads(inline)
        except json.JSONDecodeError as e:
            emit({"ok": False, "error": f"invalid --{name} JSON: {e}"}, 2)
    if file_arg:
        try:
            return json.loads(Path(file_arg).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            emit({"ok": False, "error": f"cannot read --{name}-file: {e}"}, 2)
    return None


def check_questions(q):
    """Validate the typed-questions schema without importing laya.

    Shapes: choice -> criteria {label: non-empty description};
    score -> criteria ordered non-empty list of strings;
    noul -> instructions only (P(true), no criteria).
    instructions is always a non-empty string. An unhashable or
    non-string `type` is an error, never a crash."""
    errors = []
    if not isinstance(q, dict) or not q:
        return ["questions must be a non-empty JSON object"]
    for key, spec in q.items():
        if not isinstance(spec, dict):
            errors.append(f"{key}: spec must be an object")
            continue
        t = spec.get("type")
        if not isinstance(t, str) or t not in QTYPES:
            errors.append(
                f"{key}: type must be one of {sorted(QTYPES)}, "
                f"got {t!r}")
        ins = spec.get("instructions")
        if not isinstance(ins, str) or not ins.strip():
            errors.append(f"{key}: instructions must be a non-empty "
                          "string")
        if t == "choice":
            crit = spec.get("criteria")
            if not isinstance(crit, dict) or not crit:
                errors.append(f"{key}: choice requires non-empty "
                              "criteria object {{label: description}}")
            else:
                for label, desc in crit.items():
                    if not isinstance(label, str) or not label:
                        errors.append(
                            f"{key}: choice label must be a non-empty "
                            f"string, got {label!r}")
                    if not isinstance(desc, str) or not desc.strip():
                        errors.append(
                            f"{key}: choice description for "
                            f"{label!r} must be a non-empty string")
        elif t == "score":
            crit = spec.get("criteria")
            if not isinstance(crit, list) or not crit:
                errors.append(f"{key}: score requires criteria as a "
                              "non-empty ordered list")
            elif not all(isinstance(c, str) and c.strip()
                         for c in crit):
                errors.append(f"{key}: score criteria must all be "
                              "non-empty strings")
        elif t == "noul":
            if "criteria" in spec:
                errors.append(f"{key}: noul takes instructions only "
                              "(no criteria)")
    return errors


def resolve_questions(args):
    if args.preset:
        try:
            import laya
        except ImportError:
            emit({"ok": False,
                  "error": "laya not installed — run: pip install -r "
                           "requirements.txt (in this dir)"}, 1)
        fn = getattr(laya, f"{args.preset}_questions", None)
        if fn is None:
            emit({"ok": False, "error": f"unknown preset '{args.preset}'", "presets": PRESETS}, 2)
        return fn()
    q = load_json_arg(args.questions, args.questions_file, "questions")
    if q is None:
        emit({"ok": False, "error": "provide --questions, --questions-file, or --preset"}, 2)
    errors = check_questions(q)
    if errors:
        emit({"ok": False, "error": "invalid questions schema", "details": errors}, 2)
    return q


def cmd_recommend(args):
    """One §5.1 decision request through a resident worker. mode=off
    (or missing config) abstains without spawning anything."""
    import decision_contract as dc
    import decision_client as dcl
    cfg = dc.load_config(args.config)
    if not dc.enabled(cfg):
        emit({"ok": True, "mode": "off", "outcome": "abstain",
              "reason": "feature_off"})
    goal = args.goal or ""
    candidates = load_json_arg(args.candidates, args.candidates_file,
                               "candidates") or []
    context = load_json_arg(args.context, args.context_file,
                            "context") or {}
    request = {"version": dc.VERSION,
               "request_id": f"cli-{os.getpid()}",
               "profile": args.profile, "mode": cfg["mode"],
               "context": context,
               "state": {"goal": goal},
               "candidates": candidates,
               "deadline_ms": int(cfg.get("deadline_ms") or 1000)}
    errs = dc.validate_request(request)
    if errs:
        emit({"ok": False, "error": "invalid_request",
              "details": errs}, 2)
    here = Path(__file__).resolve()
    venv_py = here.parent / ".venv" / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python")
    py = str(venv_py) if venv_py.is_file() else sys.executable
    client = dcl.DecisionClient(
        [py, str(here), "serve-stdio", "--config", args.config or ""],
        # spawn includes a cold engine build (~1min CPU); a resident
        # worker answers in ms — the deadline governs inference only
        timeout_s=max(float(request["deadline_ms"]) / 1000 + 2,
                      args.timeout))
    try:
        emit(client.recommend(request))
    finally:
        client.close()


def cmd_predict(args):
    state = load_json_arg(args.state, args.state_file, "state")
    if state is None:
        emit({"ok": False, "error": "provide --state or --state-file"}, 2)
    questions = resolve_questions(args)
    try:
        from laya import Router
    except ImportError:
        emit({"ok": False, "error": "laya not installed — run: pip install -r requirements.txt (in this dir)"}, 1)
    model = None if args.model == "auto" else args.model
    try:
        router = Router(preload=bool(args.preload), device=args.device)
        result = router.predict(state, questions, model=model)
    except Exception as e:
        emit({"ok": False, "error": f"predict failed: {type(e).__name__}: {e}"}, 1)
    emit({"ok": True, **result})


def self_test():
    good = {"dept": {"type": "choice", "instructions": "x",
                     "criteria": {"a": "desc a", "b": "desc b"}}}
    assert not check_questions(good)
    assert check_questions({})
    assert check_questions({"x": {"type": "bogus", "instructions": "x"}})
    assert check_questions({"x": {"type": "choice", "instructions": "x"}})  # missing criteria dict
    assert check_questions({"x": {"type": "score", "instructions": "x",
                                "criteria": {"a": "b"}}})  # score needs list
    emit({"ok": True, "self_test": "passed", "presets": PRESETS, "models": MODELS})


def main():
    p = argparse.ArgumentParser(description="Agent CLI over the laya decision engine.")
    sub = p.add_subparsers(dest="cmd")
    pr = sub.add_parser("predict", help="Answer typed questions over a state")
    pr.add_argument("--state", help="Inline JSON state object")
    pr.add_argument("--state-file", help="Path to JSON state")
    pr.add_argument("--questions", help="Inline JSON questions spec")
    pr.add_argument("--questions-file", help="Path to JSON questions spec")
    pr.add_argument("--preset", choices=PRESETS)
    pr.add_argument("--model", choices=MODELS, default="auto")
    pr.add_argument("--device", help="cpu|cuda (default: laya auto)")
    pr.add_argument("--preload", action="store_true",
                    help="Preload all checkpoints (skip per-request reload; uses ~2GB)")
    sv = sub.add_parser("serve-stdio",
                        help="Resident JSON-lines worker (see laya_worker)")
    sv.add_argument("--config",
                    help="Path to .devin/laya/profile.json "
                         "(default: project .devin/laya/profile.json)")
    rc = sub.add_parser("recommend",
                        help="One typed decision via resident worker "
                             "(abstains cleanly when mode=off)")
    rc.add_argument("--profile", required=True,
                    help="Closed profile id, e.g. skill-family-v1")
    rc.add_argument("--goal", required=True)
    rc.add_argument("--candidates", help="Inline JSON list of candidates")
    rc.add_argument("--candidates-file")
    rc.add_argument("--context", help="Inline JSON context object")
    rc.add_argument("--context-file")
    rc.add_argument("--config", help="Path to laya profile.json")
    rc.add_argument("--timeout", type=float, default=120.0,
                    help="Seconds to wait for worker spawn + reply "
                         "(default 120; cold engine load dominates)")
    p.add_argument("--check-questions", metavar="FILE", help="Validate questions schema offline")
    p.add_argument("--list-presets", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()

    if args.self_test:
        self_test()
    if args.list_presets:
        emit({"ok": True, "presets": PRESETS})
    if args.check_questions:
        q = load_json_arg(None, args.check_questions, "check-questions")
        errors = check_questions(q)
        emit({"ok": not errors, "errors": errors}, 0 if not errors else 2)
    if args.cmd == "predict":
        cmd_predict(args)
    if args.cmd == "serve-stdio":
        cfg = args.config
        if cfg is None:
            default = Path.cwd() / ".devin" / "laya" / "profile.json"
            cfg = str(default) if default.is_file() else None
        import laya_worker
        sys.exit(laya_worker.main(cfg))
    if args.cmd == "recommend":
        cmd_recommend(args)
    p.error("no command — see --help")


if __name__ == "__main__":
    main()
