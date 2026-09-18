#!/usr/bin/env python3
"""structured-knowledge-extraction — deterministic knowledge graph extraction.

Conceptually inspired by Hyper-Extract (Apache-2.0). No external code, prompts,
or templates are copied from Hyper-Extract. The core implementation uses only the
Python standard library.

Usage:
    python extract.py extract <source> [project] [--write] [--approve]
    python extract.py merge <source> [project] [--write] [--approve]
    python extract.py search <query> [project]
    python extract.py plan [project] [--write] [--approve]
"""
import argparse
import copy
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
NOTE_SUBDIR = Path("notes/structured-knowledge-extraction")
MAX_QUOTE = 200

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
CODE_RE = re.compile(r"`([^`]+)`")
LINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)\s]+)(?:\s+[^)]*)?\)")
WIKI_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
URL_RE = re.compile(r"https?://[^\s<>\[\]\"\'`,;()]+")
ARXIV_RE = re.compile(r"arXiv:(\d{4}\.\d{4,5})")
SOURCE_RE = re.compile(r"(?:^|\s)(?:source|citation):\s*([^\s\n,]+)", re.IGNORECASE)


def err(msg):
    sys.stderr.write(msg + "\n")


def emit_json(data):
    text = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False)
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))


def emit_text(text):
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))


def project_label(project):
    try:
        rel = Path(os.path.relpath(project.resolve(), Path.cwd())).as_posix()
        if rel.startswith(".."):
            return project.name
        return rel
    except ValueError:
        return project.name


def locate_project(project_str, require_devin=False):
    p = Path(project_str).expanduser()
    if p.name == ".devin" and p.is_dir():
        if p.is_symlink():
            raise ValueError(f"symlinked .devin not allowed: {project_str}")
        return p.parent.resolve(), p.resolve()
    devin = p / ".devin"
    if devin.is_dir():
        if devin.is_symlink():
            raise ValueError(f"symlinked .devin not allowed: {project_str}")
        return p.resolve(), devin.resolve()
    if require_devin:
        raise FileNotFoundError(f"no .devin directory in {project_str}")
    return p.resolve(), devin.resolve()


def resolve_source(source_str, project):
    project = project.resolve()
    orig = Path(source_str).expanduser()
    if not orig.is_absolute():
        orig = project / orig
    if orig.is_symlink():
        raise ValueError(f"symlink not allowed: {source_str}")
    src = orig.resolve()
    if src.is_symlink():
        raise ValueError(f"symlink not allowed: {source_str}")
    if not src.is_file():
        raise FileNotFoundError(f"source not found: {source_str}")
    try:
        rel = src.relative_to(project).as_posix()
    except ValueError:
        raise ValueError(f"source outside project: {source_str}")
    return src, rel


def clean_markdown(text):
    text = text.strip()
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*+([^*]+)\*+", r"\1", text)
    text = re.sub(r"_+([^_]+)_+", r"\1", text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", text)
    return text.strip()


def canonical_name(name):
    """Return a lowercase, whitespace-collapsed form that preserves punctuation.

    This canonicalization is used to compute collision-safe entity IDs and to
    detect name mismatches without stripping meaningful characters.
    """
    text = re.sub(r"\s+", " ", name).strip().lower()
    return text


def normalize_text(text):
    """Compatibility alias for canonical_name."""
    return canonical_name(text)


def entity_id_for(name):
    canonical = canonical_name(name)
    if not canonical:
        # Fallback to a hash of the raw bytes for truly empty/whitespace names.
        return hashlib.sha256(name.encode("utf-8")).hexdigest()
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def relation_id(source_id, target_id, kind):
    payload = f"{source_id}|{target_id}|{kind}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def content_timestamp(source_sha256):
    """Return a content-deterministic UTC ISO 8601 timestamp.

    The first 8 hex chars of the source SHA-256 are interpreted as a Unix
    timestamp. This keeps the value stable for identical content while avoiding
    dependence on file mtime.
    """
    seconds = int(source_sha256[:8], 16)
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(seconds))


def make_quote(line):
    return line.strip()[:MAX_QUOTE]


def in_skip(pos, spans):
    return any(start <= pos < end for start, end in spans)


def add_entity(entities, conflicts, entity_type, name, source, line, quote_line):
    eid = entity_id_for(name)
    prov = {"source": source, "line": line, "quote": make_quote(quote_line)}
    if eid in entities:
        existing = entities[eid]
        if existing["type"] != entity_type:
            conflicts.append({
                "kind": "entity_type_mismatch",
                "id": eid,
                "existing_type": existing["type"],
                "new_type": entity_type,
                "existing_name": existing["name"],
                "new_name": name,
                "provenance": [prov],
            })
            return eid
        if normalize_text(existing["name"]) != normalize_text(name):
            conflicts.append({
                "kind": "entity_name_mismatch",
                "id": eid,
                "existing_name": existing["name"],
                "new_name": name,
                "provenance": [prov],
            })
            return eid
        if prov not in existing["provenance"]:
            existing["provenance"].append(prov)
            existing["provenance"].sort(key=lambda p: (p["source"], p["line"], p["quote"]))
        return eid
    entities[eid] = {
        "id": eid,
        "type": entity_type,
        "name": name,
        "provenance": [prov],
    }
    return eid


def add_relation(relations, kind, source_id, target_id, source, line, quote_line):
    rid = relation_id(source_id, target_id, kind)
    prov = {"source": source, "line": line, "quote": make_quote(quote_line)}
    if rid in relations:
        existing = relations[rid]
        if prov not in existing["provenance"]:
            existing["provenance"].append(prov)
            existing["provenance"].sort(key=lambda p: (p["source"], p["line"], p["quote"]))
    else:
        relations[rid] = {
            "id": rid,
            "source": source_id,
            "target": target_id,
            "kind": kind,
            "provenance": [prov],
        }


def parse_headings(lines):
    headings = []
    for i, line in enumerate(lines, start=1):
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            name = clean_markdown(m.group(2).strip())
            headings.append((i, level, name))
    return headings


def parse_markdown(text, rel_source):
    entities = {}
    relations = {}
    conflicts = []
    lines = text.split("\n")
    headings = parse_headings(lines)
    heading_iter = iter(headings)
    next_heading = next(heading_iter, None)
    stack = []
    heading_for_line = {}

    for i, line in enumerate(lines, start=1):
        if next_heading and next_heading[0] == i:
            line_no, level, name = next_heading
            while stack and stack[-1][1] >= level:
                stack.pop()
            eid = add_entity(entities, conflicts, "heading", name, rel_source, line_no, line)
            if stack:
                add_relation(relations, "contains", stack[-1][3], eid, rel_source, line_no, line)
            stack.append((line_no, level, name, eid))
            next_heading = next(heading_iter, None)
        if stack:
            heading_for_line[i] = stack[-1][3]

    for i, line in enumerate(lines, start=1):
        current = heading_for_line.get(i)
        skip = []

        # 1. Code spans have the highest priority: nothing else is parsed inside them.
        for m in CODE_RE.finditer(line):
            skip.append((m.start(), m.end()))
            code = m.group(1).strip()
            if code:
                eid = add_entity(entities, conflicts, "code", code, rel_source, i, line)
                if current:
                    add_relation(relations, "contains", current, eid, rel_source, i, line)

        # 2. Markdown links: extract the URL and skip the whole token for downstream regexes.
        for m in LINK_RE.finditer(line):
            if in_skip(m.start(), skip):
                continue
            skip.append((m.start(), m.end()))
            skip.append((m.start(2), m.end(2)))
            url = m.group(2).split()[0]
            if url.startswith("<") and url.endswith(">"):
                url = url[1:-1]
            if url:
                eid = add_entity(entities, conflicts, "url", url, rel_source, i, line)
                if current:
                    add_relation(relations, "contains", current, eid, rel_source, i, line)

        # 3. Wikilinks: extract the target and skip the whole token.
        for m in WIKI_RE.finditer(line):
            if in_skip(m.start(), skip):
                continue
            skip.append((m.start(), m.end()))
            target = m.group(1).strip()
            eid = add_entity(entities, conflicts, "wikilink", target, rel_source, i, line)
            if current:
                add_relation(relations, "contains", current, eid, rel_source, i, line)

        # 4. Explicit source/citation references take precedence over bare arXiv/URL regexes.
        for m in SOURCE_RE.finditer(line):
            if in_skip(m.start(), skip):
                continue
            skip.append((m.start(), m.end()))
            ref = m.group(1).rstrip(".,;")
            if not ref:
                continue
            # Distinguish a URL or arXiv reference from a generic citation so that
            # the same token is not extracted twice with conflicting types.
            lower = ref.lower()
            if lower.startswith(("http://", "https://")):
                entity_type = "url"
            elif lower.startswith("arxiv:"):
                entity_type = "citation"
            else:
                entity_type = "citation"
            eid = add_entity(entities, conflicts, entity_type, ref, rel_source, i, line)
            if current:
                add_relation(relations, "cites" if entity_type == "citation" else "contains", current, eid, rel_source, i, line)

        # 5. Bare arXiv citations.
        for m in ARXIV_RE.finditer(line):
            if in_skip(m.start(), skip):
                continue
            skip.append((m.start(), m.end()))
            cite = f"arXiv:{m.group(1)}"
            eid = add_entity(entities, conflicts, "citation", cite, rel_source, i, line)
            if current:
                add_relation(relations, "cites", current, eid, rel_source, i, line)

        # 6. Bare URLs (skip anything already captured by a link, wiki, source, or arXiv).
        for m in URL_RE.finditer(line):
            if in_skip(m.start(), skip):
                continue
            skip.append((m.start(), m.end()))
            url = m.group(0).rstrip(".,;")
            eid = add_entity(entities, conflicts, "url", url, rel_source, i, line)
            if current:
                add_relation(relations, "contains", current, eid, rel_source, i, line)

    return entities, relations, conflicts


def build_extract_data(rel_source, source_text, entities, relations, conflicts):
    source_sha256 = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    extracted_at = content_timestamp(source_sha256)
    return {
        "schema_version": SCHEMA_VERSION,
        "sources": {
            rel_source: {
                "sha256": source_sha256,
                "extracted_at": extracted_at,
            },
        },
        "entities": {k: entities[k] for k in sorted(entities)},
        "relations": sorted(relations.values(), key=lambda r: r["id"]),
        "conflicts": sorted(
            conflicts,
            key=lambda c: (c.get("kind", ""), c.get("id", ""), c.get("new_type", ""), c.get("new_name", "")),
        ),
    }


def _sources_as_dict(data):
    sources = data.get("sources", {})
    if isinstance(sources, dict):
        return sources
    if isinstance(sources, list):
        return {s: {} for s in sources}
    return {}


def render_markdown(data, project_str):
    lines = [
        "# Structured knowledge extraction",
        "",
        f"Project: `{project_str}`",
        f"Schema version: {data.get('schema_version', SCHEMA_VERSION)}",
    ]
    sources = _sources_as_dict(data)
    if sources:
        lines.extend(["", "## Sources", ""])
        lines.append("| source | sha256 | extracted at |")
        lines.append("|---|---|---|")
        for src in sorted(sources):
            meta = sources[src]
            sha = meta.get("sha256", "")[:32] + "..." if meta.get("sha256") else ""
            lines.append(f"| `{src}` | `{sha}` | {meta.get('extracted_at', '')} |")
    lines.extend(["", "## Entities", ""])
    entities = data.get("entities", {})
    if entities:
        lines.append("| id | type | name | occurrences |")
        lines.append("|---|---|---|---|")
        for eid in sorted(entities):
            ent = entities[eid]
            name = ent.get("name", "").replace("|", "\\|")[:80]
            lines.append(
                f"| `{eid}` | {ent.get('type', '')} | {name} | {len(ent.get('provenance', []))} |"
            )
    else:
        lines.append("_No entities extracted._")
    lines.extend(["", "## Relations", ""])
    rels = data.get("relations", [])
    if rels:
        lines.append("| id | source | target | kind | occurrences |")
        lines.append("|---|---|---|---|---|")
        for rel in sorted(rels, key=lambda r: r.get("id", "")):
            lines.append(
                f"| `{rel.get('id', '')}` | `{rel.get('source', '')}` | `{rel.get('target', '')}` | "
                f"{rel.get('kind', '')} | {len(rel.get('provenance', []))} |"
            )
    else:
        lines.append("_No relations extracted._")
    if data.get("conflicts"):
        lines.extend(["", "## Conflicts", ""])
        for c in data["conflicts"]:
            lines.append(f"- `{c.get('kind')}` for entity `{c.get('id')}`")
    lines.extend([
        "",
        "## Source and license attribution",
        "",
        "This extraction was produced by `structured-knowledge-extraction`.",
        "It is conceptually inspired by Hyper-Extract (Apache-2.0).",
        "- Hyper-Extract: https://github.com/yifanfeng97/Hyper-Extract",
        "- License: https://github.com/yifanfeng97/Hyper-Extract/blob/main/LICENSE",
    ])
    return "\n".join(lines) + "\n"


def write_output(project, devin, data):
    out = (devin / NOTE_SUBDIR).resolve()
    try:
        out.relative_to(devin.resolve())
    except ValueError:
        raise RuntimeError("output path escapes .devin")
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "knowledge.json"
    md_path = out / "knowledge.md"
    json_text = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    json_path.write_text(json_text, encoding="utf-8", newline="\n")
    md_path.write_text(render_markdown(data, project_label(project)), encoding="utf-8", newline="\n")


def empty_kb():
    return {
        "schema_version": SCHEMA_VERSION,
        "sources": {},
        "entities": {},
        "relations": [],
        "conflicts": [],
    }


def load_knowledge(devin):
    path = (devin / NOTE_SUBDIR / "knowledge.json").resolve()
    if not path.is_file():
        return None
    try:
        path.relative_to(devin.resolve())
    except ValueError:
        raise RuntimeError("knowledge path escapes .devin")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _ensure_sources_dict(result):
    """Normalize legacy `sources` formats (list or top-level keys) to a dict."""
    if not isinstance(result.get("sources"), dict):
        old = result.get("sources", [])
        if isinstance(old, str):
            result["sources"] = {old: {}}
        elif isinstance(old, list):
            result["sources"] = {s: {} for s in old}
        else:
            result["sources"] = {}

    # Migrate single-source top-level metadata from older extractions.
    old_source = result.pop("source", "")
    old_sha = result.pop("source_sha256", "")
    old_ts = result.pop("extracted_at", "")
    if old_source:
        result["sources"].setdefault(old_source, {})
        if old_sha:
            result["sources"][old_source]["sha256"] = old_sha
        if old_ts:
            result["sources"][old_source]["extracted_at"] = old_ts

    return result["sources"]


def merge_data(existing, new):
    result = copy.deepcopy(existing)
    result.setdefault("schema_version", SCHEMA_VERSION)
    result.setdefault("sources", {})
    result.setdefault("entities", {})
    result.setdefault("relations", [])
    result.setdefault("conflicts", [])

    sources = _ensure_sources_dict(result)
    new_sources = _ensure_sources_dict(new)

    for src in sorted(new_sources):
        meta = new_sources[src]
        if src not in sources:
            sources[src] = copy.deepcopy(meta)
        else:
            existing_meta = sources[src]
            if meta.get("sha256") and meta["sha256"] != existing_meta.get("sha256"):
                # Content for this source has changed: report it as a conflict.
                result["conflicts"].append({
                    "kind": "source_changed",
                    "id": src,
                    "source": src,
                    "existing_sha256": existing_meta.get("sha256", ""),
                    "new_sha256": meta["sha256"],
                    "provenance": meta.get("provenance", []),
                })
                existing_meta["sha256"] = meta["sha256"]
                existing_meta["extracted_at"] = meta.get("extracted_at", "")
            else:
                existing_meta.setdefault("sha256", meta.get("sha256", ""))
                existing_meta.setdefault("extracted_at", meta.get("extracted_at", ""))

    for eid in sorted(new.get("entities", {})):
        ent = new["entities"][eid]
        if eid not in result["entities"]:
            result["entities"][eid] = copy.deepcopy(ent)
            continue
        existing_ent = result["entities"][eid]
        if existing_ent["type"] != ent["type"]:
            result["conflicts"].append({
                "kind": "entity_type_mismatch",
                "id": eid,
                "existing_type": existing_ent["type"],
                "new_type": ent["type"],
                "existing_name": existing_ent["name"],
                "new_name": ent["name"],
                "provenance": ent.get("provenance", []),
            })
            continue
        if canonical_name(existing_ent["name"]) != canonical_name(ent["name"]):
            result["conflicts"].append({
                "kind": "entity_name_mismatch",
                "id": eid,
                "existing_name": existing_ent["name"],
                "new_name": ent["name"],
                "provenance": ent.get("provenance", []),
            })
            continue
        for prov in ent.get("provenance", []):
            if prov not in existing_ent["provenance"]:
                existing_ent["provenance"].append(prov)
        existing_ent["provenance"].sort(key=lambda p: (p["source"], p["line"], p["quote"]))

    existing_rels = {r["id"]: r for r in result["relations"]}
    for rel in new.get("relations", []):
        rid = rel["id"]
        if rid not in existing_rels:
            existing_rels[rid] = copy.deepcopy(rel)
            result["relations"].append(existing_rels[rid])
        else:
            er = existing_rels[rid]
            for prov in rel.get("provenance", []):
                if prov not in er["provenance"]:
                    er["provenance"].append(prov)
            er["provenance"].sort(key=lambda p: (p["source"], p["line"], p["quote"]))
    result["relations"].sort(key=lambda r: r["id"])

    for c in new.get("conflicts", []):
        key = (c.get("kind"), c.get("id"), c.get("new_name"), c.get("new_type"))
        if not any(
            (x.get("kind"), x.get("id"), x.get("new_name"), x.get("new_type")) == key
            for x in result["conflicts"]
        ):
            result["conflicts"].append(copy.deepcopy(c))
    result["conflicts"].sort(
        key=lambda c: (c.get("kind", ""), c.get("id", ""), c.get("new_name", ""), c.get("new_type", ""))
    )

    return result


def lexical_search(data, query):
    try:
        pat = re.compile(re.escape(query), re.IGNORECASE)
    except re.error:
        pat = re.compile(re.escape(re.escape(query)), re.IGNORECASE)
    results = []

    for eid, ent in data.get("entities", {}).items():
        score = 0
        snippets = []
        for text in (ent.get("id", ""), ent.get("type", ""), ent.get("name", "")):
            matches = list(pat.finditer(text))
            score += len(matches)
            if matches:
                snippets.append(text[:120])
        for prov in ent.get("provenance", []):
            text = f"{prov.get('source', '')} {prov.get('quote', '')}"
            matches = list(pat.finditer(text))
            score += len(matches)
            if matches:
                snippets.append(prov.get("quote", "")[:120])
        if score:
            results.append({
                "kind": "entity",
                "id": eid,
                "name": ent.get("name", ""),
                "type": ent.get("type", ""),
                "score": score,
                "snippets": snippets[:3],
            })

    for rel in data.get("relations", []):
        score = 0
        snippets = []
        for text in (rel.get("id", ""), rel.get("kind", "")):
            matches = list(pat.finditer(text))
            score += len(matches)
            if matches:
                snippets.append(text[:120])
        for prov in rel.get("provenance", []):
            text = f"{prov.get('source', '')} {prov.get('quote', '')}"
            matches = list(pat.finditer(text))
            score += len(matches)
            if matches:
                snippets.append(prov.get("quote", "")[:120])
        if score:
            results.append({
                "kind": "relation",
                "id": rel.get("id", ""),
                "source": rel.get("source", ""),
                "target": rel.get("target", ""),
                "kind": rel.get("kind", ""),
                "score": score,
                "snippets": snippets[:3],
            })

    results.sort(key=lambda r: (-r["score"], r["id"]))
    return results


def render_plan():
    return """# structured-knowledge-extraction integration plan

This plan describes how to evaluate optional integrations without making them dependencies of the core skill.

## Hyper-Extract (Apache-2.0)

- Repository: https://github.com/yifanfeng97/Hyper-Extract
- License: https://github.com/yifanfeng97/Hyper-Extract/blob/main/LICENSE
- README: https://github.com/yifanfeng97/Hyper-Extract/blob/main/README.md
- pyproject: https://github.com/yifanfeng97/Hyper-Extract/blob/main/pyproject.toml

Evaluation steps:
1. Create an isolated virtual environment.
2. Install `hyper-extract` and run `he --help`.
3. Extract the same fixture and compare schema, entity count, and provenance.
4. Measure dependency footprint (FAISS, LangChain, Pydantic providers, python-dotenv) and Python 3.11+ requirement.
5. Only adopt if benefit exceeds the context-window and maintenance cost.

## Semantic search / embeddings

- Keep the lexical baseline as the default path (no API key).
- If evaluating embeddings, prefer local stdlib-free or local-first options first and audit context cost.
- Never require an API key for the core skill to function.

## MCP

- Audit tool definition count with `mcp-context-audit` before enabling any MCP server.
- Keep credentials in a local ignored config (e.g., `.devin/mcp_config.local.json`) and never commit unmasked values.
- Integration should be opt-in, not installed by default.

## Attribution

`structured-knowledge-extraction` is conceptually inspired by Hyper-Extract. No code, prompts, or templates are copied from Hyper-Extract. The core implementation uses only the Python standard library.
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic structured knowledge extraction")
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract", help="extract knowledge from a Markdown/text source")
    p_extract.add_argument("source")
    p_extract.add_argument("project", nargs="?", default=".")
    p_extract.add_argument("--write", "-w", action="store_true")
    p_extract.add_argument("--approve", "-a", action="store_true")

    p_merge = sub.add_parser("merge", help="merge extraction into existing knowledge base")
    p_merge.add_argument("source")
    p_merge.add_argument("project", nargs="?", default=".")
    p_merge.add_argument("--write", "-w", action="store_true")
    p_merge.add_argument("--approve", "-a", action="store_true")

    p_search = sub.add_parser("search", help="lexical search over knowledge base")
    p_search.add_argument("query")
    p_search.add_argument("project", nargs="?", default=".")

    p_plan = sub.add_parser("plan", help="generate integration guidance note")
    p_plan.add_argument("project", nargs="?", default=".")
    p_plan.add_argument("--write", "-w", action="store_true")
    p_plan.add_argument("--approve", "-a", action="store_true")

    args = parser.parse_args(argv)

    try:
        if args.command == "extract":
            project, devin = locate_project(args.project, require_devin=args.write)
            source, rel = resolve_source(args.source, project)
            if args.write and not args.approve:
                err("extract --write requires --approve")
                return 2
            text = source.read_text(encoding="utf-8", newline="")
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            entities, relations, conflicts = parse_markdown(text, rel)
            data = build_extract_data(rel, text, entities, relations, conflicts)
            if args.write:
                write_output(project, devin, data)
            emit_json(data)

        elif args.command == "merge":
            project, devin = locate_project(args.project, require_devin=args.write)
            source, rel = resolve_source(args.source, project)
            if args.write and not args.approve:
                err("merge --write requires --approve")
                return 2
            text = source.read_text(encoding="utf-8", newline="")
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            entities, relations, conflicts = parse_markdown(text, rel)
            new = build_extract_data(rel, text, entities, relations, conflicts)
            existing = load_knowledge(devin) or empty_kb()
            result = merge_data(existing, new)
            if args.write:
                write_output(project, devin, result)
            emit_json(result)

        elif args.command == "search":
            project, devin = locate_project(args.project)
            data = load_knowledge(devin) or empty_kb()
            results = lexical_search(data, args.query)
            emit_json({
                "query": args.query,
                "schema_version": data.get("schema_version", SCHEMA_VERSION),
                "results": results,
            })

        elif args.command == "plan":
            project, devin = locate_project(args.project, require_devin=args.write)
            if args.write and not args.approve:
                err("plan --write requires --approve")
                return 2
            note = render_plan()
            if args.write:
                out = (devin / NOTE_SUBDIR).resolve()
                try:
                    out.relative_to(devin.resolve())
                except ValueError:
                    raise RuntimeError("output path escapes .devin")
                out.mkdir(parents=True, exist_ok=True)
                plan_path = out / "plan.md"
                plan_path.write_text(note, encoding="utf-8", newline="\n")
                emit_json({
                    "command": "plan",
                    "project": project_label(project),
                    "written": str(plan_path.relative_to(project).as_posix()),
                })
            else:
                emit_text(note)

    except Exception as e:
        err(f"{args.command} failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
