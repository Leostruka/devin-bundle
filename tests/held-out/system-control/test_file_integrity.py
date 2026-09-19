"""Held-out file inspection/copy contracts; lead-owned."""
import hashlib
import importlib
import os
import sys
from pathlib import Path

import pytest


EXT = Path(__file__).resolve().parents[3] / "extensions" / "system-control"


def load(name):
    sys.path.insert(0, str(EXT))
    sys.modules.pop(name, None)
    return importlib.import_module(name)


@pytest.fixture
def files():
    try:
        return load("sc_files")
    except ModuleNotFoundError:
        pytest.skip("sc_files not implemented yet")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def test_hash_mismatch_rejects_and_leaves_no_partial(files, tmp_path):
    (tmp_path / "a").write_bytes(b"abc")
    r = files.copy_verified(str(tmp_path), "a", "b",
                            expected_hash=sha(b"wrong"))
    assert r["status"] == "rejected"
    assert not (tmp_path / "b").exists()
    assert [p for p in tmp_path.iterdir() if p.name != "a"] == []


def test_dry_run_verifies_without_writing(files, tmp_path):
    (tmp_path / "a").write_bytes(b"abc")
    r = files.copy_verified(str(tmp_path), "a", "b",
                            expected_hash=sha(b"abc"), dry_run=True)
    assert r["status"] == "verified"
    assert not (tmp_path / "b").exists()


def test_existing_destination_rejects_without_overwrite(files, tmp_path):
    (tmp_path / "a").write_bytes(b"abc")
    (tmp_path / "b").write_bytes(b"old")
    r = files.copy_verified(str(tmp_path), "a", "b",
                            expected_hash=sha(b"abc"))
    assert r["status"] == "rejected"
    assert (tmp_path / "b").read_bytes() == b"old"


def test_symlink_chain_escape_rejects(files, tmp_path):
    outside = tmp_path.parent / f"outside-{os.getpid()}"
    outside.write_text("secret")
    try:
        (tmp_path / "l1").symlink_to(tmp_path / "l2")
        (tmp_path / "l2").symlink_to(outside)
        assert files.inspect_path(str(tmp_path), "l1")["status"] == "rejected"
    finally:
        outside.unlink(missing_ok=True)


def test_source_mutation_invalidates_copy(files, tmp_path):
    (tmp_path / "a").write_bytes(b"abc")
    expected = sha(b"abc")
    (tmp_path / "a").write_bytes(b"mutated")
    r = files.copy_verified(str(tmp_path), "a", "b", expected_hash=expected)
    assert r["status"] == "rejected"
    assert not (tmp_path / "b").exists()
