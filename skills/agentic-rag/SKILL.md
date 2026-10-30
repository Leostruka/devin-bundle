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

## Architecture selector (when to use what)

| Corpus & workload | Pattern | Why |
|---|---|---|
| Static corpus <200k tokens (~500 pages), low churn | Prompt context + prompt caching (no RAG) | Zero retrieval infra or chunk-boundary loss |
| Single-source docs + per-user chat history | Linear RAG + cross-encoder reranker | One vector search (top-20) + reranker (`max_results = 5`); predictable latency |
| High-stakes Q&A, multi-source (docs/SQL/API), support desk | **Agentic RAG (this playbook)** | Decision gate blocks ungrounded generation, allows 1 wider retry, and escalates to human with feedback loop |

## Context separation (Conversation vs. Memory vs. RAG)

Keep the three context sources distinct in storage metadata and in the generator system prompt:

| Pattern | What it stores | Metadata / scope | Prompt rule |
|---|---|---|---|
| Conversation storage | Last $N$ verbatim turns (e.g. 6) | Passed in `Context` array | Resolves follow-ups ("how do I do that in Docker?") that lack semantic overlap |
| Long-term user memory | Earlier turns or extracted user facts | `kind = conversation`, `user_id` from auth principal | Attribute to the user only when `kind = conversation` |
| External knowledge (RAG) | Shared corpus chunks + page PNGs | `kind = document`, `title`, `url`, `page` | Technical facts only; never attribute document examples to the caller |

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
8. Tenant and user isolation via RLS / authenticated principal (`ClaimsPrincipal` / JWT):
   never accept `user_id` or `session_id` from the request body, and escape or parameterize all metadata filters.
9. No silent rerank or gate fallback: inspect stream status events (`RERANKING_FAILED`, `SUMMARIZATION_FAILED`) and verify the `rerank`/`gate` stage actually ran; enforce `max_results` cut even when reranking is off.
10. End-to-end stream deadline and reasoning token budget: `HttpClient.Timeout` only covers response headers on streamed replies; link a request-wide deadline across history load + stream read + turn store, and size `gen_token_budget` (e.g. >=2048) so reasoning models do not exhaust budget on thinking tokens.

## Phase route

| Gate | Name | Exit condition |
|---|---|---|
| P0 | Intake | Corpus shape (docs, pages, languages), tenancy model, answer channels, threshold starting values, human-review SLA defined in `.devin` notes or issue. |
| G1 | Data model | Tables for documents, chunks (vector dim per embedder), conversations, tickets, decision_log, thresholds; tenant-scoped RLS verified with two-tenant test. |
| G2 | Index pipeline | Upload -> storage -> job -> per-page text chunks + page PNG -> embed both -> persist with page tags; deterministic doc IDs + async ingestion status polling (`COMPLETED`/`FAILED`); 20-page PDF indexes in <1 min. |
| G3 | Query pipeline + gate | Embed question (+attached image) -> dual search (text, image) -> merge by page -> decision model rerank+answerability -> thresholds -> answer w/ citations OR one wider retry OR ticket. Gate unit-tested above/below threshold and on stage failure. |
| G4 | Human loop | Ticket appears realtime with question + rejected candidates + scores; rep reply emails customer; save-to-knowledge re-indexes. |
| G5 | Eval | Held-out Q&A set: retrieval ranking (`hit@1`, `hit@3`, `MRR`), gate precision/recall, citation correctness, escalation rate, and split `p50`/`p95` latency (retrieval vs. rerank/gate vs. LLM generation) reported; thresholds tuned from data. |

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
