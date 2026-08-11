#!/usr/bin/env python3
"""Scaffold an Obsidian vault for engineering project documentation.

Usage:
    python scaffold.py --project-dir PROJECT --vault-dir VAULT [--project-name NAME]

Creates:
    - SRS, Architecture, Database, Modules index, Functions, Dependencies, Config, Glossary
    - Modules/ and Functions/ subfolders
    - Project.base (Obsidian Base linking modules, functions, dependencies, config)
    - Architecture.canvas (JSON Canvas shell)
    - project-manifest.json
"""
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


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
    (vault_dir / "Media").mkdir(parents=True, exist_ok=True)

    mapping = {
        "PROJECT_NAME": project_name,
        "PROJECT_TAG": project_tag,
        "DATE": date,
    }

    files_to_write = {
        "00-SRS.md": "srs-template.md",
        "01-Architecture.md": "srs-template.md",  # minimal; user should split if needed
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

    # Project Base
    base_file = vault_dir / "Project.base"
    base_file.write_text(
        f"""filters:
  or:
    - 'file.hasTag("{project_tag}")'
    - 'file.inFolder("Modules")'
    - 'file.inFolder("Functions")'

formulas:
  is_module: 'file.hasTag("module")'
  is_function: 'file.hasTag("function")'

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
""",
        encoding="utf-8",
    )

    # Architecture Canvas
    module_id = new_id()
    db_id = new_id()
    ext_id = new_id()
    canvas = {
        "nodes": [
            {
                "id": module_id,
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 300,
                "height": 160,
                "text": f"# {project_name}\n\nCore modules and logic.",
                "color": "4",
            },
            {
                "id": db_id,
                "type": "text",
                "x": 400,
                "y": 0,
                "width": 260,
                "height": 120,
                "text": "# Database\n\nPersistence layer.",
                "color": "3",
            },
            {
                "id": ext_id,
                "type": "text",
                "x": 200,
                "y": 240,
                "width": 260,
                "height": 120,
                "text": "# External systems\n\nAPIs, third-party services.",
                "color": "2",
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
    canvas_file = vault_dir / "Architecture.canvas"
    canvas_file.write_text(json.dumps(canvas, indent=2, ensure_ascii=False), encoding="utf-8")

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
    shutil.copy(skill_dir / "templates" / "module-template.md", vault_dir / "Media/module-template.md")
    shutil.copy(skill_dir / "templates" / "function-template.md", vault_dir / "Media/function-template.md")

    print(f"Scaffolded {vault_dir}")
    print(f"Project: {project_name}")
    print(f"Files: {len(list(vault_dir.glob('*.*md')))} top-level notes, plus Project.base and Architecture.canvas")


if __name__ == "__main__":
    main()
