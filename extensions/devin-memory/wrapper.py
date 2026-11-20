#!/usr/bin/env python3
"""Manual local Devin memory CLI. JSON responses use Envelope v2."""

import argparse
from functools import partial
import json
from pathlib import Path
import sqlite3
import sys

from devin_memory import legacy, recall, store, transfer


_BUNDLE_VERSION = None


def _bundle_version():
    global _BUNDLE_VERSION
    if _BUNDLE_VERSION is None:
        _BUNDLE_VERSION = ""
        for parent in Path(__file__).absolute().parents:
            manifest = parent / "manifest.json"
            if not manifest.is_file():
                continue
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION = str(data.get("version") or "")
            break
    return _BUNDLE_VERSION


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "devin-memory"}


def _stamp(payload):
    return dict(payload, api_version=2, meta={"answered_by": _answered_by()})


def _dumps(payload):
    return json.dumps(_stamp(payload))


class Parser(argparse.ArgumentParser):
    def __init__(self, *args, json_help=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_help = json_help

    def error(self, message):
        raise store.MemoryFailure("E_FORMAT", "Invalid arguments. See --help.")

    def print_help(self, file=None):
        if self.json_help:
            print(_dumps({"ok": True, "status": "ok", "result": {"help": self.format_help()}}), file=file)
        else:
            super().print_help(file)


def _parser(as_json):
    parser = Parser(description=__doc__, json_help=as_json)
    parser.add_argument("--json", action="store_true")
    commands = parser.add_subparsers(
        dest="command", required=True, parser_class=partial(Parser, json_help=as_json)
    )
    commands.add_parser("status", help="Show local store status without creating it")
    doctor = commands.add_parser("doctor", help="Check the store or recover explicitly without resetting it")
    repair = doctor.add_mutually_exclusive_group()
    repair.add_argument("--recover", dest="action", action="store_const", const="recover",
                        help="Recover a rollback journal with SQLite")
    repair.add_argument("--rebuild-index", dest="action", action="store_const", const="rebuild-index",
                        help="Rebuild only derived search indexes")
    doctor.set_defaults(action="check")
    remember = commands.add_parser("remember", help="Save a note explicitly")
    remember.add_argument("--scope", choices=("project", "global"), help="Defaults to project for new notes")
    remember.add_argument("--key", required=True)
    remember.add_argument("--file", required=True, type=Path)
    remember.add_argument("--base-version", help="Edit against the active version SHA-256; requires --scope")
    remember.add_argument("--relate", action="append", default=[], metavar="TYPE:KEY@VERSION",
                          help="Declare a relation to an active version in this scope")
    search = commands.add_parser("search", help="Find notes in this project and the global scope")
    search.add_argument("query")
    review = commands.add_parser("review", help="Inspect history or explicitly approve a version")
    review.add_argument("key")
    review.add_argument("--scope", choices=("project", "global"))
    review.add_argument("--legacy-path", action="store_true", help="Use a Markdown path relative to the legacy source (/ separators)")
    selection = review.add_mutually_exclusive_group()
    selection.add_argument("--approve", help="Activate the version with this SHA-256; requires --scope")
    selection.add_argument("--before", type=int, help="Continue at the history cursor shown by review")
    archive = commands.add_parser("archive", help="Remove a note from search without deleting history")
    archive.add_argument("key")
    archive.add_argument("--scope", choices=("project", "global"), required=True)
    export = commands.add_parser("export", help="Write a plaintext JSONL package without overwriting")
    export.add_argument(
        "--scope", action="append", choices=("project", "global"), required=True,
        help="Select explicitly. Repeat for both; project means the current registered workspace.",
    )
    export.add_argument("--out", required=True, type=Path)
    incoming = commands.add_parser("import", help="Preview or apply a validated JSONL package")
    incoming.add_argument("source", type=Path)
    incoming.add_argument("--map", dest="mappings", action="append", required=True, metavar="SOURCE=TARGET")
    incoming.add_argument("--apply", metavar="PLAN_ID", help="Apply the exact package and mapping from a preview")
    migrate = commands.add_parser("migrate", help="Preview or merge legacy Markdown without modifying it")
    migrate.add_argument("--project", required=True, type=Path, help="Select the destination workspace")
    migrate.add_argument("--source", type=Path, help="Select another source instead of PROJECT/.devin/memory")
    migrate.add_argument("--apply", metavar="PLAN_ID", help="Apply the exact project and source from a preview")
    return parser


def _plain(text):
    return "".join(char if char.isprintable() else " " for char in text)


def _result(args):
    if args.command == "status":
        return store.status()
    if args.command == "doctor":
        return store.doctor(args.action)
    if args.command == "migrate":
        return transfer.migrate(args.project, args.source, args.apply)
    root = Path.cwd().resolve()
    if args.command == "remember":
        if args.base_version is not None and args.scope is None:
            raise store.MemoryFailure("E_FORMAT", "Specify --scope when editing a note.")
        return store.remember(root, args.scope or "project", args.key, args.file, args.base_version, args.relate)
    if args.command == "review":
        key = legacy.key(args.key) if args.legacy_path else args.key
        if args.approve is not None:
            if args.scope is None:
                raise store.MemoryFailure("E_FORMAT", "Specify --scope when approving a version.")
            return store.approve(root, key, args.scope, args.approve)
        return store.review(root, key, args.scope, args.before)
    if args.command == "archive":
        return store.archive(root, args.key, args.scope)
    if args.command == "export":
        return transfer.export(root, args.scope, args.out)
    if args.command == "import":
        return transfer.import_package(root, args.source, args.mappings, args.apply)
    return recall.search(root, args.query)


def _show(command, result):
    if command in ("status", "doctor"):
        print(f"Memory: {result['state']} (revision {result['revision']})")
        if command == "doctor":
            print(f"Check: {result['action']}; SQLite FTS5 available.")
    elif command == "remember":
        print(f"Saved {result['key']} ({result['scope']}).")
    elif command == "archive":
        print(f"Archived {result['key']} ({result['scope']}).")
    elif command == "export":
        counts = result["counts"]
        print(f"Exported {counts['memory']} versions, {counts['origin']} origins, "
              f"{counts['edge']} relations ({result['bytes']} bytes).")
        print(result["warning"])
    elif command in ("import", "migrate"):
        counts = result["counts"]
        phase = "Already applied" if result["replayed"] else ("Applied" if result["applied"] else "Preview")
        print(f"{phase}: " + ", ".join(f"{name}={count}" for name, count in sorted(counts.items())))
        if command == "migrate":
            target = next(iter(result["mapping"].values()))
            print("Destination: " + ("new project scope" if target == "project" else target))
        else:
            for source, target in sorted(result["mapping"].items()):
                print(f"  {source} -> {target}")
        if not result["applied"]:
            print(f"No changes. To confirm, repeat with --apply {result['plan_id']}")
        elif command == "migrate":
            print("Inspect a note: review RELATIVE_PATH --scope project --legacy-path")
        if "warning" in result:
            print(result["warning"])
    elif command == "review":
        if "versions" not in result:
            print(f"Approved {result['key']} ({result['scope']}): {result['version']}")
        else:
            print(f"History: {result['key']} ({result['scope']})")
            if result["conflict"]:
                print("Conflict: no version is searchable until you approve one.")
            for record in result["versions"]:
                print(_plain(f"{record['version']} [{record['state']}, {record['source']}]"))
                for origin in record.get("origins", ()):
                    if "legacy" in origin:
                        details = json.dumps(origin["legacy"], ensure_ascii=False)
                        print(_plain(f"  Legacy origin {origin['source']}: {details}"))
                for line in record["body"].splitlines():
                    print(_plain(line))
            if result["next_before"] is not None:
                print(f"More history: --before {result['next_before']}")
    elif not result:
        print("No matching memory.")
    else:
        print(recall.context(result).rstrip())


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = argv[:1] == ["--json"]
    try:
        args = _parser(as_json).parse_args(argv)
        result = _result(args)
    except store.MemoryFailure as exc:
        code, message = exc.code, str(exc)
    except UnicodeError:
        code, message = "E_FORMAT", "Input must be valid UTF-8 text."
    except OSError:
        code, message = "E_IO", "Could not read or write the local file."
    except sqlite3.Error as exc:
        error = getattr(exc, "sqlite_errorcode", 0) & 0xff
        if error in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            code, message = "E_BUSY", "The memory store is busy. Finish the other operation and retry."
        elif error == sqlite3.SQLITE_INTERRUPT:
            code, message = "E_TIMEOUT", "Search exceeded its time budget. Try a narrower query."
        else:
            code, message = "E_STORE", "The memory store or SQLite FTS5 is unavailable. Run doctor."
    else:
        if args.json:
            print(_dumps({"ok": True, "status": "ok", "result": result}))
        else:
            _show(args.command, result)
        return 0
    if as_json:
        print(_dumps({"ok": False, "status": "error", "code": code, "error": message}))
    else:
        print(f"{code}: {message}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
