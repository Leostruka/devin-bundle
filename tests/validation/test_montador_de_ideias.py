"""Contract tests for skills/montador-de-ideias and its /leo + ask-bundle routing."""
from pathlib import Path

ROOT = Path(__file__).parents[2]
SKILL_DIR = ROOT / "skills" / "montador-de-ideias"
SKILL_MD = SKILL_DIR / "SKILL.md"

REFERENCES = [
    "journalistic-osint-protocol.md",
    "first-principles-justification.md",
    "atomic-modular-hardening.md",
    "contact-surfaces-excellence.md",
]

TEMPLATES = [
    "idea-dossier.md",
    "compiled-prompt.md",
]


def skill_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_skill_frontmatter_and_core_pipeline():
    assert SKILL_MD.is_file(), "skills/montador-de-ideias/SKILL.md missing"
    text = skill_text()
    assert text.startswith("---\n"), "missing YAML frontmatter start"
    parts = text.split("---", 2)
    assert len(parts) >= 3, "unclosed YAML frontmatter"
    fm = parts[1]
    assert "name: montador-de-ideias" in fm
    desc_lines = [line for line in fm.splitlines() if line.startswith("description:")]
    assert len(desc_lines) == 1
    assert "Use when" in desc_lines[0]
    assert "triggers: [user, model]" in fm

    for required_token in (
        "original_prompt_sha256",
        "ask_user_question",
        "HARD-GATE",
        "journalistic-osint-protocol.md",
        "first-principles-justification.md",
        "atomic-modular-hardening.md",
        "contact-surfaces-excellence.md",
        "idea-dossier.md",
        "compiled-prompt.md",
        "Facilitar",
        "Resolver",
        "Impressionar",
        "Ser Intuitivo",
        "researcher",
    ):
        assert required_token in text, f"SKILL.md missing required token: {required_token}"


def test_reference_playbooks_complete():
    for name in REFERENCES:
        path = SKILL_DIR / "reference" / name
        assert path.is_file(), f"missing reference playbook: {name}"
        content = path.read_text(encoding="utf-8")
        assert len(content) > 800, f"reference playbook too short: {name}"

    osint = (SKILL_DIR / "reference" / "journalistic-osint-protocol.md").read_text(encoding="utf-8")
    for token in ("PRISMA-lite", "lateral reading", "changelogs", "job postings", "Wayback", "binary-triage"):
        assert token in osint, f"journalistic-osint-protocol.md missing {token}"

    fp = (SKILL_DIR / "reference" / "first-principles-justification.md").read_text(encoding="utf-8")
    for token in ("First Principles", "RICE", "Kano", "JTBD", "Deep Modules", "Kill Criterion", "NFR"):
        assert token in fp, f"first-principles-justification.md missing {token}"

    hardening = (SKILL_DIR / "reference" / "atomic-modular-hardening.md").read_text(encoding="utf-8")
    for token in ("Atomic Hardening", "Atomic Optimization", "Modular Hardening", "Modular Optimization", "Envelope v2", "ADR-003"):
        assert token in hardening, f"atomic-modular-hardening.md missing {token}"

    surfaces = (SKILL_DIR / "reference" / "contact-surfaces-excellence.md").read_text(encoding="utf-8")
    for token in ("Facilitar", "Resolver", "Impressionar", "Ser Intuitivo", "Time-to-Value", "Nielsen", "Doherty"):
        assert token in surfaces, f"contact-surfaces-excellence.md missing {token}"


def test_templates_complete():
    for name in TEMPLATES:
        path = SKILL_DIR / "templates" / name
        assert path.is_file(), f"missing template: {name}"
        content = path.read_text(encoding="utf-8")
        assert len(content) > 600, f"template too short: {name}"

    dossier = (SKILL_DIR / "templates" / "idea-dossier.md").read_text(encoding="utf-8")
    for section in (
        "original_prompt_sha256",
        "## 1. Filosofia, Problema Raiz e Dor",
        "## 2. Dossie Investigativo & OSINT de Mercado",
        "## 3. Justificativa por Primeiros Principios",
        "## 4. Arquitetura Master (Product Manager + Tech Lead + Staff Architect)",
        "## 5. Hardening e Otimizacao (Nivel Atomico e Nivel Modular)",
        "## 6. Superficies de Contato (Facilitar, Resolver, Impressionar, Ser Intuitivo)",
    ):
        assert section in dossier, f"idea-dossier.md missing section: {section}"

    compiled = (SKILL_DIR / "templates" / "compiled-prompt.md").read_text(encoding="utf-8")
    for section in (
        "original_prompt_sha256",
        "## 1. Prompt Original (Preservado Intacto)",
        "## 2. Registro de Mudancas Aprovadas pelo Usuario",
        "## 3. Super-Prompt Compilado (Pronto para Execucao)",
    ):
        assert section in compiled, f"compiled-prompt.md missing section: {section}"


def test_leo_and_ask_bundle_route_to_montador_de_ideias():
    leo_text = (ROOT / "skills" / "leo" / "SKILL.md").read_text(encoding="utf-8")
    ask_text = (ROOT / "skills" / "ask-bundle" / "SKILL.md").read_text(encoding="utf-8")
    flows_text = (ROOT / "skills" / "ask-bundle" / "modes" / "flows-detail.md").read_text(encoding="utf-8")

    assert "`montador-de-ideias`" in leo_text, "leo SKILL.md missing montador-de-ideias route"
    assert "`montador-de-ideias`" in ask_text, "ask-bundle SKILL.md missing montador-de-ideias route"
    assert "`montador-de-ideias`" in flows_text, "flows-detail.md missing montador-de-ideias"

    # Quick-start menu must expose montador-de-ideias and stay within 4 bullets
    leo_qs = leo_text.split("## Quick-start menu", 1)[1].split("## Quick AFK issue creation", 1)[0]
    assert "`montador-de-ideias`" in leo_qs, "leo Quick-start menu missing montador-de-ideias"
    leo_bullets = [line for line in leo_qs.splitlines() if line.strip().startswith("- **")]
    assert 2 <= len(leo_bullets) <= 4, f"leo Quick-start menu must have 2-4 options, found {len(leo_bullets)}"


def test_no_em_dashes_in_montador_de_ideias():
    em_dash = chr(0x2014)
    en_dash = chr(0x2013)
    for f in SKILL_DIR.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        assert em_dash not in text and en_dash not in text, f"Forbidden dash found in {f}"
