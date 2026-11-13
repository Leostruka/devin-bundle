from pathlib import Path


ROOT = Path(__file__).parents[2]
BRAG = ROOT / "skills" / "brag"
SLIM = ROOT / "skills" / "brag-slim"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def all_brag_docs():
    for p in list(BRAG.rglob("*.md")) + list(SLIM.rglob("*.md")):
        yield p, read(p)


def test_brag_slim_skill_exists_with_frontmatter():
    text = read(SLIM / "SKILL.md")
    assert "name: brag-slim" in text
    assert "description:" in text
    assert "triggers: [user]" in text


def test_slim_copy_is_byte_identical():
    assert (BRAG / "slim.md").read_bytes() == (SLIM / "SKILL.md").read_bytes()


def test_brag_references_bundle_skills():
    text = read(BRAG / "SKILL.md")
    assert "`hyperframes`" in text
    assert "`animation-direction`" in text
    assert "extensions/hyperframes/wrapper.py" in text
    assert "triggers: [user]" in text


def test_no_stale_heygen_skill_refs():
    for path, text in all_brag_docs():
        for stale in (
            "hyperframes-core",
            "hyperframes-animation",
            "hyperframes-creative",
            "hyperframes-keyframes",
        ):
            assert stale not in text, f"{stale} in {path}"


def test_no_claude_install_paths():
    for path, text in all_brag_docs():
        assert "~/.claude" not in text, f"claude path in {path}"


def test_brag_scripts_present():
    for name in ("analyze_music_cues.py", "pyproject.toml", "uv.lock"):
        assert (BRAG / "scripts" / name).is_file(), name
