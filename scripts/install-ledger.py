#!/usr/bin/env python3
"""Install drift ledger — installs.json + reconcile.

Upstream pattern (agency-agents-app installs.json, adapted): record every
managed file with slug, dest, source_hash (bundle), rendered_hash (sha256
of the bytes on disk), installed_at, corpus_version (bundle version).

Reconcile reports five states per managed file:
  Current   live == bundle hash, OR live == recorded rendered_hash and the
            record's source_hash matches the current bundle source
            (rendered files never equal their raw source)
  Outdated  live == recorded rendered_hash but the recorded source_hash
            differs from the current bundle source — or is absent
            (bundle moved forward, install not yet refreshed)
  Modified  live exists, live hash != rendered_hash (local edit or
            never-recorded content) — local drift
  Removed   file recorded but missing on disk
  Foreign   file exists in a managed dir but is not in the ledger/manifest

Install-time build artifacts (.pyc/.pyd/.so/.dll, ADR 003) are not
shipped sources and never drift — excluded from iteration and reconcile.

backup_if_differs is already covered by the installers (Backup-File /
byte-identical skip); this module is the missing drift detection +
audit trail. Renderers must be deterministic: render timestamps belong in
the ledger record, not in rendered bytes.

Commands:
    record-all    snapshot every managed file (post-install pass)
    record NAME   snapshot one live-relative file
    reconcile     print the 5-state report (JSON on stdout)
    status        human-readable summary

Paths: bundle root = DEVIN_PROJECT_DIR or cwd; live root = DEVIN_HOME or
$APPDATA%/devin (Windows) / ~/.config/devin. Ledger lives at
.devin/install-ledger/installs.json in the bundle repo.
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys

LEDGER_REL = os.path.join(".devin", "install-ledger", "installs.json")
MANAGED_TOP = ("skills", "scripts", "agents", "docs", "data",
               "extensions")
MANAGED_FILES = ("AGENTS.md", "config.json", "hooks.v1.json")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _root():
    return os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()


def _live():
    if os.environ.get("DEVIN_HOME"):
        return os.environ["DEVIN_HOME"]
    if os.name == "nt":
        return os.path.join(os.environ.get("APPDATA", ""), "devin")
    return os.path.expanduser(os.path.join("~", ".config", "devin"))


def _ledger_path():
    return os.path.join(_root(), LEDGER_REL)


def _load_ledger():
    try:
        with open(_ledger_path(), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"version": 1, "files": {}}


def _save_ledger(data):
    path = _ledger_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
    os.replace(tmp, path)


# installer remaps (install.ps1 §7b): live dirs whose sources are
# dissolved under .devin/ in the bundle repo
_BUNDLE_REMAP = (("docs/plans/", ".devin/plans/"),
                 ("docs/templates/", ".devin/templates/"),
                 ("docs/", ".devin/docs/"))


def _bundle_rel(rel):
    """Live-side relative path -> bundle-side relative path."""
    for pre, bundle_pre in _BUNDLE_REMAP:
        if rel.startswith(pre):
            return bundle_pre + rel[len(pre):]
    return rel


def _bundle_hash(root, rel):
    """Hash of the bundle-side source bytes for a managed relative path."""
    src = os.path.join(root, *_bundle_rel(rel).split("/"))
    return _sha256(src) if os.path.isfile(src) else None


def _record_file(root, live, rel, files):
    dst = os.path.join(live, rel)
    if not os.path.isfile(dst):
        return
    files[rel] = {
        "dest": dst,
        "source_hash": _bundle_hash(root, rel),
        "rendered_hash": _sha256(dst),
        "installed_at": datetime.datetime.now(
            datetime.timezone.utc).isoformat(timespec="seconds"),
        "corpus_version": _corpus_version(root),
    }


def _corpus_version(root):
    try:
        m = json.load(open(os.path.join(root, "manifest.json"),
                           encoding="utf-8"))
        return m.get("version", "")
    except (OSError, ValueError):
        return ""


_NOISE_DIRS = ("__pycache__", ".venv", "venv", "target",
               "node_modules", ".git", ".backups")


def _is_artifact(rel):
    """Install-time build artifacts (ADR 003) — never shipped sources."""
    return rel.endswith((".pyc", ".pyd", ".so", ".dll"))


def _iter_live_files(live):
    """Yield relative paths of files under managed live dirs."""
    for top in MANAGED_TOP:
        base = os.path.join(live, top)
        if not os.path.isdir(base):
            continue
        for dirpath, dirs, names in os.walk(base):
            dirs[:] = [d for d in dirs if d not in _NOISE_DIRS]
            for n in names:
                if _is_artifact(n):
                    continue
                yield os.path.relpath(
                    os.path.join(dirpath, n), live).replace("\\", "/")
    for f in MANAGED_FILES:
        if os.path.isfile(os.path.join(live, f)):
            yield f


def cmd_record_all(_args):
    root, live = _root(), _live()
    data = _load_ledger()
    files = data.setdefault("files", {})
    live_set = set(_iter_live_files(live))
    n = 0
    for rel in sorted(live_set):
        _record_file(root, live, rel, files)
        n += 1
    pruned = [rel for rel in list(files) if rel not in live_set]
    for rel in pruned:
        del files[rel]
    _save_ledger(data)
    _write_corpus_index(root)
    print(json.dumps({"ok": True, "recorded": n, "pruned": len(pruned)}))
    return 0


def cmd_record(args):
    root, live = _root(), _live()
    data = _load_ledger()
    rel = args.name.replace("\\", "/")
    _record_file(root, live, rel, data.setdefault("files", {}))
    _save_ledger(data)
    print(json.dumps({"ok": True, "recorded": rel}))
    return 0


def reconcile():
    """Return {state: [rels]} across the five states."""
    root, live = _root(), _live()
    ledger = _load_ledger().get("files", {})
    out = {"Current": [], "Outdated": [], "Modified": [],
           "Removed": [], "Foreign": []}
    for rel in sorted(set(_iter_live_files(live)) | set(ledger)):
        if _is_artifact(rel):
            continue  # stale records for build artifacts don't drift
        dst = os.path.join(live, rel)
        rec = ledger.get(rel)
        if not os.path.isfile(dst):
            if rec:
                out["Removed"].append(rel)
            continue
        live_hash = _sha256(dst)
        bundle_hash = _bundle_hash(root, rel)
        if rec is None:
            if bundle_hash is not None and live_hash == bundle_hash:
                out["Current"].append(rel)
            else:
                out["Foreign"].append(rel)
            continue
        rendered = rec.get("rendered_hash")
        rec_src = rec.get("source_hash")
        if bundle_hash is not None and live_hash == bundle_hash:
            out["Current"].append(rel)
        elif rendered and live_hash == rendered:
            # live is the recorded render/copy; it is stale only when the
            # bundle source moved since the record (rendered files like
            # config.json can never equal their raw source)
            if rec_src is not None and rec_src == bundle_hash:
                out["Current"].append(rel)
            else:
                out["Outdated"].append(rel)
        else:
            out["Modified"].append(rel)
    return out


def cmd_reconcile(_args):
    print(json.dumps(reconcile(), indent=2, sort_keys=True))
    return 0


def cmd_status(_args):
    rep = reconcile()
    total = sum(len(v) for v in rep.values())
    print("Install ledger status (%d files tracked):" % total)
    for state in ("Current", "Outdated", "Modified", "Removed", "Foreign"):
        n = len(rep[state])
        print("  %-9s %d" % (state, n))
        for rel in rep[state][:10]:
            print("    %s" % rel)
        if n > 10:
            print("    ... +%d more" % (n - 10))
    return 0


def backup_if_differs(dst, backup_root):
    """Copy dst to backup_root/<name>.<fs-safe-ts> before overwrite.

    Returns the backup path, or None when dst is absent. Raises OSError
    on failure — callers must abort the pending write.
    """
    if not os.path.isfile(dst):
        return None
    ts = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")
    target = os.path.join(backup_root, os.path.basename(dst) + "." + ts)
    os.makedirs(backup_root, exist_ok=True)
    shutil.copyfile(dst, target)
    return target


def _write_corpus_index(root):
    """Index bundle-side managed files (sha256), stable key order."""
    files = {}
    for top in MANAGED_TOP + MANAGED_FILES:
        base = os.path.join(root, top)
        if os.path.isfile(base):
            files[top] = _sha256(base)
        elif os.path.isdir(base):
            for dirpath, dirs, names in os.walk(base):
                dirs[:] = [d for d in dirs if d not in _NOISE_DIRS]
                for n in names:
                    if _is_artifact(n) or "__pycache__" in dirpath:
                        continue
                    p = os.path.join(dirpath, n)
                    files[os.path.relpath(p, root).replace(
                        "\\", "/")] = _sha256(p)
    # remapped sources (.devin/* -> live docs/*) keyed under live rels;
    # a live rel claimed by a more specific prefix (docs/plans ->
    # .devin/plans) is skipped by the generic docs/ walk
    for pre, bundle_pre in _BUNDLE_REMAP:
        base = os.path.join(root, *bundle_pre.split("/"))
        if not os.path.isdir(base):
            continue
        for dirpath, dirs, names in os.walk(base):
            dirs[:] = [d for d in dirs if d not in _NOISE_DIRS]
            for n in names:
                if _is_artifact(n) or "__pycache__" in dirpath:
                    continue
                p = os.path.join(dirpath, n)
                rel = pre + os.path.relpath(p, base).replace("\\", "/")
                if any(len(other) > len(pre) and rel.startswith(other)
                       for other, _bp in _BUNDLE_REMAP):
                    continue
                files[rel] = _sha256(p)
    path = os.path.join(
        root, ".devin", "install-ledger", "corpus-index.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"version": 1, "corpus_version": _corpus_version(root),
                   "files": files}, fh, indent=2, sort_keys=True)


def main():
    ap = argparse.ArgumentParser(prog="install-ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("record-all")
    p = sub.add_parser("record")
    p.add_argument("name", help="live-relative path under a managed dir")
    sub.add_parser("reconcile")
    sub.add_parser("status")
    args = ap.parse_args()
    fn = {"record-all": cmd_record_all, "record": cmd_record,
          "reconcile": cmd_reconcile, "status": cmd_status}[args.cmd]
    return fn(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # callers tolerate non-zero (install.sh `|| true`,
        # install.ps1 pipes to Out-Null); ok:false must exit non-zero (contract).
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)
