#!/usr/bin/env python3
"""Scaffold an Obsidian vault for engineering project documentation.

Usage:
    python scaffold.py --project-dir PROJECT --vault-dir VAULT [--project-name NAME]

Creates:
    - Overview, SRS, Architecture, Database, Modules index, Functions, Dependencies, Config, Glossary, Decisions
    - Modules/ and Functions/ and Decisions/ subfolders
    - Diagrams/ with Mermaid (.md) shells
    - Daily/ logbook folder and 10-Logbook.md index
    - Project.base (Obsidian Base linking modules, functions, dependencies, config)
    - wiki-config.json (steering config)
    - refresh.py (re-index script)
    - project-manifest.json (with last_indexed timestamp)
"""
import argparse
import json
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
            text=True, encoding="utf-8", errors="replace",
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
    except Exception:
        pass  # fail-soft: probe fallback
    return None



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
    skill_dir = script_path.parent

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
        srs_text = srs_text.replace('status: active', 'status: active\nparent: 00-Overview', 1)
        srs.write_text(srs_text, encoding="utf-8")

    # Architecture
    arch = vault_dir / "02-Architecture.md"
    if not arch.exists():
        arch.write_text(
            f"---\ntitle: \"{project_name} - Architecture\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - architecture\n  - {project_tag}\nstatus: active\n---\n\n# Architecture\n\n_Generated on {date}. Document system overview, layers, seams, adapters, data flow and ADRs. Every claim must have a `source: path/to/file:line` citation._\n",
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
            f"---\ntitle: \"{project_name} - Modules\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - modules\n  - {project_tag}\nstatus: active\n---\n\n# Modules\n\n| Module | Purpose | Dependencies | Tests | Source | Status |\n|--------|---------|--------------|-------|--------|--------|\n\n> Create one note per module inside `Modules/`. Each must have `source: path/to/file:line`.\n",
            encoding="utf-8",
        )

    # Functions index
    functions_index = vault_dir / "05-Functions.md"
    if not functions_index.exists():
        functions_index.write_text(
            f"---\ntitle: \"{project_name} - Functions\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - functions\n  - {project_tag}\nstatus: active\n---\n\n# Functions\n\n| Function | Module | Signature | Source | Side effects | Tests |\n|----------|--------|-----------|--------|--------------|-------|\n",
            encoding="utf-8",
        )

    # Dependencies
    deps = vault_dir / "06-Dependencies.md"
    if not deps.exists():
        deps.write_text(
            f"---\ntitle: \"{project_name} - Dependencies\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - dependencies\n  - {project_tag}\nstatus: active\n---\n\n# Dependencies\n\n## Production dependencies\n\n| Name | Version | Purpose | License | Source |\n|------|---------|---------|---------|--------|\n\n## Development dependencies\n\n| Name | Version | Purpose | License | Source |\n|------|---------|---------|---------|--------|\n\n## Internal dependencies\n\n| Module | Depends on | Relationship | Source |\n|--------|------------|--------------|--------|\n",
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
            f"---\ntitle: \"{project_name} - Glossary\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - glossary\n  - {project_tag}\nstatus: active\n---\n\n# Glossary\n\n| Term | Definition | Aliases | Source | Used in |\n|------|------------|---------|--------|---------|\n",
            encoding="utf-8",
        )

    # Decisions
    decisions = vault_dir / "09-Decisions.md"
    if not decisions.exists():
        decisions.write_text(
            f"---\ntitle: \"{project_name} - Decisions\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - decisions\n  - adr\n  - {project_tag}\nstatus: active\n---\n\n# Decisions (ADRs)\n\n| ADR | Title | Status | Date |\n|-----|-------|--------|------|\n\n> Create one note per ADR inside `Decisions/`. Use `templates/adr-template.md`.\n",
            encoding="utf-8",
        )

    # Logbook index
    logbook = vault_dir / "10-Logbook.md"
    if not logbook.exists():
        logbook.write_text(
            f"---\ntitle: \"{project_name} - Logbook\"\nproject: \"{project_name}\"\nparent: 00-Overview\ntags:\n  - logbook\n  - {project_tag}\nstatus: active\n---\n\n# Logbook\n\nRunning log of daily work. Each entry is a daily note under `Daily/`.\n\n## Activity log\n\n### [[{date}]]\n- Initial scaffold and project setup\n",
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
    for tpl in sorted((skill_dir / "templates" / "mermaid").glob("*.md")):
        dest = vault_dir / "Diagrams" / tpl.name
        if not dest.exists():
            dest.write_text(tpl.read_text(encoding="utf-8").replace("{project_name}", project_name), encoding="utf-8")

    # wiki-config.json (steering config with mode, language, importance, filePaths)
    wiki_config = {
        "mode": "comprehensive",
        "language": "en",
        "repo_notes": [
            {
                "content": f"This repository contains {project_name}. Document the main components, their interactions, and key architectural decisions.",
                "author": "agent",
            }
        ],
        "pages": [
            {"title": "Overview", "purpose": "Codebase summary and entry point", "parent": None, "importance": "high", "filePaths": ["README.md", "package.json"]},
            {"title": "SRS", "purpose": "Software requirements specification", "parent": "Overview", "importance": "high", "filePaths": ["README.md"]},
            {"title": "Architecture", "purpose": "System layers, seams, data flow, ADRs", "parent": "Overview", "importance": "high", "filePaths": ["src/"]},
            {"title": "Database", "purpose": "Schema, tables, relationships", "parent": "Architecture", "importance": "medium", "filePaths": ["migrations/", "src/models/"]},
            {"title": "Modules", "purpose": "Module catalog with interfaces and dependencies", "parent": "Architecture", "importance": "high", "filePaths": ["src/"]},
            {"title": "Functions", "purpose": "Function registry with signatures and callers", "parent": "Modules", "importance": "medium", "filePaths": ["src/"]},
            {"title": "Dependencies", "purpose": "Third-party and internal dependencies", "parent": "Overview", "importance": "low", "filePaths": ["package.json", "requirements.txt"]},
            {"title": "Config", "purpose": "Environment variables, config files, feature flags", "parent": "Overview", "importance": "medium", "filePaths": [".env.example", "config/"]},
            {"title": "Glossary", "purpose": "Domain terms with code references", "parent": "Overview", "importance": "low", "filePaths": ["src/types/"]},
            {"title": "Decisions", "purpose": "ADR log", "parent": "Overview", "importance": "medium", "filePaths": [".devin/adr/"]},
        ],
    }
    (vault_dir / "wiki-config.json").write_text(
        json.dumps(wiki_config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Scripts: refresh.py, validate_wiki_config.py, wiki_structure.py, wiki_contents.py, query.py
    for src_script in (skill_dir / "templates" / "vault-scripts").glob("*.py"):
        (vault_dir / src_script.name).write_text(src_script.read_text(encoding="utf-8"), encoding="utf-8")

    # Manifest with last_indexed timestamp and indexed_branch
    now = datetime.now()
    # Detect current branch if possible
    indexed_branch = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
        if result.returncode == 0:
            indexed_branch = result.stdout.strip()
    except Exception:
        pass  # fail-soft: cleanup; preserve primary error
    manifest = {
        "project_name": project_name,
        "project_dir": str(project_dir),
        "vault_dir": str(vault_dir),
        "created": date,
        "version": "0.3.0",
        "last_indexed": now.isoformat(),
        "last_indexed_ts": now.timestamp(),
        "indexed_branch": indexed_branch,
    }
    (vault_dir / "project-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # Copy helper templates into vault for later reuse
    for template in ["module-template.md", "function-template.md", "daily-note-template.md", "overview-template.md", "adr-template.md"]:
        src = skill_dir / "templates" / template
        if src.exists():
            shutil.copy(src, vault_dir / "Media" / template)

    print(f"Scaffolded {vault_dir}")
    print(f"Project: {project_name}")
    if indexed_branch:
        print(f"Branch: {indexed_branch}")
    print(f"Files: {len(list(vault_dir.glob('*.*md')))} top-level notes, plus Modules/, Functions/, Decisions/, Diagrams/ (13 Mermaid), Daily/, Project.base, wiki-config.json, refresh.py, validate_wiki_config.py, wiki_structure.py, wiki_contents.py, query.py")


if __name__ == "__main__":
    main()
