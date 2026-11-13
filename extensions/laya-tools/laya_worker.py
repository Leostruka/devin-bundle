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
import math
import os
import sys
import time
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_contract as dc  # noqa: E402

_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    """Nearest ancestor manifest.json with a "name" marker, else ""."""
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    import json as _json
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = _json.loads(
                    manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "laya-tools"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    return json.dumps(_stamp(payload), **kw)


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
        router = Router(models=paths or None, device=device)
        if paths:
            # preload() bare would build EVERY registered model,
            # including checkpoints we never approved
            router.preload(list(paths))
    except TypeError:
        router = Router(preload=bool(paths), device=device)
    return router


def _question_key(profile):
    return dc._PROFILES[profile][0]


def _calibrated(cal, x):
    """Apply the calibration map: identity | platt(a,b) | table of
    sorted [x, y] points with linear interpolation."""
    m = (cal or {}).get("map") or {}
    kind = m.get("kind", "identity")
    if kind == "identity":
        return float(x)
    if kind == "platt":
        a, b = m.get("a"), m.get("b")
        if not (dc._is_num(a) and dc._is_num(b)):
            return None
        z = a * x + b
        return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z))))
    if kind == "table":
        pts = m.get("points")
        if not isinstance(pts, list) or not pts:
            return None
        pts = sorted((p[0], p[1]) for p in pts
                     if isinstance(p, (list, tuple)) and len(p) == 2)
        if not pts:
            return None
        if x <= pts[0][0]:
            return float(pts[0][1])
        if x >= pts[-1][0]:
            return float(pts[-1][1])
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x0 <= x <= x1:
                t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
                return float(y0 + t * (y1 - y0))
    return None


def recommend(request, engine, calibration=None, assist_ok=False,
              model=None):
    """One typed request -> suggestion|abstain. Engine answer is
    untrusted data: label must be inside the request's closed set,
    numbers must be finite. `model` pins an approved checkpoint name
    (e.g. "multilingual"); None lets the Router auto-route."""
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
            kw = {"model": model} if model else {}
            result = engine.predict(state, questions, **kw)
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
    dist = ans.get("distribution") or ans.get("probabilities") or {}
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
    others = [v for k, v in dist.items() if k != choice and dc._is_num(v)]
    if others:
        rec["raw_runner_up_probability"] = float(max(others))

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
        cal_p = _calibrated(calibration, rec["raw_confidence"])
        if cal_p is not None:
            rec["calibrated_probability"] = cal_p
            thr = calibration.get("threshold")
            if assist_ok and request.get("mode") == "assist" \
                    and dc._is_num(thr) and cal_p >= thr:
                rec["adoptable"] = True
                rec["reason"] = "calibrated"
                return rec
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
                            (config or {}).get("calibration"),
                            assist_ok=dc.effective_mode(config)
                            == "assist",
                            model=(config or {}).get("model"))
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


def warm_engine(engine, config):
    """Run one throwaway prediction so first-request cold latency
    (~>1s on CPU) does not eat a consumer's deadline_ms budget.
    Best-effort: never raises, never blocks serving on failure."""
    started = time.monotonic()
    try:
        recommend({
            "version": dc.VERSION,
            "request_id": "warmup",
            "profile": "issue-category-v1",
            "mode": "off",
            "state": {"goal": "warmup"},
            "candidates": [{"id": "warmup"}],
            "deadline_ms": 60000,
        }, engine, ((config or {}).get("calibration") or None),
            assist_ok=False, model=((config or {}).get("model") or None))
    except Exception:
        pass  # fail-soft: probe fallback
    return (time.monotonic() - started) * 1000


def main(config_path=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    dc.pin_stdio_utf8()
    cfg = dc.load_config(config_path)
    if not dc.enabled(cfg):
        print(_dumps({"ok": True, "mode": "off",
                          "note": "feature disabled; engine not loaded"}))
        return 0
    model = cfg.get("model")
    if model and model not in (cfg.get("models") or {}):
        print(_dumps({"ok": False,
                          "error": f"model_not_approved:{model}"}))
        return 1
    try:
        engine = load_engine(cfg.get("models") or {},
                             cfg.get("device") or "cpu")
    except RuntimeError as e:
        print(_dumps({"ok": False, "error": str(e)}))
        return 1
    # Warm the engine once so the first real request does not eat
    # cold-start latency inside its deadline_ms budget.
    warm_ms = warm_engine(engine, cfg)
    _diag("engine loaded; warmup %.0fms; serving stdio" % warm_ms)
    serve(sys.stdin, sys.stdout, engine, cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
