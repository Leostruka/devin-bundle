#!/usr/bin/env python3
"""Scaffold an Obsidian vault for engineering project documentation.

Usage:
    python scaffold.py --project-dir PROJECT --vault-dir VAULT [--project-name NAME]

Creates:
    - Overview, SRS, Architecture, Database, Modules index, Functions, Dependencies, Config, Glossary, Decisions
    - Modules/ and Functions/ and Decisions/ subfolders
    - Diagrams/ with Mermaid (.md) shells
    - Daily/ logbook folder and Logbook.md index
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
            text=True,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
    except Exception:
        pass
    return None


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

<!-- Sources: src/commands/OrderCommand.ts:1, src/events/OrderCreated.ts:1, src/handlers/EmailHandler.ts:1 -->

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
    "Sequence.md": """---
parent: 02-Architecture
tags: [diagram, sequence]
---

# Sequence Diagram — Authentication Flow

<!-- Sources: src/auth/login.ts:1, src/auth/session.ts:1, src/middleware/auth.ts:1 -->

```mermaid
sequenceDiagram
  actor U as User
  participant C as Client
  participant S as Server
  participant DB as Database
  U->>C: Enter credentials
  C->>S: POST /login
  S->>DB: Query user
  DB-->>S: User record
  S->>S: Verify password
  S-->>C: 200 + session token
  C-->>U: Redirect to dashboard
```

## Links
- [[02-Architecture]]
- [[Modules/Auth]]
""",
    "Class.md": """---
parent: 02-Architecture
tags: [diagram, class]
---

# Class Diagram — Core Domain Types

<!-- Sources: src/models/User.ts:1, src/models/Order.ts:1, src/models/OrderItem.ts:1 -->

```mermaid
classDiagram
  class User {
    +id: int
    +email: string
    +createdAt: Date
    +authenticate(password): boolean
  }
  class Order {
    +id: int
    +userId: int
    +total: decimal
    +status: OrderStatus
    +addItem(item): void
  }
  class OrderItem {
    +id: int
    +orderId: int
    +productId: int
    +qty: int
  }
  User "1" --> "*" Order : places
  Order "1" --> "*" OrderItem : contains
```

## Links
- [[02-Architecture]]
- [[03-Database]]
""",
    "State.md": """---
parent: 02-Architecture
tags: [diagram, state]
---

# State Machine — Order Lifecycle

<!-- Sources: src/models/Order.ts:1, src/services/OrderService.ts:1 -->

```mermaid
stateDiagram-v2
  [*] --> Pending
  Pending --> Paid: payment received
  Paid --> Shipped: items dispatched
  Shipped --> Delivered: carrier confirms
  Delivered --> [*]
  Pending --> Cancelled: user cancels
  Paid --> Refunded: refund issued
  Cancelled --> [*]
  Refunded --> [*]
```

## Links
- [[02-Architecture]]
- [[Modules/OrderService]]
""",
    "C4Dynamic.md": """---
parent: 02-Architecture
tags: [diagram, c4, dynamic]
---

# C4 Dynamic — Checkout Runtime Collaboration

<!-- Sources: src/controllers/CheckoutController.ts:1, src/services/PaymentService.ts:1, src/services/InventoryService.ts:1 -->

```mermaid
C4Dynamic
  User ->> API : POST /checkout
  API ->> Payment : charge()
  Payment ->> Gateway : authorize
  Gateway -->> Payment : approved
  API ->> Inventory : reserve items
  Inventory -->> API : reserved
  API -->> User : 200 OK
```

## Links
- [[02-Architecture]]
""",
    "C4Deployment.md": """---
parent: 02-Architecture
tags: [diagram, c4, deployment]
---

# C4 Deployment — Infrastructure Topology

<!-- Sources: infra/terraform/main.tf:1, docker-compose.yml:1, .env.example:1 -->

```mermaid
C4Deployment
  Developer ->> WebServer : HTTPS
  WebServer ->> AppContainer : Node.js
  AppContainer ->> DbContainer : PostgreSQL
  AppContainer ->> CacheContainer : Redis
  CacheContainer ->> QueueContainer : RabbitMQ
```

## Links
- [[02-Architecture]]
- [[07-Config]]
""",
    "GitGraph.md": """---
parent: 02-Architecture
tags: [diagram, git]
---

# Git Graph — Branching Strategy

<!-- Sources: .github/workflows/ci.yml:1, CONTRIBUTING.md:1 -->

```mermaid
gitGraph
  commit id: "main"
  branch develop
  checkout develop
  commit id: "feat-1"
  branch feature/auth
  checkout feature/auth
  commit id: "auth-1"
  commit id: "auth-2"
  checkout develop
  merge feature/auth
  branch feature/checkout
  checkout feature/checkout
  commit id: "checkout-1"
  checkout develop
  merge feature/checkout
  checkout main
  merge develop
```

## Links
- [[02-Architecture]]
""",
    "Mindmap.md": """---
parent: 02-Architecture
tags: [diagram, mindmap]
---

# Mindmap — Feature / Domain Overview

<!-- Sources: README.md:1, src/index.ts:1 -->

```mermaid
mindmap
  root((MyApp))
    Authentication
      OAuth2
      Session
      Roles
    Orders
      Cart
      Checkout
      Payment
    Inventory
      Stock
      Reservations
    Notifications
      Email
      SMS
```

## Links
- [[02-Architecture]]
""",
}

REFRESH_SCRIPT = r'''#!/usr/bin/env python3
"""Re-index the wiki: detect changed source files and flag stale pages.

Usage:
    python refresh.py --project-dir <PROJECT> [--branch <BRANCH>]

Scans the project for files changed since the last index (stored in
project-manifest.json `last_indexed`). For each changed file, finds which
wiki pages reference it via `source: <file>` citations. Prints a report
of stale pages and updates the timestamp. If --branch is provided, records
the indexed branch and warns if it differs from the previously indexed branch.
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
    parser.add_argument("--branch", help="Branch being indexed (recorded in manifest)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    vault_dir = Path(__file__).parent.resolve()
    manifest_path = vault_dir / "project-manifest.json"

    if not manifest_path.exists():
        print("ERROR: project-manifest.json not found in vault dir.")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    last_indexed = manifest.get("last_indexed_ts", 0)
    prev_branch = manifest.get("indexed_branch")

    print(f"Vault: {vault_dir}")
    print(f"Project: {project_dir}")
    print(f"Last indexed: {datetime.fromtimestamp(last_indexed, tz=timezone.utc).isoformat() if last_indexed else 'never'}")
    if prev_branch:
        print(f"Previously indexed branch: {prev_branch}")
    if args.branch:
        print(f"Requested branch: {args.branch}")
        if prev_branch and prev_branch != args.branch:
            print(f"WARNING: branch changed from '{prev_branch}' to '{args.branch}' — wiki may need full re-generation.")
    print()

    # Find changed files
    changed = find_changed_files(project_dir, last_indexed)
    print(f"Changed files since last index: {len(changed)}")

    if not changed:
        print("No changes detected. All pages are up to date.")
        # Still update timestamp and branch
        manifest["last_indexed_ts"] = datetime.now(tz=timezone.utc).timestamp()
        manifest["last_indexed"] = datetime.now(tz=timezone.utc).isoformat()
        if args.branch:
            manifest["indexed_branch"] = args.branch
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
    if args.branch:
        manifest["indexed_branch"] = args.branch
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print()
    print(f"Updated last_indexed: {manifest['last_indexed']}")
    if args.branch:
        print(f"Updated indexed_branch: {args.branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


VALIDATE_SCRIPT = r'''#!/usr/bin/env python3
"""Validate wiki-config.json against the steering schema.

Usage:
    python validate_wiki_config.py

Checks:
    - Valid JSON
    - Max 30 pages (80 if --enterprise flag)
    - Max 100 total notes (repo_notes + all page_notes)
    - Max 10000 chars per note
    - Page titles unique and non-empty
    - Each page has title and purpose
    - parent references resolve to existing page titles
    - mode and language are valid values
"""
import argparse
import json
import sys
from pathlib import Path

VALID_MODES = {"comprehensive", "concise"}
VALID_LANGS = {"en", "pt", "es", "ja", "zh", "ko", "vi", "he"}
MAX_PAGES_DEFAULT = 30
MAX_PAGES_ENTERPRISE = 80
MAX_NOTES = 100
MAX_NOTE_CHARS = 10000


def count_notes(config):
    repo_notes = len(config.get("repo_notes", []))
    page_notes = sum(len(p.get("page_notes", [])) for p in config.get("pages", []))
    return repo_notes + page_notes


def validate(config, enterprise=False):
    errors = []
    warnings = []
    max_pages = MAX_PAGES_ENTERPRISE if enterprise else MAX_PAGES_DEFAULT

    mode = config.get("mode", "comprehensive")
    if mode not in VALID_MODES:
        errors.append(f"Invalid mode '{mode}'. Must be one of {VALID_MODES}.")

    lang = config.get("language", "en")
    if lang not in VALID_LANGS:
        errors.append(f"Invalid language '{lang}'. Must be one of {VALID_LANGS}.")

    repo_notes = config.get("repo_notes", [])
    if not isinstance(repo_notes, list):
        errors.append("repo_notes must be an array.")
    else:
        for i, note in enumerate(repo_notes):
            content = note.get("content", "")
            if len(content) > MAX_NOTE_CHARS:
                errors.append(f"repo_notes[{i}] exceeds {MAX_NOTE_CHARS} chars ({len(content)}).")

    pages = config.get("pages", [])
    if not isinstance(pages, list):
        errors.append("pages must be an array.")
        return errors, warnings

    if len(pages) > max_pages:
        errors.append(f"Too many pages: {len(pages)} (max {max_pages}).")

    titles = []
    for i, page in enumerate(pages):
        title = page.get("title", "")
        if not title or not title.strip():
            errors.append(f"pages[{i}] has empty or missing title.")
        titles.append(title)
        purpose = page.get("purpose", "")
        if not purpose or not purpose.strip():
            errors.append(f"pages[{i}] '{title}' has empty or missing purpose.")
        importance = page.get("importance", "medium")
        if importance not in {"high", "medium", "low"}:
            warnings.append(f"pages[{i}] '{title}' has invalid importance '{importance}' (expected high/medium/low).")
        for j, pn in enumerate(page.get("page_notes", [])):
            content = pn.get("content", "")
            if len(content) > MAX_NOTE_CHARS:
                errors.append(f"pages[{i}] '{title}' page_notes[{j}] exceeds {MAX_NOTE_CHARS} chars.")

    # Check unique titles
    seen = set()
    for t in titles:
        if t in seen:
            errors.append(f"Duplicate page title: '{t}'.")
        seen.add(t)

    # Check parent references
    title_set = set(titles)
    for i, page in enumerate(pages):
        parent = page.get("parent")
        if parent is not None and parent not in title_set:
            errors.append(f"pages[{i}] '{page.get('title','')}' has parent '{parent}' that does not match any page title.")

    total_notes = count_notes(config)
    if total_notes > MAX_NOTES:
        errors.append(f"Too many notes: {total_notes} (max {MAX_NOTES}).")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate wiki-config.json steering config.")
    parser.add_argument("--enterprise", action="store_true", help="Use enterprise page limit (80 instead of 30)")
    args = parser.parse_args()

    config_path = Path(__file__).parent / "wiki-config.json"
    if not config_path.exists():
        print(f"ERROR: wiki-config.json not found at {config_path}")
        return 1

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        return 1

    errors, warnings = validate(config, enterprise=args.enterprise)

    if warnings:
        for w in warnings:
            print(f"  [WARN] {w}")
    if errors:
        for e in errors:
            print(f"  [FAIL] {e}")
        print(f"\nValidation FAILED with {len(errors)} error(s).")
        return 1

    print(f"Validation PASSED. {len(config.get('pages', []))} pages, {count_notes(config)} notes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


WIKI_STRUCTURE_SCRIPT = r'''#!/usr/bin/env python3
"""Dump the wiki page tree (local equivalent of read_wiki_structure).

Usage:
    python wiki_structure.py

Reads frontmatter from all .md files in the vault and prints the hierarchical
page tree based on the `parent` field.
"""
import re
from pathlib import Path
from collections import defaultdict


def parse_frontmatter(text):
    fm = {}
    if not text.startswith("---"):
        return fm
    end = text.find("---", 3)
    if end == -1:
        return fm
    block = text[3:end]
    for line in block.strip().splitlines():
        m = re.match(r"^(\w+):\s*(.+)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm


def build_tree(vault_dir):
    pages = {}
    for md_file in vault_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        if not fm:
            continue
        title = fm.get("title", md_file.stem)
        parent = fm.get("parent", "null")
        if parent == "null":
            parent = None
        rel = str(md_file.relative_to(vault_dir)).replace("\\", "/")
        pages[rel] = {"title": title, "parent": parent, "path": rel}

    # Build children map
    children = defaultdict(list)
    roots = []
    for path, info in pages.items():
        if info["parent"] is None:
            roots.append(path)
        else:
            # Find parent by title or path stem
            parent_path = None
            for p, i in pages.items():
                if i["title"] == info["parent"] or p.endswith(info["parent"] + ".md") or Path(p).stem == info["parent"]:
                    parent_path = p
                    break
            if parent_path:
                children[parent_path].append(path)
            else:
                roots.append(path)

    return pages, children, roots


def print_tree(pages, children, roots, indent=0):
    for root in sorted(roots):
        info = pages[root]
        prefix = "  " * indent
        print(f"{prefix}- {info['title']}  ({info['path']})")
        print_tree(pages, children, children.get(root, []), indent + 1)


def main():
    vault_dir = Path(__file__).parent.resolve()
    pages, children, roots = build_tree(vault_dir)
    print(f"Wiki structure ({len(pages)} pages):")
    print()
    print_tree(pages, children, roots)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


WIKI_CONTENTS_SCRIPT = r'''#!/usr/bin/env python3
"""Dump the full content of a wiki page (local equivalent of read_wiki_contents).

Usage:
    python wiki_contents.py --page "02-Architecture"
    python wiki_contents.py --page "Modules/Auth"
"""
import argparse
from pathlib import Path


def find_page(vault_dir, name):
    # Try exact file match
    candidates = [
        vault_dir / f"{name}.md",
        vault_dir / f"{name}",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    # Try by stem
    for md in vault_dir.rglob("*.md"):
        if md.stem == name or md.name == name or str(md.relative_to(vault_dir)).replace("\\", "/") == name:
            return md
    # Try by title in frontmatter
    import re
    for md in vault_dir.rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1 and f'title: "{name}"' in text[3:end]:
                return md
    return None


def main():
    parser = argparse.ArgumentParser(description="Dump wiki page content.")
    parser.add_argument("--page", required=True, help="Page name, path, or title")
    args = parser.parse_args()

    vault_dir = Path(__file__).parent.resolve()
    page = find_page(vault_dir, args.page)
    if page is None:
        print(f"Page not found: {args.page}")
        return 1

    print(page.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


QUERY_SCRIPT = r'''#!/usr/bin/env python3
"""Keyword search across the wiki (local equivalent of ask_question).

Usage:
    python query.py --query "authentication flow"
    python query.py --query "database schema" --max-results 10

Searches all .md files for the query terms, returns matching pages with
context snippets and source citations.
"""
import argparse
import re
from pathlib import Path


def search(vault_dir, query, max_results=5):
    terms = [t.lower() for t in query.split() if t]
    results = []

    for md_file in vault_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="replace")
        text_lower = text.lower()
        score = sum(1 for term in terms if term in text_lower)
        if score == 0:
            continue

        # Extract context snippets around matches
        snippets = []
        for term in terms:
            for m in re.finditer(re.escape(term), text_lower):
                start = max(0, m.start() - 80)
                end = min(len(text), m.end() + 80)
                snippet = text[start:end].replace("\n", " ").strip()
                snippets.append(f"...{snippet}...")
                if len(snippets) >= 3:
                    break
            if len(snippets) >= 3:
                break

        # Extract source citations
        sources = set()
        for m in re.finditer(r"source:\s*[`]?([^\s`]+)[`]?", text):
            sources.add(m.group(1).strip())

        rel = str(md_file.relative_to(vault_dir)).replace("\\", "/")
        results.append({
            "page": rel,
            "score": score,
            "snippets": snippets,
            "sources": sorted(sources)[:5],
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]


def main():
    parser = argparse.ArgumentParser(description="Search the wiki by keyword.")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--max-results", type=int, default=5, help="Max results to return")
    args = parser.parse_args()

    vault_dir = Path(__file__).parent.resolve()
    results = search(vault_dir, args.query, args.max_results)

    if not results:
        print(f"No results for: {args.query}")
        return 0

    print(f"Search results for '{args.query}' ({len(results)} pages):")
    print()
    for r in results:
        print(f"## {r['page']}  (score: {r['score']})")
        for s in r["snippets"]:
            print(f"  {s}")
        if r["sources"]:
            print(f"  Sources: {', '.join(r['sources'])}")
        print()
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
            {"title": "Decisions", "purpose": "ADR log", "parent": "Overview", "importance": "medium", "filePaths": ["docs/adr/"]},
        ],
    }
    (vault_dir / "wiki-config.json").write_text(
        json.dumps(wiki_config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Scripts: refresh.py, validate_wiki_config.py, wiki_structure.py, wiki_contents.py, query.py
    (vault_dir / "refresh.py").write_text(REFRESH_SCRIPT, encoding="utf-8")
    (vault_dir / "validate_wiki_config.py").write_text(VALIDATE_SCRIPT, encoding="utf-8")
    (vault_dir / "wiki_structure.py").write_text(WIKI_STRUCTURE_SCRIPT, encoding="utf-8")
    (vault_dir / "wiki_contents.py").write_text(WIKI_CONTENTS_SCRIPT, encoding="utf-8")
    (vault_dir / "query.py").write_text(QUERY_SCRIPT, encoding="utf-8")

    # Manifest with last_indexed timestamp and indexed_branch
    now = datetime.now()
    # Detect current branch if possible
    indexed_branch = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            indexed_branch = result.stdout.strip()
    except Exception:
        pass
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
