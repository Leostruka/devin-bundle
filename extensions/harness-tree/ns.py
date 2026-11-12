#!/usr/bin/env python3
"""ns.py - run namespacing: snapshot a harness tree into .devin/runs/<ts>-<seed>/.

CLI:
  ns.py create <root> [--seed NAME] [--runs-dir DIR]
  ns.py resume <run-dir>            # prints snapshot path + evidence log
Writes ONLY under the runs dir; never touches the bundle tree.
"""
import json
import os
import sys
import time


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import read, tree_hash  # noqa: E402


def create(root, seed="run", runs_dir=None):
    runs_dir = runs_dir or os.path.join(root, ".devin", "runs")
    ts = time.strftime("%Y%m%d-%H%M%S")
    name = f"{ts}-{seed}"
    rdir = os.path.join(runs_dir, name)
    os.makedirs(rdir, exist_ok=False)
    tree = read(root)
    with open(os.path.join(rdir, "tree.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(tree, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    meta = {"run": name, "root": os.path.abspath(root),
            "created": ts, "files": len(tree), "sha": tree_hash(tree)}
    with open(os.path.join(rdir, "meta.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(meta, fh, indent=1, sort_keys=True)
        fh.write("\n")
    open(os.path.join(rdir, "evidence.log"), "a", encoding="utf-8").close()
    return rdir


def resume(run_dir):
    meta_p = os.path.join(run_dir, "meta.json")
    if not os.path.isfile(meta_p):
        raise FileNotFoundError(f"no meta.json in {run_dir}")
    with open(meta_p, encoding="utf-8") as fh:
        meta = json.load(fh)
    return {"run": meta["run"], "tree": os.path.join(run_dir, "tree.json"),
            "evidence": os.path.join(run_dir, "evidence.log"),
            "files": meta["files"], "sha": meta["sha"]}


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) < 3:
        print(__doc__.strip())
        return 2
    cmd = argv[1]
    if cmd == "create":
        root = argv[2]
        seed = argv[argv.index("--seed") + 1] if "--seed" in argv else "run"
        rdir = (argv[argv.index("--runs-dir") + 1]
                if "--runs-dir" in argv else None)
        print(create(root, seed=seed, runs_dir=rdir))
        return 0
    if cmd == "resume":
        print(json.dumps(resume(argv[2]), indent=1, sort_keys=True))
        return 0
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
