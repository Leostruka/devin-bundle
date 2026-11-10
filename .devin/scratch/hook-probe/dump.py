import sys, pathlib
data = sys.stdin.read()
pathlib.Path(r"D:/Programing/ai_workspace/devin-bundle/.devin/scratch/hook-probe/payloads.jsonl").open("a", encoding="utf-8").write(data + "\n")
sys.exit(0)
