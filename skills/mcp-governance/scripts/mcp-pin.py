#!/usr/bin/env python3
"""mcp-pin - pin MCP server configs and tool descriptions; detect drift.

Rug-pull defense: an MCP server's tool descriptions feed straight into the
agent prompt. If a server (or its npm/pip package) is swapped for one that
keeps the same name but new descriptions, that is prompt injection via
supply chain. Pin the structure once; `check` fails on any drift.

Pin material per server (never secret values):
  transport, command, args, url, env key names, header key names.

Optional `--tools name=path` inputs pin the live tool list
(name/description/input_schema) - a description swap with unchanged
config is caught here, not in the config pin.

Usage:
    python mcp-pin.py update --config mcp_config.json [--tools n=t.json]
    python mcp-pin.py check  --config mcp_config.json [--tools n=t.json]
    python mcp-pin.py show   --config mcp_config.json
Pins file defaults to <config-stem>.pins.json next to the config.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

WRAPPER = "mcp-pin"
PINS_VERSION = 1


_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _stamp(payload):
    if isinstance(payload, dict):
        meta = payload.get("meta")
        if not isinstance(meta, dict):
            meta = {}
            payload["meta"] = meta
        payload["api_version"] = 2
        meta.setdefault("answered_by",
                        {"bundle": _bundle_version(), "wrapper": WRAPPER})
    return payload


def _emit(payload, code=0):
    text = json.dumps(_stamp(payload), sort_keys=True, indent=2,
                      ensure_ascii=False)
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    return code


def _pins_path(config_path, override=None):
    if override:
        return Path(override)
    c = Path(config_path)
    return c.with_name(c.stem + ".pins.json")


def _server_material(name, scfg):
    """Canonical, secret-free pin material for one server entry."""
    if not isinstance(scfg, dict):
        return {"name": name, "invalid": True}
    env = scfg.get("env")
    headers = scfg.get("headers")
    args = scfg.get("args")
    if isinstance(args, str):
        args = [args]
    elif not isinstance(args, list):
        args = []
    transport = "http" if "url" in scfg else "stdio"
    return {
        "name": name,
        "transport": transport,
        "command": scfg.get("command") or "",
        "args": args,
        "url": scfg.get("url") or "",
        "env_keys": sorted(env) if isinstance(env, dict) else [],
        "header_keys": sorted(headers) if isinstance(headers, dict) else [],
    }


def _sha(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")
                          ).hexdigest()


def _load_config(path):
    p = Path(path)
    if not p.is_file():
        return None, f"config not found: {path}"
    try:
        cfg = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        return None, f"cannot parse config: {e}"
    if not isinstance(cfg, dict) or not isinstance(
            cfg.get("mcpServers"), dict):
        return None, "config missing mcpServers object"
    return cfg["mcpServers"], None


def _load_tools(spec):
    """spec = name=path -> (name, normalized_tools) or error string."""
    name, _, path = spec.partition("=")
    if not name or not path:
        return None, f"bad --tools spec (want name=path): {spec}"
    p = Path(path)
    if not p.is_file():
        return None, f"tools file not found: {path}"
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        return None, f"cannot parse tools file {path}: {e}"
    tools = data.get("tools", data) if isinstance(data, dict) else data
    if not isinstance(tools, list):
        return None, f"tools file {path} is not a tool list"
    norm = sorted(({"name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "input_schema": t.get("input_schema", {})}
                   for t in tools if isinstance(t, dict)),
                  key=lambda t: t["name"])
    return (name, norm), None


def _compute_pins(servers, tool_specs):
    pins = {}
    for name in sorted(servers):
        mat = _server_material(name, servers[name])
        pins[name] = {"config_sha256": _sha(mat),
                      "material": mat,
                      "tools_sha256": None,
                      "tool_names": []}
    for name, norm in tool_specs:
        if name in pins:
            pins[name]["tools_sha256"] = _sha(norm)
            pins[name]["tool_names"] = [t["name"] for t in norm]
    return {"version": PINS_VERSION, "servers": pins}


def _load_tool_specs(args, servers):
    """Parse every --tools spec; fail loud on bad specs and on dumps
    for servers the config does not define (silent ignore hides typos)."""
    specs = []
    for spec in args.tools or []:
        res, err = _load_tools(spec)
        if err:
            return None, err
        specs.append(res)
    unknown = sorted(n for n, _ in specs if n not in servers)
    if unknown:
        return None, ("--tools dump for unknown server(s): "
                      + ", ".join(unknown))
    return specs, None


def _atomic_write(path, text):
    """Write temp file in the same directory then os.replace - a crash
    mid-write can never leave a half-written pins file behind."""
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def cmd_update(args):
    servers, err = _load_config(args.config)
    if err:
        return _emit({"ok": False, "error": err}, 1)
    tool_specs, err = _load_tool_specs(args, servers)
    if err:
        return _emit({"ok": False, "error": err}, 1)
    pins = _compute_pins(servers, tool_specs)
    pp = _pins_path(args.config, args.pins)
    if pp.exists() and not args.force:
        return _emit({"ok": False,
                      "error": f"pins file exists: {pp} (use --force to refresh)"}, 1)
    try:
        _atomic_write(pp, json.dumps(pins, indent=2, sort_keys=True,
                                     ensure_ascii=False) + "\n")
    except OSError as e:
        return _emit({"ok": False, "error": f"cannot write pins: {e}"}, 1)
    return _emit({"ok": True, "pins": str(pp),
                  "servers": sorted(pins["servers"])})


def _current(args):
    servers, err = _load_config(args.config)
    if err:
        return None, err
    tool_specs, err = _load_tool_specs(args, servers)
    if err:
        return None, err
    return _compute_pins(servers, tool_specs), None


def cmd_check(args):
    pp = _pins_path(args.config, args.pins)
    if not pp.is_file():
        return _emit({"ok": False,
                      "error": f"no pins file: {pp} (run 'mcp-pin.py update' first)"}, 1)
    try:
        stored = json.loads(pp.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        return _emit({"ok": False, "error": f"cannot parse pins: {e}"}, 1)
    if not isinstance(stored, dict) or not isinstance(
            stored.get("servers"), dict):
        return _emit({"ok": False,
                      "error": "pins file malformed (want {servers:{}})"}, 1)
    current, err = _current(args)
    if err:
        return _emit({"ok": False, "error": err}, 1)
    drift = []
    notes = []
    old = stored["servers"]
    new = current["servers"]
    for name in sorted(set(old) - set(new)):
        drift.append({"server": name, "kind": "removed"})
    for name in sorted(set(new) - set(old)):
        mat = new[name]["material"]
        detail = (mat.get("command") or mat.get("url")
                  or ("invalid server entry" if mat.get("invalid") else ""))
        drift.append({"server": name, "kind": "added", "detail": detail})
    for name in sorted(set(old) & set(new)):
        if old[name].get("config_sha256") != new[name].get("config_sha256"):
            drift.append({"server": name, "kind": "config_changed"})
        o_t, n_t = (old[name].get("tools_sha256"),
                    new[name].get("tools_sha256"))
        if n_t is not None and o_t is not None and o_t != n_t:
            drift.append({"server": name, "kind": "tools_changed",
                          "detail": "tool list or descriptions drifted (rug-pull signal)"})
        elif o_t is not None and n_t is None:
            notes.append({"server": name, "kind": "tools_unverified",
                          "detail": "pinned tools exist but no --tools dump given"})
    out = {"ok": not drift, "pins": str(pp), "drift": drift}
    if notes:
        out["notes"] = notes
    return _emit(out, 1 if drift else 0)


def cmd_show(args):
    current, err = _current(args)
    if err:
        return _emit({"ok": False, "error": err}, 1)
    return _emit({"ok": True, "computed": current})


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)
    for name, fn in (("update", cmd_update), ("check", cmd_check),
                     ("show", cmd_show)):
        sp = sub.add_parser(name)
        sp.add_argument("--config", required=True)
        sp.add_argument("--pins")
        sp.add_argument("--tools", action="append")
        if name == "update":
            sp.add_argument("--force", action="store_true")
        sp.set_defaults(fn=fn)
    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except Exception as e:
        return _emit({"ok": False, "error": f"{type(e).__name__}: {e}"}, 1)


if __name__ == "__main__":
    sys.exit(main())
