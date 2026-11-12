"""audit-r6 skill scripts: jwt_tool malformed input, vault scan encodings."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
JWT_DIR = ROOT / "skills" / "dma" / "tools"
OBS_DIR = ROOT / "skills" / "obsidian-workflow" / "scripts"

sys.path.insert(0, str(JWT_DIR))
jwt_spec = importlib.util.spec_from_file_location(
    "jwt_tool", JWT_DIR / "jwt_tool.py")
jwt_tool = importlib.util.module_from_spec(jwt_spec)
jwt_spec.loader.exec_module(jwt_tool)

sys.path.insert(0, str(OBS_DIR))
ss_spec = importlib.util.spec_from_file_location(
    "scan_secrets", OBS_DIR / "scan_secrets.py")
scan_secrets = importlib.util.module_from_spec(ss_spec)
ss_spec.loader.exec_module(scan_secrets)


def test_jwt_malformed_segments_dies():
    # die() -> clean SystemExit, not a binascii/JSONDecodeError traceback
    with pytest.raises(SystemExit):
        jwt_tool.analyze("aaa.bbb.ccc")


def _b64seg(obj):
    import base64
    import json as _json
    return base64.urlsafe_b64encode(
        _json.dumps(obj).encode()).rstrip(b"=").decode()


def test_jwt_scalar_header_dies():
    with pytest.raises(SystemExit):
        jwt_tool.analyze(f"{_b64seg(42)}.{_b64seg({})}.AAAA")


def test_jwt_valid_token_analyzes():
    tok = f"{_b64seg({'alg': 'HS256'})}.{_b64seg({'sub': 'u'})}.AAAA"
    header, payload, sig, alg, flags = jwt_tool.analyze(tok)
    assert alg == "HS256" and payload == {"sub": "u"}


def test_scan_secrets_cp1252_file(tmp_path):
    f = tmp_path / "note.md"
    f.write_bytes(b"caf\xe9 \x93quote\x94")
    findings = scan_secrets.scan_file(str(f))
    assert isinstance(findings, list)


def test_scaffold_end_to_end(tmp_path):
    """scaffold.py must produce a working vault (regression: skill_dir
    pointed at scripts/ -> templates 404; refresh.py shipped NameError)."""
    import subprocess
    vault = tmp_path / "vault"
    r = subprocess.run(
        [sys.executable, str(OBS_DIR / "scaffold.py"),
         "--project-dir", str(tmp_path), "--vault-dir", str(vault),
         "--project-name", "T"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stderr
    assert (vault / "00-Overview.md").exists()
    assert len(list((vault / "Diagrams").glob("*.md"))) == 14
    for name in ("refresh.py", "validate_wiki_config.py",
                 "wiki_structure.py", "wiki_contents.py", "query.py"):
        gen = vault / name
        assert gen.exists(), name
        h = subprocess.run(
            [sys.executable, str(gen), "--help"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace")
        assert h.returncode == 0, (name, h.stderr[-300:])
