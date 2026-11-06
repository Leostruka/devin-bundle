"""M2_04 brain-upgrade contract: creative-engineering + art-director."""
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..")
SKILL = os.path.join(ROOT, "skills", "creative-engineering", "SKILL.md")
ART = os.path.join(ROOT, "agents", "art-director.md")


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def test_skill_retrieval_step0():
    s = read(SKILL)
    assert "design-intelligence/search.py" in s
    assert "--domain style" in s
    assert "index.json" in s  # alias layer preserved


def test_skill_5fq_mapping():
    s = read(SKILL)
    for token in ("Motivo visual", "Temperatura visual",
                  "Distancia de audiencia", "Papel narrativo",
                  "colors.csv", "typography.csv"):
        assert token in s, token


def test_skill_frontend_rules_pointer():
    s = read(SKILL)
    assert "frontend-rules" in s
    assert "React" in s


def test_art_director_5fq_and_direction():
    s = read(ART)
    for token in ("5 Form Questions", "papel narrativo",
                  "direction-approved.md", "frontend-rules",
                  "3 real directions"):
        assert token in s, token


def test_art_director_v3_contract_intact():
    s = read(ART)
    assert "schema_version: 3" in s
    assert "upstream_hashes" in s
    assert "rework_cycle" in s
    # frontmatter still parses as yaml-ish block
    m = re.match(r"^---\n(.*?)\n---", s, re.S)
    assert m and "name: art-director" in m.group(1)
