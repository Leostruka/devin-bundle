---
name: agentic-rag
description: Use when implementing an agentic RAG product in a target project (support desk, knowledge assistant, evidence-gated Q&A). Playbook for the retrieve -> decision-gate -> answer-or-escalate architecture with multimodal index and human-review loop. Builds the system; does not answer questions with it.
triggers: [user, model]
---

# Agentic RAG (evidence-gated Q&A)

## Overview

Implementation playbook for the agentic RAG support-desk architecture
(source: Daily Dose of DS "Jev-powered Agentic RAG" walkthrough). The
system retrieves evidence, asks a decision model whether the evidence is
sufficient, answers with citations when it is, and escalates to a human
ticket when it is not. Human replies feed back into the index.

Five slots, stack-agnostic:

| Slot | Reference choice | Swappable with |
|---|---|---|
| Backend | InsForge OSS (Postgres+pgvector, auth, storage, edge functions, realtime, model gateway) | Supabase / plain Postgres+pgvector + functions |
| Embeddings | EmbeddingGemma 2 (multimodal, 768-dim, text+image same space) | Any text embedder if corpus is text-only |
| Decision model | Laya multilingual (Convai Innovations; 322M BERT-style encoder, Apache 2.0, self-host, free; this bundle already ships `laya-tools`/`layad` and the `implement-laya` skill) | Free/open: Kev 9B, Jeeves 9B, Strands Decider 2B, open-weight d1-3B/d1-omni-600M. Paid optional: Jev or hosted d1/d1-ultra (Choice/Score/Noul API, text+image). Last resort: LLM-judge with strict JSON schema |
| Generator | Vision-capable LLM through a model gateway, model id in secrets | Any cited-generation capable model |
| Hosting | One L4 (~7.2 GB both models); SIE for multi-model single-GPU serving | Any GPU host or managed endpoint |

## Iron rules

1. Never call the generation model when the gate fails. Escalation is a
   first-class output, not an error.
2. Thresholds live in a DB/config table, separate for text and image
   candidates; tuning must never require a deploy.
3. Log every gate decision (candidates, scores, verdict) to
   `decision_log` before answering or escalating.
4. Index each page twice: ~220-word text chunks AND a rendered page PNG,
   both tagged with the page number. Merge candidates by page.
5. Answers must cite page numbers and return thumbnails/excerpts when the
   channel supports it. The generator answers only from supplied evidence.
6. One wider retry max before ticketing: widen top-k/filters once, never
   loop.
7. Human actions stay human: reps write replies, customer receives email.
   "Save to knowledge" re-indexes the Q&A pair as a new chunk.
8. Tenant isolation via RLS (per company/team) is part of the data model,
   not an app-level afterthought.

## Phase route

| Gate | Name | Exit condition |
|---|---|---|
| P0 | Intake | Corpus shape (docs, pages, languages), tenancy model, answer channels, threshold starting values, human-review SLA defined in `.devin` notes or issue. |
| G1 | Data model | Tables for documents, chunks (vector dim per embedder), conversations, tickets, decision_log, thresholds; tenant-scoped RLS verified with two-tenant test. |
| G2 | Index pipeline | Upload -> storage -> job -> per-page text chunks + page PNG -> embed both -> persist with page tags; progress events stream to dashboard; 20-page PDF indexes in <1 min. |
| G3 | Query pipeline + gate | Embed question (+attached image) -> dual search (text, image) -> merge by page -> decision model rerank+answerability -> thresholds -> answer w/ citations OR one wider retry OR ticket. Gate unit-tested above/below threshold. |
| G4 | Human loop | Ticket appears realtime with question + rejected candidates + scores; rep reply emails customer; save-to-knowledge re-indexes. |
| G5 | Eval | Held-out Q&A set: gate precision/recall, citation correctness, escalation rate reported; thresholds tuned from data. |

## Acceptance criteria

- Query with sufficient evidence: answer + page citations + decision_log row.
- Query with insufficient evidence: single wider retry, then ticket with
  candidate scores visible to the rep; generation model never called.
- Rep reply reaches customer by email; save-to-knowledge makes the same
  question retrievable.
- Threshold change in DB alters gate behavior without a deploy.

## Non-goals

- No auto-submit/auto-send to end users without rep confirmation.
- No figure-level extraction (full-page PNG only; vector diagrams lose
  captions otherwise).
- No unbounded retry loops, no answer on sub-threshold evidence.

## Integration notes

- `data-analyst`/`research` skills can reuse the gate pattern for
  evidence sufficiency before answering.
- On this bundle host, `extensions/voicebox` (tts) + `asr` can add voice
  to the desk frontend; optional, not part of the core pipeline.
