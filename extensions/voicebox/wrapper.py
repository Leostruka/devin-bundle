#!/usr/bin/env python3
"""voicebox: local wrapper for the jamiepine/voicebox TTS backend.

Talks to a user-started voicebox FastAPI backend over HTTP
(`python -m backend.main` inside a voicebox checkout), serving on
127.0.0.1:17493. Stdlib only (urllib); no pip dependency.

Alternate backend: `--backend voicestudio` (or VB_BACKEND=voicestudio)
targets the VoiceStudio app's OpenAI-compatible API on
127.0.0.1:3900 (/v1/models, /v1/audio/speech).

Safety contract:
  - Localhost-only: VB_HOST override must resolve to a loopback host.
  - Whitelisted actions only: doctor / generate / models.
  - Bounded request bodies and responses; hard timeout per call.
  - Backend down -> {"status": "missing"}; never fabricate.

Output: JSON envelope on stdout:
  {"api_version": 2, "status": ..., "action": ..., "result"|"error": ...,
   "duration_s": ..., "meta": {"answered_by": ...}}
Exit 0 = ok, non-zero = error/missing.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_HOST = "http://127.0.0.1:17493"
GENERATE_TIMEOUT = 300
PROBE_TIMEOUT = 10
MAX_BODY = 64 * 1024 * 1024  # 64 MiB response cap

ACTIONS = ["doctor", "generate", "models"]

MISSING_HINT = "start backend: python -m backend.main in voicebox checkout"
VS_MISSING_HINT = "start the VoiceStudio app (API on 127.0.0.1:3900)"

BACKENDS = {
    "voicebox": {"default_host": DEFAULT_HOST, "hint": MISSING_HINT},
    "voicestudio": {"default_host": "http://127.0.0.1:3900",
                    "hint": VS_MISSING_HINT},
}

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def emit(payload, code=0):
    json.dump(payload, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")
    sys.exit(code)


def resolve_backend(args):
    """Return backend name: --backend flag wins, else VB_BACKEND env."""
    name = getattr(args, "backend", None) or \
        os.environ.get("VB_BACKEND", "voicebox")
    name = name.strip().lower()
    if name not in BACKENDS:
        emit(envelope(getattr(args, "command", None) or "doctor", "error",
                      0.0, error="unknown backend: %s" % name), 2)
    return name


def resolve_base_url(backend="voicebox"):
    """Return base URL for the backend, or None if VB_HOST is not loopback."""
    raw = os.environ.get(
        "VB_HOST", BACKENDS[backend]["default_host"]).strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if host not in LOOPBACK_HOSTS:
        return None
    if parsed.scheme not in ("http", ""):
        return None
    return raw.rstrip("/")


def http_request(method, url, payload=None, timeout=PROBE_TIMEOUT,
                 out_path=None):
    """Perform an HTTP request. Returns (status_code, headers, body_bytes).

    Raises urllib.error.URLError / OSError on transport failure.
    """
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method=method)
    resp = urllib.request.urlopen(req, timeout=timeout)
    body = resp.read(MAX_BODY + 1)
    if len(body) > MAX_BODY:
        raise ValueError("response exceeds %d bytes" % MAX_BODY)
    if out_path:
        with open(out_path, "wb") as fh:
            fh.write(body)
    return resp.status, dict(resp.headers), body


_BUNDLE_VERSION = None


def _bundle_version():
    """Bundle version from the nearest manifest.json ancestor, cached."""
    global _BUNDLE_VERSION
    if _BUNDLE_VERSION is None:
        _BUNDLE_VERSION = ""
        for parent in Path(__file__).resolve().parents:
            mf = parent / "manifest.json"
            if mf.is_file():
                try:
                    _BUNDLE_VERSION = str(
                        json.loads(mf.read_text(encoding="utf-8"))
                        .get("version") or "")
                except (OSError, ValueError):
                    pass
                break
    return _BUNDLE_VERSION


def envelope(action, status, duration, result=None, error=None):
    env = {"api_version": 2, "status": status, "action": action,
           "duration_s": round(duration, 2),
           "meta": {"answered_by": {
               "bundle": _bundle_version(), "wrapper": "voicebox"}}}
    if result is not None:
        env["result"] = result
    if error is not None:
        env["error"] = error
    return env


def missing(action, duration, extra=None, hint=MISSING_HINT):
    env = envelope(action, "missing", duration, error=hint)
    env["hint"] = hint
    if extra:
        env.update(extra)
    return env


def try_json(body):
    try:
        return json.loads(body.decode("utf-8", "replace"))
    except Exception:
        return None


def cmd_doctor(args):
    backend = resolve_backend(args)
    if backend == "voicestudio":
        return vs_doctor()
    t0 = time.time()
    base = resolve_base_url()
    if base is None:
        emit(envelope("doctor", "error", time.time() - t0,
                      error="VB_HOST must be a localhost http URL"),
             2)
    report = {"base_url": base, "liveness": None, "models": None}
    try:
        status, _h, body = http_request("GET", base + "/health",
                                        timeout=PROBE_TIMEOUT)
        report["liveness"] = {"health_status": status,
                              "health": try_json(body)}
    except (urllib.error.URLError, OSError, ValueError) as e:
        report["liveness"] = {"error": str(e)}
        emit(missing("doctor", time.time() - t0, report), 1)
    try:
        status, _h, body = http_request("GET", base + "/models",
                                        timeout=PROBE_TIMEOUT)
        report["models"] = {"status": status, "data": try_json(body)}
    except (urllib.error.URLError, OSError, ValueError) as e:
        report["models"] = {"error": str(e)}
    emit(envelope("doctor", "ok", time.time() - t0, result=report), 0)


def cmd_models(args):
    backend = resolve_backend(args)
    if backend == "voicestudio":
        return vs_models()
    t0 = time.time()
    base = resolve_base_url()
    if base is None:
        emit(envelope("models", "error", time.time() - t0,
                      error="VB_HOST must be a localhost http URL"), 2)
    try:
        status, _h, body = http_request("GET", base + "/models",
                                        timeout=PROBE_TIMEOUT)
    except (urllib.error.URLError, OSError, ValueError) as e:
        emit(missing("models", time.time() - t0, {"detail": str(e)}), 1)
    emit(envelope("models", "ok", time.time() - t0,
                  result={"http_status": status,
                          "models": try_json(body)}), 0)


def _check_out(args, action):
    """Refuse to overwrite an existing --out path (fail before the
    potentially slow synthesis call)."""
    if os.path.exists(args.out):
        emit(envelope(action, "error", 0.0,
                      error="out_exists:%s (refusing to overwrite; "
                            "pick another --out)" % args.out), 2)


def cmd_generate(args):
    backend = resolve_backend(args)
    if backend == "voicestudio":
        return vs_generate(args)
    t0 = time.time()
    base = resolve_base_url()
    if base is None:
        emit(envelope("generate", "error", time.time() - t0,
                      error="VB_HOST must be a localhost http URL"), 2)
    _check_out(args, "generate")
    payload = {"text": args.text, "voice": args.voice}
    if args.engine:
        payload["engine"] = args.engine
    try:
        status, headers, body = http_request(
            "POST", base + "/generate", payload=payload,
            timeout=args.timeout, out_path=args.out)
    except (urllib.error.URLError, OSError, ValueError) as e:
        emit(missing("generate", time.time() - t0, {"detail": str(e)}), 1)
    emit(envelope("generate", "ok", time.time() - t0,
                  result={"http_status": status, "out": args.out,
                          "bytes": len(body)}), 0)


def vs_base(action):
    """Resolve VoiceStudio base URL or emit error envelope and exit."""
    base = resolve_base_url("voicestudio")
    if base is None:
        emit(envelope(action, "error", 0.0,
                      error="VB_HOST must be a localhost http URL"), 2)
    return base


def vs_doctor():
    t0 = time.time()
    base = vs_base("doctor")
    try:
        status, _h, body = http_request("GET", base + "/v1/models",
                                        timeout=PROBE_TIMEOUT)
    except (urllib.error.URLError, OSError, ValueError) as e:
        emit(missing("doctor", time.time() - t0,
                     {"base_url": base, "detail": str(e)},
                     hint=VS_MISSING_HINT), 1)
    emit(envelope("doctor", "ok", time.time() - t0,
                  result={"base_url": base, "http_status": status,
                          "models": try_json(body)}), 0)


def vs_models():
    t0 = time.time()
    base = vs_base("models")
    try:
        status, _h, body = http_request("GET", base + "/v1/models",
                                        timeout=PROBE_TIMEOUT)
    except (urllib.error.URLError, OSError, ValueError) as e:
        emit(missing("models", time.time() - t0, {"detail": str(e)},
                     hint=VS_MISSING_HINT), 1)
    emit(envelope("models", "ok", time.time() - t0,
                  result={"http_status": status,
                          "models": try_json(body)}), 0)


def vs_generate(args):
    t0 = time.time()
    base = vs_base("generate")
    _check_out(args, "generate")
    payload = {"model": args.engine or "tts-1", "voice": args.voice,
               "input": args.text, "response_format": "wav"}
    try:
        status, headers, body = http_request(
            "POST", base + "/v1/audio/speech", payload=payload,
            timeout=args.timeout, out_path=args.out)
    except (urllib.error.URLError, OSError, ValueError) as e:
        emit(missing("generate", time.time() - t0, {"detail": str(e)},
                     hint=VS_MISSING_HINT), 1)
    emit(envelope("generate", "ok", time.time() - t0,
                  result={"http_status": status, "out": args.out,
                          "bytes": len(body)}), 0)


def main():
    ap = argparse.ArgumentParser(
        prog="voicebox",
        description="Wrapper for local voicebox TTS backend (:17493)")
    ap.add_argument("--backend", choices=sorted(BACKENDS), default=None,
                    help="backend selection (default: VB_BACKEND env or "
                         "voicebox)")
    sub = ap.add_subparsers(dest="command")

    sub.add_parser("doctor", help="probe backend liveness + models")
    sub.add_parser("models", help="list available engines/models")

    p = sub.add_parser("generate", help="POST text -> audio file")
    p.add_argument("--text", required=True, help="text to synthesize")
    p.add_argument("--voice", required=True, help="voice id/name")
    p.add_argument("--engine", help="engine override (optional)")
    p.add_argument("--out", required=True, help="output audio file path")
    p.add_argument("--timeout", type=int, default=GENERATE_TIMEOUT)

    args = ap.parse_args()
    if args.command == "doctor" or args.command is None:
        cmd_doctor(args)
    elif args.command == "models":
        cmd_models(args)
    elif args.command == "generate":
        cmd_generate(args)
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
