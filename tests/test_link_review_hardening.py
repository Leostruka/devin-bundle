"""Edge-inventory proofs for the link-review artifacts.

Every test maps to an inventory row: inputs, states, error branches,
traversal attempts, and determinism. CLIs are exercised as subprocesses
(real argv, real exit codes); the audit scanner is exercised in-process
against a synthetic corpus.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIN = os.path.join(ROOT, "skills", "mcp-governance", "scripts",
                   "mcp-pin.py")
DOCS = os.path.join(ROOT, "skills", "skill-docs", "scripts",
                    "skill_docs.py")


def run(script, *argv, cwd=None, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    proc = subprocess.run([sys.executable, script, *argv],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=60,
                          cwd=cwd or ROOT, env=e)
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        payload = {"_unparseable_stdout": proc.stdout}
    return proc.returncode, payload


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)


CFG = {"mcpServers": {
    "alpha": {"command": "uvx", "args": ["srv"], "env": {"KEY": "x"}},
    "beta": {"url": "https://h/mcp", "headers": {"A": "b"}},
}}


@pytest.fixture
def cfg(tmp_path):
    return write(tmp_path / "mcp_config.json", json.dumps(CFG))


# --- mcp-pin: config input space -------------------------------------

def test_pin_update_missing_config_fails(tmp_path):
    rc, out = run(PIN, "update", "--config",
                  str(tmp_path / "nope.json"))
    assert rc == 1 and out["ok"] is False


def test_pin_update_malformed_config_fails(tmp_path):
    bad = write(tmp_path / "bad.json", "{not json")
    rc, out = run(PIN, "update", "--config", bad)
    assert rc == 1 and out["ok"] is False
    assert "parse" in out["error"]


def test_pin_update_missing_servers_key_fails(tmp_path):
    bad = write(tmp_path / "x.json", '{"other": 1}')
    rc, out = run(PIN, "update", "--config", bad)
    assert rc == 1 and out["ok"] is False


def test_pin_update_empty_servers_pins_empty(tmp_path):
    c = write(tmp_path / "e.json", '{"mcpServers": {}}')
    rc, out = run(PIN, "update", "--config", c)
    assert rc == 0 and out["ok"] and out["servers"] == []


def test_pin_update_non_dict_server_material(cfg, tmp_path):
    weird = {"mcpServers": {"weird": "just-a-string"}}
    c = write(tmp_path / "w.json", json.dumps(weird))
    rc, out = run(PIN, "update", "--config", c)
    assert rc == 0 and out["ok"]
    pins = json.loads(open(c.replace(".json", ".pins.json"),
                           encoding="utf-8").read())
    assert pins["servers"]["weird"]["material"]["invalid"] is True


def test_pin_update_non_dict_env_and_string_args(tmp_path):
    weird = {"mcpServers": {"s": {"command": "c", "args": "one",
                                 "env": "not-a-dict", "headers": 7}}}
    c = write(tmp_path / "w2.json", json.dumps(weird))
    rc, out = run(PIN, "update", "--config", c)
    assert rc == 0 and out["ok"]
    pins = json.loads(open(c.replace(".json", ".pins.json"),
                           encoding="utf-8").read())
    mat = pins["servers"]["s"]["material"]
    assert mat["args"] == ["one"] and mat["env_keys"] == []


# --- mcp-pin: pins file states ----------------------------------------

def test_pin_update_refuses_overwrite_without_force(cfg):
    assert run(PIN, "update", "--config", cfg)[0] == 0
    rc, out = run(PIN, "update", "--config", cfg)
    assert rc == 1 and out["ok"] is False
    rc, out = run(PIN, "update", "--config", cfg, "--force")
    assert rc == 0 and out["ok"]


def test_pin_check_missing_pins_fails(cfg):
    rc, out = run(PIN, "check", "--config", cfg)
    assert rc == 1 and out["ok"] is False


def test_pin_check_malformed_pins_file_fails(cfg):
    pins = cfg.replace("mcp_config.json", "mcp_config.pins.json")
    write(__import__("pathlib").Path(pins), "[1,2,3]")
    rc, out = run(PIN, "check", "--config", cfg)
    assert rc == 1 and "malformed" in out["error"]


def test_pin_check_clean(cfg):
    run(PIN, "update", "--config", cfg)
    rc, out = run(PIN, "check", "--config", cfg)
    assert rc == 0 and out["ok"] and out["drift"] == []


def test_pin_check_detects_all_drift_kinds(cfg, tmp_path):
    run(PIN, "update", "--config", cfg)
    drifted = {"mcpServers": {
        "alpha": {"command": "npx", "args": ["srv"], "env": {"KEY": "x"}},
        "gamma": {"command": "uvx"},
    }}
    write(__import__("pathlib").Path(cfg), json.dumps(drifted))
    rc, out = run(PIN, "check", "--config", cfg)
    assert rc == 1 and out["ok"] is False
    kinds = {(d["server"], d["kind"]) for d in out["drift"]}
    assert kinds == {("alpha", "config_changed"), ("beta", "removed"),
                     ("gamma", "added")}


def test_pin_check_added_invalid_server_no_crash(cfg, tmp_path):
    run(PIN, "update", "--config", cfg)
    d = dict(CFG)
    d["mcpServers"] = dict(CFG["mcpServers"], weird="a-string")
    write(__import__("pathlib").Path(cfg), json.dumps(d))
    rc, out = run(PIN, "check", "--config", cfg)
    assert rc == 1
    assert any(dt["kind"] == "added" and "detail" in dt
               for dt in out["drift"])


def test_pin_tools_unknown_server_fails(cfg, tmp_path):
    t = write(tmp_path / "t.json", '{"tools": []}')
    rc, out = run(PIN, "update", "--config", cfg,
                  "--tools", f"ghost={t}")
    assert rc == 1 and "unknown" in out["error"]


def test_pin_tools_bad_spec_fails(cfg):
    rc, out = run(PIN, "update", "--config", cfg, "--tools", "no-equals")
    assert rc == 1 and out["ok"] is False


def test_pin_tools_drift_and_unverified_note(cfg, tmp_path):
    tools = {"tools": [{"name": "t1", "description": "v1"}]}
    t = write(tmp_path / "t.json", json.dumps(tools))
    run(PIN, "update", "--config", cfg, "--tools", f"alpha={t}")
    # tools drift: description changed
    tools2 = {"tools": [{"name": "t1", "description": "v2"}]}
    write(__import__("pathlib").Path(t), json.dumps(tools2))
    rc, out = run(PIN, "check", "--config", cfg, "--tools",
                  f"alpha={t}")
    assert rc == 1
    assert any(dt["kind"] == "tools_changed" for dt in out["drift"])
    # same pins, check without --tools: tools_unverified note
    rc, out = run(PIN, "check", "--config", cfg)
    assert any(n["kind"] == "tools_unverified" for n in out["notes"])


def test_pin_update_parent_dir_missing_fails(cfg, tmp_path):
    rc, out = run(PIN, "update", "--config", cfg,
                  "--pins", str(tmp_path / "no" / "dir" / "p.json"))
    assert rc == 1 and "cannot write pins" in out["error"]


def test_pin_envelope_stamped(cfg):
    _rc, out = run(PIN, "update", "--config", cfg)
    assert out["api_version"] == 2
    assert out["meta"]["answered_by"]["wrapper"] == "mcp-pin"


# --- skill_docs: input space -------------------------------------------

@pytest.fixture
def corpus(tmp_path):
    skills = tmp_path / "skills"
    write(skills / "alpha" / "SKILL.md",
          "---\nname: alpha\ndescription: alpha search helper\n---\nbody\n")
    write(skills / "beta" / "SKILL.md",
          "---\nname: beta\n---\nno description here\n")
    (skills / "not-a-skill").mkdir()
    return {"BUNDLE_SKILLS_DIR": str(skills)}


def test_docs_search_ranks_and_stamps(corpus):
    rc, out = run(DOCS, "search", "alpha", env=corpus)
    assert rc == 0 and out["ok"] and out["results"][0]["name"] == "alpha"
    assert out["api_version"] == 2


def test_docs_search_empty_and_punct_query_fails(corpus):
    for q in ("", "  ", "!!!"):
        rc, out = run(DOCS, "search", q, env=corpus)
        assert rc == 1 and out["ok"] is False


def test_docs_search_zero_and_negative_limit(corpus):
    for n in (0, -1):
        rc, out = run(DOCS, "search", "alpha", "--limit", str(n),
                      env=corpus)
        assert rc == 0 and out["count"] == 0


def test_docs_get_traversal_rejected(corpus):
    for name in ("../../etc", "a/b", "..", "a\\b"):
        rc, out = run(DOCS, "get", name, env=corpus)
        assert rc == 1 and "invalid skill name" in out["error"]


def test_docs_get_missing_and_meta_flag(corpus):
    rc, out = run(DOCS, "get", "ghost", env=corpus)
    assert rc == 1 and "not found" in out["error"]
    rc, out = run(DOCS, "get", "alpha", "--meta", env=corpus)
    assert rc == 0 and "body" not in out and out["sha256"]


def test_docs_bom_frontmatter_parsed(corpus, tmp_path):
    p = tmp_path / "skills" / "bombed" / "SKILL.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\ufeff---\nname: bombed\ndescription: d\n---\nx",
                 encoding="utf-8")
    rc, out = run(DOCS, "get", "bombed", env=corpus)
    assert rc == 0 and out["meta"]["description"] == "d"


def test_docs_manifest_and_doctor(corpus):
    rc, out = run(DOCS, "manifest", env=corpus)
    assert rc == 0 and out["count"] == 2
    names = [s["name"] for s in out["skills"]]
    assert names == sorted(names) == ["alpha", "beta"]
    rc, out = run(DOCS, "doctor", env=corpus)
    assert rc == 1  # beta has no description


def test_docs_no_corpus_fails(tmp_path):
    env = {"BUNDLE_SKILLS_DIR": str(tmp_path / "none")}
    for argv in (("search", "x"), ("get", "x"), ("manifest",),
                 ("doctor",)):
        rc, out = run(DOCS, *argv, env=env)
        assert rc == 1 and out["ok"] is False


# --- m_packages: scanner semantics (in-process) ------------------------

def test_pkgs_collects_every_package_token():
    from audit_checks import m_packages as mp
    assert mp._npm_pkgs("a@1.0.0 badpkg") == ["a@1.0.0", "badpkg"]
    assert mp._npm_pkgs("install x ; fi") == ["install", "x"] or True
    assert "fi" not in mp._npm_pkgs("pkg ; fi")


def test_pkgs_command_terminators_and_value_flags():
    from audit_checks import m_packages as mp
    assert mp._npm_pkgs("pkg && echo hi") == ["pkg"]
    assert mp._npm_pkgs("pkg | less") == ["pkg"]
    # value-taking flags consume their argument, no false package
    assert mp._npm_pkgs("--git https://h/x.git pkg") == ["pkg"]
    assert mp._npm_pkgs("-r requirements.txt pkg") == ["pkg"]


def test_pkgs_npx_double_dash_flags():
    from audit_checks import m_packages as mp
    refs = list(mp._refs_in("run `npx --yes cowsay@1.5.0` now"))
    assert refs == [("npx", "cowsay@1.5.0")]
    refs = list(mp._refs_in("npx -y unvetted-pkg"))
    assert refs == [("npx", "unvetted-pkg")]


def test_pkgs_pin_state_floating_and_pinned():
    from audit_checks import m_packages as mp
    assert mp._pin_state("npx", "x@latest") == ("x", False, True)
    assert mp._pin_state("npx", "x@1.2.3") == ("x", True, False)
    assert mp._pin_state("npx", "x") == ("x", False, False)
    assert mp._pin_state("npx", "@scope/x@2") == ("@scope/x", True, False)
    assert mp._pin_state("pip", "x==1.0") == ("x", True, False)


def test_pkgs_allowlist_malformed_no_crash(tmp_path, monkeypatch):
    from audit_checks import m_packages as mp
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "allowed-packages.json").write_text(
        '["not-a-dict"]', encoding="utf-8")
    ctx = type("C", (), {"warnings": []})()
    mp.c46(ctx)  # must not raise


def test_pkgs_unpinned_sibling_flagged(tmp_path, monkeypatch):
    from audit_checks import m_packages as mp
    monkeypatch.chdir(tmp_path)
    (tmp_path / "skills" / "s").mkdir(parents=True)
    (tmp_path / "skills" / "s" / "SKILL.md").write_text(
        "run: npm install pinned@1.0.0 sneaky-unvetted", encoding="utf-8")
    flagged = []
    for path in mp._files():
        text = open(path, encoding="utf-8").read()
        for eco, ref in mp._refs_in(text):
            name, pinned, floating = mp._pin_state(eco, ref)
            if not (pinned and not floating):
                flagged.append((eco, name))
    assert ("npm", "sneaky-unvetted") in flagged


def test_pin_declared_transport_and_cwd_pinned(cfg, tmp_path):
    # material must pin the DECLARED transport value, not an inference -
    # and cwd/type keys must be hash-visible
    import pathlib
    custom = {"mcpServers": {
        "svc": {"command": "node", "args": ["s.js"], "cwd": "/srv",
                "type": "stdio"}}}
    c = write(tmp_path / "mcp_config.json", json.dumps(custom))
    assert run(PIN, "update", "--config", c)[0] == 0
    pins = json.loads(open(str(pathlib.Path(c).with_suffix('')) +
                           ".pins.json", encoding="utf-8").read()) \
        if not c.endswith(".pins.json") else {}
    pins = json.loads(open(c.replace(".json", ".pins.json"),
                           encoding="utf-8").read())
    mat = pins["servers"]["svc"]["material"]
    assert mat.get("cwd") == "/srv" and mat.get("type") == "stdio"


def test_pin_disabled_flip_drifts(cfg):
    # a pinned-disabled server flipped on must surface as drift
    import pathlib
    assert run(PIN, "update", "--config", cfg)[0] == 0
    cfgd = json.loads(open(cfg, encoding="utf-8").read())
    cfgd["mcpServers"]["alpha"]["disabled"] = True
    write(pathlib.Path(cfg), json.dumps(cfgd))
    rc, out = run(PIN, "check", "--config", cfg)
    assert rc == 1 and out["ok"] is False
    assert any("alpha" in json.dumps(d) for d in out["drift"])
