"""laya_worker — resident stdio worker for typed decisions.

Speaks versioned JSON-lines: one request envelope per line on stdin,
one recommendation per line on stdout. ALL diagnostics go to stderr —
stdout is the protocol channel and carries nothing else.

  envelope: {"version": 1, "request_id": "...", "request": {...§5.1...}}
  reply:    recommendation dict (suggestion | abstain), request_id echoed

The engine is built ONCE per process (load_engine) and reused across
requests — never respawn or rebuild per request. Offline flags are set
before the lazy laya import; weights come only from approved local
paths pinned by sha256. No downloads during predict, ever.

Entry point: `python laya_cli.py serve-stdio --config .devin/laya/profile.json`
Mode "off" (default when config is missing) exits without loading the
engine — off means off: no subprocess work, no weight reads.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_contract as dc  # noqa: E402

PROTO_VERSION = 1


def _diag(msg):
    print(f"[laya-worker] {msg}", file=sys.stderr)


def _file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _artifact_sha256(path):
    """Digest of an approved artifact: file bytes, or a deterministic
    manifest hash over a directory's (relpath, file-sha256) pairs."""
    p = Path(path)
    if p.is_file():
        return _file_sha256(p)
    h = hashlib.sha256()
    for f in sorted(p.rglob("*")):
        if f.is_file():
            h.update(str(f.relative_to(p)).encode())
            h.update(_file_sha256(f).encode())
    return h.hexdigest()


def load_engine(approved_local_models, device="cpu"):
    """Build the Router ONCE from approved local checkpoints.

    approved_local_models: {name: {"path": <local file|dir>,
    "sha256": <hex>, "identity": <str>}}. Sets offline env flags BEFORE
    importing laya so a missing snapshot can never trigger a download.
    Raises RuntimeError with a typed reason on any violation."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
    paths = {}
    for name, spec in (approved_local_models or {}).items():
        p = spec.get("path") if isinstance(spec, dict) else None
        if not p or not Path(p).exists():
            raise RuntimeError(f"model_path_missing:{name}")
        want = spec.get("sha256")
        if want and _artifact_sha256(p) != want:
            raise RuntimeError(f"model_digest_mismatch:{name}")
        paths[name] = p
    try:
        from laya import Router
    except ImportError as e:
        raise RuntimeError(f"laya_import_failed:{e}") from e
    try:
        router = Router(models=paths or None, preload=list(paths) or None,
                        device=device)
    except TypeError:
        router = Router(preload=bool(paths), device=device)
    return router


def _question_key(profile):
    return dc._PROFILES[profile][0]


def recommend(request, engine, calibration=None):
    """One typed request -> suggestion|abstain. Engine answer is
    untrusted data: label must be inside the request's closed set,
    numbers must be finite."""
    rid = request.get("request_id", "")
    rec = dc.make_abstention(rid, "invalid_request")
    rec["context"] = dict(request.get("context") or {})
    rec["mode"] = request.get("mode", "off")
    rec["profile_version"] = request.get("profile", "none")

    errs = dc.validate_request(request)
    if errs:
        rec["reason"] = "invalid_request:" + errs[0]
        return rec
    try:
        questions = dc.build_questions(
            request["profile"], request["candidates"])
    except ValueError as e:
        rec["reason"] = f"questions_invalid:{e}"
        return rec

    state = dict(request.get("state") or {})
    if request.get("language"):
        state["locale"] = request["language"]

    with contextlib.redirect_stdout(sys.stderr):
        try:
            result = engine.predict(state, questions)
        except Exception as e:
            rec["reason"] = f"engine_error:{type(e).__name__}"
            return rec

    try:
        ans = result["answers"][_question_key(request["profile"])]
    except (TypeError, KeyError):
        rec["reason"] = "engine_answer_missing"
        return rec

    choice = ans.get("choice")
    conf = ans.get("confidence")
    dist = ans.get("distribution") or {}
    routing = result.get("routing") or {}
    rec["model_identity"] = str(
        getattr(engine, "identity", None)
        or routing.get("model") or "unknown")
    rec["device"] = str(getattr(engine, "device", "unknown"))
    if routing:
        rec["routing"] = {k: routing[k] for k in
                          ("model", "reason", "language") if k in routing}

    if not dc._is_num(conf):
        rec["reason"] = "confidence_invalid"
        return rec
    top = dist.get(choice)
    rec["raw_confidence"] = float(conf)
    rec["raw_top_probability"] = float(top) if dc._is_num(top) else float(conf)

    if choice == dc.NONE_ID:
        rec["reason"] = "no_match"
        return rec
    if choice not in {c["id"] for c in request["candidates"]}:
        rec["reason"] = "unknown_label"
        return rec

    rec["outcome"] = "suggestion"
    rec["candidate_id"] = choice
    if calibration and isinstance(calibration, dict):
        rec["calibration_id"] = calibration.get("id")
    rec["reason"] = "uncalibrated"
    return rec


def serve(reader, writer, engine, config):
    """JSON-lines loop until reader EOF. Replies are written and flushed
    per line. Engine noise is redirected to stderr so the protocol
    channel stays pure JSON."""
    for line in reader:
        line = line.strip()
        if not line:
            continue
        try:
            envelope = json.loads(line)
        except json.JSONDecodeError:
            rec = dc.make_abstention("", "malformed_json")
            writer.write(json.dumps(rec, ensure_ascii=False) + "\n")
            writer.flush()
            continue
        request = envelope.get("request") if isinstance(envelope, dict) \
            else None
        if not isinstance(request, dict):
            request = envelope if isinstance(envelope, dict) else {}
        started = time.monotonic()
        if not dc.enabled(config):
            rec = dc.make_abstention(
                str(request.get("request_id", "")), "feature_off")
            rec["context"] = dict(request.get("context") or {})
            rec["mode"] = "off"
        else:
            rec = recommend(request, engine,
                            (config or {}).get("calibration"))
            deadline = request.get("deadline_ms")
            if rec["outcome"] == "suggestion" and isinstance(deadline, int) \
                    and (time.monotonic() - started) * 1000 > deadline:
                rec = dc.make_abstention(
                    str(request.get("request_id", "")),
                    "deadline_exceeded")
                rec["context"] = dict(request.get("context") or {})
                rec["mode"] = request.get("mode", "off")
                rec["profile_version"] = request.get("profile", "none")
        rid = envelope.get("request_id") if isinstance(envelope, dict) \
            else None
        if rid:
            rec["request_id"] = str(rid)
        writer.write(json.dumps(rec, ensure_ascii=False) + "\n")
        writer.flush()


def main(config_path=None):
    cfg = dc.load_config(config_path)
    if not dc.enabled(cfg):
        print(json.dumps({"ok": True, "mode": "off",
                          "note": "feature disabled; engine not loaded"}))
        return 0
    try:
        engine = load_engine(cfg.get("models") or {},
                             cfg.get("device") or "cpu")
    except RuntimeError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    _diag("engine loaded; serving stdio")
    serve(sys.stdin, sys.stdout, engine, cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
