"""sc_files — root-bound inspection and hash-verified copy."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                      / "extensions" / "system-control"))
import sc_cli  # noqa: E402
import sc_files  # noqa: E402
import sc_policy  # noqa: E402


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _link(src, dst):
    try:
        os.symlink(src, dst)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")


def _junction(src, dst):
    if os.name != "nt":
        pytest.skip("junctions are Windows-only")
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(dst), str(src)],
                       capture_output=True)
    if r.returncode != 0:
        pytest.skip(f"mklink /J failed: {r.stderr!r}")


def _root_listing(root):
    return sorted(p.name for p in Path(root).iterdir())


def test_inspect_rejects_parent_escape(tmp_path):
    r = sc_files.inspect_path(str(tmp_path), "../outside")
    assert r["ok"] is False and r["status"] == "rejected"


def test_inspect_rejects_dotdot_component_inside(tmp_path):
    (tmp_path / "d").mkdir()
    (tmp_path / "f").write_text("x")
    r = sc_files.inspect_path(str(tmp_path), "d/../f")
    assert r["ok"] is False and r["status"] == "rejected"


def test_inspect_rejects_absolute_path(tmp_path):
    r = sc_files.inspect_path(str(tmp_path), str(tmp_path / "f"))
    assert r["ok"] is False and r["status"] == "rejected"


def test_inspect_rejects_empty_and_nul(tmp_path):
    assert sc_files.inspect_path(str(tmp_path), "")["status"] == "rejected"
    assert sc_files.inspect_path(
        str(tmp_path), "a\x00b")["status"] == "rejected"
    assert sc_files.inspect_path(str(tmp_path), None)["status"] == "rejected"


def test_inspect_rejects_symlink_escape(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir(exist_ok=True)
    (outside / "secret").write_text("s")
    _link(str(outside / "secret"), str(tmp_path / "link"))
    r = sc_files.inspect_path(str(tmp_path), "link")
    assert r["ok"] is False and r["status"] == "rejected"


def test_inspect_rejects_symlink_chain_escape(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-chain"
    outside.mkdir(exist_ok=True)
    (outside / "secret").write_text("s")
    _link(str(outside / "secret"), str(tmp_path / "l2"))
    _link(str(tmp_path / "l2"), str(tmp_path / "l1"))
    r = sc_files.inspect_path(str(tmp_path), "l1")
    assert r["ok"] is False and r["status"] == "rejected"


def test_inspect_rejects_symlink_inside_root(tmp_path):
    (tmp_path / "real").write_text("x")
    _link(str(tmp_path / "real"), str(tmp_path / "lnk"))
    r = sc_files.inspect_path(str(tmp_path), "lnk")
    assert r["ok"] is False and r["status"] == "rejected"


def test_inspect_rejects_junction_component(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "inner").write_text("x")
    _junction(str(target), str(tmp_path / "jct"))
    assert sc_files.inspect_path(str(tmp_path), "jct")["status"] == "rejected"
    assert sc_files.inspect_path(
        str(tmp_path), "jct/inner")["status"] == "rejected"


def test_inspect_missing(tmp_path):
    r = sc_files.inspect_path(str(tmp_path), "nope")
    assert r["ok"] is True and r["status"] == "verified"
    assert r["value"]["type"] == "missing"
    assert not r["value"].get("sha256")


def test_inspect_dir(tmp_path):
    (tmp_path / "d").mkdir()
    r = sc_files.inspect_path(str(tmp_path), "d")
    assert r["status"] == "verified"
    assert r["value"]["type"] == "dir"
    assert r["value"]["is_link"] is False


def test_inspect_file_streaming_hash(tmp_path):
    p = tmp_path / "big"
    blob = os.urandom(4 * 1024 * 1024 + 7)
    p.write_bytes(blob)
    r = sc_files.inspect_path(str(tmp_path), "big")
    assert r["status"] == "verified"
    v = r["value"]
    assert v["type"] == "file"
    assert v["sha256"] == hashlib.sha256(blob).hexdigest()
    assert v["size"] == len(blob)
    assert v["is_link"] is False


def test_inspect_never_returns_contents(tmp_path):
    (tmp_path / "f").write_text("top secret payload")
    r = sc_files.inspect_path(str(tmp_path), "f")
    assert "top secret payload" not in json.dumps(r)


def test_copy_verified_envelope(tmp_path):
    (tmp_path / "a").write_bytes(b"abc")
    expected = hashlib.sha256(b"abc").hexdigest()
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash=expected)
    assert r["ok"] is True and r["status"] == "verified"
    assert r["precondition"]["sha256"] == expected
    assert r["postcondition"]["sha256"] == expected
    assert (tmp_path / "b").read_bytes() == b"abc"


def test_copy_hash_mismatch_leaves_no_residue(tmp_path):
    (tmp_path / "a").write_bytes(b"abc")
    before = _root_listing(tmp_path)
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash="0" * 64)
    assert r["ok"] is False and r["status"] == "rejected"
    assert not (tmp_path / "b").exists()
    assert _root_listing(tmp_path) == before


def test_copy_dry_run_writes_nothing(tmp_path):
    (tmp_path / "a").write_bytes(b"abc")
    expected = hashlib.sha256(b"abc").hexdigest()
    before = _root_listing(tmp_path)
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash=expected, dry_run=True)
    assert r["status"] == "verified"
    assert r["value"]["src_sha256"] == expected
    assert r["value"]["bytes"] == 3
    assert r["value"]["dst"]
    assert _root_listing(tmp_path) == before


def test_copy_dry_run_mismatch_still_rejects(tmp_path):
    (tmp_path / "a").write_bytes(b"abc")
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash="f" * 64, dry_run=True)
    assert r["status"] == "rejected"


def test_copy_existing_dst_rejected_without_overwrite(tmp_path):
    (tmp_path / "a").write_bytes(b"new")
    (tmp_path / "b").write_bytes(b"old")
    expected = hashlib.sha256(b"new").hexdigest()
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash=expected)
    assert r["status"] == "rejected"
    assert (tmp_path / "b").read_bytes() == b"old"


def test_copy_overwrite_replaces_dst(tmp_path):
    (tmp_path / "a").write_bytes(b"new")
    (tmp_path / "b").write_bytes(b"old")
    expected = hashlib.sha256(b"new").hexdigest()
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash=expected, overwrite=True)
    assert r["status"] == "verified"
    assert (tmp_path / "b").read_bytes() == b"new"


def test_copy_dst_in_subdir(tmp_path):
    (tmp_path / "a").write_bytes(b"data")
    (tmp_path / "sub").mkdir()
    expected = hashlib.sha256(b"data").hexdigest()
    r = sc_files.copy_verified(str(tmp_path), "a", "sub/b",
                               expected_hash=expected)
    assert r["status"] == "verified"
    assert (tmp_path / "sub" / "b").read_bytes() == b"data"


def test_copy_rejects_missing_dst_parent(tmp_path):
    (tmp_path / "a").write_bytes(b"data")
    expected = hashlib.sha256(b"data").hexdigest()
    r = sc_files.copy_verified(str(tmp_path), "a", "no/b",
                               expected_hash=expected)
    assert r["status"] == "rejected"


def test_copy_rejects_escape_paths(tmp_path):
    (tmp_path / "a").write_bytes(b"data")
    expected = hashlib.sha256(b"data").hexdigest()
    for src, dst in (("../x", "b"), ("a", "../b"), ("a", "/abs"),
                     ("a", "d/../b")):
        r = sc_files.copy_verified(str(tmp_path), src, dst,
                                   expected_hash=expected)
        assert r["status"] == "rejected", (src, dst)


def test_copy_rejects_symlink_src(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-src"
    outside.mkdir(exist_ok=True)
    (outside / "real").write_bytes(b"z")
    _link(str(outside / "real"), str(tmp_path / "a"))
    r = sc_files.copy_verified(
        str(tmp_path), "a", "b",
        expected_hash=hashlib.sha256(b"z").hexdigest())
    assert r["status"] == "rejected"
    assert not (tmp_path / "b").exists()


def test_copy_source_mutation_invalidates(tmp_path, monkeypatch):
    src = tmp_path / "a"
    src.write_bytes(b"original")
    expected = hashlib.sha256(b"original").hexdigest()
    real_copy = sc_files._stream_copy

    def mutating_copy(src_fd, dst_fd):
        src.write_bytes(b"mutated!")
        return real_copy(src_fd, dst_fd)

    monkeypatch.setattr(sc_files, "_stream_copy", mutating_copy)
    before = _root_listing(tmp_path)
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash=expected)
    assert r["ok"] is False and r["status"] == "rejected"
    assert not (tmp_path / "b").exists()
    assert _root_listing(tmp_path) == before


def test_copy_missing_src_rejected(tmp_path):
    r = sc_files.copy_verified(str(tmp_path), "gone", "b",
                               expected_hash="0" * 64)
    assert r["status"] == "rejected"
    assert not (tmp_path / "b").exists()


def test_copy_bad_expected_hash_rejected(tmp_path):
    (tmp_path / "a").write_bytes(b"x")
    for bad in ("", "zz" * 32, "0" * 63, None, 5):
        r = sc_files.copy_verified(str(tmp_path), "a", "b",
                                   expected_hash=bad)
        assert r["status"] == "rejected", bad


def _run(argv, capsys):
    code = sc_cli.main(argv)
    out = capsys.readouterr().out.strip()
    return code, json.loads(out)


def test_cli_file_inspect(capsys, tmp_path):
    (tmp_path / "f").write_text("x")
    code, r = _run(["file", "inspect", "--root", str(tmp_path),
                    "--path", "f"], capsys)
    assert code == 0 and r["status"] == "verified"
    assert r["value"]["type"] == "file"


def test_cli_file_inspect_reject_exit_2(capsys, tmp_path):
    code, r = _run(["file", "inspect", "--root", str(tmp_path),
                    "--path", "../x"], capsys)
    assert code == 2 and r["status"] == "rejected"


def _copy_request(request_id, root, src, dst, expected, overwrite=False):
    return {
        "version": 1, "request_id": request_id,
        "capability": ("file.copy_overwrite" if overwrite
                       else "file.copy"),
        "args": {"root": str(root), "src": src, "dst": dst,
                 "expected_hash": expected, "dry_run": False,
                 "overwrite": overwrite},
        "deadline_ms": 30000,
        "policy": {"dry_run": False, "confirmation_id": None}}


def _copy_argv(root, src, dst, expected, cid="c" * 64, rid="r1",
               overwrite=False, dry_run=False):
    args = ["file", "copy", "--root", str(root), "--src", src,
            "--dst", dst, "--expected-hash", expected,
            "--request-id", rid, "--confirmation-id", cid]
    if overwrite:
        args.append("--overwrite")
    if dry_run:
        args.append("--dry-run")
    return args


def test_cli_file_copy_requires_confirmation(capsys, tmp_path,
                                             monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path / "tok")
    (tmp_path / "a").write_bytes(b"x")
    expected = hashlib.sha256(b"x").hexdigest()
    code, r = _run(_copy_argv(tmp_path, "a", "b", expected), capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_file_copy_requires_request_id(capsys, tmp_path,
                                           monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path / "tok")
    (tmp_path / "a").write_bytes(b"x")
    expected = hashlib.sha256(b"x").hexdigest()
    args = ["file", "copy", "--root", str(tmp_path), "--src", "a",
            "--dst", "b", "--expected-hash", expected,
            "--confirmation-id", "c" * 64]
    code, r = _run(args, capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_file_copy_confirmed(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path / "tok")
    (tmp_path / "a").write_bytes(b"payload")
    expected = hashlib.sha256(b"payload").hexdigest()
    req = _copy_request("r1", tmp_path, "a", "b", expected)
    cid = sc_policy.issue_confirmation(req)["confirmation_id"]
    code, r = _run(_copy_argv(tmp_path, "a", "b", expected, cid=cid),
                   capsys)
    assert code == 0 and r["status"] == "verified"
    assert (tmp_path / "b").read_bytes() == b"payload"
    code, r = _run(_copy_argv(tmp_path, "a", "b", expected, cid=cid),
                   capsys)
    assert code == 2 and r["status"] == "rejected"


def test_cli_file_copy_invalid_never_consumes_token(
        capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path / "tok")
    (tmp_path / "a").write_bytes(b"payload")
    expected = hashlib.sha256(b"payload").hexdigest()
    req = _copy_request("r1", tmp_path, "a", "b", expected)
    cid = sc_policy.issue_confirmation(req)["confirmation_id"]
    for bad in (
            _copy_argv(tmp_path, "../x", "b", expected, cid=cid),
            _copy_argv(tmp_path, "a", "../b", expected, cid=cid),
            _copy_argv(tmp_path, "a", "b", "nothex", cid=cid),
            _copy_argv(tmp_path / "missing", "a", "b", expected,
                       cid=cid)):
        code, r = _run(bad, capsys)
        assert code == 2 and r["status"] == "rejected", bad
        assert (sc_policy.STATE_DIR / f"{cid}.json").exists()
    code, r = _run(_copy_argv(tmp_path, "a", "b", expected, cid=cid),
                   capsys)
    assert code == 0 and r["status"] == "verified"


def test_cli_file_copy_overwrite_uses_overwrite_capability(
        capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path / "tok")
    (tmp_path / "a").write_bytes(b"new")
    (tmp_path / "b").write_bytes(b"old")
    expected = hashlib.sha256(b"new").hexdigest()
    req = _copy_request("r1", tmp_path, "a", "b", expected)
    cid = sc_policy.issue_confirmation(req)["confirmation_id"]
    code, r = _run(_copy_argv(tmp_path, "a", "b", expected, cid=cid,
                              overwrite=True), capsys)
    assert code == 2 and r["status"] == "rejected"
    req = _copy_request("r1", tmp_path, "a", "b", expected,
                        overwrite=True)
    cid = sc_policy.issue_confirmation(req)["confirmation_id"]
    code, r = _run(_copy_argv(tmp_path, "a", "b", expected, cid=cid,
                              overwrite=True), capsys)
    assert code == 0 and r["status"] == "verified"
    assert (tmp_path / "b").read_bytes() == b"new"


# --- review fixes -------------------------------------------------------

def test_copy_temp_reread_after_fsync(tmp_path, monkeypatch):
    """F2: temp must be re-hashed by re-reading, not trusting writes."""
    (tmp_path / "a").write_bytes(b"abc")
    expected = hashlib.sha256(b"abc").hexdigest()
    calls = []
    real = sc_files._sha256_path

    def spy(path):
        calls.append(path)
        return real(path)

    monkeypatch.setattr(sc_files, "_sha256_path", spy)
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash=expected)
    assert r["status"] == "verified"
    assert len(calls) >= 2  # temp re-read + dst re-read
    assert tmp_path / "b" == Path(calls[-1])


def test_copy_corrupt_temp_reread_rejects(tmp_path, monkeypatch):
    """F2: a corrupted temp (re-read mismatch) rejects, dst absent."""
    (tmp_path / "a").write_bytes(b"abc")
    expected = hashlib.sha256(b"abc").hexdigest()
    real = sc_files._sha256_path
    before = _root_listing(tmp_path)

    def corrupt_first(path):
        if Path(path).name.startswith(".copy-"):
            return ("f" * 64, 3)
        return real(path)

    monkeypatch.setattr(sc_files, "_sha256_path", corrupt_first)
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash=expected)
    assert r["ok"] is False and r["status"] == "rejected"
    assert not (tmp_path / "b").exists()
    assert _root_listing(tmp_path) == before


def test_copy_no_clobber_uses_hardlink(tmp_path, monkeypatch):
    """F3: non-overwrite commit goes through os.link, never os.replace."""
    (tmp_path / "a").write_bytes(b"abc")
    expected = hashlib.sha256(b"abc").hexdigest()
    calls = {"link": 0, "replace": 0}
    real_link, real_replace = os.link, os.replace

    def link(*a, **k):
        calls["link"] += 1
        return real_link(*a, **k)

    def replace(*a, **k):
        calls["replace"] += 1
        return real_replace(*a, **k)

    monkeypatch.setattr(os, "link", link)
    monkeypatch.setattr(os, "replace", replace)
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash=expected)
    assert r["status"] == "verified"
    assert calls["link"] == 1 and calls["replace"] == 0


def test_copy_no_clobber_race_rejected(tmp_path, monkeypatch):
    """F3: dst appearing between lexists check and commit is not
    clobbered — os.link raises FileExistsError → rejected."""
    (tmp_path / "a").write_bytes(b"new")
    expected = hashlib.sha256(b"new").hexdigest()

    real_link = os.link

    def racing_link(src, dst):
        Path(dst).write_bytes(b"racer")
        return real_link(src, dst)

    monkeypatch.setattr(os, "link", racing_link)
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash=expected)
    assert r["ok"] is False and r["status"] == "rejected"
    assert (tmp_path / "b").read_bytes() == b"racer"


def test_cli_file_copy_full_envelope(capsys, tmp_path, monkeypatch):
    """F4: CLI emits the canonical contract.result envelope."""
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path / "tok")
    (tmp_path / "a").write_bytes(b"p")
    expected = hashlib.sha256(b"p").hexdigest()
    req = _copy_request("r1", tmp_path, "a", "b", expected)
    cid = sc_policy.issue_confirmation(req)["confirmation_id"]
    code, r = _run(_copy_argv(tmp_path, "a", "b", expected, cid=cid),
                   capsys)
    assert code == 0
    for key in ("ok", "status", "request_id", "backend", "privilege",
                "precondition", "value", "postcondition", "evidence",
                "error"):
        assert key in r, key
    assert r["backend"] == "files"
    assert r["precondition"]["sha256"] == expected
    assert r["postcondition"]["sha256"] == expected
    assert set(r["evidence"]) == {"cursor", "spill", "dropped"}


@pytest.mark.skipif(os.name == "nt", reason="POSIX fifo test")
def test_inspect_fifo_not_blocked(tmp_path):
    """F5: non-regular files report type, never a blocking open."""
    os.mkfifo(tmp_path / "pipe")
    r = sc_files.inspect_path(str(tmp_path), "pipe")
    assert r["status"] == "verified"
    assert r["value"]["type"] == "other"
    assert not r["value"]["sha256"]


@pytest.mark.skipif(os.name == "nt", reason="POSIX fifo test")
def test_copy_fifo_src_rejected(tmp_path):
    os.mkfifo(tmp_path / "pipe")
    r = sc_files.copy_verified(str(tmp_path), "pipe", "b",
                               expected_hash="0" * 64)
    assert r["status"] == "rejected"


def test_cli_copy_missing_src_no_token_burn(capsys, tmp_path,
                                            monkeypatch):
    """F6: missing source rejects before the token is consumed."""
    monkeypatch.setattr(sc_policy, "STATE_DIR", tmp_path / "tok")
    req = _copy_request("r1", tmp_path, "gone", "b", "0" * 64)
    cid = sc_policy.issue_confirmation(req)["confirmation_id"]
    code, r = _run(_copy_argv(tmp_path, "gone", "b", "0" * 64,
                              cid=cid), capsys)
    assert code == 2 and r["status"] == "rejected"
    assert (sc_policy.STATE_DIR / f"{cid}.json").exists()


def test_copy_oserror_maps_to_unknown(tmp_path, monkeypatch):
    """F8: operational OSError → status unknown, not rejected."""
    (tmp_path / "a").write_bytes(b"x")
    expected = hashlib.sha256(b"x").hexdigest()

    def deny(*a, **k):
        raise PermissionError(13, "denied")

    monkeypatch.setattr(sc_files.os, "open", deny)
    r = sc_files.copy_verified(str(tmp_path), "a", "b",
                               expected_hash=expected)
    assert r["ok"] is False and r["status"] == "unknown"


def test_cli_file_inspect_oserror_exit_1(capsys, tmp_path, monkeypatch):
    (tmp_path / "f").write_text("x")

    def deny(*a, **k):
        raise PermissionError(13, "denied")

    monkeypatch.setattr(sc_files.os, "open", deny)
    code, r = _run(["file", "inspect", "--root", str(tmp_path),
                    "--path", "f"], capsys)
    assert code == 1 and r["status"] == "unknown"


def test_cli_flag_value_swallow_rejected(capsys, tmp_path):
    """F9: a --flag where a value is expected is a missing value."""
    code, r = _run(["file", "inspect", "--root", "--path", "f"],
                   capsys)
    assert code == 2 and r["status"] == "rejected"


@pytest.mark.skipif(os.name != "nt", reason="Windows name mangling")
def test_inspect_trailing_dot_space_rejected(tmp_path):
    """F10: 'a.'/'a ' resolve to 'a' on Windows — reject the alias."""
    (tmp_path / "a").write_text("x")
    for rel in ("a.", "a ", "sub./a", "a/./b"):
        r = sc_files.inspect_path(str(tmp_path), rel)
        assert r["status"] == "rejected", rel
