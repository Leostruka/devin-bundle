"""parse.py contract tests — fake scrapling injected; no network, no venv."""
import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scrape_load  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "scrape-tools" / "sample.html"


class FakeEl:
    def __init__(self, tag, text, attrib=None):
        self.tag = tag
        self.text = text
        self.attrib = attrib or {}


class FakeSelector:
    def __init__(self, html):
        self.html = html

    def css(self, sel):
        if sel == "!!bad":
            raise ValueError("invalid css")
        if sel == ".item":
            return [FakeEl("li", "alpha"), FakeEl("li", "beta"),
                    FakeEl("li", "gamma")]
        return []

    def xpath(self, xp):
        if xp == "//bad[":
            raise ValueError("invalid xpath")
        if xp == "//a":
            return [FakeEl("a", "link-text",
                           {"id": "lnk", "href": "https://example.com/x"})]
        return []


@pytest.fixture(autouse=True)
def fake_scrapling(monkeypatch):
    mod = types.ModuleType("scrapling")
    mod.Selector = FakeSelector
    monkeypatch.setitem(sys.modules, "scrapling", mod)
    yield


@pytest.fixture
def parse():
    return scrape_load.load("parse")


def run_main(parse, argv, capsys, stdin_text=None, monkeypatch=None):
    if stdin_text is not None and monkeypatch is not None:
        monkeypatch.setattr("sys.stdin.read", lambda: stdin_text)
    monkeypatch_argv = sys.argv
    sys.argv = ["parse.py"] + argv
    code = 0
    try:
        parse.main()
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.argv = monkeypatch_argv
    out = capsys.readouterr().out
    return code, json.loads(out)


def test_css_select_count(parse, capsys):
    code, out = run_main(parse, [str(FIXTURE), "--css", ".item"], capsys)
    assert code == 0
    assert out["ok"] is True
    assert out["count"] == 3
    assert [n["text"] for n in out["nodes"]] == ["alpha", "beta", "gamma"]


def test_css_first(parse, capsys):
    code, out = run_main(parse, [str(FIXTURE), "--css", ".item", "--first"], capsys)
    assert out["count"] == 1
    assert out["nodes"][0]["text"] == "alpha"


def test_xpath_attribs(parse, capsys):
    code, out = run_main(parse, [str(FIXTURE), "--xpath", "//a"], capsys)
    assert out["nodes"][0]["attrib"]["href"] == "https://example.com/x"


def test_bad_selector_nonzero(parse, capsys):
    code, out = run_main(parse, [str(FIXTURE), "--css", "!!bad"], capsys)
    assert code == 1
    assert out["ok"] is False
    assert "selector_error" in out["error"]


def test_zero_matches_ok(parse, capsys):
    code, out = run_main(parse, [str(FIXTURE), "--css", ".nomatch"], capsys)
    assert code == 0
    assert out["count"] == 0


def test_missing_file_exit_2(parse, capsys):
    code, out = run_main(parse, ["no/such/file.html", "--css", "x"], capsys)
    assert code == 2
    assert "read_error" in out["error"]


def test_stdin_source(parse, capsys, monkeypatch):
    code, out = run_main(parse, ["-", "--css", ".item"], capsys,
                         stdin_text="<ul><li class='item'>x</li></ul>",
                         monkeypatch=monkeypatch)
    assert code == 0
    assert out["source"] == "-"
