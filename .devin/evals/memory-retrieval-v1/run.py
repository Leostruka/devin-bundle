#!/usr/bin/env python3
"""memory-retrieval-v1: cue-substring vs BM25 vs RRF on held-out queries.

Replicates the production scorer from scripts/memory-retrieval.py (cue
weights 3/4/2, body-tag +1, non-active halved) and compares against a
pure-python BM25 and an RRF fusion of both rankings. No deps.
Usage: python run.py [--json]
"""
import json, math, re, sys, os, glob
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
TOP_K = 3


def load_note(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    cues, title, category, status = [], "", "", ""
    if content.startswith("---"):
        m = re.search(r"^---\n(.*?)\n---", content, re.S)
        if m:
            for line in m.group(1).splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"')
                elif line.startswith("category:"):
                    category = line.split(":", 1)[1].strip()
                elif line.startswith("status:"):
                    status = line.split(":", 1)[1].strip()
                elif line.strip().startswith("- "):
                    kv = line.strip()[2:]
                    if ":" in kv:
                        k, v = kv.split(":", 1)
                        cues.append((k.strip(), v.strip().strip('"').lower()))
    body = re.sub(r"^---\n.*?\n---", "", content, flags=re.S, count=1).strip()
    return {"id": os.path.splitext(os.path.basename(path))[0], "title": title,
            "category": category, "status": status, "cues": cues, "body": body}


def cue_score(note, prompt):
    """Production scorer from scripts/memory-retrieval.py, verbatim logic."""
    pl = prompt.lower()
    sc = 0
    for kind, val in note["cues"]:
        if val in pl:
            sc += {"keyword": 3, "symbol": 4, "path": 2}.get(kind, 0)
    for tag in re.findall(r"- (\S+)", note["body"][:1000]):
        if tag.lower() in pl:
            sc += 1
    if note["status"] != "active":
        sc //= 2
    return sc


STOP = set("the a an and or of to in on for with is are was were be how do does "
           "did i my we it its this that what why when which can could should".split())


def tok(s):
    return [t for t in re.findall(r"[a-z0-9_.\-/]+", s.lower()) if t not in STOP]


def bm25_rank(notes, prompt, k1=1.2, b=0.75):
    docs = [tok(n["title"] + " " + n["body"] + " " + n["category"]) for n in notes]
    df = Counter()
    for d in docs:
        df.update(set(d))
    N, avgdl = len(docs), sum(map(len, docs)) / max(len(docs), 1)
    q = tok(prompt)
    out = []
    for i, d in enumerate(docs):
        tf = Counter(d)
        dl = len(d) or 1
        s = 0.0
        for t in q:
            if not tf[t]:
                continue
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / (avgdl or 1)))
        out.append(s)
    return out


def rank_of(scores):
    order = sorted(range(len(scores)), key=lambda i: -scores[i])
    return {i: r for r, i in enumerate(order)}


def main():
    notes = [load_note(p) for p in sorted(glob.glob(os.path.join(HERE, "corpus", "*.md")))]
    cases = json.load(open(os.path.join(HERE, "cases.json"), encoding="utf-8"))["cases"]
    methods = {"cue": {}, "bm25": {}, "rrf": {}, "hybrid": {}}
    detail = []
    for c in cases:
        prompt = c["query"]
        cs = [cue_score(n, prompt) for n in notes]
        bs = bm25_rank(notes, prompt)
        cr, br = rank_of(cs), rank_of(bs)
        rrf = [1 / (60 + cr[i] + 1) + 1 / (60 + br[i] + 1) for i in range(len(notes))]
        # hybrid: additive fusion - cue acts as a boost on top of BM25,
        # never a gate that suppresses lexical matches
        hy = [cs[i] + bs[i] for i in range(len(notes))]
        for name, scores in (("cue", cs), ("bm25", bs), ("rrf", rrf), ("hybrid", hy)):
            top = sorted(range(len(notes)), key=lambda i: -scores[i])[:TOP_K]
            top = [i for i in top if scores[i] > 0]
            hit = notes.index(next(n for n in notes if n["id"] == c["gold"])) in top
            methods[name][c["case_id"]] = hit
        detail.append({"case": c["case_id"], "gold": c["gold"], "difficulty": c["difficulty"],
                       "cue": methods["cue"][c["case_id"]],
                       "bm25": methods["bm25"][c["case_id"]],
                       "rrf": methods["rrf"][c["case_id"]],
                       "hybrid": methods["hybrid"][c["case_id"]]})
    rep = {"eval": "memory-retrieval-v1", "corpus": len(notes), "cases": len(cases),
           "top_k": TOP_K, "recall_at_k": {}, "by_difficulty": {}}
    for name in methods:
        rep["recall_at_k"][name] = round(sum(methods[name].values()) / len(cases), 3)
        for diff in ("easy", "hard"):
            ids = [c["case_id"] for c in cases if c["difficulty"] == diff]
            rep["by_difficulty"].setdefault(diff, {})[name] = round(
                sum(methods[name][i] for i in ids) / max(len(ids), 1), 3)
    rep["detail"] = detail
    print(json.dumps(rep, indent=2))
    with open(os.path.join(HERE, "report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)


if __name__ == "__main__":
    main()
