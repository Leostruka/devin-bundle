"""render — plan v2 JSON -> Remotion project -> rendered frames.

Materializes the template project (templates/remotion-project) into a
work dir, writes the plan as src/plan.json, then invokes
`npx remotion render` unless --dry is passed. Requires Node + npx for
the real render; the materialization step is pure Python and testable.

  python render.py plan.json --workdir out/ [--dry] [--comp Plan]
    -> {"ok": bool, "workdir": ..., "rendered": bool, "cmd": [...]}
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from remotion_envelope import _stamp, _dumps



TEMPLATE = Path(__file__).parent / "templates" / "remotion-project"


def materialize(plan, workdir):
    """Copy template + write src/plan.json. Returns workdir Path."""
    workdir = Path(workdir)
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template missing: {TEMPLATE}")
    if workdir.exists():
        shutil.rmtree(workdir)
    shutil.copytree(TEMPLATE, workdir)
    (workdir / "src" / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return workdir


def render(plan, workdir, dry=True, comp="Plan", out_name="out.mp4",
           timeout=1800):
    workdir = materialize(plan, workdir)
    # Windows: npx/npm are .cmd shims - bare names resolve to the
    # extensionless sh scripts which CreateProcess cannot exec
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    cmd = [npx or "npx", "--yes", "remotion", "render", comp,
           str(Path("out") / out_name)]
    result = {"ok": True, "workdir": str(workdir), "cmd": cmd,
              "rendered": False}
    if dry:
        result["note"] = "dry_run:project_materialized"
        return result
    if not npx:
        return {"ok": False, "error": "npx_missing",
                "hint": "install Node.js", "workdir": str(workdir)}
    # fresh workdir has no node_modules - npx remotion render fails
    # without deps; install once (verified: 244 pkgs ~1min)
    if not (workdir / "node_modules").is_dir():
        # Windows: npm is a .cmd shim - bare "npm" resolves to the
        # extensionless sh script which CreateProcess cannot exec
        npm = shutil.which("npm.cmd") or shutil.which("npm")
        if not npm:
            return {"ok": False, "error": "npm_missing",
                    "hint": "install Node.js (npm required for deps)",
                    "workdir": str(workdir)}
        inst = subprocess.run(
            [npm, "install", "--no-audit", "--no-fund"], cwd=workdir,
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=900,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if inst.returncode != 0:
            return {"ok": False, "error": "npm_install_failed",
                    "stderr": inst.stderr[-2000:],
                    "workdir": str(workdir)}
        result["deps_installed"] = True
    p = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    result.update({"rendered": p.returncode == 0,
                   "stdout": p.stdout[-2000:],
                   "stderr": p.stderr[-2000:]})
    result["ok"] = p.returncode == 0
    return result


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="scene-plan -> remotion render")
    ap.add_argument("plan")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--comp", default="Plan")
    ap.add_argument("--out", default="out.mp4")
    args = ap.parse_args(argv)
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(_dumps({"ok": False,
                          "error": f"plan unreadable: {e}"}))
        return 2
    res = render(plan, args.workdir, dry=args.dry,
                 comp=args.comp, out_name=args.out)
    print(_dumps(res, indent=2))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
