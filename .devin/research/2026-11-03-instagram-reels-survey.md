# Survey: Instagram reels -> bundle opportunities (2026-11-03)

Source material: 5 reel links (4 unique; `lowcodepedro/DfNccTsKizM` repeated).
Extraction method: yt-dlp metadata + `extensions/asr` (whisper.cpp, ggml-base,
`--lang pt`) full transcription for reels with thin captions. Transcripts are
authoritative below; captions are clickbait and were not trusted alone.

## Item map

| # | Reel | Author | Subject (verified via transcript) |
|---|---|---|---|
| 1 | `DcWPJIxx9G8` | @_eduardojcruz | **MoneyPrinterTurbo** (harry0703): one-click AI short-video factory |
| 2 | `DfQIkZSFCgO` | @tecajudabr | **JPEG XL** (.jxl) format explainer |
| 3 | `DfNccTsKizM` | @lowcodepedro | 3 GitHub repos: **Ponytail**, **cloudflare/security-audit-skill**, **VoiceStudio** |
| 4 | `DfSNs9QoD_d` | @super_invencoes | **Alternative data**: satellite/CV alpha for hedge funds |

---

## 1. MoneyPrinterTurbo (`harry0703/MoneyPrinterTurbo`, ~13K+ stars claimed)

What it is: topic/keyword -> LLM script -> stock footage (Pexels/Pixabay/Coverr,
or text-to-video clips) -> TTS (Edge TTS free, Azure, ElevenLabs, Kokoro,
Chatterbox, etc.) -> styled subtitles -> BGM -> composed video (9:16/16:9/1:1)
-> batch generation -> optional auto-publish (TikTok/IG/YT). Ships as WebUI +
API + CLI + agent mode. Local or Colab.

Bundle overlap: we already own every stage:

| MPT stage | Bundle asset |
|---|---|
| Script generation | the model itself + `prompt-compiler` |
| Stock footage | *gap*: no Pexels/Pixabay fetcher |
| Narration | `extensions/voicebox` + `tts` skill |
| Transcription/alignment | `extensions/asr` (whisper.cpp) |
| Composition | `extensions/remotion-render` + `animation-direction` + `hyperframes` |
| ffmpeg finishing | used by animation-direction pipeline |
| Subtitle styling | partial (Remotion can render captions) |
| Batch jobs | *gap*: no job-queue/`seen.txt` pattern for media |
| Auto-publish | *gap*: `youtube-fetcher` is read-only; no upload |

Verdict: **build, don't vendor.** MPT is a monolith Python app with its own
provider zoo; our modular extensions cover ~80%. The missing 20% (footage
fetch, batch queue, publish) is a new skill + thin extension, not a MPT dep.
Also note: reels promote faceless-"dark channel" spam monetization; the
capability is legitimate automation, the *content farm* use is the user's call.

## 2. JPEG XL (.jxl)

What the reel claims: smaller than JPEG at same quality, smaller than WebP,
alpha/transparency, >8-bit color, lossless mode, animation, HDR,
region-of-interest encoding, progressive block decode, stable Chrome support
(alongside Firefox/Safari; Windows needs a free extension).

Fact-check: claims are accurate modulo hype. Chrome dropped JXL in 2022 and
re-shipped support in late-2025. `cjxl`/`djxl` (libjxl) is the
reference toolchain; Pillow 11+ has a plugin path.

Bundle fit: `extensions/media-tools` is an image pipeline, so JXL is a natural
codec addition (decode + encode + `identify`). `image-forensics` could extend
metadata extraction to JXL containers. ROI encoding is genuinely useful for
thumbnail/contact-sheet generation in `computer-use` recording pipelines.

Verdict: **small, clean adopt**: cjxl/djxl binary fetch + wrapper in
media-tools; flag as optional codec.

## 3a. Ponytail (`DietrichGebert/ponytail`, MIT, ~160-183K stars claimed)

What it is: a single `SKILL.md` containing a decision ladder the agent climbs before
writing code (does it need to exist? already in codebase? stdlib? platform?
dependency? one line? then minimum + one small test for risky logic). Never
cuts validation/security/accessibility. Ships `ponytail-review`,
`ponytail-audit`, `ponytail-debt` commands. Claimed bench: -53% LOC, -45%
output tokens, -26% cost, 98% coverage on risky logic vs 68% baseline
(self-reported, reproducible harness).

Bundle fit: Rule 18 already says "smallest solution / reject token maxing", but it's one line, no procedure, no guardrails, no test discipline. Ponytail
is that rule operationalized, plus review/audit commands we lack.

Verdict: **adopt, adapted.** Port as our own skill (name e.g. `lean-code`):
keep the ladder + never-cut guardrails + one-test-for-risky-logic rule;
integrate with our `code-review`/`debt` flows. MIT license allows vendoring
with attribution; a clean-room port is also trivial since it's one markdown.

## 3b. cloudflare/security-audit-skill (MIT, ~26K stars)

What it is: 6-phase audit discipline: (1) recon -> `architecture.md` +
`coverage-ledger.json`; (2) coverage-led hunting via *isolated* hunter
subagents + coverage critics; (3) candidate validation: a *fresh verifier
tries to disprove* each candidate; (4) structured `findings.json` validated
against schema (confirmed / needs_validation / rejected); (5) independent
record verification of final claims; (6) target-neutral report
(`REPORT.md`/`FINDINGS-DETAIL.md`/`NEEDS-VALIDATION.md`). Trust-boundary rule:
a missing best-practice is never a finding. Repeat runs are additive via
ledgers. Two zero-dep Node validators included.

Bundle fit: our `security-audit` is a flat checklist (SAST/deps/secrets/
OWASP-lite). CF adds the machinery: coverage ledger, isolation between hunter
and verifier, disprove-first validation, machine-readable verdicts, additive
re-runs. Same skill *name*, so collision handling needed.

Verdict: **adopt the discipline.** Options: (a) vendor CF skill under a
distinct name (`security-audit-cf`/`vuln-harness`): MIT, honest, zero
re-derivation risk; (b) graft ledger+verifier phases onto our skill. (a) is
lower risk and preserves our OWASP checklist as complementary. Node.js
validators only needed at audit time.

## 3c. VoiceStudio (`debpalash/VoiceStudio`, AGPL-3.0, ~17-82K stars)

What it is: fully-local ElevenLabs alternative: voice clone/design, video
dubbing, dictation widget, WhisperX transcription (646 langs), audiobook
batch, OpenAI-compatible API on :3900, MCP server, multi-engine model manager
(OmniVoice default; VibeVoice, Kokoro, KittenTTS, CosyVoice, IndexTTS...).

License caveats (verified in reporting): app is AGPL-3.0; **default OmniVoice
engine is non-commercial**; per-model licenses shown in manager. Fine for
personal/dev use; redistribution/commercial needs care.

Bundle fit: `voicebox` ext wraps `jamiepine/voicebox` (FastAPI :17493,
doctor/generate/models). VoiceStudio is a superset: cloning, dubbing, MCP,
wider engines, but heavier (Electron + Python backend, ~5GB models) and
AGPL. Our wrapper pattern (thin HTTP client, localhost-only, whitelisted
actions, bounded I/O) maps 1:1 onto VoiceStudio's OpenAI-compatible API :3900.

Verdict: **adapt, don't replace.** Keep voicebox as the default backend; add
an OpenAI-compatible TTS client path (same wrapper contract) targeting
VoiceStudio when the user runs it. Document license caveats in the skill.
Zero new runtime; it's a host-URL + payload-shape variant.

## 4. Alternative data (satellite alpha), MERIDIAN-scope

What the reel describes: hedge funds buying satellite imagery to count
Walmart parking-lot cars (67K-store university study, ~5%/3-day edge),
floating-roof oil-tank shadow volumetrics (~10K tanks/week, SAR night radar),
weather-foresight desks (July-2021 MG coffee frost -> +25%). "Dados
alternativos": seeing numbers before they become numbers.

Reality check: real industry (RS Metrics, Orbital Insight, Planet, Kayrros).
Barriers: imagery cost (Planet paid; Sentinel-2 free at 10m res, marginal for
car counting (0.3-0.5m needed), CV pipeline, historical backtests, licensing.
Free tier path exists: Sentinel-2 + Landsat for tank-shadow and site-activity
proxies; OpenSky/ADS-B for logistics; AIS for shipping.

Bundle fit: none directly; this is product domain, not agent tooling.
`data-analyst` + `scrape-tools` + `image-forensics` are incidental helpers.

Verdict: **route to `leostruka/MERIDIAN` backlog** (repo not present locally,
items recorded here for transfer): alt-data source registry, Sentinel-2/ESA
ingestion, car-count CV baseline, tank-shadow estimator, ADS-B/AIS feeders,
signal->backtest harness.

---

## Priority synthesis (RICE-ish)

| Item | Reach | Effort | Confidence | Rank |
|---|---|---|---|---|
| Ponytail -> `lean-code` skill | every task | S | high (self-reported bench) | 1 |
| CF security-audit vendored | audit runs | S | high (MIT, proven design) | 2 |
| VoiceStudio OpenAI-compat path | TTS users | S | high | 3 |
| JXL codec in media-tools | media pipelines | S | medium | 4 |
| shorts-factory skill (MPT-equivalent) | video work | M | medium | 5 |
| MERIDIAN alt-data backlog | n/a here | XL | n/a | - |
