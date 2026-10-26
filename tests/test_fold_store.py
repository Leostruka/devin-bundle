"""Tests for the reversible fold store (context-hygiene)."""

import importlib.util
import json
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "skills", "context-hygiene", "scripts",
                      "fold_store.py")


@pytest.fixture
def store(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("fold_store", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "STORE", str(tmp_path / "folds"))
    return mod


def test_save_unfold_roundtrip(store):
    res = store.save("f1", "log of session 1", "full content " * 100)
    assert res["id"] == "f1" and res["tokens_est"] > 0
    assert store.unfold("f1") == "full content " * 100


def test_grep_matches_content_and_summary(store):
    store.save("a", "deploy notes", "release checklist body")
    store.save("b", "unrelated", "other body")
    hits = store.grep("checklist")
    assert [h["id"] for h in hits] == ["a"]
    assert [h["id"] for h in store.grep("deploy")] == ["a"]
    assert store.grep("nonexistent") == []


def test_list_and_delete(store):
    store.save("x", "s", "c")
    assert [f["id"] for f in store.list_folds()] == ["x"]
    store.delete("x")
    assert store.list_folds() == []


def test_invalid_id_rejected(store):
    with pytest.raises(ValueError):
        store.save("../escape", "s", "c")


def test_cli(tmp_path, monkeypatch):
    env = dict(os.environ, FOLD_STORE_DIR=str(tmp_path / "folds"))
    src = tmp_path / "big.txt"
    src.write_text("payload " * 50)
    p = subprocess.run([sys.executable, SCRIPT, "save", "cli1",
                        "--summary", "cli fold", "--content-file", str(src)],
                       capture_output=True, text=True, env=env)
    assert p.returncode == 0
    p = subprocess.run([sys.executable, SCRIPT, "unfold", "cli1"],
                       capture_output=True, text=True, env=env)
    assert "payload" in p.stdout
    p = subprocess.run([sys.executable, SCRIPT, "grep", "payload"],
                       capture_output=True, text=True, env=env)
    assert "cli1" in p.stdout
