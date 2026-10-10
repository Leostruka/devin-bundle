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
    cmd = ["npx", "--yes", "remotion", "render", comp,
           str(Path("out") / out_name)]
    result = {"ok": True, "workdir": str(workdir), "cmd": cmd,
              "rendered": False}
    if dry:
        result["note"] = "dry_run:project_materialized"
        return result
    if not shutil.which("npx"):
        return {"ok": False, "error": "npx_missing",
                "hint": "install Node.js", "workdir": str(workdir)}
    p = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True,
                       timeout=timeout)
    result.update({"rendered": p.returncode == 0,
                   "stdout": p.stdout[-2000:],
                   "stderr": p.stderr[-2000:]})
    result["ok"] = p.returncode == 0
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description="scene-plan -> remotion render")
    ap.add_argument("plan")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--comp", default="Plan")
    ap.add_argument("--out", default="out.mp4")
    args = ap.parse_args(argv)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    print(json.dumps(render(plan, args.workdir, dry=args.dry,
                            comp=args.comp, out_name=args.out),
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
