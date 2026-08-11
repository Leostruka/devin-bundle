#!/usr/bin/env python3
"""Scaffold an Obsidian vault for engineering project documentation.

Usage:
    python scaffold.py --project-dir PROJECT --vault-dir VAULT [--project-name NAME]

Creates:
    - SRS, Architecture, Database, Modules index, Functions, Dependencies, Config, Glossary
    - Modules/ and Functions/ subfolders
    - Diagrams/ with C4 / DDD / data-model canvas shells
    - Daily/ logbook folder and Logbook.md index
    - Project.base (Obsidian Base linking modules, functions, dependencies, config)
    - Architecture.canvas (JSON Canvas shell)
    - project-manifest.json
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
    (vault_dir / "Diagrams").mkdir(parents=True, exist_ok=True)
    (vault_dir / "Daily").mkdir(parents=True, exist_ok=True)
    (vault_dir / "Media").mkdir(parents=True, exist_ok=True)

    mapping = {
        "PROJECT_NAME": project_name,
        "PROJECT_TAG": project_tag,
        "DATE": date,
    }

    files_to_write = {
        "00-SRS.md": "srs-template.md",
        "01-Architecture.md": "srs-template.md",
        "02-Database.md": "database-template.md",
        "03-Modules.md": None,
        "04-Functions.md": None,
        "05-Dependencies.md": None,
        "06-Config.md": "config-template.md",
        "07-Glossary.md": None,
    }

    # Write templated notes
    for target, template in files_to_write.items():
        dest = vault_dir / target
        if dest.exists():
            continue
        if template:
            text = load_template(skill_dir, template, mapping)
        else:
            text = f"---\ntitle: \"{project_name} - {target[3:].replace('-', ' ').strip('.md')}\"\nproject: \"{project_name}\"\ntags:\n  - {project_tag}\n---\n\n# {target[3:].replace('.md', '').replace('-', ' ')}\n\n_Generated on {date}. Fill this page with project-specific content._\n"
        dest.write_text(text, encoding="utf-8")

    # Fix Architecture title by rewriting the SRS template leftovers
    arch = vault_dir / "01-Architecture.md"
    arch.write_text(
        f"---\ntitle: \"{project_name} - Architecture\"\nproject: \"{project_name}\"\ntags:\n  - architecture\n  - {project_tag}\n---\n\n# Architecture\n\n_Generated on {date}. Document system overview, layers, seams, adapters, data flow and ADRs._\n",
        encoding="utf-8",
    )

    # Modules index
    modules_index = vault_dir / "03-Modules.md"
    modules_index.write_text(
        f"---\ntitle: \"{project_name} - Modules\"\nproject: \"{project_name}\"\ntags:\n  - modules\n  - {project_tag}\n---\n\n# Modules\n\n| Module | Purpose | Dependencies | Tests | Status |\n|--------|---------|--------------|-------|--------|\n\n> Create one note per module inside `Modules/`.\n",
        encoding="utf-8",
    )

    # Functions index
    functions_index = vault_dir / "04-Functions.md"
    functions_index.write_text(
        f"---\ntitle: \"{project_name} - Functions\"\nproject: \"{project_name}\"\ntags:\n  - functions\n  - {project_tag}\n---\n\n# Functions\n\n| Function | Module | Signature | Side effects | Tests |\n|----------|--------|-----------|--------------|-------|\n",
        encoding="utf-8",
    )

    # Dependencies
    deps = vault_dir / "05-Dependencies.md"
    deps.write_text(
        f"---\ntitle: \"{project_name} - Dependencies\"\nproject: \"{project_name}\"\ntags:\n  - dependencies\n  - {project_tag}\n---\n\n# Dependencies\n\n## Production dependencies\n\n| Name | Version | Purpose | License |\n|------|---------|---------|---------|\n\n## Development dependencies\n\n| Name | Version | Purpose | License |\n|------|---------|---------|---------|\n\n## Internal dependencies\n\n| Module | Depends on | Relationship |\n|--------|------------|--------------|\n",
        encoding="utf-8",
    )

    # Glossary
    glossary = vault_dir / "07-Glossary.md"
    glossary.write_text(
        f"---\ntitle: \"{project_name} - Glossary\"\nproject: \"{project_name}\"\ntags:\n  - glossary\n  - {project_tag}\n---\n\n# Glossary\n\n| Term | Definition | Aliases | Used in |\n|------|------------|---------|---------|\n",
        encoding="utf-8",
    )

    # Logbook index
    logbook = vault_dir / "Logbook.md"
    logbook.write_text(
        f"---\ntitle: \"{project_name} - Logbook\"\nproject: \"{project_name}\"\ntags:\n  - logbook\n  - {project_tag}\n---\n\n# Logbook\n\nRunning log of daily work. Each entry is a daily note under `Daily/`.\n\n## Activity log\n\n### [[{date}]]\n- Initial scaffold and project setup\n",
        encoding="utf-8",
    )

    # First daily note from template
    daily_note = vault_dir / "Daily" / f"{date}.md"
    daily_note.write_text(load_template(skill_dir, "daily-note-template.md", mapping), encoding="utf-8")

    # Project Base
    base_file = vault_dir / "Project.base"
    base_file.write_text(
        f"""filters:
  or:
    - 'file.hasTag("{project_tag}")'
    - 'file.inFolder("Modules")'
    - 'file.inFolder("Functions")'
    - 'file.inFolder("Daily")'

formulas:
  is_module: 'file.hasTag("module")'
  is_function: 'file.hasTag("function")'
  is_logbook: 'file.hasTag("logbook")'

properties:
  status:
    displayName: Status
  module:
    displayName: Module

views:
  - type: table
    name: "All project notes"
    order:
      - file.name
      - file.folder
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

    # Diagram canvases
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

    # Manifest
    manifest = {
        "project_name": project_name,
        "project_dir": str(project_dir),
        "vault_dir": str(vault_dir),
        "created": date,
        "version": "0.1.0",
    }
    (vault_dir / "project-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # Copy helper templates into vault for later reuse
    for template in ["module-template.md", "function-template.md", "daily-note-template.md"]:
        src = skill_dir / "templates" / template
        if src.exists():
            shutil.copy(src, vault_dir / "Media" / template)

    print(f"Scaffolded {vault_dir}")
    print(f"Project: {project_name}")
    print(f"Files: {len(list(vault_dir.glob('*.*md')))} top-level notes, plus Daily/, Diagrams/, Project.base and Architecture.canvas")


if __name__ == "__main__":
    main()
