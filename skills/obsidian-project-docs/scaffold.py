#!/usr/bin/env python3
"""Scaffold an Obsidian vault for engineering project documentation.

Usage:
    python scaffold.py --project-dir PROJECT --vault-dir VAULT [--project-name NAME]

Creates:
    - Overview, SRS, Architecture, Database, Modules index, Functions, Dependencies, Config, Glossary, Decisions
    - Modules/ and Functions/ and Decisions/ subfolders
    - Diagrams/ with Mermaid (.md) and Canvas (.canvas) shells
    - Daily/ logbook folder and Logbook.md index
    - Project.base (Obsidian Base linking modules, functions, dependencies, config)
    - Architecture.canvas (JSON Canvas shell)
    - wiki-config.json (steering config)
    - refresh.py (re-index script)
    - project-manifest.json (with last_indexed timestamp)
"""
import argparse
import json
import random
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


C4_COLORS = {
    "actor": "6",      # purple
    "module": "4",     # green
    "app": "4",        # green
    "api": "5",        # cyan
    "db": "3",         # yellow
    "queue": "2",      # orange
    "external": "1",   # red
    "legend": "0",
}


def load_template(skill_dir, name, mapping):
    src = skill_dir / "templates" / name
    text = src.read_text(encoding="utf-8")
    for key, value in mapping.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text


def slugify(name):
    return re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")


def git_name(project_dir):
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
    except Exception:
        pass
    return None


def new_id():
    return "".join(random.choice("0123456789abcdef") for _ in range(16))


def make_text_node(x, y, w, h, text, color="0", **kwargs):
    node = {
        "id": new_id(),
        "type": "text",
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "text": text,
    }
    if color:
        node["color"] = color
    node.update(kwargs)
    return node


def make_edge(from_id, to_id, label="", from_side="right", to_side="left", color=""):
    edge = {
        "id": new_id(),
        "fromNode": from_id,
        "fromSide": from_side,
        "toNode": to_id,
        "toSide": to_side,
        "toEnd": "arrow",
        "label": label,
    }
    if color:
        edge["color"] = color
    return edge


def write_canvas(path, nodes, edges):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"nodes": nodes, "edges": edges}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def context_canvas(project_name):
    user = make_text_node(
        -320, 40, 160, 80, f"# User\n\nUses {project_name}.", C4_COLORS["actor"]
    )
    system = make_text_node(
        0, 0, 280, 160, f"# {project_name}\n\nThe system in scope.", C4_COLORS["module"]
    )
    email = make_text_node(
        400, -60, 220, 100, "# Email system\n\nExternal.", C4_COLORS["external"]
    )
    payment = make_text_node(
        400, 120, 220, 100, "# Payment gateway\n\nExternal.", C4_COLORS["external"]
    )
    legend = make_text_node(
        -360, 180, 260, 120,
        "# Legend\n\n| Color | Meaning |\n|-------|---------|\n| green | in scope |\n| red | external |\n| purple | person/actor |",
        color=C4_COLORS["legend"],
    )
    nodes = [user, system, email, payment, legend]
    edges = [
        make_edge(user["id"], system["id"], "uses", "right", "left"),
        make_edge(system["id"], email["id"], "sends", "top", "left"),
        make_edge(system["id"], payment["id"], "charges", "bottom", "left"),
    ]
    return nodes, edges


def container_canvas(project_name):
    web = make_text_node(-120, -60, 220, 100, "# Web App\n\nReact / Vue", C4_COLORS["app"])
    api = make_text_node(200, -60, 220, 100, "# API\n\nNode / Laravel / Go", C4_COLORS["api"])
    db = make_text_node(520, -80, 200, 140, "# Database\n\nPostgres / MySQL\n\nMain store.", C4_COLORS["db"])
    queue = make_text_node(520, 120, 200, 100, "# Queue\n\nRedis / RabbitMQ", C4_COLORS["queue"])
    ext = make_text_node(200, 200, 220, 100, "# External service\n\nAPI / webhook", C4_COLORS["external"])
    user = make_text_node(-460, -40, 160, 80, "# User", C4_COLORS["actor"])
    legend = make_text_node(-480, 120, 280, 160,
        "# Legend\n\n| Color | Meaning |\n|-------|---------|\n| green | app |\n| cyan | API/service |\n| yellow | database |\n| orange | queue/broker |\n| red | external |",
        color=C4_COLORS["legend"],
    )
    nodes = [web, api, db, queue, ext, user, legend]
    edges = [
        make_edge(user["id"], web["id"], "uses", "right", "left"),
        make_edge(web["id"], api["id"], "calls /json", "right", "left"),
        make_edge(api["id"], db["id"], "reads/writes", "right", "left"),
        make_edge(api["id"], queue["id"], "publishes", "bottom", "top"),
        make_edge(api["id"], ext["id"], "calls /api", "bottom", "top"),
    ]
    return nodes, edges


def component_canvas():
    ctrl = make_text_node(-200, 0, 220, 100, "# Controller\n\nHTTP handlers", C4_COLORS["api"])
    svc = make_text_node(80, 0, 220, 100, "# Service\n\nBusiness logic", C4_COLORS["api"])
    repo = make_text_node(360, 0, 220, 100, "# Repository\n\nData access", C4_COLORS["api"])
    gateway = make_text_node(80, 180, 220, 100, "# Gateway\n\nExternal adapter", C4_COLORS["external"])
    db = make_text_node(360, 180, 220, 100, "# Database", C4_COLORS["db"])
    nodes = [ctrl, svc, repo, gateway, db]
    edges = [
        make_edge(ctrl["id"], svc["id"], "calls", "right", "left"),
        make_edge(svc["id"], repo["id"], "uses", "right", "left"),
        make_edge(svc["id"], gateway["id"], "calls", "bottom", "top"),
        make_edge(repo["id"], db["id"], "reads/writes", "bottom", "top"),
    ]
    return nodes, edges


def domain_canvas():
    ctx_a = {
        "id": new_id(),
        "type": "group",
        "x": -300,
        "y": 0,
        "width": 260,
        "height": 220,
        "label": "Context A",
        "color": "4",
    }
    ctx_b = {
        "id": new_id(),
        "type": "group",
        "x": 100,
        "y": 0,
        "width": 260,
        "height": 220,
        "label": "Context B",
        "color": "5",
    }
    event = make_text_node(20, -140, 200, 80, "# Domain Event\n\nSomething happened.", C4_COLORS["queue"])
    nodes = [ctx_a, ctx_b, event]
    edges = [
        make_edge(ctx_a["id"], ctx_b["id"], "upstream → downstream", "right", "left"),
        make_edge(event["id"], ctx_b["id"], "consumed by", "bottom", "top"),
    ]
    return nodes, edges


def data_model_canvas():
    users = make_text_node(-280, 0, 240, 160, "# Users\n\n- id: PK\n- email\n- created_at", C4_COLORS["db"])
    orders = make_text_node(40, 0, 260, 180, "# Orders\n\n- id: PK\n- user_id: FK\n- total\n- status", C4_COLORS["db"])
    items = make_text_node(380, 0, 240, 180, "# OrderItems\n\n- id: PK\n- order_id: FK\n- product_id\n- qty", C4_COLORS["db"])
    nodes = [users, orders, items]
    edges = [
        make_edge(users["id"], orders["id"], "1 : *", "right", "left"),
        make_edge(orders["id"], items["id"], "1 : *", "right", "left"),
    ]
    return nodes, edges


def flow_canvas():
    trigger = make_text_node(-420, 60, 180, 80, "# Trigger\n\nUser action", C4_COLORS["actor"])
    cmd = make_text_node(-140, 60, 200, 80, "# Command\n\nCreate order", C4_COLORS["api"])
    event1 = make_text_node(140, 60, 200, 80, "# Event\n\nOrderCreated", C4_COLORS["queue"])
    handler = make_text_node(140, 200, 220, 80, "# Handler\n\nSend email", C4_COLORS["api"])
    read = make_text_node(460, 60, 200, 80, "# Read model\n\nOrder view", C4_COLORS["db"])
    nodes = [trigger, cmd, event1, handler, read]
    edges = [
        make_edge(trigger["id"], cmd["id"], "", "right", "left"),
        make_edge(cmd["id"], event1["id"], "emits", "right", "left"),
        make_edge(event1["id"], handler["id"], "subscribes", "bottom", "top"),
        make_edge(cmd["id"], read["id"], "updates", "top", "bottom"),
    ]
    return nodes, edges


MERMAID_TEMPLATES = {
    "Context.md": """---
parent: 02-Architecture
tags: [diagram, c4, context]
---

# System Context

```mermaid
graph TB
  User([User]) --> System[{project_name}]
  System --> Email[Email Service]
  System --> Payment[Payment Gateway]
```

## Links
- [[02-Architecture]]
""",
    "Container.md": """---
parent: 02-Architecture
tags: [diagram, c4, container]
---

# Container Diagram

```mermaid
graph TB
  User([User]) --> Web[Web App<br/>React]
  Web --> API[API<br/>Node/Laravel/Go]
  API --> DB[(Database<br/>Postgres)]
  API --> Queue[Queue<br/>Redis]
  API --> Ext[External Service]
```

## Links
- [[02-Architecture]]
""",
    "Component.md": """---
parent: 02-Architecture
tags: [diagram, c4, component]
---

# Component Diagram

```mermaid
graph TB
  Ctrl[Controller<br/>HTTP handlers] --> Svc[Service<br/>Business logic]
  Svc --> Repo[Repository<br/>Data access]
  Svc --> Gateway[Gateway<br/>External adapter]
  Repo --> DB[(Database)]
```

## Links
- [[02-Architecture]]
""",
    "Domain.md": """---
parent: 02-Architecture
tags: [diagram, ddd, domain]
---

# Domain Context Map

```mermaid
graph LR
  subgraph ContextA[Context A]
    A1[Aggregate 1]
  end
  subgraph ContextB[Context B]
    B1[Aggregate 2]
  end
  A1 -->|upstream| B1
  Event[Domain Event] --> B1
```

## Links
- [[02-Architecture]]
""",
    "DataModel.md": """---
parent: 03-Database
tags: [diagram, er, data-model]
---

# Data Model

```mermaid
erDiagram
  Users ||--o{ Orders : places
  Orders ||--|{ OrderItems : contains
  Users {
    int id PK
    string email
    datetime created_at
  }
  Orders {
    int id PK
    int user_id FK
    decimal total
    string status
  }
  OrderItems {
    int id PK
    int order_id FK
    int product_id
    int qty
  }
```

## Links
- [[03-Database]]
""",
    "Flow.md": """---
parent: 02-Architecture
tags: [diagram, flow]
---

# Data / Event Flow

```mermaid
graph LR
  Trigger[User Action] --> Cmd[Command]
  Cmd --> Event[OrderCreated]
  Event --> Handler[Send Email]
  Cmd --> Read[Read Model]
```

## Links
- [[02-Architecture]]
""",
}

REFRESH_SCRIPT = r'''#!/usr/bin/env python3
"""Re-index the wiki: detect changed source files and flag stale pages.

Usage:
    python refresh.py --project-dir <PROJECT>

Scans the project for files changed since the last index (stored in
project-manifest.json `last_indexed`). For each changed file, finds which
wiki pages reference it via `source: <file>` citations. Prints a report
of stale pages and updates the timestamp.
"""
import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def find_source_refs(vault_dir):
    """Scan all .md files in the vault for `source: path/to/file` citations."""
    refs = {}  # source_file -> set of wiki pages
    for md_file in vault_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"source:\s*[`]?([^\s`]+)[`]?", text):
            src_path = m.group(1).strip()
            # Strip line number suffix
            src_file = src_path.rsplit(":", 1)[0] if ":" in src_path else src_path
            refs.setdefault(src_file, set()).add(str(md_file.relative_to(vault_dir)))
    return refs


def find_changed_files(project_dir, since_ts):
    """Find files in project_dir modified after since_ts."""
    changed = []
    for root, dirs, files in os.walk(project_dir):
        # Skip common ignore dirs
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "target"}]
        for f in files:
            fp = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(fp)
                if mtime > since_ts:
                    rel = os.path.relpath(fp, project_dir).replace("\\\\", "/")
                    changed.append(rel)
            except OSError:
                pass
    return changed


def main():
    parser = argparse.ArgumentParser(description="Re-index wiki and flag stale pages.")
    parser.add_argument("--project-dir", required=True, help="Project directory to scan")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    vault_dir = Path(__file__).parent.resolve()
    manifest_path = vault_dir / "project-manifest.json"

    if not manifest_path.exists():
        print("ERROR: project-manifest.json not found in vault dir.")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    last_indexed = manifest.get("last_indexed_ts", 0)

    print(f"Vault: {vault_dir}")
    print(f"Project: {project_dir}")
    print(f"Last indexed: {datetime.fromtimestamp(last_indexed, tz=timezone.utc).isoformat() if last_indexed else 'never'}")
    print()

    # Find changed files
    changed = find_changed_files(project_dir, last_indexed)
    print(f"Changed files since last index: {len(changed)}")

    if not changed:
        print("No changes detected. All pages are up to date.")
        # Still update timestamp
        manifest["last_indexed_ts"] = datetime.now(tz=timezone.utc).timestamp()
        manifest["last_indexed"] = datetime.now(tz=timezone.utc).isoformat()
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        return 0

    # Find source refs in vault
    refs = find_source_refs(vault_dir)

    # Map changed files to stale pages
    stale_pages = set()
    for changed_file in changed:
        # Try exact match and basename match
        if changed_file in refs:
            for page in refs[changed_file]:
                stale_pages.add(page)
        else:
            # Try basename match
            basename = os.path.basename(changed_file)
            for src_file, pages in refs.items():
                if os.path.basename(src_file) == basename:
                    stale_pages.update(pages)

    print()
    print(f"Stale pages ({len(stale_pages)}):")
    for page in sorted(stale_pages):
        print(f"  [STALE] {page}")

    print()
    print(f"Changed files with no wiki reference ({len(changed) - len(stale_pages)}):")
    for f in changed:
        if not any(f in pages or os.path.basename(f) in [os.path.basename(s) for s in refs] for pages in refs.values()):
            print(f"  [NEW] {f}")

    # Update manifest
    manifest["last_indexed_ts"] = datetime.now(tz=timezone.utc).timestamp()
    manifest["last_indexed"] = datetime.now(tz=timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print()
    print(f"Updated last_indexed: {manifest['last_indexed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True, help="Project directory to document")
    parser.add_argument("--vault-dir", required=True, help="Obsidian vault directory to create")
    parser.add_argument("--project-name", help="Project name (defaults to directory or git repo name)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Project directory does not exist: {project_dir}")
        sys.exit(1)

    if args.project_name:
        project_name = args.project_name
    else:
        project_name = git_name(project_dir) or project_dir.name

    project_tag = slugify(project_name)
    date = datetime.now().strftime("%Y-%m-%d")
    vault_dir = Path(args.vault_dir).resolve()

    script_path = Path(__file__).resolve().parent
    skill_dir = script_path

    # Create vault directories
    (vault_dir / "Modules").mkdir(parents=True, exist_ok=True)
    (vault_dir / "Functions").mkdir(parents=True, exist_ok=True)
    (vault_dir / "Decisions").mkdir(parents=True, exist_ok=True)
    (vault_dir / "Diagrams").mkdir(parents=True, exist_ok=True)
    (vault_dir / "Daily").mkdir(parents=True, exist_ok=True)
    (vault_dir / "Media").mkdir(parents=True, exist_ok=True)

    mapping = {
        "PROJECT_NAME": project_name,
        "PROJECT_TAG": project_tag,
        "DATE": date,
    }

    # Write Overview from template
    overview = vault_dir / "00-Overview.md"
    if not overview.exists():
        overview.write_text(load_template(skill_dir, "overview-template.md", mapping), encoding="utf-8")

    # Write SRS from template (renumbered to 01)
    srs = vault_dir / "01-SRS.md"
    if not srs.exists():
        srs_text = load_template(skill_dir, "srs-template.md", mapping)
        # Add parent frontmatter
        srs_text = srs_text.replace('status: draft', 'status: draft\nparent: 00-Overview')
        srs.write_text(srs_text, encoding="utf-8")

    # Architecture
    arch = vault_dir / "02-Architecture.md"
    if not arch.exists():
        arch.write_text(
            f"---\ntitle: \"{project_name} - Architecture\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - architecture\n  - {project_tag}\n---\n\n# Architecture\n\n_Generated on {date}. Document system overview, layers, seams, adapters, data flow and ADRs. Every claim must have a `source: path/to/file:line` citation._\n",
            encoding="utf-8",
        )

    # Database
    db = vault_dir / "03-Database.md"
    if not db.exists():
        db_text = load_template(skill_dir, "database-template.md", mapping)
        db_text = db_text.replace('---\n', '---\nparent: 00-Overview\n', 1)
        db.write_text(db_text, encoding="utf-8")

    # Modules index
    modules_index = vault_dir / "04-Modules.md"
    if not modules_index.exists():
        modules_index.write_text(
            f"---\ntitle: \"{project_name} - Modules\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - modules\n  - {project_tag}\n---\n\n# Modules\n\n| Module | Purpose | Dependencies | Tests | Source | Status |\n|--------|---------|--------------|-------|--------|--------|\n\n> Create one note per module inside `Modules/`. Each must have `source: path/to/file:line`.\n",
            encoding="utf-8",
        )

    # Functions index
    functions_index = vault_dir / "05-Functions.md"
    if not functions_index.exists():
        functions_index.write_text(
            f"---\ntitle: \"{project_name} - Functions\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - functions\n  - {project_tag}\n---\n\n# Functions\n\n| Function | Module | Signature | Source | Side effects | Tests |\n|----------|--------|-----------|--------|--------------|-------|\n",
            encoding="utf-8",
        )

    # Dependencies
    deps = vault_dir / "06-Dependencies.md"
    if not deps.exists():
        deps.write_text(
            f"---\ntitle: \"{project_name} - Dependencies\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - dependencies\n  - {project_tag}\n---\n\n# Dependencies\n\n## Production dependencies\n\n| Name | Version | Purpose | License | Source |\n|------|---------|---------|---------|--------|\n\n## Development dependencies\n\n| Name | Version | Purpose | License | Source |\n|------|---------|---------|---------|--------|\n\n## Internal dependencies\n\n| Module | Depends on | Relationship | Source |\n|--------|------------|--------------|--------|\n",
            encoding="utf-8",
        )

    # Config
    config = vault_dir / "07-Config.md"
    if not config.exists():
        config_text = load_template(skill_dir, "config-template.md", mapping)
        config_text = config_text.replace('---\n', '---\nparent: 00-Overview\n', 1)
        config.write_text(config_text, encoding="utf-8")

    # Glossary
    glossary = vault_dir / "08-Glossary.md"
    if not glossary.exists():
        glossary.write_text(
            f"---\ntitle: \"{project_name} - Glossary\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - glossary\n  - {project_tag}\n---\n\n# Glossary\n\n| Term | Definition | Aliases | Source | Used in |\n|------|------------|---------|--------|---------|\n",
            encoding="utf-8",
        )

    # Decisions
    decisions = vault_dir / "09-Decisions.md"
    if not decisions.exists():
        decisions.write_text(
            f"---\ntitle: \"{project_name} - Decisions\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - decisions\n  - adr\n  - {project_tag}\n---\n\n# Decisions (ADRs)\n\n| ADR | Title | Status | Date |\n|-----|-------|--------|------|\n\n> Create one note per ADR inside `Decisions/`. Use `templates/adr-template.md`.\n",
            encoding="utf-8",
        )

    # Logbook index
    logbook = vault_dir / "Logbook.md"
    if not logbook.exists():
        logbook.write_text(
            f"---\ntitle: \"{project_name} - Logbook\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - logbook\n  - {project_tag}\n---\n\n# Logbook\n\nRunning log of daily work. Each entry is a daily note under `Daily/`.\n\n## Activity log\n\n### [[{date}]]\n- Initial scaffold and project setup\n",
            encoding="utf-8",
        )

    # First daily note from template
    daily_note = vault_dir / "Daily" / f"{date}.md"
    if not daily_note.exists():
        daily_note.write_text(load_template(skill_dir, "daily-note-template.md", mapping), encoding="utf-8")

    # Project Base
    base_file = vault_dir / "Project.base"
    if not base_file.exists():
        base_file.write_text(
            f"""filters:
  or:
    - 'file.hasTag("{project_tag}")'
    - 'file.inFolder("Modules")'
    - 'file.inFolder("Functions")'
    - 'file.inFolder("Decisions")'
    - 'file.inFolder("Daily")'

formulas:
  is_module: 'file.hasTag("module")'
  is_function: 'file.hasTag("function")'
  is_decision: 'file.hasTag("adr")'
  is_logbook: 'file.hasTag("logbook")'

properties:
  status:
    displayName: Status
  module:
    displayName: Module
  parent:
    displayName: Parent

views:
  - type: table
    name: "All project notes"
    order:
      - file.name
      - file.folder
      - parent
      - status
  - type: table
    name: "Modules"
    filters:
      and:
        - 'file.inFolder("Modules")'
    order:
      - file.name
      - status
  - type: table
    name: "Functions"
    filters:
      and:
        - 'file.inFolder("Functions")'
    order:
      - file.name
      - module
  - type: table
    name: "Decisions"
    filters:
      and:
        - 'file.inFolder("Decisions")'
    order:
      - file.name
      - status
  - type: table
    name: "Logbook"
    filters:
      and:
        - 'file.inFolder("Daily")'
    order:
      - file.name
      - file.folder
""",
            encoding="utf-8",
        )

    # Mermaid diagram shells
    for name, template in MERMAID_TEMPLATES.items():
        dest = vault_dir / "Diagrams" / name
        if not dest.exists():
            dest.write_text(template.replace("{project_name}", project_name), encoding="utf-8")

    # Canvas diagrams
    write_canvas(vault_dir / "Diagrams" / "Context.canvas", *context_canvas(project_name))
    write_canvas(vault_dir / "Diagrams" / "Container.canvas", *container_canvas(project_name))
    write_canvas(vault_dir / "Diagrams" / "Component.canvas", *component_canvas())
    write_canvas(vault_dir / "Diagrams" / "Domain.canvas", *domain_canvas())
    write_canvas(vault_dir / "Diagrams" / "DataModel.canvas", *data_model_canvas())
    write_canvas(vault_dir / "Diagrams" / "Flow.canvas", *flow_canvas())

    # Master Architecture canvas
    module_id = new_id()
    db_id = new_id()
    ext_id = new_id()
    architecture_canvas = {
        "nodes": [
            {
                "id": module_id,
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 300,
                "height": 160,
                "text": f"# {project_name}\n\nCore modules and logic.",
                "color": C4_COLORS["module"],
            },
            {
                "id": db_id,
                "type": "text",
                "x": 400,
                "y": 0,
                "width": 260,
                "height": 120,
                "text": "# Database\n\nPersistence layer.",
                "color": C4_COLORS["db"],
            },
            {
                "id": ext_id,
                "type": "text",
                "x": 200,
                "y": 240,
                "width": 260,
                "height": 120,
                "text": "# External systems\n\nAPIs, third-party services.",
                "color": C4_COLORS["external"],
            },
        ],
        "edges": [
            {
                "id": new_id(),
                "fromNode": module_id,
                "fromSide": "right",
                "toNode": db_id,
                "toSide": "left",
                "toEnd": "arrow",
                "label": "reads/writes",
            },
            {
                "id": new_id(),
                "fromNode": module_id,
                "fromSide": "bottom",
                "toNode": ext_id,
                "toSide": "top",
                "toEnd": "arrow",
                "label": "calls",
            },
        ],
    }
    (vault_dir / "Architecture.canvas").write_text(
        json.dumps(architecture_canvas, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # wiki-config.json (steering config)
    wiki_config = {
        "repo_notes": [
            {
                "content": f"This repository contains {project_name}. Document the main components, their interactions, and key architectural decisions.",
                "author": "agent",
            }
        ],
        "pages": [
            {"title": "Overview", "purpose": "Codebase summary and entry point", "parent": None},
            {"title": "SRS", "purpose": "Software requirements specification", "parent": "Overview"},
            {"title": "Architecture", "purpose": "System layers, seams, data flow, ADRs", "parent": "Overview"},
            {"title": "Database", "purpose": "Schema, tables, relationships", "parent": "Architecture"},
            {"title": "Modules", "purpose": "Module catalog with interfaces and dependencies", "parent": "Architecture"},
            {"title": "Functions", "purpose": "Function registry with signatures and callers", "parent": "Modules"},
            {"title": "Dependencies", "purpose": "Third-party and internal dependencies", "parent": "Overview"},
            {"title": "Config", "purpose": "Environment variables, config files, feature flags", "parent": "Overview"},
            {"title": "Glossary", "purpose": "Domain terms with code references", "parent": "Overview"},
            {"title": "Decisions", "purpose": "ADR log", "parent": "Overview"},
        ],
    }
    (vault_dir / "wiki-config.json").write_text(
        json.dumps(wiki_config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # refresh.py (re-index script)
    (vault_dir / "refresh.py").write_text(REFRESH_SCRIPT, encoding="utf-8")

    # Manifest with last_indexed timestamp
    now = datetime.now()
    manifest = {
        "project_name": project_name,
        "project_dir": str(project_dir),
        "vault_dir": str(vault_dir),
        "created": date,
        "version": "0.2.0",
        "last_indexed": now.isoformat(),
        "last_indexed_ts": now.timestamp(),
    }
    (vault_dir / "project-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # Copy helper templates into vault for later reuse
    for template in ["module-template.md", "function-template.md", "daily-note-template.md", "overview-template.md", "adr-template.md"]:
        src = skill_dir / "templates" / template
        if src.exists():
            shutil.copy(src, vault_dir / "Media" / template)

    print(f"Scaffolded {vault_dir}")
    print(f"Project: {project_name}")
    print(f"Files: {len(list(vault_dir.glob('*.*md')))} top-level notes, plus Modules/, Functions/, Decisions/, Diagrams/, Daily/, Project.base, Architecture.canvas, wiki-config.json, refresh.py")


if __name__ == "__main__":
    main()
