"""Held-out path and bounded-output contracts; lead-owned."""
import importlib
import os
import stat
import sys
from pathlib import Path

import pytest


EXT = Path(__file__).resolve().parents[3] / "extensions" / "system-control"


def load(name):
    sys.path.insert(0, str(EXT))
    sys.modules.pop(name, None)
    return importlib.import_module(name)


def test_process_exec_rejects_string_and_secret_environment(tmp_path):
    process = load("sc_process")
    with pytest.raises(ValueError):
        process.spawn("echo unsafe")
    with pytest.raises(ValueError, match="environment"):
        process.spawn(
            [sys.executable, "-c", "pass"],
            env_allow={"API_TOKEN": "not-a-real-secret"},
            spill_dir=tmp_path,
        )


def test_process_exec_rejects_non_directory_cwd(tmp_path):
    process = load("sc_process")
    not_directory = tmp_path / "file.txt"
    not_directory.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="cwd"):
        process.spawn([sys.executable, "-c", "pass"], cwd=not_directory)


def test_process_exec_bounds_output_and_spills_full_stream(tmp_path):
    process = load("sc_process")
    result = process.spawn(
        [sys.executable, "-c",
         "import sys;sys.stdout.write('A'*20000)"],
        output_limit=1024,
        spill_dir=tmp_path,
    )
    value = result["value"]
    assert result["status"] == "dispatched"
    assert value["stdout_bytes"] == 20000
    assert value["stdout_truncated"] is True
    assert value["stdout"]["untrusted"] is True
    assert len(value["stdout"]["value"].encode("utf-8")) == 1024
    spill = Path(result["evidence"]["spill"])
    assert spill.is_file()
    assert spill.stat().st_size >= 20000
    if os.name == "posix":
        assert stat.S_IMODE(spill.stat().st_mode) == 0o600


def test_process_exec_timeout_reports_tree_cleanup(tmp_path):
    process = load("sc_process")
    result = process.spawn(
        [sys.executable, "-c", "import time;time.sleep(10)"],
        timeout_s=0.05,
        spill_dir=tmp_path,
    )
    assert result["status"] == "timeout"
    assert result["ok"] is False
    assert result["postcondition"]["exit_observed"] is True
    assert result["postcondition"]["tree_cleanup"] is True
