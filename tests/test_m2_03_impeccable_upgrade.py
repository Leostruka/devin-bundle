"""M2_03: skills/impeccable upgrade contract.

Covers: 24-command sync, PRODUCT.md/DESIGN.md schema sections,
huashu direction protocol artifacts, muscle wiring tokens.
"""
import os
import re

SKILL = os.path.join(os.path.dirname(__file__), "..", "skills",
                     "impeccable", "SKILL.md")
TEXT = open(SKILL, encoding="utf-8").read()


def test_frontmatter_intact():
    assert TEXT.startswith("---\nname: impeccable\n")
    assert "description:" in TEXT
    assert "triggers: [user]" in TEXT


def test_24_commands_synced():
    cmds = re.findall(r"^\| `(\w+)`", TEXT, re.M)
    upstream = {"craft", "shape", "init", "document", "extract", "critique",
                "audit", "polish", "bolder", "quieter", "distill", "harden",
                "onboard", "animate", "colorize", "typeset", "layout",
                "delight", "clarify", "adapt", "optimize", "overdrive",
                "live", "generate", "impeccable"}
    assert upstream <= set(cmds), upstream - set(cmds)
    assert "24" in TEXT


def test_product_schema_sections():
    for section in ("Platform", "Users", "Product Purpose", "Positioning",
                    "Operating Context", "Capabilities and Constraints",
                    "Brand Commitments", "Evidence on Hand",
                    "Product Principles", "Accessibility & Inclusion"):
        assert section in TEXT, section
    assert "impeccable:product-schema 1" in TEXT
    assert "Never invent" in TEXT


def test_design_md_spec():
    for section in ("1. Overview", "2. The Kit", "3. Colors",
                    "4. Typography", "5. Elevation and Material",
                    "6. Components", "7. Do and Do Not"):
        assert section in TEXT, section
    assert "YAML frontmatter" in TEXT


def test_direction_protocol_artifacts():
    for token in ("product-facts.md", "direction-approved.md",
                  "sec0 fact-verify", "Five Form Questions",
                  "3 real directions", "verbatim"):
        assert token in TEXT, token
    for q in ("papel narrativo", "distancia de audiencia",
              "temperatura visual", "capacidade/densidade",
              "motivo visual"):
        assert q in TEXT, q


def test_muscle_wiring():
    assert "design_lint.py" in TEXT
    assert "search.py" in TEXT
    assert "frontend-rules" in TEXT
    assert "--domain" in TEXT


def test_boundaries():
    assert "never invent" in TEXT.lower() or "Never invent" in TEXT
    assert "greenfield" in TEXT
