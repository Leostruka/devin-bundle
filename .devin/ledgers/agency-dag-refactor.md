# GATES: agency pipeline -> asset-driven agentic DAG (ssp.sh ingestion)

- [x] G1: ssp.sh reference ingested, patterns extracted and presented
  CHECK: webfetch ai-orchestrators + linked data-orchestrators + reinventing-tools notes
  EXPECT: patterns listed with source provenance
  EVIDENCE: 8 patterns (P1-P8) extracted + presented Phase 1; approved by user ("provado")

- [x] G2: cyclic DAG design (7 agents, bounded 04->02 loop, Laya gates) presented + approved
  CHECK: Phase 1 stop-and-approve
  EXPECT: user replies go/approve
  EVIDENCE: user replied "provado" (approved)

- [x] G3: KB artifact saved per AC1
  CHECK: test -f .devin/research/ssp_ai_orchestrators.md
  EXPECT: file exists with extraction + provenance
  EVIDENCE: written; P1-P8 + mapping table + provenance per claim + open references

- [x] G4: .devin/orchestrator_prompts_v2.md rewritten: 7 personas incl. 07_Chief_of_Staff (Goose),
  frontmatter upstream_hashes/status(DRAFT|APPROVED|BLOCKED)/schema_version, hardened writes,
  tool limits, bounded feedback loop, Laya state-controller spec
  CHECK: token counts + header scan
  EXPECT: all present; no bare 'EOF' delimiters
  EVIDENCE: em-dash 0; upstream_hashes x22; 07_Chief x3; all 7 `## [Agency]` headers present;
  455 lines; only 'EOF' occurrence is the prose reference documenting the replaced pattern;
  asset registry + controller pseudocode + laya router/guard gate spec included

- [x] G5: repo checks green after edits
  CHECK: python audit.py
  EXPECT: 0 errors
  EVIDENCE: audit.py "Errors: 0"; 1 pre-existing warning (post-exec.py script hash, identical in HEAD)
