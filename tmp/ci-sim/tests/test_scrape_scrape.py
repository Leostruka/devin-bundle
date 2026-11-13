"""scrape.py contract tests — fake Fetcher; browser-gate honesty."""
import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scrape_load  # noqa: E402


class FakeEl:
    def __init__(self, tag="li", text="x", attrib=None):
        self.tag = tag
        self.text = text
        self.attrib = attrib or {}


class FakePage:
    status = 200
    url = "https://t.test/"

    def __init__(self, adaptive_enabled=False):
        self._adaptive_enabled = adaptive_enabled
        self.calls = []

    def css(self, sel, **kw):
        self.calls.append(("css", sel, kw))
        if kw.get("adaptive") and not self._adaptive_enabled:
            raise RuntimeError("adaptive disabled")
        return [FakeEl()]

    def xpath(self, xp, **kw):
        self.calls.append(("xpath", xp, kw))
        return [FakeEl()]


class FakeFetcher:
    last_kwargs = None
    last_page = None

    def get(self, url, **kw):
        FakeFetcher.last_kwargs = kw
        cfg = kw.get("selector_config") or {}
        FakeFetcher.last_page = FakePage(adaptive_enabled=cfg.get("adaptive", False))
        return FakeFetcher.last_page


@pytest.fixture(autouse=True)
def fake_scrapling(monkeypatch):
    mod = types.ModuleType("scrapling")
    mod.Fetcher = FakeFetcher
    monkeypatch.setitem(sys.modules, "scrapling", mod)
    FakeFetcher.last_kwargs = None
    orig_get = FakeFetcher.get
    yield
    FakeFetcher.get = orig_get


@pytest.fixture
def mods(monkeypatch):
    scrape = scrape_load.load("scrape")
    # t.test does not resolve; pretend it is a public host.
    monkeypatch.setattr(scrape, "_resolve", lambda host: {"93.184.216.34"})
    return scrape, scrape_load.load("st_common")


def run_main(scrape, argv, capsys):
    old = sys.argv
    sys.argv = ["scrape.py"] + argv
    code = 0
    try:
        scrape.main()
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.argv = old
    return code, json.loads(capsys.readouterr().out)


def test_fetch_json_shape(mods, capsys, monkeypatch):
    scrape, st_common = mods
    monkeypatch.setattr(st_common, "browser_tier_installed", lambda: True)
    code, out = run_main(scrape, ["https://t.test", "--css", ".item"], capsys)
    assert code == 0
    assert out["ok"] is True
    assert out["status"] == 200
    assert out["url"] == "https://t.test/"
    assert out["count"] == 1 and out["nodes"][0]["tag"] == "li"
    assert "adaptive" not in out


def test_fetch_kwargs_ssrf_and_impersonate(mods, capsys, monkeypatch):
    scrape, st_common = mods
    monkeypatch.setattr(st_common, "browser_tier_installed", lambda: True)
    run_main(scrape, ["https://t.test", "--css", "x",
                      "--impersonate", "edge"], capsys)
    kw = FakeFetcher.last_kwargs
    assert kw["follow_redirects"] == "safe"
    assert kw["impersonate"] == "edge"


def test_adaptive_wires_storage_and_flags(mods, capsys, monkeypatch, tmp_path):
    scrape, st_common = mods
    monkeypatch.setattr(st_common, "browser_tier_installed", lambda: True)
    monkeypatch.setenv("SCRAPE_STATE_ROOT", str(tmp_path))
    code, out = run_main(
        scrape, ["https://t.test", "--css", ".item", "--adaptive"], capsys)
    assert code == 0
    cfg = FakeFetcher.last_kwargs["selector_config"]
    assert cfg["adaptive"] is True
    assert str(tmp_path) in cfg["storage_args"]["storage_file"]
    call = FakeFetcher.last_page.calls[0]
    assert call[2]["auto_save"] is True and call[2]["adaptive"] is True
    assert out["adaptive"]["auto_save"] is True


def test_browser_gate_rejects_when_not_installed(mods, capsys, monkeypatch):
    scrape, st_common = mods
    monkeypatch.setattr(st_common, "browser_tier_installed", lambda: False)
    code, out = run_main(
        scrape, ["https://t.test", "--css", "x", "--browser", "stealthy"],
        capsys)
    assert code == 2
    assert out["ok"] is False
    assert "feature_off:browser_tier_not_installed" in out["error"]


def test_selector_error_exit_1(mods, capsys, monkeypatch):
    scrape, st_common = mods
    monkeypatch.setattr(st_common, "browser_tier_installed", lambda: True)

    class BoomPage(FakePage):
        def css(self, sel, **kw):
            raise ValueError("bad sel")

    FakeFetcher.get = lambda self, url, **kw: BoomPage()
    code, out = run_main(scrape, ["https://t.test", "--css", "x"], capsys)
    assert code == 1
    assert "selector_error" in out["error"]


def test_ssrf_scheme_rejected(mods, capsys, monkeypatch):
    scrape, st_common = mods
    monkeypatch.setattr(st_common, "browser_tier_installed", lambda: True)
    for url in ("file:///etc/passwd", "gopher://x/", "ftp://x/"):
        code, out = run_main(scrape, [url, "--css", "x"], capsys)
        assert code == 2 and "ssrf_blocked" in out["error"]
        assert FakeFetcher.last_kwargs is None


def test_ssrf_private_ip_rejected(mods, capsys, monkeypatch):
    scrape, st_common = mods
    monkeypatch.setattr(st_common, "browser_tier_installed", lambda: True)
    for url in ("http://127.0.0.1:19693/", "http://169.254.169.254/latest",
                "http://10.0.0.1/", "http://[::1]/"):
        code, out = run_main(scrape, [url, "--css", "x"], capsys)
        assert code == 2, url
        assert "ssrf_blocked" in out["error"]


def test_ssrf_private_host_resolution_rejected(mods, capsys, monkeypatch):
    scrape, st_common = mods
    monkeypatch.setattr(st_common, "browser_tier_installed", lambda: True)
    monkeypatch.setattr(scrape, "_resolve", lambda host: {"192.168.1.10"})
    code, out = run_main(scrape, ["https://intranet.corp", "--css", "x"],
                         capsys)
    assert code == 2 and "allow-private" in out["error"]


def test_ssrf_allow_private_flag_passes(mods, capsys, monkeypatch):
    scrape, st_common = mods
    monkeypatch.setattr(st_common, "browser_tier_installed", lambda: True)
    code, out = run_main(
        scrape, ["http://127.0.0.1:8080/", "--css", "x",
                 "--allow-private"], capsys)
    assert code == 0 and out["ok"] is True


def test_ssrf_unresolvable_host_rejected(mods, capsys, monkeypatch):
    scrape, st_common = mods
    monkeypatch.setattr(st_common, "browser_tier_installed", lambda: True)

    def boom(host):
        raise OSError("name or service not known")
    monkeypatch.setattr(scrape, "_resolve", boom)
    code, out = run_main(scrape, ["https://nope.invalid", "--css", "x"],
                         capsys)
    assert code == 2 and "ssrf_blocked" in out["error"]


def test_check_url_allowed_unit(mods):
    scrape, _ = mods
    assert scrape.check_url_allowed("notaurl") is not None
    assert scrape.check_url_allowed("https://ok.test") is None
