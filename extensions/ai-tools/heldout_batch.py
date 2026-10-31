"""Frozen held-out manifest batch runner (Rule 15).

Runs a bounded batch over a frozen manifest of public/synthetic held-out
entries for offline evaluation. Never part of the agent online path, never
imported by hooks, never sends anything anywhere: the runner is a local
callable.

Manifest format (JSON):

    {"entries": [{"id": "...", "path": "...", "sha256": "...",
                  "split": "heldout", "source": "public"|"synthetic"}]}

Relative entry paths resolve against `data_root` (default: the manifest's
directory), never against the process CWD. Every entry is fully validated
up front — field types, split, source, sensitive-path patterns, root
escape, per-file size, and sha256 — and its verified bytes are bound to
the returned entry, so a file tampered with after load cannot execute
under a stale recorded hash. Oversized files are rejected, never silently
truncated. Result records are deterministic: sorted by id, fixed schema,
no wall clock. Stdlib only.
"""
import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_SPLIT = "heldout"
ALLOWED_SOURCES = {"public", "synthetic"}
DEFAULT_MAX_JOBS = 64
DEFAULT_MAX_ENTRY_BYTES = 8192
MAX_ENTRIES = 1024
MAX_MANIFEST_BYTES = 4 << 20
_SHA256_LEN = 64
_SENSITIVE = ("credential", ".env", "secret", "token", "password",
              "private_key", ".pem", "apikey", "api_key")
_ENTRY_FIELDS = ("id", "path", "sha256", "split", "source")


class ManifestError(ValueError):
    pass


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _sensitive(path):
    low = str(path).lower()
    return any(s in low for s in _SENSITIVE)


def _check_str(e, key, eid):
    v = e[key]
    if not isinstance(v, str) or not v:
        raise ManifestError(f"entry {eid!r} field {key!r} must be a "
                            "non-empty string")
    return v


def _resolve(raw, root, eid):
    p = Path(raw)
    if not p.is_absolute():
        p = root / raw
    rp = p.resolve()
    if rp != root and root not in rp.parents:
        raise ManifestError(f"entry {eid!r} escapes manifest root: {p}")
    return rp


def load_manifest(manifest_path, data_root=None,
                  max_entry_bytes=DEFAULT_MAX_ENTRY_BYTES):
    """Load, validate and bind bytes for a frozen manifest.

    Returns entries carrying their verified bytes; every check runs before
    any job may execute. Raises ManifestError on the first violation.
    """
    manifest_path = Path(manifest_path)
    try:
        with open(manifest_path, "rb") as f:
            raw = f.read(MAX_MANIFEST_BYTES + 1)
    except OSError as e:
        raise ManifestError(f"cannot read manifest: {e}")
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ManifestError("manifest exceeds size bound")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ManifestError(f"manifest is not JSON: {e}")
    if not isinstance(data, dict):
        raise ManifestError("manifest must be a JSON object")
    root = Path(data_root) if data_root else manifest_path.parent
    root = root.resolve()
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ManifestError("manifest has no entries")
    if len(entries) > MAX_ENTRIES:
        raise ManifestError(f"{len(entries)} entries exceed "
                            f"bound {MAX_ENTRIES}")
    out = []
    seen = set()
    for e in entries:
        if not isinstance(e, dict):
            raise ManifestError("entry is not an object")
        for key in _ENTRY_FIELDS:
            if key not in e:
                raise ManifestError(f"entry missing field {key!r}")
        eid = _check_str(e, "id", e.get("id", "?"))
        if eid in seen:
            raise ManifestError(f"duplicate entry id {eid!r}")
        seen.add(eid)
        raw_path = _check_str(e, "path", eid)
        sha = _check_str(e, "sha256", eid)
        if len(sha) != _SHA256_LEN or any(
                c not in "0123456789abcdef" for c in sha):
            raise ManifestError(f"entry {eid!r} sha256 malformed")
        if _check_str(e, "split", eid) != REQUIRED_SPLIT:
            raise ManifestError(
                f"entry {eid!r} split {e['split']!r} is not heldout")
        if _check_str(e, "source", eid) not in ALLOWED_SOURCES:
            raise ManifestError(
                f"entry {eid!r} source {e['source']!r} is not "
                "public/synthetic")
        if _sensitive(raw_path):
            raise ManifestError(
                f"entry {eid!r} path looks sensitive: {raw_path}")
        p = _resolve(raw_path, root, eid)
        if not p.is_file():
            raise ManifestError(f"entry {eid!r} file missing: {p}")
        try:
            with open(p, "rb") as f:
                blob = f.read(max_entry_bytes + 1)
        except OSError as e:
            raise ManifestError(f"entry {eid!r} unreadable: {e}")
        if len(blob) > max_entry_bytes:
            raise ManifestError(
                f"entry {eid!r} is {len(blob)} bytes > "
                f"max_entry_bytes={max_entry_bytes}")
        if _sha256(blob) != sha:
            raise ManifestError(
                f"entry {eid!r} sha256 mismatch (tampered?)")
        rec = {"id": eid, "path": str(p), "sha256": sha,
               "split": e["split"], "source": e["source"],
               "_data": blob}
        out.append(rec)
    return out


def run_batch(entries, runner, max_jobs=DEFAULT_MAX_JOBS):
    """Run `runner(entry, prompt)` per entry, bounded and deterministic.

    Only entries returned by load_manifest are accepted — their verified
    bytes are the prompt input, so no file is reread after validation.
    """
    if len(entries) > max_jobs:
        raise ValueError(
            f"{len(entries)} entries exceed max_jobs={max_jobs}")
    for e in entries:
        if not isinstance(e, dict) or "_data" not in e \
                or any(k not in e for k in _ENTRY_FIELDS):
            raise ValueError(
                "entries must come from load_manifest (verified bytes "
                "bound at load)")
    results = []
    for e in sorted(entries, key=lambda x: x["id"]):
        prompt = e["_data"].decode("utf-8", errors="replace")
        try:
            r = runner(e, prompt)
        except Exception as exc:
            r = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        rec = {"id": e["id"], "ok": bool(r.get("ok")),
               "input_sha256": e["sha256"]}
        if r.get("ok"):
            out = str(r.get("output", ""))
            rec["output_sha256"] = hashlib.sha256(
                out.encode()).hexdigest()
        else:
            rec["error"] = str(r.get("error", "unknown"))[:200]
        results.append(rec)
    return {"manifest_entries": len(entries), "results": results}


def main():
    ap = argparse.ArgumentParser(description="frozen held-out batch runner")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--data-root")
    ap.add_argument("--max-jobs", type=int, default=DEFAULT_MAX_JOBS)
    ap.add_argument("--binary", help="llama-cli path for the bitnet runner")
    ap.add_argument("--model", help="GGUF path for the bitnet runner")
    ap.add_argument("--out", help="write result JSON here")
    args = ap.parse_args()
    try:
        entries = load_manifest(args.manifest, args.data_root)
    except ManifestError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        raise SystemExit(2)
    if not (args.binary and args.model):
        print(json.dumps({"ok": False,
                          "error": "no backend configured: pass --binary "
                                   "and --model"}))
        raise SystemExit(2)
    import bitnet_adapter as ba
    if not Path(args.binary).is_file() or not Path(args.model).is_file():
        print(json.dumps({"ok": False,
                          "error": "backend unavailable: binary or model "
                                   "missing"}))
        raise SystemExit(2)

    if args.out:
        out_path = Path(args.out).resolve()
        protected = {Path(args.manifest).resolve(),
                     Path(args.binary).resolve(),
                     Path(args.model).resolve()}
        protected.update(Path(e["path"]).resolve() for e in entries)
        if out_path in protected:
            print(json.dumps(
                {"ok": False,
                 "error": "output path collides with a batch input"}))
            raise SystemExit(2)
        if out_path.exists():
            print(json.dumps(
                {"ok": False,
                 "error": "output file exists; refusing to overwrite"}))
            raise SystemExit(2)

    def runner(entry, prompt):
        cfg = ba.BitNetConfig(binary=args.binary, model=args.model)
        return ba.run(prompt, cfg)

    res = run_batch(entries, runner, max_jobs=args.max_jobs)
    res["ok"] = all(r["ok"] for r in res["results"])
    text = json.dumps(res, indent=2)
    if args.out:
        try:
            Path(args.out).write_text(text)
        except OSError as e:
            print(json.dumps({"ok": False,
                              "error": f"write_failed:{e}"}))
            raise SystemExit(2)
    print(text)
    raise SystemExit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
