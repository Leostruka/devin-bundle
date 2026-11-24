"""ui-dsl `emit --format a2ui` - A2UI v1.0 basic-catalog projection (P5).

Golden structure, data-binding boundary (structure + references only,
no business data), determinism, and error-path exit codes.
"""
import json
import os
import sys
from pathlib import Path

import pytest

CB_DIR = Path(__file__).resolve().parents[1] / "extensions" / "ui-dsl"
sys.path.insert(0, str(CB_DIR))

import ui_dsl

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "openui" / "hud_form.dsl"
ALLOWED = {"Text", "Row", "Column", "Card", "Button", "TextField",
           "CheckBox", "Divider", "List"}


def emit_doc(src):
    return ui_dsl.to_a2ui(ui_dsl.parse(src))


def test_golden_top_level_shape():
    d = emit_doc(FIXTURE.read_text(encoding="utf-8"))
    assert d["version"] == "1.0"
    su = d["surfaceUpdate"]
    assert su["surfaceId"].startswith("dsl-")
    assert su["catalogId"].endswith("catalogs/basic/catalog.json")
    assert isinstance(su["components"], list) and su["components"]


def test_component_names_within_basic_catalog_subset():
    d = emit_doc(FIXTURE.read_text(encoding="utf-8"))
    comps = d["surfaceUpdate"]["components"]
    names = {c["component"] for c in comps}
    assert names <= ALLOWED, names - ALLOWED
    assert {"Text", "Row", "Column", "Card", "Button", "CheckBox"} <= names


def test_referential_integrity_and_unique_ids():
    d = emit_doc(FIXTURE.read_text(encoding="utf-8"))
    comps = d["surfaceUpdate"]["components"]
    ids = [c["id"] for c in comps]
    assert len(ids) == len(set(ids))
    assert "root" in ids
    idset = set(ids)
    for c in comps:
        for key in ("child", "children"):
            if key not in c:
                continue
            refs = c[key] if isinstance(c[key], list) else [c[key]]
            assert all(r in idset for r in refs), (c["id"], key, refs)


def test_data_bindings_are_paths_not_literals():
    d = emit_doc(FIXTURE.read_text(encoding="utf-8"))
    comps = d["surfaceUpdate"]["components"]
    paths = []

    def walk(v):
        if isinstance(v, dict):
            if "@path" in v:
                paths.append(v["@path"])
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(comps)
    assert "/blocks/0/children/0/value" in paths
    assert "/blocks/0/children/2/value" in paths  # bar
    assert "/forms/grill-3/questions/q1/options/0" in paths
    assert "/forms/grill-3/questions/q2/options/2" in paths
    # boundary: no dataModel payload - the host binds server-side
    assert "dataModel" not in json.dumps(d)
    # literal DSL data values must not leak as bound content
    text_vals = [c.get("text") for c in comps
                 if c["component"] == "Text" and isinstance(c.get("text"), str)]
    assert "12" not in text_vals and "0.6" not in text_vals


def test_button_action_and_variant():
    d = emit_doc(FIXTURE.read_text(encoding="utf-8"))
    comps = {c["id"]: c for c in d["surfaceUpdate"]["components"]}
    submit = comps["blk1-ch2-btn"]
    assert submit["component"] == "Button"
    assert submit["variant"] == "primary"
    assert submit["action"]["event"]["name"] == "submit"
    assert submit["action"]["event"]["context"] == {"form": "grill-3"}
    cancel = comps["blk1-ch3-btn"]
    assert cancel["variant"] == "borderless"


def test_deterministic_roundtrip():
    src = FIXTURE.read_text(encoding="utf-8")
    a = ui_dsl.a2ui_json(ui_dsl.parse(src))
    b = ui_dsl.a2ui_json(ui_dsl.parse(ui_dsl.emit(ui_dsl.parse(src))))
    assert a == b
    d1, d2 = json.loads(a), json.loads(b)
    assert d1["surfaceUpdate"]["surfaceId"] == \
        d2["surfaceUpdate"]["surfaceId"]


def test_no_secrets_or_urls_in_output():
    out = ui_dsl.a2ui_json(ui_dsl.parse(FIXTURE.read_text(encoding="utf-8")))
    for bad in ("http://", "https://", "api_key", "token", "password",
                "secret"):
        # catalogId is the only permitted URL-ish string
        assert bad not in out.replace(A2UI_CATALOG_URL, "")


A2UI_CATALOG_URL = ("https://a2ui.org/specification/v1_0/catalogs/"
                    "basic/catalog.json")


def test_cli_emit_writes_json_and_refuses_clobber(tmp_path):
    out = tmp_path / "out.json"
    assert ui_dsl.main(["emit", "--input", str(FIXTURE),
                        "--output", str(out), "--format", "a2ui"]) == 0
    d = json.loads(out.read_text(encoding="utf-8"))
    assert d["version"] == "1.0" and "surfaceUpdate" in d
    assert "api_version" not in d  # artifact doc, not an envelope
    # overwrite refusal
    assert ui_dsl.main(["emit", "--input", str(FIXTURE),
                        "--output", str(out), "--format", "a2ui"]) == 2
    assert ui_dsl.main(["emit", "--input", str(FIXTURE),
                        "--output", str(out), "--format", "a2ui",
                        "--force"]) == 0


def test_cli_emit_stdout_default(tmp_path, capsys):
    assert ui_dsl.main(["emit", "--input", str(FIXTURE)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["version"] == "1.0"


def test_cli_emit_error_paths(tmp_path, capsys):
    bad = tmp_path / "bad.dsl"
    bad.write_text("hud\nrow bogus=1\nend\n", encoding="utf-8")
    rc = ui_dsl.main(["emit", "--input", str(bad), "--format", "a2ui"])
    assert rc != 0
    env = json.loads(capsys.readouterr().out)
    assert env["ok"] is False and env["api_version"] == 2
    # unsupported format -> typed envelope + nonzero
    rc = ui_dsl.main(["emit", "--input", str(FIXTURE),
                      "--format", "yaml"])
    assert rc != 0
    env = json.loads(capsys.readouterr().out)
    assert env["ok"] is False
    # missing input -> io envelope + nonzero
    rc = ui_dsl.main(["emit", "--input", str(tmp_path / "nope.dsl"),
                      "--format", "a2ui"])
    assert rc != 0
    env = json.loads(capsys.readouterr().out)
    assert env["ok"] is False and env["api_version"] == 2
