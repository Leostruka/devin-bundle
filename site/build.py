#!/usr/bin/env python3
"""Generate the devin-bundle Pages site (dist/) from live bundle data.

Reads: manifest.json, skills/*/SKILL.md, agents/*.md, hooks.v1.json,
.devin/adr/*.md, .devin/docs/**/*.md, CHANGELOG.md, README.md.
Emits: site/dist/index.html, style.css, app.js (stdlib only).
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import status_vocab  # noqa: E402  (shared done/terminal vocabulary,
                     # issues #405/#407)
SRC = os.path.join(ROOT, "site", "src")
DIST = os.path.join(ROOT, "site", "dist")


def read(path, base=ROOT):
    p = os.path.join(base, path)
    if not os.path.exists(p):
        return None
    return open(p, encoding="utf-8-sig").read()


def fm_and_body(text):
    """Split YAML-ish frontmatter (--- ... ---) from body."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text or "", re.S)
    if not m:
        return {}, text or ""
    fm = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line.strip())
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"')
    return fm, m.group(2)


# ---------------------------------------------------------------- markdown

def md_inline(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def md_to_html(text):
    """Small markdown subset -> HTML. mermaid fences keep raw text."""
    out, lines = [], text.split("\n")
    i, in_code, code_lang, buf = 0, False, "", []
    list_open = None

    def flush_para():
        if buf:
            out.append("<p>" + md_inline(" ".join(buf)) + "</p>")
            buf.clear()

    def close_list():
        nonlocal list_open
        if list_open:
            out.append(list_open == "ol" and "</ol>" or "</ul>")
            list_open = None

    while i < len(lines):
        line = lines[i]
        fence = re.match(r"^```(\w*)\s*$", line)
        if fence:
            if in_code:
                code = html.escape("\n".join(buf))
                if code_lang == "mermaid":
                    out.append(f'<pre class="mermaid">{code}</pre>')
                else:
                    out.append(
                        f'<pre class="codeblock"><code data-lang="{code_lang}">'
                        f"{code}</code></pre>")
                buf.clear()
                in_code = False
                code_lang = ""
            else:
                flush_para()
                close_list()
                in_code = True
                code_lang = fence.group(1)
            i += 1
            continue
        if in_code:
            buf.append(line)
            i += 1
            continue

        h = re.match(r"^(#{1,4})\s+(.*)$", line)
        if h:
            flush_para(); close_list()
            lvl = len(h.group(1))
            out.append(f"<h{lvl}>{md_inline(h.group(2).strip())}</h{lvl}>")
            i += 1
            continue
        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", line):
            flush_para(); close_list()
            out.append("<hr>")
            i += 1
            continue
        if line.strip().startswith("|") and i + 1 < len(lines) and \
                re.match(r"^\s*\|?[\s:|-]+\|\s*$", lines[i + 1]):
            flush_para(); close_list()
            heads = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in
                             lines[i].strip().strip("|").split("|")])
                i += 1
            t = "<table><thead><tr>" + "".join(
                f"<th>{md_inline(c)}</th>" for c in heads) + "</tr></thead><tbody>"
            for r in rows:
                t += "<tr>" + "".join(
                    f"<td>{md_inline(c)}</td>" for c in r) + "</tr>"
            out.append(t + "</tbody></table>")
            continue
        ul = re.match(r"^\s*[-*]\s+(.*)$", line)
        ol = re.match(r"^\s*\d+[.)]\s+(.*)$", line)
        if ul or ol:
            flush_para()
            kind = "ul" if ul else "ol"
            if list_open != kind:
                close_list()
                out.append(f"<{kind}>")
                list_open = kind
            item = (ul or ol).group(1)
            out.append(f"<li>{md_inline(item)}</li>")
            i += 1
            continue
        if not line.strip():
            flush_para(); close_list()
            i += 1
            continue
        buf.append(line.strip())
        i += 1
    flush_para(); close_list()
    return "\n".join(out)


# ---------------------------------------------------------------- sources

def collect_skills():
    skills = []
    sdir = os.path.join(ROOT, "skills")
    for name in sorted(os.listdir(sdir)):
        p = os.path.join(sdir, name, "SKILL.md")
        if not os.path.isfile(p):
            continue
        fm, body = fm_and_body(open(p, encoding="utf-8-sig").read())
        desc = fm.get("description", "")
        first_h = re.search(r"^#\s+(.*)$", body, re.M)
        skills.append({
            "name": fm.get("name", name),
            "dir": name,
            "file": f"skills/{name}/SKILL.md",
            "desc": desc,
            "title": first_h.group(1).strip() if first_h else name,
            "html": md_to_html(body),
            "lines": body.count("\n") + 1,
        })
    return skills


def collect_agents():
    agents = []
    adir = os.path.join(ROOT, "agents")
    for fn in sorted(os.listdir(adir)):
        if not fn.endswith(".md") or fn == "README.md":
            continue
        fm, body = fm_and_body(open(os.path.join(adir, fn),
                                    encoding="utf-8-sig").read())
        agents.append({
            "name": fm.get("name", fn[:-3]),
            "file": f"agents/{fn}",
            "model": fm.get("model", ""),
            "desc": fm.get("description", ""),
            "html": md_to_html(body),
        })
    return agents


def collect_docs(subdir):
    docs = []
    base = os.path.join(ROOT, ".devin", subdir)
    for dirpath, _, files in os.walk(base):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), base)
            text = open(os.path.join(dirpath, fn), encoding="utf-8-sig").read()
            h = re.search(r"^#\s+(.*)$", text, re.M)
            docs.append({
                "file": f".devin/{subdir}/{rel}".replace("\\", "/"),
                "title": h.group(1).strip() if h else fn[:-3],
                "html": md_to_html(text),
                "has_mermaid": "```mermaid" in text,
            })
    return docs


def collect_apps():
    apps = []
    base = os.path.join(ROOT, ".devin", "apps")
    if not os.path.isdir(base):
        return apps
    for d in sorted(os.listdir(base)):
        f = os.path.join(base, d, "APP.md")
        if not os.path.isfile(f):
            continue
        text = open(f, encoding="utf-8-sig").read()
        h = re.search(r"^#\s+(.*)$", text, re.M)

        def _field(name):
            m = re.search(rf"^{name}:\s*(.+?)\s*$", text, re.M | re.I)
            return m.group(1).strip() if m else ""

        apps.append({
            "name": d,
            "file": f".devin/apps/{d}/APP.md",
            "title": h.group(1).strip() if h else d,
            "intent": _field("intent"),
            "schedule": _field("schedule"),
            "done_when": _field("done-when"),
            "html": md_to_html(text),
        })
    return apps


def collect_hooks():
    raw = json.loads(read("hooks.v1.json") or "{}")
    events = []
    for ev, matchers in raw.items():
        rows = []
        for m in matchers:
            for hk in m.get("hooks", []):
                cmd = hk.get("command", "")
                script = re.search(r"scripts[/\\]([\w.-]+)", cmd)
                rows.append({
                    "matcher": m.get("matcher", "*"),
                    "script": script.group(1) if script else cmd,
                    "command": cmd,
                    "timeout": hk.get("timeout"),
                    "fail_closed": bool(hk.get("fail_closed")),
                })
        events.append({"event": ev, "hooks": rows})
    return events


def collect_scripts():
    rows = []
    for fn in sorted(os.listdir(os.path.join(ROOT, "scripts"))):
        if fn.startswith("__"):
            continue
        path = os.path.join(ROOT, "scripts", fn)
        if not os.path.isfile(path):
            continue
        first = ""
        for line in open(path, encoding="utf-8", errors="replace"):
            if line.startswith("#!") or not line.strip():
                continue
            if line.startswith(('"""', "'''")) or line.startswith("#"):
                first = line.strip().strip("#").strip('"').strip()
                if first:
                    break
        rows.append({"file": f"scripts/{fn}",
                     "doc": first[:160],
                     "lines": sum(1 for _ in open(path, encoding="utf-8",
                                                errors="replace"))})
    return rows


def _issue_items(idir):
    items = []
    for fn in sorted(os.listdir(idir)):
        if not fn.endswith(".md"):
            continue
        text = open(os.path.join(idir, fn), encoding="utf-8-sig").read()
        title = re.search(r"^#\s+(.*)$", text, re.M)
        def _field(*names):
            for name in names:
                m = re.search(
                    rf"^(?:-\s*)?\*{{0,2}}{name}\*{{0,2}}:?\*{{0,2}}"
                    rf"\s*[:=]?\s*(.+?)\s*$",
                    text, re.M | re.I)
                if m:
                    return m.group(1).strip()
            return ""
        status = _field("status").split("\u00b7")[0].split("(")[0].strip().lower()
        # shared vocabulary (#407): same done-set as roadmap-board;
        # heading match exact-line only - "## Done when" is NOT done
        done = status_vocab.is_terminal(status) or bool(re.search(
            r"^## (Answer|Done|Shipped|Landed)\s*$", text, re.M))
        items.append({
            "file": fn,
            "title": title.group(1).strip() if title else fn[:-3],
            "status": "resolved" if done else (status or "open"),
            "priority": _field("priority", "severity"),
            "answered": "## Answer" in text,
        })
    return items


def collect_issues():
    """Scan issue dirs -> grouped ledger: .devin/issues (roadmap) +
    .devin/scratch/*/issues (effort-level execution)."""
    groups = []
    macro = os.path.join(ROOT, ".devin", "issues")
    if os.path.isdir(macro):
        items = _issue_items(macro)
        if items:
            groups.append({"group": "roadmap", "count": len(items),
                           "resolved": sum(1 for i in items
                                           if i["status"] == "resolved"),
                           "items": items})
    base = os.path.join(ROOT, ".devin", "scratch")
    archived = set(status_vocab.archived_efforts(ROOT))
    if os.path.isdir(base):
        for grp in sorted(os.listdir(base)):
            if grp in archived:
                continue
            idir = os.path.join(base, grp, "issues")
            if not os.path.isdir(idir):
                continue
            items = _issue_items(idir)
            if items:
                groups.append({"group": grp, "count": len(items),
                               "resolved": sum(1 for i in items
                                               if i["status"] == "resolved"),
                               "items": items})
    return groups


def collect_github():
    """Fetch open GitHub issues + PRs via the public API (repo is public).

    Build must never fail on network: any error -> empty list, the group
    just does not render. 10s timeout, no auth needed.
    """
    url = ("https://api.github.com/repos/Leostruka/devin-bundle/issues"
           "?state=open&per_page=100")
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "devin-bundle-atlas-build",
                          "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = json.loads(r.read().decode("utf-8"))
    except Exception:
        return []
    _PRI = {"critical": "P1", "high": "P2", "medium": "P3"}
    issues, prs = [], []
    for it in raw:
        labels = [lb["name"] for lb in it.get("labels", [])]
        pri = next((_PRI[lb.split(":", 1)[1]]
                    for lb in labels
                    if lb.startswith("priority:")
                    and lb.split(":", 1)[1] in _PRI), "")
        row = {"file": f"#{it['number']}", "title": it["title"],
               "priority": pri, "status": "open",
               "answered": bool(it.get("comments")),
               "url": it.get("html_url", "")}
        (prs if "pull_request" in it else issues).append(row)
    groups = []
    if issues:
        groups.append({"group": "github issues (open)",
                       "count": len(issues), "resolved": 0,
                       "items": issues})
    if prs:
        groups.append({"group": "github prs (open)",
                       "count": len(prs), "resolved": 0,
                       "items": prs})
    return groups


def git_sha():
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha[:7]
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=10).stdout.strip() or None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def collect_changelog():
    text = read("CHANGELOG.md") or ""
    rels = []
    for m in re.finditer(
            r"^## \[?([^\]\s]+)\]?(?:\s*-\s*(\d{4}-\d{2}-\d{2}))?\s*$",
            text, re.M):
        start = m.end()
        nxt = text.find("\n## ", start)
        body = text[start:nxt if nxt > 0 else len(text)]
        # count top-level bullets - entries aren't required to be bold
        feats = len(re.findall(r"^- ", body, re.M))
        rels.append({"version": m.group(1), "date": m.group(2) or "",
                     "entries": feats,
                     "html": md_to_html(body)[:6000]})
        if len(rels) >= 12:
            break
    return rels


def main():
    manifest = json.loads(read("manifest.json"))
    skills = collect_skills()
    agents = collect_agents()
    scripts = collect_scripts()
    adrs = collect_docs("adr")
    docs = collect_docs("docs")
    apps = collect_apps()
    data = {
        "version": manifest.get("version"),
        "generated_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"),
        "git_sha": git_sha(),
        "counts": {
            "skills": len(skills),
            "agents": len(agents),
            "scripts": len(scripts),
            "adrs": len(adrs),
            "docs": len(docs),
            "apps": len(apps),
        },
        "skills": skills,
        "agents": agents,
        "hooks": collect_hooks(),
        "scripts": scripts,
        "adrs": adrs,
        "docs": docs,
        "apps": apps,
        "changelog": collect_changelog(),
        "issues": collect_github() + collect_issues(),
        "readme_html": md_to_html(read("README.md") or "")[:8000],
    }
    if os.path.isdir(DIST):
        for entry in os.listdir(DIST):
            p = os.path.join(DIST, entry)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(DIST, exist_ok=True)

    # Lazy HTML: move big rendered bodies out of window.DATA into
    # per-item files fetched on demand (skills ~1.3MB, docs ~240KB).
    os.makedirs(os.path.join(DIST, "data"), exist_ok=True)

    def _lazy(items, prefix, key):
        for i, it in enumerate(items):
            html = it.pop("html", None)
            if html is None:
                continue
            ref = f"{prefix}-{it.get(key, i)}"
            with open(os.path.join(DIST, "data", ref + ".html"),
                      "w", encoding="utf-8") as fh:
                fh.write(html)
            it["html_ref"] = ref

    _lazy(skills, "skill", "dir")
    _lazy(agents, "agent", "name")
    _lazy(adrs, "adr", None)
    _lazy(docs, "doc", None)
    _lazy(apps, "app", "name")
    _lazy(data["changelog"], "rel", "version")

    # Raw markdown copies alongside the lazy HTML (reader "raw" link).
    rawdir = os.path.join(DIST, "raw")
    os.makedirs(rawdir, exist_ok=True)
    for items in (adrs, docs, apps, skills, agents):
        for it in items:
            ref, f = it.get("html_ref"), it.get("file", "")
            src = os.path.join(ROOT, f) if f.endswith(".md") else None
            if ref and src and os.path.isfile(src):
                shutil.copy(src, os.path.join(rawdir, ref + ".md"))
                it["raw_ref"] = ref + ".md"
    for s in scripts:
        src = os.path.join(ROOT, s["file"])
        if s["file"].endswith(".py") and os.path.isfile(src):
            ref = "script-" + s["file"].rsplit("/", 1)[-1][:-3]
            shutil.copy(src, os.path.join(rawdir, ref + ".py"))
            s["raw_ref"] = ref + ".py"

    tpl = read("index.html", SRC)
    tpl = (tpl
           .replace("__N_SKILLS__", str(len(skills)))
           .replace("__N_AGENTS__", str(len(agents))))
    for asset in ("style.css", "app.js"):
        shutil.copy(os.path.join(SRC, asset), os.path.join(DIST, asset))
    open(os.path.join(DIST, "index.html"), "w",
         encoding="utf-8").write(
        tpl.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False)
                    .replace("<", "\\u003c")))
    print(f"dist built: {data['counts']} -> {DIST}")


if __name__ == "__main__":
    main()
