#!/usr/bin/env python3
"""PostToolUse(write|edit) hook: warn on AI-UI slop patterns at write
time (M2_05). ~12 cheap inline rules - deliberately self-contained
(no extension import); the full 46-rule static set lives in
extensions/design-intelligence/design_lint.py.

Warn-only: emits hookSpecificOutput.additionalContext when a pattern
fires; silent exit 0 otherwise. Never blocks.
"""
import json
import os
import re
import sys

UI_EXTS = {'.html', '.htm', '.css', '.tsx', '.jsx', '.vue', '.svelte'}
SKIP_PARTS = {'node_modules', 'vendor', 'dist', 'build', '.git',
              '__pycache__', 'site-packages', 'data', 'fixtures',
              'extensions'}
MAX_BYTES = 400_000

PURPLE_HEX = re.compile(
    r"#(?:8b5cf6|a855f7|7c3aed|9333ea|6366f1|6d28d9|5b21b6)\b", re.I)
CYAN_HEX = re.compile(r"#(?:06b6d4|22d3ee|0ea5e9|3b82f6|60a5fa)\b", re.I)
BUZZWORDS = ("delve", "leverage", "unlock", "elevate", "seamless",
             "cutting-edge", "revolutionary", "empower", "supercharge",
             "unleash", "game-changer")


def _line_of(text, pos):
    return text[:pos].count("\n") + 1


def lint(path, text):
    findings = []
    low = text.lower()

    def add(rule, pos, ev):
        findings.append(f"{rule}: {os.path.basename(path)}:"
                        f"{_line_of(text, pos)} ({ev})")

    for m in re.finditer(r"linear-gradient\([^)]*\)", low):
        seg = m.group(0)
        if PURPLE_HEX.search(seg) and CYAN_HEX.search(seg):
            add("ai-color-palette", m.start(),
                "purple+cyan gradient - the default AI palette")
            break
    for m in re.finditer(
            r"background[^;{}]*gradient[^;{}]*;[^;{}]*"
            r"-webkit-text-fill-color\s*:\s*transparent|"
            r"background-clip\s*:\s*text", low, re.S):
        add("gradient-text", m.start(), "gradient clipped to text")
        break
    for m in re.finditer(
            r"border-(?:left|right)\s*:\s*(\d+)px\s+solid", low):
        if int(m.group(1)) >= 4:
            add("side-tab", m.start(), f"{m.group(1)}px accent border")
            break
    for m in re.finditer(r"font-family\s*:([^;{}]+)", low):
        fams = m.group(1)
        for f in ("inter", "roboto", "geist", "fraunces", "poppins"):
            if f in fams:
                add("overused-font", m.start(),
                    f"'{f.strip()}' is a convergence font")
                break
        else:
            continue
        break
    for m in re.finditer(
            r"border-radius\s*:[^;{}]*;\s*[^}]*border[^;{}]*"
            r"(blue|purple|cyan|violet|indigo|#[0-9a-f]{3,8})",
            low, re.S):
        add("border-accent-on-rounded", m.start(),
            "colored border on rounded element")
        break
    if text.count("\u2014") > 5:
        add("em-dash-overuse", low.find("\u2014"),
            f"{text.count(chr(0x2014))} em-dashes")
    for m in re.finditer(
            r"<marquee|animate-marquee|animation[^;}]*marquee", low):
        add("marquee", m.start(), "marquee/ticker")
        break
    for m in re.finditer(
            r"class=\"[^\"]*(rounded-full|pill|badge|chip)[^\"]*\"[^>]*>"
            r"[^<]{1,80}</[a-z]+>\s*<h1", text, re.I):
        add("hero-eyebrow-chip", m.start(), "eyebrow chip above h1")
        break
    for w in BUZZWORDS:
        m = re.search(r"\b" + re.escape(w) + r"\b", low)
        if m:
            add("marketing-buzzword", m.start(), f"'{w}'")
            break
    heads = [int(x) for x in re.findall(r"<h([1-6])[\s>]", low)]
    for a, b in zip(heads, heads[1:]):
        if b - a > 1:
            add("skipped-heading", 0, f"h{a} -> h{b}")
            break
    for m in re.finditer(
            r"box-shadow\s*:\s*(\d+)px\s+(\d+)px\s+0(?:px)?\b", low):
        if int(m.group(1)) >= 3 or int(m.group(2)) >= 3:
            add("hard-offset-shadow", m.start(),
                f"{m.group(1)}px {m.group(2)}px 0 blur")
            break
    m = re.search(r"animate-(ping|pulse)", low)
    if m and "rounded-full" in low:
        add("pulsing-dot", m.start(), "animate-ping/pulse dot")
    return findings


def main():
    for stream in (sys.stdin, sys.stdout):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    try:
        payload = json.loads(sys.stdin.read() or '{}')
    except Exception:
        return
    path = (payload.get('tool_input') or {}).get('file_path') or ''
    if not path:
        return
    ext = os.path.splitext(path)[1].lower()
    parts = set(os.path.normpath(path).lower().split(os.sep))
    if ext not in UI_EXTS or parts & SKIP_PARTS:
        return
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return
        with open(path, encoding='utf-8', errors='replace') as f:
            text = f.read()
    except OSError:
        return
    findings = lint(path, text)
    if not findings:
        return
    msg = ('[DESIGN-LINT] ' + ' ; '.join(findings[:4]) +
           '. Deterministic pattern warnings (impeccable registry) - '
           'waive only via user-stated exemption; full scan: '
           'extensions/design-intelligence/design_lint.py')
    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'PostToolUse',
            'additionalContext': msg,
        }
    }))


if __name__ == '__main__':
    main()
