#!/usr/bin/env python3
"""validate_csv.py - schema check for the design-intelligence corpus.

Each domain declares search_cols/output_cols in core.CSV_CONFIG; a CSV is
valid when its header covers every declared column and has >=1 data row.
Stack CSVs share _STACK_COLS columns via core.STACK_CONFIG.

CLI: python validate_csv.py [--json]
exit 0 all valid / 1 problems found
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import CSV_CONFIG, DATA_DIR, STACK_CONFIG, _STACK_COLS

from design_envelope import _stamp, _dumps



def check_domain(name, path, expected_cols):
    problems = []
    if not path.exists():
        return [f"{name}: missing file {path.name}"]
    try:
        with open(path, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            header = set(reader.fieldnames or [])
            rows = sum(1 for _ in reader)
    except (csv.Error, UnicodeDecodeError, OSError) as exc:
        return [f"{name}: unreadable {path.name}: {exc}"]
    missing = [c for c in expected_cols if c not in header]
    if missing:
        problems.append(f"{name}: {path.name} missing cols {missing}")
    if rows == 0:
        problems.append(f"{name}: {path.name} has no data rows")
    return problems


def main():
    problems = []
    report = {}
    for domain, cfg in sorted(CSV_CONFIG.items()):
        cols = set(cfg["search_cols"]) | set(cfg["output_cols"])
        p = check_domain(domain, DATA_DIR / cfg["file"], cols)
        problems.extend(p)
        report[domain] = "FAIL" if p else "ok"
    for stack, cfg in sorted(STACK_CONFIG.items()):
        cols = set(_STACK_COLS["search_cols"]) | set(_STACK_COLS["output_cols"])
        p = check_domain(f"stack:{stack}", DATA_DIR / cfg["file"], cols)
        problems.extend(p)
        report[f"stack:{stack}"] = "FAIL" if p else "ok"

    if "--json" in sys.argv:
        print(_dumps({"problems": problems, "domains": report},
                         indent=1, sort_keys=True))
    else:
        for name, status in sorted(report.items()):
            print(f"{'FAIL' if status == 'FAIL' else 'OK  '} {name}")
        for p in problems:
            print(" ", p)
        print(f"{sum(v == 'ok' for v in report.values())}/{len(report)} domains valid")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
