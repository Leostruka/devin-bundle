#!/usr/bin/env python3
"""dep-audit — deterministic dependency vulnerability scan.

Detects package ecosystems in the current directory and shells out to
already-installed scanners. Never installs anything; a missing scanner is
reported as skipped, not fetched. Output is a single JSON object:

  {"ok": true, "root": "...", "detected": ["python", "node"],
   "scanned": [{"ecosystem": "python", "scanner": "pip-audit",
                "findings": [{"pkg", "id", "severity", "fixed_in"}]}],
   "skipped": [{"ecosystem": "rust", "reason": "cargo-audit-missing"}],
   "errors": []}

Exit 0 when the scan ran (findings are data, not failure); exit 1 only on
internal error. Stdlib only.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

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
    return {"bundle": _bundle_version(), "wrapper": "dep-audit"}


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


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


try:
    _CF = subprocess.CREATE_NO_WINDOW
except AttributeError:
    _CF = 0

DETECT = {
    "python": ["requirements*.txt", "pyproject.toml", "Pipfile",
               "poetry.lock", "uv.lock", "pdm.lock", "setup.py"],
    "node": ["package.json"],
    "rust": ["Cargo.toml"],
    "go": ["go.mod"],
    "php": ["composer.json", "composer.lock"],
    "ruby": ["Gemfile", "Gemfile.lock"],
    "elixir": ["mix.exs", "mix.lock"],
}

SCANNERS = {
    "python": ["pip-audit", "osv-scanner"],
    "node": ["npm", "osv-scanner"],
    "rust": ["cargo-audit", "osv-scanner"],
    "go": ["govulncheck", "osv-scanner"],
    "php": ["osv-scanner"],
    "ruby": ["osv-scanner"],
    "elixir": [],
}


def _which(*names):
    for n in names:
        p = shutil.which(n)
        if p:
            return n, p
    return None, None


class _Deadline:
    """Total-scan budget (issue #404): caps each scanner subprocess to
    the remaining wall time so a hook-bounded caller never gets orphaned
    mid-scan. None = unbounded (manual CLI runs)."""

    def __init__(self, seconds):
        self.end = (time.monotonic() + seconds
                    if seconds is not None else None)

    def left(self):
        if self.end is None:
            return None
        return max(0.0, self.end - time.monotonic())

    def cap(self, default):
        left = self.left()
        return default if left is None else max(1.0, min(default, left))

    def expired(self):
        left = self.left()
        return left is not None and left <= 0.5


def _detect(root):
    found = []
    for eco, pats in DETECT.items():
        for pat in pats:
            if "*" in pat:
                import glob
                if glob.glob(os.path.join(root, pat)):
                    found.append(eco)
                    break
            elif os.path.exists(os.path.join(root, pat)):
                found.append(eco)
                break
    return found


def _run(argv, cwd, timeout=120, dl=None):
    if dl is not None:
        timeout = dl.cap(timeout)
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=timeout, creationflags=_CF)


def _pip_audit(root, dl=None):
    reqs = []
    for f in sorted(os.listdir(root)):
        if f.startswith("requirements") and f.endswith(".txt"):
            reqs.append(f)
    findings = []
    mode = "env"
    if reqs:
        mode = "requirements"
        for req in reqs:
            if dl is not None and dl.expired():
                break
            p = _run(["pip-audit", "-r", req, "--format", "json",
                      "--progress-spinner", "off"], root, dl=dl)
            if p.returncode not in (0, 1):
                return None, f"pip-audit exit {p.returncode}: {p.stderr[-300:]}"
            try:
                data = json.loads(p.stdout or "[]")
            except json.JSONDecodeError:
                continue
            deps = data if isinstance(data, list) else data.get("dependencies", [])
            for d in deps:
                for v in d.get("vulns", []):
                    findings.append({
                        "pkg": d.get("name"), "id": v.get("id"),
                        "severity": (v.get("severity") or "").lower() or None,
                        "fixed_in": v.get("fix_versions") or None})
    else:
        p = _run(["pip-audit", "--format", "json",
                  "--progress-spinner", "off"], root, dl=dl)
        if p.returncode not in (0, 1):
            return None, f"pip-audit exit {p.returncode}: {p.stderr[-300:]}"
        try:
            data = json.loads(p.stdout or "[]")
        except json.JSONDecodeError:
            data = []
        deps = data if isinstance(data, list) else data.get("dependencies", [])
        for d in deps:
            for v in d.get("vulns", []):
                findings.append({
                    "pkg": d.get("name"), "id": v.get("id"),
                    "severity": (v.get("severity") or "").lower() or None,
                    "fixed_in": v.get("fix_versions") or None})
    return {"findings": findings, "mode": mode}, None


def _npm_audit(root, dl=None):
    p = _run(["npm", "audit", "--json"], root, timeout=180, dl=dl)
    try:
        data = json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        return None, "npm audit: unparseable output"
    findings = []
    vulns = data.get("vulnerabilities") or {}
    for name, v in vulns.items():
        sev = (v.get("severity") or "").lower() or None
        via = v.get("via") or []
        fix = v.get("fixAvailable")
        fixed = fix.get("version") if isinstance(fix, dict) else (
            fix if isinstance(fix, str) else None)
        ids = []
        for item in via:
            if isinstance(item, dict) and item.get("url"):
                ids.append(item["url"].rsplit("/", 1)[-1])
            elif isinstance(item, str):
                ids.append(item)
        findings.append({"pkg": name, "id": ",".join(ids) or None,
                         "severity": sev, "fixed_in": fixed})
    return {"findings": findings}, None


_RUSTSEC_RE = re.compile(r"RUSTSEC-\d{4}-\d{4}")
_CRATE_RE = re.compile(r"Crate:\s*(\S+)")


def _cargo_audit(root, dl=None):
    p = _run(["cargo", "audit"], root, timeout=180, dl=dl)
    text = p.stdout + "\n" + p.stderr
    findings = []
    for m in _RUSTSEC_RE.finditer(text):
        findings.append({"pkg": None, "id": m.group(0),
                         "severity": None, "fixed_in": None})
    # dedupe ids
    seen, out = set(), []
    for f in findings:
        if f["id"] not in seen:
            seen.add(f["id"])
            out.append(f)
    return {"findings": out}, None


def _osv_scanner(root, dl=None):
    p = _run(["osv-scanner", "scan", "source", "--recursive", ".",
              "--format", "json"], root, timeout=300, dl=dl)
    try:
        data = json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        return None, "osv-scanner: unparseable output"
    findings = []
    for res in data.get("results", []):
        for pkg in res.get("packages", []):
            name = (pkg.get("package") or {}).get("name")
            eco = (pkg.get("package") or {}).get("ecosystem")
            for v in pkg.get("vulnerabilities", []):
                findings.append({
                    "pkg": name, "id": v.get("id"),
                    "severity": (v.get("database_specific", {}) or {})
                    .get("severity"),
                    "fixed_in": None, "ecosystem_hint": eco})
    return {"findings": findings}, None


def scan(root, max_seconds=None):
    detected = _detect(root)
    dl = _Deadline(max_seconds)
    scanned, skipped, errors = [], [], []
    for eco in detected:
        if dl.expired():
            skipped.append({"ecosystem": eco,
                            "reason": "budget-exhausted"})
            continue
        tool, path = _which(*SCANNERS.get(eco, []))
        if not tool:
            skipped.append({"ecosystem": eco,
                            "reason": f"no-scanner ({'/'.join(SCANNERS.get(eco, [])) or 'none-mapped'})"})
            continue
        try:
            if tool == "pip-audit":
                res, err = _pip_audit(root, dl)
            elif tool == "npm":
                res, err = _npm_audit(root, dl)
            elif tool in ("cargo-audit", "cargo"):
                res, err = _cargo_audit(root, dl)
            elif tool == "osv-scanner":
                res, err = _osv_scanner(root, dl)
            else:
                skipped.append({"ecosystem": eco,
                                "reason": f"scanner-not-implemented ({tool})"})
                continue
        except subprocess.TimeoutExpired:
            errors.append(f"{eco}: scanner timeout")
            continue
        except Exception as e:  # noqa: BLE001 - report, never crash the hook
            errors.append(f"{eco}: {e}")
            continue
        if err:
            errors.append(f"{eco}: {err}")
            continue
        for f in res["findings"]:
            f.setdefault("ecosystem", eco)
        scanned.append({"ecosystem": eco, "scanner": tool,
                        "mode": res.get("mode"),
                        "findings": res["findings"]})
    return {"ok": True, "root": os.path.abspath(root),
            "detected": detected, "scanned": scanned,
            "skipped": skipped, "errors": errors}


def main(argv=None):
    root = os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
    if argv is None:
        argv = sys.argv[1:]
    max_seconds = None
    # --root/--max-seconds accepted in any position (review: --root was
    # only honored at argv[0], silently scanning cwd otherwise)
    for i, a in enumerate(argv):
        if a == "--root" and i + 1 < len(argv):
            root = argv[i + 1]
        elif a == "--max-seconds" and i + 1 < len(argv):
            try:
                max_seconds = float(argv[i + 1])
            except ValueError:
                pass
    try:
        out = scan(root, max_seconds=max_seconds)
    except Exception as e:  # noqa: BLE001
        out = {"ok": False, "error": str(e)}
        print(_dumps(out))
        return 1
    print(_dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
