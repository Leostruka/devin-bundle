#!/usr/bin/env python3
"""PostToolUse hook: inject memory notes after write/edit based on cues.path.

Evidence:
- arXiv:2607.20972: retrieval must be deterministic, not voluntary.
- arXiv:2608.15008: keep retrieved context small.
"""
import json, os, re, sys, glob

BASE = '.devin/memory'
TOP_K = 2


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
                        cues.append((k.strip(), v.strip().strip('"')))
    body = re.sub(r'^---\n.*?\n---', '', content, flags=re.S, count=1).strip()
    return {
        'rel': path.replace(BASE + os.sep, '').replace('.md', '').replace(os.sep, '/'),
        'title': title,
        'category': category,
        'status': status,
        'cues': cues,
        'body': body,
    }


def score_path(note, file_path):
    if note['status'] != 'active':
        return 0
    sc = 0
    for kind, val in note['cues']:
        if kind == 'path' and val:
            # match if cue is a substring of the edited file path, or vice versa
            v_norm = val.lower().replace('\\', '/')
            f_norm = file_path.lower().replace('\\', '/')
            if v_norm in f_norm or f_norm in v_norm:
                sc += 5
    return sc


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)

    if data.get('hookEventName') != 'PostToolUse' and data.get('hook_event_name') != 'PostToolUse':
        sys.exit(0)

    tool_name = data.get('tool_name', '')
    if tool_name not in ('write', 'edit'):
        sys.exit(0)

    tool_input = data.get('tool_input') or {}
    file_path = tool_input.get('file_path', '')
    if not file_path:
        sys.exit(0)

    try:
        rel = os.path.relpath(file_path, os.getcwd())
    except ValueError:
        rel = file_path

    if not os.path.isdir(BASE):
        sys.exit(0)

    notes = []
    for p in glob.glob(os.path.join(BASE, '**', '*.md'), recursive=True):
        if p.endswith('MOC.md'):
            continue
        notes.append(load_note(p))

    scored = [(score_path(n, rel), n) for n in notes]
    scored = [(s, n) for s, n in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        sys.exit(0)

    top = scored[:TOP_K]
    print(f"memory-post-edit: {len(top)} memory note(s) injected for {rel}", file=sys.stderr)
    lines = [f"> [!note] Memory for edited file `{rel}` ({len(top)} match{'es' if len(top) > 1 else ''})\n"]
    for s, n in top:
        lines.append(f"> **[[{n['rel']}|{n['title']}]]** ({n['category']})\n")
        for bline in n['body'].splitlines():
            bline = bline.strip()
            if bline:
                lines.append(f"> {bline}\n")
                break
        lines.append(">\n")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": ''.join(lines).rstrip()
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
