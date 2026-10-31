#!/usr/bin/env python3
"""skill-picker — lexical manifest hints on UserPromptSubmit (JEV-2).

stdin: hook payload {hook_event_name, prompt, session_id}.
Matches the prompt against manifest.json skill name/purpose and emits
at most 3 candidates via hookSpecificOutput.additionalContext. Output
is a read hint only — skills are never invoked, no laya call, no
network, stdlib only. Silent exit 0 on missing/malformed manifest,
non-prompt events, or no lexical match.
"""
import json
import os
import re
import sys

MAX_HINTS = 3
MAX_MANIFEST_BYTES = 2_000_000
MAX_SKILLS = 2000
MAX_PROMPT_CHARS = 8000
SLUG = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\Z")
TOKEN = re.compile(r"[a-z0-9]+")
STOP = frozenset(
    "the and for are with this that from you your have has was were "
    "will would can could should not all any each into about over "
    "use when then them they its our out but been being".split())


def _devin_home():
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return os.path.join(appdata, "devin")
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        return os.path.join(xdg, "devin")
    return os.path.join(os.path.expanduser("~"), ".config", "devin")


def _manifest_path():
    cands = []
    env = os.environ.get("DEVIN_PROJECT_DIR")
    if env:
        cands.append(os.path.join(env, "manifest.json"))
    cands.append(os.path.join(os.getcwd(), "manifest.json"))
    cands.append(os.path.join(_devin_home(), "manifest.json"))
    cands.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "manifest.json"))
    for c in cands:
        if os.path.isfile(c):
            return os.path.normpath(c)
    return None


def _tokens(text):
    return [t for t in TOKEN.findall(text.lower())
            if len(t) >= 3 and t not in STOP]


def pick_skills(prompt, skills, max_hints=MAX_HINTS):
    """[(name, score)] by (-score, name); malformed entries skipped.

    Only canonical slug names are eligible — anything else could carry
    injected text into additionalContext. Names deduped; the cap is
    absolute: callers cannot exceed MAX_HINTS.
    """
    try:
        cap = int(max_hints)
    except (TypeError, ValueError):
        cap = MAX_HINTS
    cap = max(0, min(cap, MAX_HINTS))
    if cap == 0:
        return []
    ptok = set(_tokens(prompt if isinstance(prompt, str) else ""))
    if not ptok:
        return []
    scored = []
    seen = set()
    for s in (skills if isinstance(skills, list) else [])[:MAX_SKILLS]:
        if not isinstance(s, dict):
            continue
        name = s.get("name")
        if not isinstance(name, str) or not SLUG.fullmatch(name) \
                or name in seen:
            continue
        seen.add(name)
        purpose = s.get("purpose")
        if not isinstance(purpose, str):
            purpose = ""
        name_tokens = set(_tokens(name.replace("-", " ").replace("_", " ")))
        purpose_tokens = set(_tokens(purpose))
        score = 2 * len(ptok & name_tokens) + len(ptok & purpose_tokens)
        if score > 0:
            scored.append((name, score))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return scored[:cap]


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError, UnicodeError):
        sys.exit(0)
    if not isinstance(payload, dict) \
            or payload.get("hook_event_name") != "UserPromptSubmit":
        sys.exit(0)
    prompt = (payload.get("prompt") or payload.get("user_prompt")
              or payload.get("text") or "")
    if not isinstance(prompt, str) or not prompt.strip():
        sys.exit(0)
    prompt = prompt[:MAX_PROMPT_CHARS]
    path = _manifest_path()
    if not path:
        sys.exit(0)
    try:
        if os.path.getsize(path) > MAX_MANIFEST_BYTES:
            sys.exit(0)
        with open(path, "rb") as f:
            data = json.loads(f.read().decode("utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        sys.exit(0)
    skills = data.get("skills") if isinstance(data, dict) else None
    if not isinstance(skills, list):
        sys.exit(0)
    hits = pick_skills(prompt, skills)
    if not hits:
        sys.exit(0)
    names = ", ".join(n for n, _ in hits)
    print(json.dumps({"hookSpecificOutput": {"additionalContext":
                      "SKILL-HINTS (lexical match — read before use; "
                      "never auto-invoked): " + names}}))
    sys.exit(0)


if __name__ == "__main__":
    main()
