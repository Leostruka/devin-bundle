#!/usr/bin/env python3
"""PostToolUse hook: cue-anchored retrieval after exec based on cues.symbol/keyword.

Evidence:
- arXiv:2607.20972: deterministic retrieval works; voluntary recall does not.
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
                        cues.append((k.strip(), v.strip().strip('"').lower()))
    body = re.sub(r'^---\n.*?\n---', '', content, flags=re.S, count=1).strip()
    return {
        'rel': path.replace(BASE + os.sep, '').replace('.md', '').replace(os.sep, '/'),
        'title': title,
        'category': category,
        'status': status,
        'cues': cues,
        'body': body,
    }


def score(note, command, output):
    if note['status'] != 'active':
        return 0
    text = (command or '') + ' ' + (output or '')
    text_l = text.lower()
    sc = 0
    for kind, val in note['cues']:
        if val in text_l:
            if kind == 'symbol':
                sc += 5
            elif kind == 'keyword':
                sc += 3
            elif kind == 'path':
                sc += 1
    return sc


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)

    if data.get('hookEventName') != 'PostToolUse' and data.get('hook_event_name') != 'PostToolUse':
        sys.exit(0)

    if data.get('tool_name') != 'exec':
        sys.exit(0)

    tool_input = data.get('tool_input') or {}
    tool_response = data.get('tool_response') or {}
    command = tool_input.get('command', '')
    output = ''
    if isinstance(tool_response, str):
        output = tool_response
    elif isinstance(tool_response, dict):
        output = tool_response.get('output', '') or tool_response.get('stdout', '')

    if not os.path.isdir(BASE):
        sys.exit(0)

    notes = []
    for p in glob.glob(os.path.join(BASE, '**', '*.md'), recursive=True):
        if p.endswith('MOC.md'):
            continue
        notes.append(load_note(p))

    scored = [(score(n, command, output), n) for n in notes]
    scored = [(s, n) for s, n in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        sys.exit(0)

    top = scored[:TOP_K]
    print(f'memory-post-exec: {len(top)} memory note(s) matched exec context', file=sys.stderr)
    lines = [f"> [!note] Memory after exec (`{command[:60]}{'...' if len(command) > 60 else ''}`) — {len(top)} match{'es' if len(top) > 1 else ''}\n"]
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
