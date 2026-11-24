"""P4 design-intelligence additions: unslop-ui copy tells + CSS craft.

Each new check-id must fire on a positive fragment/fixture and stay
silent on a negative one. Registry entries carry source citations.
"""
import json
import os
import subprocess
import sys

EXT = os.path.join(os.path.dirname(__file__), "..", "extensions",
                   "design-intelligence")
FIX = os.path.join(EXT, "tests", "fixtures")
PY = sys.executable
sys.path.insert(0, EXT)
import checks  # noqa: E402
from rules_registry import ANTIPATTERNS  # noqa: E402

NEW_RULES = [
    "unslop-eyebrow-label",
    "unslop-decorative-numbering",
    "unslop-subtitle-repeat",
    "unslop-self-explaining-caption",
    "unslop-dead-status-chip",
    "static-viewport-units",
    "palette-color-sprawl",
    "gradient-missing-oklch",
    "non-concentric-radius",
    "unmasked-horizontal-scroll",
]


def run(script, *argv):
    return subprocess.run([PY, os.path.join(EXT, script), *argv],
                          capture_output=True, encoding="utf-8",
                          errors="replace")


def fires(rule, html="", css=""):
    return bool(checks.CHECKS[rule](html, css, "t.html"))


def test_new_rules_registered_with_citations():
    by_id = {r["id"]: r for r in ANTIPATTERNS}
    for rid in NEW_RULES:
        r = by_id[rid]
        assert r["scope"] == "static"
        assert r.get("source"), rid
        assert r.get("severity") in ("warn", "info"), rid
    unslop = [by_id[r]["source"] for r in NEW_RULES if r.startswith("unslop")]
    assert all("unslop-ui" in s for s in unslop)


def test_unslop_copy_tells_positive_and_negative():
    pos = [
        ("unslop-eyebrow-label",
         '<span class="eyebrow">INTRODUCING</span><h1>Ledger</h1>'),
        ("unslop-eyebrow-label",
         '<p>NEW · BETA</p>\n<h3>Pricing</h3>'),
        ("unslop-decorative-numbering",
         '<span>01</span><h2>Features</h2>'),
        ("unslop-decorative-numbering",
         '<h2>01 // Features</h2>'),
        ("unslop-subtitle-repeat",
         '<h2>Pricing Plans</h2><p>Pricing plans for every team</p>'),
        ("unslop-self-explaining-caption",
         '<p class="helper">Click the button below to get started</p>'),
        ("unslop-self-explaining-caption",
         '<figcaption>Each bar represents one month of revenue</figcaption>'),
        ("unslop-dead-status-chip",
         '<span class="badge live-dot">LIVE</span>'),
        ("unslop-dead-status-chip",
         '<span class="chip">v2.4 · Synced</span>'),
    ]
    for rid, frag in pos:
        assert fires(rid, html=frag), rid

    neg = [
        ("unslop-eyebrow-label",
         '<p>Simple honest copy</p><h1>Products</h1>'),
        ("unslop-decorative-numbering",
         '<ol><li>First install the CLI</li></ol><h2>Guide</h2>'),
        ("unslop-subtitle-repeat",
         '<h1>Products</h1><p>Simple, honest interface. No noise.</p>'),
        ("unslop-self-explaining-caption",
         '<p>Revenue grew 12% year over year in every region</p>'),
        ("unslop-dead-status-chip",
         '<span class="badge">{isLive && "LIVE"}</span>'),
        ("unslop-dead-status-chip",
         '<span class="badge">🔥 Popular</span>'),
    ]
    for rid, frag in neg:
        assert not fires(rid, html=frag), rid


def test_css_craft_positive_and_negative():
    pos = [
        ("static-viewport-units", "", ".hero{min-height:100vh}"),
        ("palette-color-sprawl",
         "", ":root{--a:#fff;--b:#000;--c:#f00;--d:#0f0;--e:#00f}"),
        ("gradient-missing-oklch",
         "", ".x{background:linear-gradient(90deg,#fff,#000)}"),
        ("non-concentric-radius",
         "", ".card{border-radius:16px;padding:16px}"
              ".card .thumb{border-radius:8px}"),
        ("unmasked-horizontal-scroll",
         "", ".carousel{overflow-x:auto;scroll-snap-type:x mandatory}"),
    ]
    for rid, h, css in pos:
        assert fires(rid, html=h, css=css), rid

    neg = [
        ("static-viewport-units",
         "", "@media (min-width:1200px){.hero{height:100vh}}"),
        ("static-viewport-units", "", ".hero{min-height:100dvh}"),
        ("palette-color-sprawl", "", ":root{--a:#fff;--b:#000}"),
        ("gradient-missing-oklch",
         "", ".x{background:linear-gradient(in oklch,red,blue)}"),
        ("non-concentric-radius",
         "", ".card{border-radius:16px;padding:8px}"
              ".card .thumb{border-radius:8px}"),
        ("unmasked-horizontal-scroll",
         "", ".carousel{overflow-x:auto;"
              "mask-image:linear-gradient(90deg,transparent,#000)}"),
        ("unmasked-horizontal-scroll", "", ".table-wrap{overflow-x:auto}"),
    ]
    for rid, h, css in neg:
        assert not fires(rid, html=h, css=css), rid


def test_fixtures_cover_all_new_ids():
    r = run("design_lint.py", FIX, "--json")
    assert r.returncode == 2
    payload = json.loads(r.stdout[r.stdout.find("{"):])
    rules = {f["rule"] for f in payload["findings"]}
    assert set(NEW_RULES) <= rules


def test_clean_fixtures_stay_silent_for_new_rules():
    for name in ("clean.html", "clean.css"):
        r = run("design_lint.py", os.path.join(FIX, name), "--json")
        payload = json.loads(r.stdout[r.stdout.find("{"):])
        hit = {f["rule"] for f in payload["findings"]} & set(NEW_RULES)
        assert not hit, (name, hit)


def test_jsx_classname_and_binding_guards():
    # className= (JSX) still detects eyebrow; {expr} binding suppresses
    # the dead-status chip.
    assert fires("unslop-eyebrow-label",
                 html='<span className="eyebrow">NEW</span><h2>Go</h2>')
    assert not fires("unslop-dead-status-chip",
                     html='<span className="badge">{"LIVE"}</span>')
