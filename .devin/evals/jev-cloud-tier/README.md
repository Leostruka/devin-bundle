# Eval: Jev (TypeSafe System One) as cloud decision tier above laya

Issue: #444. Status: eval doc, SPIKE recommendation. No code landed.

Source reel: instagram michaelhroberson/reel/DfWJElGNZDz
(`.devin/scratch/reels-7/transcripts/DfWJElGNZDz.txt`) -- an eldercare
fall-detection demo. The reel itself never names the API; the
"michaelhroberson" demo is consistent with TypeSafe AI's Jev marketing
but the hardware/robotics part is the demo author's own stack.

## What Jev is (verified)

Jev is the flagship "System One" model from TypeSafe AI (typesafe.ai).
System One is a model class that takes state in and returns typed,
probabilistic answers out -- it does not generate free text.

Verified from primary docs:

- Endpoint: `POST https://api.typesafe.ai/v1/systemone`, Bearer API key
  auth (`TYPESAFE_API_KEY`). SDKs exist for Python and TypeScript.
  Source: https://docs.typesafe.ai/api/system-one ,
  https://docs.typesafe.ai/introduction/quickstart
- Model IDs: `jev-latest` (alias), `jev-1.14.0` (current, released
  2026-10-14), `jev-1.13.0`.
  Source: https://docs.typesafe.ai/models
- Pricing: $0.042 per million input tokens; output tokens free.
  Source: https://docs.typesafe.ai/models
- Context: 64k tokens per request, 32k per question; a
  `TypeSafe-Danger-Zone-Long-Context: true` header raises this.
- Input: `state` accepts a string, JSON object, or array of text
  values; PNG/JPEG images may be embedded (requires
  `TypeSafe-Danger-Zone-Images: true` header). No audio/video yet.
- Question types (the output contract):
  - `Choice` -- pick one of a closed label set, with probability.
  - `Score` -- numeric rating.
  - `Noul` -- yes/no (boolean) with probability.
  - `Box` -- bounding-box image grounding (Jev 1.14 only).
  One request may ask several named questions at once; answers come
  back keyed by question name with model id and token usage.
- Founder signal (from reel-research notes, partially corroborated by
  typesafe.ai positioning): founded by Diogo Almeida (ex-OpenAI).
  Treat as background, not a technical fact.

Latency claims of 70-500ms in the issue brief are reel-sourced, not
doc-sourced; docs do not publish an SLA. Realistically: hosted frontier
model over HTTPS, expect 200ms-2s depending on state size and images.

## Structural fit vs laya

The bundle's decision layer is laya
(`extensions/laya-tools/decision_contract.py`, `.devin/laya/models/`):
a local checkpoint answering closed-world Choice-style questions over
an allowlisted state schema (goal, page_text, element_text, snippets...),
returning suggest/abstain only, ~200ms CPU, free, fully offline.

The contracts are near-identical in shape:

| | laya | Jev |
|---|---|---|
| Input | typed state dict, allowlisted keys | freeform string/JSON/images |
| Output | pick 1 of <=8 candidates or `__none__` | Choice/Noul/Score/Box + probability |
| Latency | ~200ms local CPU (post-warmup) | network + frontier inference |
| Cost | free | $0.042/Mtok in |
| Privacy | fully offline | state leaves the machine |
| Modes | off/shadow/assist, calibration-gated | n/a (remote service) |
| Calibration | Platt fit + frozen manifests | vendor claims RLCD-calibrated probs |

Key asymmetry the eval campaign found (see
`.devin/scratch/egm-laya-bitnet-upgrade/issues/04-laya-jev-rollout.md`):
laya decides well on *prose state* and fails/abstains on structured
state, comprehension-heavy tasks, and anything multimodal. Those are
exactly Jev's strengths.

## Routing design: local-first, cloud-escalate

```
request -> laya (local, ~200ms)
   |-> suggestion with calibrated p >= threshold  -> adopt
   |-> abstain (__none__) or p < threshold
          |-> escalate? (lane flagged cloud_ok)
               |-> Jev /v1/systemone Choice question
               |-> Jev p >= threshold -> suggestion
               |-> else -> abstain
```

Escalation gate rules (proposed):

1. Only lanes tagged `cloud_ok` in `profile.json` may escalate --
   state may contain secrets/PII; `STATE_FORBIDDEN` regex already
   strips credential-shaped keys, so reuse the contract validator
   before any cloud call.
2. Never escalate safety-gate lanes (cmd-risk-v1 / laya-guard):
   deterministic checks stay authoritative; a paid network call in a
   block path is a reliability and latency regression.
3. Images only where a lane legitimately has them -- the prime
   candidate is computer-use perception (ui-target-v1 / cu_dom_picker),
   where Jev's `Box` question type is a capability laya cannot have.
4. Cap cost: budget counter in `.devin/ledgers/metrics.jsonl` style;
   e.g. hard cap requests/day, abort lane on exceed.

## Adapter sketch vs decision_contract.py

Mapping is straightforward:

- `Choice` question per laya profile: `options` = candidate ids +
  `__none__`; question text = the profile's frozen question string
  (verbatim -- preserves frozen-question semantics).
- `state` = serialized allowlisted state (prose-join snippets; the
  eval campaign showed prose state is what decision models engage
  with anyway).
- Response: Jev returns per-option probabilities; pick argmax ->
  suggestion, `__none__` argmax or p < threshold -> abstain. Reuse
  `suggestion`/`abstain` envelope unchanged so downstream consumers
  (review_gate, skill-picker, cu_dom_picker) see no difference.
- Failure handling: timeout/network error -> fall back to laya's
  answer or abstain; never propagate as commit.

## Cost / latency / privacy tradeoffs

- Cost: a typical laya request is a few hundred input tokens -> ~
  $0.00001 per call. Negligible at bundle volumes; the real cost is
  engineering, not tokens.
- Latency: 200ms local -> likely 500ms-2s cloud. Fine for
  suggestion-tier lanes; disqualifying for anything in a hot hook
  path (UserPromptSubmit chain already budgets tight).
- Privacy: state allowlist + STATE_FORBIDDEN already minimizes
  leakage, but page_text/window_title can still carry user data.
  Offline-only users lose the tier entirely -- must degrade to
  local-only silently.
- Dependency: introduces the bundle's first paid per-call API in the
  decision path; all current decision infra is stdlib + local.

## Recommendation: SPIKE (deferred, P4)

Do not adopt broadly now. The evidence (14-profile campaign) shows
laya's failure modes are concentrated in lanes where Jev is strong,
but only media-intent-v1 is near activation and it already works
locally. The one lane where Jev is a genuine capability unlock is
computer-use perception (Box grounding, screenshot state) -- laya
cannot see images at all.

Concrete spike, if/when scheduled:

1. `extensions/laya-tools/jev_client.py` -- stdlib urllib POST to
   `/v1/systemone`, `TYPESAFE_API_KEY` env, builds a `Choice` question
   from an existing profile + candidates, returns the same
   suggestion/abstain envelope.
2. Reuse `ui-target-v1` frozen manifest: run Jev on the 16 held-out
   cases (text-only first) and compare against laya's 0.714 decided
   accuracy / dangerous `__none__` commits.
3. If Jev fixes the `__none__` failure mode on perception lanes,
   design the `cloud_ok` profile flag + escalation gate as above.
4. Do NOT wire into production hooks until a calibration block
   (threshold + frozen manifest evidence) exists, same standard as
   laya activation.

Skip condition: if no lane is scheduled for activation anyway, this
stays spec-only -- an unexercised paid API client is dead code.
