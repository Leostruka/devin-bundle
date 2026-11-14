#!/usr/bin/env python3
"""phase-zero - read-only Fase Zero situational-awareness battery.

Emits the git/GitHub state probes that the git-github-adaptive-engineering
skill runs before any state-changing git/GitHub action: git status,
branches, remotes, recent log, gh auth, repo capabilities, .github/
tree presence, rulesets (best-effort), and workflow list.

Purely diagnostic: never writes files, never mutates git/gh state.
Every probe is optional and offline-safe - failures are captured as
{"ok": false, "error": ...} entries inside the envelope, never crashes.

Envelope v2: api_version=2 + meta.answered_by {bundle, wrapper} via
scripts/bundle_envelope.py (see .devin/docs/CLI-CONTRACT.md).
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bundle_envelope import bind


_stamp, _dumps = bind("phase-zero")


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_VIEW_FIELDS = (
    "nameWithOwner,defaultBranchRef,hasIssuesEnabled,"
    "hasProjectsEnabled,hasDiscussionsEnabled,mergeCommitAllowed,"
    "squashMergeAllowed,rebaseMergeAllowed,deleteBranchOnMerge,"
    "repositoryTopics"
)

DEFAULT_TIMEOUT = 20


def _run(argv, timeout):
    """Run argv read-only; return {ok, returncode?, stdout?, error?}."""
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout)
    except FileNotFoundError:
        return {"ok": False, "error": "%s not found" % argv[0]}
    except subprocess.TimeoutExpired:
        return {"ok": False,
                "error": "%s timed out after %ds" % (argv[0], timeout)}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}
    entry = {"ok": proc.returncode == 0, "returncode": proc.returncode,
             "stdout": proc.stdout.strip()}
    if proc.returncode != 0:
        entry["error"] = (proc.stderr.strip()
                          or "exit %d" % proc.returncode)[:500]
    return entry


def _probe(name, argv, timeout, json_out=False):
    res = _run(argv, timeout)
    entry = {"probe": name, "ok": res["ok"]}
    if "returncode" in res:
        entry["returncode"] = res["returncode"]
    if res["ok"]:
        entry["stdout"] = res.get("stdout", "")
        if json_out:
            try:
                entry["json"] = json.loads(res["stdout"])
            except ValueError:
                entry["error"] = "stdout was not valid JSON"
    else:
        entry["error"] = res.get("error")
    return entry


def _github_tree(root):
    """Presence of .github/ contents - read-only os.listdir."""
    entry = {"probe": "github_tree", "ok": True}
    gh_dir = os.path.join(root, ".github")
    if not os.path.isdir(gh_dir):
        entry.update({"present": False, "entries": []})
        return entry
    try:
        entry["entries"] = sorted(os.listdir(gh_dir))
    except OSError as exc:
        entry.update({"ok": False, "error": str(exc)})
        return entry
    entry["present"] = True
    wf_dir = os.path.join(gh_dir, "workflows")
    if os.path.isdir(wf_dir):
        try:
            entry["workflows"] = sorted(os.listdir(wf_dir))
        except OSError:
            entry["workflows"] = []
    return entry


def collect(root, timeout):
    probes = []

    def add(name, argv, json_out=False):
        entry = _probe(name, argv, timeout, json_out=json_out)
        probes.append(entry)
        return entry

    add("git_status", ["git", "status", "-sb"])
    add("git_branches", ["git", "branch", "-a"])
    add("git_remotes", ["git", "remote", "-v"])
    add("git_log", ["git", "log", "-n", "5", "--oneline"])
    toplevel = add("git_toplevel",
                   ["git", "rev-parse", "--show-toplevel"])
    add("gh_auth", ["gh", "auth", "status"])
    repo = add("gh_repo_view",
               ["gh", "repo", "view", "--json", REPO_VIEW_FIELDS],
               json_out=True)
    # .github/ lives at the repo root: prefer the toplevel reported by
    # git rev-parse so the probe works from any subdirectory (falls
    # back to cwd when not inside a git work tree).
    tree_root = root
    if toplevel.get("ok") and toplevel.get("stdout"):
        tree_root = toplevel["stdout"]
    probes.append(_github_tree(tree_root))

    slug = None
    if repo.get("ok") and isinstance(repo.get("json"), dict):
        slug = repo["json"].get("nameWithOwner")
    if slug:
        rulesets = add("gh_rulesets",
                       ["gh", "api", "repos/%s/rulesets" % slug],
                       json_out=True)
        if not rulesets.get("ok"):
            err = str(rulesets.get("error") or "")
            if "404" in err or "403" in err:
                # Feature off, no rulesets, or insufficient scope:
                # expected on many repos - mark tolerated, stay honest.
                rulesets["tolerated"] = True
    else:
        probes.append({
            "probe": "gh_rulesets", "ok": False, "skipped": True,
            "error": "repo slug unavailable (gh repo view failed)"})

    add("gh_workflows", ["gh", "workflow", "list"])

    ok_count = sum(1 for p in probes if p.get("ok"))
    return {
        "ok": True,
        "battery": "fase-zero",
        "cwd": root,
        "probes": probes,
        "summary": {"total": len(probes), "ok": ok_count,
                    "failed": len(probes) - ok_count},
    }


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    parser = argparse.ArgumentParser(
        prog="phase-zero",
        description="Read-only Fase Zero situational-awareness battery "
                    "(git + GitHub state) emitted as a JSON envelope v2. "
                    "Never writes files or mutates state.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="per-probe timeout in seconds "
                             "(default: %(default)s)")
    args = parser.parse_args(argv[1:])
    try:
        payload = collect(os.getcwd(), timeout=args.timeout)
    except Exception as exc:  # fail-open on unexpected errors
        print(_dumps({"ok": False, "error": str(exc)}))
        return 1
    print(_dumps(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
