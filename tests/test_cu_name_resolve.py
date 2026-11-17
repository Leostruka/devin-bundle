"""cu_hints.resolve_name - live element lookup by UIA name (issue #632
gap): exact match first, substring fallback, typed rejections.
mouse.py --name wiring: mutual exclusion and via-browser guard reject
before any resolution."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load

cu_hints = load("cu_hints")


def _el(name, x=10, y=20, ct="Button", bounds=None):
    return {"x": x, "y": y, "name": name, "type": ct,
            "bounds": bounds or [x, y, 80, 24], "hwnd": 100,
            "enabled": True}


def _enum(els):
    return {"elements": els, "window": {"hwnd": 100}, "truncated": False}


@pytest.fixture
def fake_enum(monkeypatch):
    holder = {"els": []}
    monkeypatch.setattr(cu_hints, "enum_clickables",
                        lambda scope="focused", timeout=6.0: _enum(holder["els"]))
    return holder


def test_exact_match_returns_entry(fake_enum):
    fake_enum["els"] = [_el("Save"), _el("Cancel")]
    e, r, m = cu_hints.resolve_name("Save")
    assert r is None and m == []
    assert e["name"] == "Save" and e["x"] == 10


def test_exact_is_case_insensitive(fake_enum):
    fake_enum["els"] = [_el("Save As..."), _el("Save")]
    e, r, _ = cu_hints.resolve_name("save")
    assert r is None and e["name"] == "Save"


def test_exact_beats_substring(fake_enum):
    fake_enum["els"] = [_el("Save As..."), _el("Save")]
    e, r, _ = cu_hints.resolve_name("save as")
    assert r is None and e["name"] == "Save As..."


def test_substring_single_match(fake_enum):
    fake_enum["els"] = [_el("Apply changes"), _el("Discard")]
    e, r, _ = cu_hints.resolve_name("apply")
    assert r is None and e["name"] == "Apply changes"


def test_ambiguous_lists_candidates(fake_enum):
    fake_enum["els"] = [_el("File Open"), _el("File Save"), _el("OK")]
    e, r, m = cu_hints.resolve_name("file")
    assert e is None and r == "ambiguous"
    assert m == ["File Open", "File Save"]


def test_no_match(fake_enum):
    fake_enum["els"] = [_el("OK")]
    e, r, m = cu_hints.resolve_name("zzzz")
    assert e is None and r == "no_match" and m == []


def test_empty_name_rejected(fake_enum):
    e, r, _ = cu_hints.resolve_name("   ")
    assert e is None and r == "empty_name"


def test_enum_failure_typed(monkeypatch):
    monkeypatch.setattr(cu_hints, "enum_clickables",
                        lambda scope="focused", timeout=6.0: None)
    e, r, _ = cu_hints.resolve_name("Save")
    assert e is None and r == "enum_failed"


def test_entry_shape_uia_perform_compatible(fake_enum):
    fake_enum["els"] = [_el("Open", bounds=[5, 5, 100, 30])]
    e, _, _ = cu_hints.resolve_name("open")
    for k in ("x", "y", "name", "type", "bounds", "hwnd", "enabled"):
        assert k in e
