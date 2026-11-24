#!/usr/bin/env python3
"""UserPromptSubmit hook: cue-anchored retrieval from .devin/memory/.

Scans .devin/memory/ notes, matches the user's prompt against cues
(keyword, path, symbol) in frontmatter, and injects the top-k relevant
notes as additionalContext.

Evidence:
- arXiv:2607.20972: voluntary memory use ≈ 0; deterministic injection works.
- arXiv:2608.15008: excessive retrieval hurts sequential tasks; keep top-k small.
"""
import json, math, os, re, sys, glob
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

TOP_K = 3

STOP = set("the a an and or of to in on for with is are was were be how do does "
           "did i my we it its this that what why when which can could should".split())


def _tok(s):
    return [t for t in re.findall(r"[a-z0-9_.\-/]+", s.lower()) if t not in STOP]


def bm25_scores(notes, prompt, k1=1.2, b=0.75):
    """Pure-python BM25 over title+body+category. Held-out eval
    (.devin/evals/memory-retrieval-v1): cue-only 0.25 -> additive
    cue+BM25 0.85 recall@3 on paraphrased prompts."""
    docs = [_tok(n['title'] + ' ' + n['body'] + ' ' + n['category']) for n in notes]
    df = Counter()
    for d in docs:
        df.update(set(d))
    n_docs = len(docs)
    avgdl = sum(map(len, docs)) / max(n_docs, 1)
    q = _tok(prompt)
    out = []
    for d in docs:
        tf = Counter(d)
        dl = len(d) or 1
        s = 0.0
        for t in q:
            if not tf[t]:
                continue
            idf = math.log(1 + (n_docs - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / (avgdl or 1)))
        out.append(s)
    return out


def get_memory_dir():
    """Resolve memory directory from env, falling back to project .devin/memory."""
    return os.environ.get('BUNDLE_MEMORY_DIR') or os.environ.get('DEVIN_MEMORY_DIR') or os.path.join(
        os.environ.get('DEVIN_PROJECT_DIR') or os.getcwd(), '.devin', 'memory'
    )


BASE = get_memory_dir()


def load_note(path):
    with open(path, encoding='utf-8') as f:
        content = f.read()
    cues = []
    title = ''
    category = ''
    status = ''
    if content.startswith('---'):
        m = re.search(r'^---\n(.*?)\n---', content, re.S)
        if m:
            fm = m.group(1)
            for line in fm.splitlines():
                if line.startswith('title:'):
                    title = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('category:'):
                    category = line.split(':', 1)[1].strip()
                elif line.startswith('status:'):
                    status = line.split(':', 1)[1].strip()
                elif line.strip().startswith('- '):
                    kv = line.strip()[2:]
                    if ':' in kv:
                        k, v = kv.split(':', 1)
                        cues.append((k.strip(), v.strip().strip('"').lower()))
    body = re.sub(r'^---\n.*?\n---', '', content, flags=re.S, count=1).strip()
    return {
        'path': path,
        'rel': path.replace(BASE + os.sep, '').replace('.md', '').replace(os.sep, '/'),
        'title': title,
        'category': category,
        'status': status,
        'cues': cues,
        'body': body,
    }


def score(note, prompt):
    prompt_l = prompt.lower()
    sc = 0
    for kind, val in note['cues']:
        # '' in prompt_l is always True - same empty-cue bug fixed in
        # memory-post-exec (score guard, 2026-11-24).
        if val and val in prompt_l:
            if kind == 'keyword':
                sc += 3
            elif kind == 'symbol':
                sc += 4
            elif kind == 'path':
                sc += 2
    for tag in re.findall(r'- (\S+)', note['body'][:1000]):
        if tag.lower() in prompt_l:
            sc += 1
    if note['status'] != 'active':
        sc = sc // 2
    return sc


def main():
    try:
        _hookrun.pin_stdio_utf8(sys.stdin)
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError("payload not a dict")
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)

    if data.get('hookEventName') != 'UserPromptSubmit' and data.get('hook_event_name') != 'UserPromptSubmit':
        sys.exit(0)

    prompt = data.get('prompt', '')
    if not prompt or not isinstance(prompt, str) or not os.path.isdir(BASE):
        sys.exit(0)

    notes = []
    for p in glob.glob(os.path.join(BASE, '**', '*.md'), recursive=True):
        if p.endswith('MOC.md'):
            continue
        try:
            notes.append(load_note(p))
        except (OSError, ValueError) as e:
            # one unreadable note must not silence all retrieval
            print(f"memory-retrieval: skipping unreadable note "
                  f"{os.path.basename(p)}: {e}", file=sys.stderr)

    bm25 = bm25_scores(notes, prompt)
    scored = [(score(n, prompt) + bm25[i], n) for i, n in enumerate(notes)]
    scored = [(s, n) for s, n in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        sys.exit(0)

    top = scored[:TOP_K]
    print(f"memory-retrieval: {len(top)} memory note(s) matched user prompt", file=sys.stderr)
    lines = [f"> [!note] Project memory ({len(top)} match{'es' if len(top) > 1 else ''})\n"]
    for s, n in top:
        lines.append(f"> **[[{n['rel']}|{n['title']}]]** ({n['category']})\n")
        # first non-empty body line
        for bline in n['body'].splitlines():
            bline = bline.strip()
            if bline:
                lines.append(f"> {bline}\n")
                break
        lines.append(f"> Source: `{n['path']}`\n")
        lines.append(">\n")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": ''.join(lines).rstrip()
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
