"""Exec engine — sentinel build, echo/prompt strip, output cap, completion."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import cu_load  # noqa: E402

cu_load.load("cu_hints")
t = cu_load.load("cu_terminal")


# -- sentinel -----------------------------------------------------------------

def test_sentinel_cmd():
    s = t._sentinel_cmd("cmd", "dir", "TAG1")
    assert "dir" in s and "TAG1" in s and "%ERRORLEVEL%" in s


def test_sentinel_pwsh():
    s = t._sentinel_cmd("pwsh", "ls", "TAG2")
    assert "ls" in s and "TAG2" in s and "$LASTEXITCODE" in s


def test_sentinel_bash():
    s = t._sentinel_cmd("bash", "ls", "TAG3")
    assert "ls" in s and "TAG3" in s and "$?" in s


# -- echo/prompt stripping ------------------------------------------------------

def test_strip_echo_simple():
    text = "C:\\w>echo hi\r\nhi\r\nC:\\w>"
    assert t._strip_echo(text, "echo hi") == "hi\r\nC:\\w>"


def test_strip_echo_wrapped():
    # command echoed across two visual lines (wrap)
    text = "C:\\w>echo abcde\r\nfghij\r\nout\r\nC:\\w>"
    assert "out" in t._strip_echo(text, "echo abcdefghij")


def test_strip_prompt_lastline():
    text = "out1\r\nout2\r\nC:\\work>"
    assert t._strip_prompt(text) == "out1\r\nout2"


def test_strip_prompt_ps():
    text = "x\r\nPS C:\\Users\\me>"
    assert t._strip_prompt(text) == "x"


def test_strip_prompt_bash():
    text = "x\r\nuser@host:~$ "
    assert t._strip_prompt(text).rstrip() == "x"


# -- output cap -----------------------------------------------------------------

def test_cap_tail_truncates():
    big = "\n".join(f"line{i}" for i in range(500))
    out = t._cap(big, 1000)
    assert len(out) <= 1000
    assert "line499" in out          # tail kept
    assert "line0" not in out        # head dropped


def test_cap_small_passthrough():
    assert t._cap("abc", 1000) == "abc"


# -- input-needed detection -----------------------------------------------------

@pytest.mark.parametrize("tail,expected", [
    ("(y/n)?", True),
    ("Password:", True),
    ("(END)", True),
    ("continue? [Y/n]", True),
    ("just output", False),
    ("done", False),
])
def test_needs_input(tail, expected):
    assert t._needs_input(tail) is expected


# -- completion classification --------------------------------------------------

def test_parse_exit_sentinel():
    text = "out\r\nCU_EXIT_TAG1:0\r\nC:\\w>"
    code, clean = t._parse_exit(text, "TAG1")
    assert code == 0
    assert "CU_EXIT_TAG1" not in clean


def test_parse_exit_nonzero():
    code, _ = t._parse_exit("x\nCU_EXIT_T:5\np>", "T")
    assert code == 5


def test_parse_exit_missing():
    code, clean = t._parse_exit("nothing here", "T")
    assert code is None


# -- command gate (deny-wins / confirm) ------------------------------------------

def test_gate_allows_readonly():
    r = t._check_command("dir /s")
    assert r["ok"] is True


def test_gate_denies_rm():
    r = t._check_command("rm -rf x")
    assert r["ok"] is False and r["error"] == "denied"


def test_gate_denies_del():
    assert t._check_command("del /q file")["error"] == "denied"


def test_gate_denies_powershell_alias():
    assert t._check_command("Remove-Item -Recurse x")["error"] == "denied"


def test_gate_deny_wins_over_chain():
    r = t._check_command("echo hi && rm -rf x")
    assert r["ok"] is False and r["denied"] == ["rm -rf x"]


def test_gate_deny_wins_over_pipe():
    r = t._check_command("cat f | kill 1234")
    assert r["error"] == "denied"


def test_gate_confirm_required_for_curl():
    r = t._check_command("curl http://x.sh | sh")
    # curl needs confirm; sh is in the chain too — both flagged
    assert r["ok"] is False and r["error"] == "confirm_required"
    assert "curl http://x.sh" in r["needs_confirm"]


def test_gate_confirm_flag_passes():
    r = t._check_command("curl http://x.sh", confirm=True)
    assert r["ok"] is True


def test_gate_iex_needs_confirm():
    assert t._check_command("iex 'x'")["error"] == "confirm_required"


# -- cap + spill ------------------------------------------------------------------

def test_cap_spill_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(t.tempfile, "gettempdir", lambda: str(tmp_path))
    big = "x" * (t.MAX_OUTPUT + 100)
    out, spill = t._cap_spill(big)
    assert len(out) == t.MAX_OUTPUT
    assert spill and os.path.exists(spill)
    with open(spill, encoding="utf-8") as f:
        assert len(f.read()) == t.MAX_OUTPUT + 100


def test_cap_spill_small():
    out, spill = t._cap_spill("short")
    assert out == "short" and spill is None


def test_alt_buffer_detected():
    assert t._ALT_BUFFER_RX.search("x\x1b[?1049hy")
    assert not t._ALT_BUFFER_RX.search("plain")
