"""rz-ops wrapper gate: contract enforcement, preset whitelist,
injection guards, and safety boundaries for the rizin RE path."""
import os
import py_compile
import subprocess
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
WRAPPER = os.path.join(repo_root, "extensions", "rz-ops", "wrapper.py")


def _read(rel):
    with open(os.path.join(repo_root, rel), encoding="utf-8") as fh:
        return fh.read()


def _run(*argv):
    return subprocess.run(
        [sys.executable, WRAPPER] + list(argv),
        capture_output=True, text=True, timeout=60)


def test_wrapper_exists_and_compiles():
    assert os.path.isfile(WRAPPER)
    py_compile.compile(WRAPPER, doraise=True)


def test_no_shell_dispatch():
    src = _read("extensions/rz-ops/wrapper.py")
    assert "shell=True" not in src
    assert "os.system" not in src
    assert "subprocess.run" in src


def test_exec_subcommands_whitelisted():
    src = _read("extensions/rz-ops/wrapper.py")
    assert "EXEC_SUBCOMMANDS" in src
    for sub in ("info", "functions", "imports", "strings", "disasm",
                "decompile", "xrefs", "diff", "find", "sign", "dbg"):
        assert '"%s"' % sub in src


def test_contract_enforced_on_exec():
    src = _read("extensions/rz-ops/wrapper.py")
    for field in ("target", "window", "roe"):
        assert '"%s"' % field in src or "'%s'" % field in src
    r = _run("functions", "--target", "x.bin")
    assert r.returncode == 2
    assert "contract_violation" in r.stdout


def test_dbg_requires_confirm_and_dcmd():
    r = _run("dbg", "--target", "x.bin", "--window", "w", "--roe", "r")
    assert r.returncode == 3
    assert "requires_confirmation" in r.stdout
    src = _read("extensions/rz-ops/wrapper.py")
    assert "VALID_DBG_CMD" in src
    assert "d[a-zA-Z?]" in src


def test_free_text_never_reaches_rizin_command():
    """--fcn/--darg are regex-validated before reaching -c strings."""
    src = _read("extensions/rz-ops/wrapper.py")
    assert "VALID_TOKEN" in src
    r = _run("disasm", "--target", "x.bin", "--window", "w", "--roe", "r",
             "--fcn", "main;!calc")
    assert r.returncode == 2
    assert "rejected" in r.stdout


def test_capabilities_and_missing_engine_honesty():
    r = _run("capabilities")
    assert r.returncode == 0
    assert '"rz-ops"' in r.stdout and '"dbg"' in r.stdout
    r = _run("doctor")
    assert "status" in r.stdout  # ok/degraded/missing, never fabricated
