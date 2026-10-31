"""openui runtime — strict line DSL parser, streaming feeder, HTML renderer.

Exercises extensions/craft-bridge/ui_dsl.py: grammar, roundtrip, bounds,
XSS-safe rendering, semantic-equivalent JSON, real-tokenizer benchmark.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

CB_DIR = Path(__file__).resolve().parents[1] / "extensions" / "craft-bridge"
sys.path.insert(0, str(CB_DIR))

import ui_dsl

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "openui" / "hud_form.dsl"



def test_parse_fixture_structure():
    doc = ui_dsl.parse(FIXTURE.read_text())
    assert len(doc.blocks) == 2
    hud, form = doc.blocks
    assert hud.type == "hud" and hud.attrs["anchor"] == "top-right"
    assert [c.type for c in hud.children] == ["row", "row", "bar"]
    assert form.type == "form" and form.attrs["id"] == "grill-3"
    q1 = form.children[0]
    assert q1.type == "q" and q1.attrs["kind"] == "choice"
    assert q1.attrs["options"] == ["yes", "no", "skip"]


def test_canonical_roundtrip():
    src = FIXTURE.read_text()
    assert ui_dsl.emit(ui_dsl.parse(src)) == src


def test_emit_quotes_only_when_needed():
    doc = ui_dsl.parse('hud title="A B" anchor=top\nbar value=0.5\nend\n')
    out = ui_dsl.emit(doc)
    assert 'title="A B"' in out and "anchor=top" in out


def test_escaped_quote_and_backslash_roundtrip():
    src = ('hud title="say \\"hi\\" \\\\ ok"\n'
           'row label=r value=1\nend\n')
    doc = ui_dsl.parse(src)
    assert doc.blocks[0].attrs["title"] == 'say "hi" \\ ok'
    assert ui_dsl.emit(doc) == src



@pytest.mark.parametrize("src", [
    "hud\nend\nextra=1\n",
    "hud nope=1\nend\n",
    "hud title=a title=b\nend\n",
    "form\nend\n",
    "q choice id=q text=t options=a|b\n",
    "hud\nform id=f\nend\nend\n",
    "hud\nrow label=x value=1\n",
    "end\n",
    "hud title=\"unterminated\nend\n",
    "bar value=0.5\n",
    "form id=f\nrow label=x value=1\nend\n",
    "form id=f\nq id=q text=t options=a\nend\n",
    "hud title=bad<value\nend\n",
    "form id=f\nq choice id=q text=t options=\nend\n",
    "form id=f\nbtn action=\"http://x\"\nend\n",
])
def test_rejects_malformed(src):
    with pytest.raises(ui_dsl.ParseError):
        ui_dsl.parse(src)


def test_error_reports_line_number():
    with pytest.raises(ui_dsl.ParseError) as e:
        ui_dsl.parse("hud\nrow label=x value=1 bogus=2\nend\n")
    assert "line 2" in str(e.value)



def test_line_byte_element_bounds(monkeypatch):
    monkeypatch.setattr(ui_dsl, "MAX_LINES", 5)
    with pytest.raises(ui_dsl.ParseError):
        ui_dsl.parse(FIXTURE.read_text())
    monkeypatch.setattr(ui_dsl, "MAX_LINES", 10**6)
    monkeypatch.setattr(ui_dsl, "MAX_BYTES", 10)
    with pytest.raises(ui_dsl.ParseError):
        ui_dsl.parse(FIXTURE.read_text())
    monkeypatch.setattr(ui_dsl, "MAX_BYTES", 10**9)
    monkeypatch.setattr(ui_dsl, "MAX_ELEMENTS", 2)
    with pytest.raises(ui_dsl.ParseError):
        ui_dsl.parse(FIXTURE.read_text())



def test_stream_partial_line_not_committed():
    sp = ui_dsl.StreamParser()
    sp.feed("hud title=T\nrow label=Kills val")
    snap = sp.snapshot()
    assert len(snap.blocks) == 1
    assert len(snap.blocks[0].children) == 0
    sp.feed("ue=1\nbar value=0.5\nend\n")
    snap = sp.snapshot()
    assert [c.type for c in snap.blocks[0].children] == ["row", "bar"]
    assert snap.blocks[0].children[0].attrs["value"] == "1"


def test_stream_split_across_quote_and_utf8():
    src = 'form id=f title="Café ☕"\nq choice id=q text="T?" options=a|b\nend\n'
    sp = ui_dsl.StreamParser()
    for i in range(0, len(src), 7):
        sp.feed(src[i:i + 7])
    sp.finish()
    doc = sp.snapshot()
    assert doc.blocks[0].attrs["title"] == "Café ☕"


def test_stream_invalid_line_raises_immediately():
    sp = ui_dsl.StreamParser()
    sp.feed("hud\n")
    with pytest.raises(ui_dsl.ParseError):
        sp.feed("row bogus=1\n")


def test_stream_finish_with_dangling_partial():
    sp = ui_dsl.StreamParser()
    sp.feed("hud\nrow label=x value=1")
    with pytest.raises(ui_dsl.ParseError):
        sp.finish()


def test_stream_snapshot_deterministic():
    a, b = ui_dsl.StreamParser(), ui_dsl.StreamParser()
    src = FIXTURE.read_text()
    a.feed(src)
    for i in range(0, len(src), 13):
        b.feed(src[i:i + 13])
    a.finish(); b.finish()
    assert ui_dsl.emit(a.snapshot()) == ui_dsl.emit(b.snapshot()) == src



def test_render_escapes_xss():
    doc = ui_dsl.parse(
        'hud title="<script>alert(1)</script>"\n'
        'row label="<img onerror=x>" value="&<>"\nend\n')
    html = ui_dsl.render_html(doc)
    assert "<script>" not in html and 'onerror="' not in html
    assert "&lt;script&gt;" in html and "&lt;img" in html
    assert "&amp;&lt;&gt;" in html


def test_render_native_controls_and_labels():
    html = ui_dsl.render_html(ui_dsl.parse(FIXTURE.read_text()))
    assert 'role="progressbar"' in html
    assert 'aria-valuenow="60"' in html
    assert '<input type="radio" name="q1"' in html
    assert '<input type="checkbox" name="q2"' in html
    assert '<button type="submit"' in html
    assert 'aria-label="Quest Tracker"' in html
    assert "<legend>" in html and 'for="q1-opt0"' in html
    assert 'id="q1-opt0"' in html and 'id="q2-opt2"' in html
    for bad in ("<script", "http://", "https://", "src=", "href=", "fetch(",
                "onsubmit", "onclick", "onerror="):
        assert bad not in html
    assert 'method="dialog"' in html
    assert "<dialog" in html and " open " in html
    assert "</form></dialog>" in html
    assert 'aria-labelledby="grill-3-title"' in html
    assert 'id="grill-3-title"' in html
    assert "autofocus" in html
    assert "position:static" in html
    assert "<progress" in html and 'value="0.6"' in html and ">60%<" in html


def test_render_multiple_forms_in_flow():
    doc = ui_dsl.parse(
        "form id=a\nbtn action=go\nend\n"
        "form id=b\nbtn action=stop\nend\n")
    html = ui_dsl.render_html(doc)
    assert html.count("<dialog") == 2
    assert html.count("<form") == 2
    assert "position:static" in html


def test_render_progressbar_clamps_value():
    doc = ui_dsl.parse("hud\nbar value=0.05 color=red\nend\n")
    html = ui_dsl.render_html(doc)
    assert 'aria-valuenow="5"' in html
    assert '<progress class="ui-bar-fill" value="0.05" max="1">5%</progress>' \
        in html
    assert 'aria-label="progress"' in html



def equivalent_json(doc):
    return {"version": ui_dsl.DSL_VERSION, "blocks": [
        {"type": b.type, "attrs": b.attrs,
         "children": [{"type": c.type, "attrs": c.attrs}
                      for c in b.children]}
        for b in doc.blocks]}


def test_semantic_json_projection():
    doc = ui_dsl.parse(FIXTURE.read_text())
    sem = ui_dsl.to_jsonable(doc)
    assert sem == equivalent_json(doc)
    q1 = sem["blocks"][1]["children"][0]
    assert q1["attrs"]["options"] == ["yes", "no", "skip"]


def test_tokenizer_benchmark_dsl_beats_json(tmp_path):
    tok, meta = ui_dsl.load_tokenizer()
    src = FIXTURE.read_text()
    doc = ui_dsl.parse(src)
    json_src = json.dumps(equivalent_json(doc), ensure_ascii=False)
    dsl_toks = len(tok.encode(src).ids)
    json_toks = len(tok.encode(json_src).ids)
    ratio = dsl_toks / json_toks
    results = {"tokenizer": meta["tokenizer"],
               "dsl_tokens": dsl_toks, "json_tokens": json_toks,
               "ratio": round(ratio, 4)}
    (tmp_path / "bench.json").write_text(json.dumps(results))
    assert dsl_toks < json_toks
    assert ratio < 0.75



def test_cli_parse_render_roundtrip(tmp_path):
    out = tmp_path / "out.dsl"
    assert ui_dsl.main(["parse", "--input", str(FIXTURE),
                        "--output", str(out)]) == 0
    assert out.read_text() == FIXTURE.read_text()
    html = tmp_path / "out.html"
    assert ui_dsl.main(["render", "--input", str(FIXTURE),
                        "--output", str(html)]) == 0
    assert "<form" in html.read_text()
    assert ui_dsl.main(["render", "--input", str(FIXTURE),
                        "--output", str(html)]) != 0
    assert ui_dsl.main(["render", "--input", str(FIXTURE),
                        "--output", str(html), "--force"]) == 0


def test_cli_benchmark(tmp_path, capsys):
    res = tmp_path / "res.json"
    assert ui_dsl.main(["benchmark", "--fixture", str(FIXTURE),
                        "--output", str(res)]) == 0
    data = json.loads(res.read_text())
    assert data["dsl_tokens"] < data["json_tokens"]
    assert data["tokenizer"]
    assert data["json_form"] == "minified"



def test_stream_bytes_split_multibyte():
    src = ('form id=f title="Café ☕"\n'
           'q choice id=q text=t options=a|b\nend\n')
    b = src.encode("utf-8")
    sp = ui_dsl.StreamParser()
    for i in range(0, len(b), 5):
        sp.feed(b[i:i + 5])
    sp.finish()
    assert sp.snapshot().blocks[0].attrs["title"] == "Café ☕"


def test_stream_invalid_and_truncated_utf8():
    sp = ui_dsl.StreamParser()
    with pytest.raises(ui_dsl.ParseError):
        sp.feed(b"hud\nrow label=\xffbad value=1\n")
    sp2 = ui_dsl.StreamParser()
    sp2.feed("hud\nrow label=x value=1\nend\n".encode() + "é".encode()[:1])
    with pytest.raises(ui_dsl.ParseError):
        sp2.finish()


def test_stream_lone_surrogate_poisons():
    sp = ui_dsl.StreamParser()
    with pytest.raises(ui_dsl.ParseError):
        sp.feed("hud\nrow label=\ud800bad value=1\n")
    with pytest.raises(ui_dsl.ParseError):
        sp.feed("x")


def test_parse_encoding_errors_are_parseerror():
    with pytest.raises(ui_dsl.ParseError):
        ui_dsl.parse(b"hud\n\xff\nend\n")
    with pytest.raises(ui_dsl.ParseError):
        ui_dsl.parse("hud title=\ud800bad\nend\n")


def test_stream_partial_line_length_bound(monkeypatch):
    monkeypatch.setattr(ui_dsl, "MAX_LINE_LEN", 16)
    sp = ui_dsl.StreamParser()
    with pytest.raises(ui_dsl.ParseError):
        sp.feed("hud\n" + "x" * 20)


@pytest.mark.parametrize("src", [
    "form id=f\nq choice kind=evil id=q text=t options=a\nend\n",
    "form id=f\nq kind=evil id=q text=t options=a\nend\n",
    "form id=9bad\nbtn action=go\nend\n",
    "form id=\"has space\"\nbtn action=go\nend\n",
    "form id=f\nq choice id=q text=t options=a\nend\n"
    "form id=f\nbtn action=go\nend\n",
    "form id=f\nq choice id=q text=t options=a\n"
    "q multi id=q text=u options=b\nend\n",
    "form id=f\nq choice id=q text=t options=a|a\nend\n",
    "form id=f title=T\nq choice id=f-title text=Q options=a|b\nend\n",
    "form id=q1-opt0\nq choice id=q1 text=t options=a\nend\n",
    "form id=f\nq choice id=q text=t options=a\nend\n"
    "form id=q-opt0\nbtn action=go\nend\n",
])
def test_rejects_ids_reserved_kind_dup_options(src):
    with pytest.raises(ui_dsl.ParseError):
        ui_dsl.parse(src)


def test_cli_bounded_input_and_no_clobber(tmp_path, monkeypatch):
    monkeypatch.setattr(ui_dsl, "MAX_BYTES", 50)
    assert ui_dsl.main(["parse", "--input", str(FIXTURE),
                        "--output", str(tmp_path / "o.dsl")]) == 2
    monkeypatch.setattr(ui_dsl, "MAX_BYTES", 10**9)
    out = tmp_path / "o.html"
    out.write_text("KEEP ME")
    assert ui_dsl.main(["render", "--input", str(FIXTURE),
                        "--output", str(out)]) == 2
    assert out.read_text() == "KEEP ME"


def test_benchmark_local_tokenizer_artifact(tmp_path):
    import hashlib
    tok, _ = ui_dsl.load_tokenizer()
    p = tmp_path / "tok.json"
    tok.save(str(p))
    res = ui_dsl.benchmark(FIXTURE.read_text(), tokenizer=str(p),
                           fixture_name="hud_form.dsl")
    assert res["tokenizer"] == str(p)
    assert res["tokenizer_sha256"] == hashlib.sha256(
        tok.to_str().encode("utf-8")).hexdigest()
    assert res["input_sha256"] == hashlib.sha256(
        ui_dsl.emit(ui_dsl.parse(FIXTURE.read_text()))
        .encode("utf-8")).hexdigest()
    assert res["fixture"] == "hud_form.dsl"
    assert res["json_form"] == "minified"
    doc = ui_dsl.parse(FIXTURE.read_text())
    min_json = json.dumps(equivalent_json(doc), ensure_ascii=False,
                          separators=(",", ":"))
    assert res["fixture_bytes_json"] == len(min_json.encode("utf-8"))


@pytest.mark.skipif(importlib.util.find_spec("playwright") is None,
                    reason="playwright not installed")
def test_browser_native_dialog_submit(tmp_path):
    """Real headless Chrome smoke (system binary, ephemeral profile):
    radio select + native submit must close the dialog in-page — URL
    unchanged, no network request issued."""
    from playwright.sync_api import sync_playwright
    html = tmp_path / "ui.html"
    html.write_text(ui_dsl.render_html(ui_dsl.parse(FIXTURE.read_text())))
    requests = []
    with sync_playwright() as pw:
        exe = None
        for cand in (
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ):
            if Path(cand).exists():
                exe = cand
                break
        browser = pw.chromium.launch(
            headless=True,
            executable_path=exe) if exe else pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("request", lambda r: requests.append(r.url))
        page.goto(html.as_uri())
        before = page.url
        assert page.eval_on_selector("dialog", "d => d.open") is True
        page.check("#q1-opt0")
        assert page.eval_on_selector("#q1-opt0", "i => i.checked") is True
        page.click("button[type=submit]")
        assert page.url == before
        assert page.eval_on_selector("dialog", "d => d.open") is False
        assert page.eval_on_selector("progress", "p => p.value") == 0.6
        browser.close()
    assert all(u.startswith("file:") for u in requests)
