"""M2_14: .devin/orchestrator_prompts_v3.md (v4 content) contract."""
import os

DOC = os.path.join(os.path.dirname(__file__), "..", ".devin",
                   "orchestrator_prompts_v3.md")
TEXT = open(DOC, encoding="utf-8").read()
V2 = open(os.path.join(os.path.dirname(__file__), "..", ".devin",
                       "orchestrator_prompts_v2.md"),
          encoding="utf-8").read()


def test_v4_supersedes_v3():
    assert "Status: v4" in TEXT
    assert "orchestrator_prompts_v2.md" in TEXT


def test_team_guards_declared():
    for token in ("silent-worker", "turn-kill", "no-assignment",
                  "round-cap", "pause-free"):
        assert token in TEXT, token
    assert "20 minutes" in TEXT
    assert "<=3 workers" in TEXT
    assert "20 architect-worker rounds" in TEXT


def test_queue_vs_steer():
    assert "Queue vs steer" in TEXT
    assert "intents" in TEXT


def test_direction_contract_in_03():
    assert "DIRECTION CONTRACT" in TEXT
    assert "direction-approved.md" in TEXT
    assert "3 real directions" in TEXT
    for q in ("papel narrativo", "distancia de audiencia",
              "temperatura visual", "capacidade/densidade",
              "motivo visual"):
        assert q in TEXT, q
    assert "frontend-rules" in TEXT


def test_schema_and_personas_preserved():
    assert "schema_version 3" in TEXT
    assert "upstream_hashes" in TEXT
    for p in ("01_Product_Manager", "02_Tech_Lead", "03_Art_Director",
              "04_Security_Legal_Auditor", "05_Scrum_Master",
              "06_Copywriter", "07_Chief_of_Staff"):
        assert p in TEXT, p
    # v3 file is a superset of v2 personas (not a rewrite)
    assert len(TEXT) > len(V2)
