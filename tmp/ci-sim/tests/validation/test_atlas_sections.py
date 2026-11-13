"""Atlas section parity: app.js SECTIONS, index.html views, build.py data keys.

Drift guard: a section added to one file but not the others renders as a dead
tab (or a view with no data). Each non-boot section must have a <section
id="view-X"> and a data key produced by build.py.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SECTION_DATA_KEY = {"adr": "adrs"}
STATIC_SECTIONS = {"boot"}


def _sections():
    src = open(os.path.join(ROOT, "site", "src", "app.js"), encoding="utf-8").read()
    m = re.search(r'const SECTIONS = \[([^\]]+)\]', src)
    assert m, "SECTIONS array not found in app.js"
    return re.findall(r'"([a-z]+)"', m.group(1))


def _view_ids():
    src = open(os.path.join(ROOT, "site", "src", "index.html"),
               encoding="utf-8").read()
    return re.findall(r'<section id="view-([a-z]+)"', src)


def _data_keys():
    src = open(os.path.join(ROOT, "site", "build.py"), encoding="utf-8").read()
    m = re.search(r'data = \{(.*?)\n    \}', src, re.S)
    assert m, "data dict not found in build.py main()"
    return set(re.findall(r'"([a-z_]+)":', m.group(1)))


def test_every_section_has_a_view():
    assert _sections() == _view_ids(), (
        f"SECTIONS={_sections()} but views={_view_ids()}")


def test_every_section_has_data():
    keys = _data_keys()
    for sec in _sections():
        if sec in STATIC_SECTIONS:
            continue
        key = SECTION_DATA_KEY.get(sec, sec)
        assert key in keys, f"section '{sec}' needs data['{key}'] in build.py"


LISTABLE = {"skills", "agents", "apps", "adr", "docs", "scripts", "hooks"}


def test_repl_ls_covers_listable_sections():
    src = open(os.path.join(ROOT, "site", "src", "app.js"), encoding="utf-8").read()
    ls_block = re.search(r'if\(c === "ls"\)\{(.*?)\n  \}\n', src, re.S)
    assert ls_block, "ls handler not found"
    handled = set(re.findall(r't === "([a-z]+)"', ls_block.group(1)))
    missing = LISTABLE - handled
    assert not missing, f"ls handler missing sections: {missing}"
