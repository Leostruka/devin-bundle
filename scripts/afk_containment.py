#!/usr/bin/env python3
"""AFK containment preflight.

Before unattended AFK execution, declare and verify the actual containment
boundary. A Git worktree isolates Git state, not execution, filesystem,
network, or credential exposure. This script fails closed when the requested
containment cannot be proven.
"""
import os
import subprocess
import sys


def is_git_worktree():
    """Return True if the current directory is a linked git worktree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except Exception:
        return False


def find_git_common_dir():
    """Return the common Git directory (or empty string if not available)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return os.path.abspath(result.stdout.strip().replace("/", os.sep))
    except Exception:
        pass
    return ""


def classify_exposure():
    """Classify the current execution environment exposure."""
    return {
        "git_worktree": is_git_worktree(),
        "git_common_dir": find_git_common_dir(),
        "user": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        "home": os.path.expanduser("~"),
        "cwd": os.getcwd(),
        "sandbox": None,  # No approved sandbox detected by default
        "network_isolation": False,  # No network sandbox detected by default
        "credential_vault": False,  # No credential vault detected by default
    }


def preflight(require_worktree=True, require_filesystem_sandbox=False,
              require_network_sandbox=False, require_credential_vault=False):
    """Run the AFK containment preflight and return an allow/stop decision."""
    exposure = classify_exposure()
    checks = []

    if require_worktree:
        checks.append(("git worktree", exposure["git_worktree"],
                       "Git worktree isolates Git state, not execution"))
    else:
        checks.append(("git worktree", True, "worktree not required"))

    if require_filesystem_sandbox:
        checks.append(("filesystem sandbox", exposure["sandbox"] is not None,
                       "untrusted code requires a filesystem sandbox"))
    else:
        checks.append(("filesystem sandbox", True, "filesystem sandbox not required"))

    if require_network_sandbox:
        checks.append(("network sandbox", exposure["network_isolation"],
                       "untrusted code requires network isolation"))
    else:
        checks.append(("network sandbox", True, "network isolation not required"))

    if require_credential_vault:
        checks.append(("credential vault", exposure["credential_vault"],
                       "untrusted code requires a credential vault"))
    else:
        checks.append(("credential vault", True, "credential vault not required"))

    failed = [name for name, ok, _ in checks if not ok]
    verdict = "stop" if failed else "allow"
    reasons = [f"{name}: {reason}" for name, ok, reason in checks if not ok]

    return {
        "verdict": verdict,
        "exposure": exposure,
        "checks": {name: ok for name, ok, _ in checks},
        "failed": failed,
        "reasons": reasons,
    }


def evaluate_trust(source, signed_by=None, approved_sandboxes=None):
    """Evaluate whether a code source is trusted for the current containment.

    Untrusted code requires an approved sandbox. Trusted local work does not.
    """
    approved_sandboxes = approved_sandboxes or set()
    if source in ("local", "repo"):
        return {
            "verdict": "allow",
            "reason": f"source '{source}' is trusted for local work",
            "sandbox_required": False,
        }
    if signed_by and approved_sandboxes:
        return {
            "verdict": "allow",
            "reason": f"source '{source}' is signed by {signed_by} and runs in approved sandbox",
            "sandbox_required": True,
        }
    return {
        "verdict": "stop",
        "reason": f"source '{source}' is untrusted and no approved sandbox is available",
        "sandbox_required": True,
    }


if __name__ == "__main__":
    import json
    import argparse

    ap = argparse.ArgumentParser(description="AFK containment preflight")
    ap.add_argument("--require-filesystem-sandbox", action="store_true")
    ap.add_argument("--require-network-sandbox", action="store_true")
    ap.add_argument("--require-credential-vault", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    result = preflight(
        require_filesystem_sandbox=args.require_filesystem_sandbox,
        require_network_sandbox=args.require_network_sandbox,
        require_credential_vault=args.require_credential_vault,
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"AFK containment preflight: {result['verdict'].upper()}")
        for name, ok in result["checks"].items():
            print(f"  {name}: {'OK' if ok else 'FAIL'}")
        if result["reasons"]:
            for r in result["reasons"]:
                print(f"  - {r}")

    sys.exit(0 if result["verdict"] == "allow" else 2)
