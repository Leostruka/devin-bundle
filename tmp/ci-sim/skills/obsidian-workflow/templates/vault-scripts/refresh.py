#!/usr/bin/env python3
"""Re-index the wiki: detect changed source files and flag stale pages.

Usage:
    python refresh.py --project-dir <PROJECT> [--branch <BRANCH>]

Scans the project for files changed since the last index (stored in
project-manifest.json `last_indexed`). For each changed file, finds which
wiki pages reference it via `source: <file>` citations. Prints a report
of stale pages and updates the timestamp. If --branch is provided, records
the indexed branch and warns if it differs from the previously indexed branch.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def find_source_refs(vault_dir):
    """Scan all .md files in the vault for `source: path/to/file` citations."""
    refs = {}  # source_file -> set of wiki pages
    for md_file in vault_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"source:\s*[`]?([^\s`]+)[`]?", text):
            src_path = m.group(1).strip()
            # Strip line number suffix
            src_file = src_path.rsplit(":", 1)[0] if ":" in src_path else src_path
            refs.setdefault(src_file, set()).add(str(md_file.relative_to(vault_dir)))
    return refs


def find_changed_files(project_dir, since_ts):
    """Find files in project_dir modified after since_ts."""
    changed = []
    for root, dirs, files in os.walk(project_dir):
        # Skip common ignore dirs
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "target"}]
        for f in files:
            fp = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(fp)
                if mtime > since_ts:
                    rel = os.path.relpath(fp, project_dir).replace("\\\\", "/")
                    changed.append(rel)
            except OSError:
                pass
    return changed


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Re-index wiki and flag stale pages.")
    parser.add_argument("--project-dir", required=True, help="Project directory to scan")
    parser.add_argument("--branch", help="Branch being indexed (recorded in manifest)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    vault_dir = Path(__file__).parent.resolve()
    manifest_path = vault_dir / "project-manifest.json"

    if not manifest_path.exists():
        print("ERROR: project-manifest.json not found in vault dir.")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    last_indexed = manifest.get("last_indexed_ts", 0)
    prev_branch = manifest.get("indexed_branch")

    print(f"Vault: {vault_dir}")
    print(f"Project: {project_dir}")
    print(f"Last indexed: {datetime.fromtimestamp(last_indexed, tz=timezone.utc).isoformat() if last_indexed else 'never'}")
    if prev_branch:
        print(f"Previously indexed branch: {prev_branch}")
    if args.branch:
        print(f"Requested branch: {args.branch}")
        if prev_branch and prev_branch != args.branch:
            print(f"WARNING: branch changed from '{prev_branch}' to '{args.branch}' — wiki may need full re-generation.")
    print()

    # Find changed files
    changed = find_changed_files(project_dir, last_indexed)
    print(f"Changed files since last index: {len(changed)}")

    if not changed:
        print("No changes detected. All pages are up to date.")
        # Still update timestamp and branch
        manifest["last_indexed_ts"] = datetime.now(tz=timezone.utc).timestamp()
        manifest["last_indexed"] = datetime.now(tz=timezone.utc).isoformat()
        if args.branch:
            manifest["indexed_branch"] = args.branch
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        return 0

    # Find source refs in vault
    refs = find_source_refs(vault_dir)

    # Map changed files to stale pages
    stale_pages = set()
    for changed_file in changed:
        # Try exact match and basename match
        if changed_file in refs:
            for page in refs[changed_file]:
                stale_pages.add(page)
        else:
            # Try basename match
            basename = os.path.basename(changed_file)
            for src_file, pages in refs.items():
                if os.path.basename(src_file) == basename:
                    stale_pages.update(pages)

    print()
    print(f"Stale pages ({len(stale_pages)}):")
    for page in sorted(stale_pages):
        print(f"  [STALE] {page}")

    print()
    print(f"Changed files with no wiki reference ({len(changed) - len(stale_pages)}):")
    for f in changed:
        if not any(f in pages or os.path.basename(f) in [os.path.basename(s) for s in refs] for pages in refs.values()):
            print(f"  [NEW] {f}")

    # Update manifest
    manifest["last_indexed_ts"] = datetime.now(tz=timezone.utc).timestamp()
    manifest["last_indexed"] = datetime.now(tz=timezone.utc).isoformat()
    if args.branch:
        manifest["indexed_branch"] = args.branch
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print()
    print(f"Updated last_indexed: {manifest['last_indexed']}")
    if args.branch:
        print(f"Updated indexed_branch: {args.branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
