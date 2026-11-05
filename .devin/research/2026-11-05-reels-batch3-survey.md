# Reels batch-3 survey - saved collection "prog", after DePGBFXtswr

Date: 2026-11-05. Source: Instagram saved grid (Arc, visual enumeration via
computer-use). Carousel order after `DePGBFXtswr` (batch-2 #15):

| # | URL | Author | Status |
|---|---|---|---|
| R3-01 | /p/DfSNs9QoD_d/ | super_invencoes | already surveyed (batch-2 #16) |
| R3-02 | /p/DeVOCSPAtll/ | fabianocarvalhojr | transcribed |
| R3-03 | /p/DfNccTsKizM/ | lowcodepedro | transcribed |
| R3-04 | /p/DfQIkZSFCgO/ | tecajudabr | transcribed |
| R3-05 | /p/DcWPJIxx9G8/ | _eduardojcruz | transcribed |
| R3-06 | /p/DfDRAFSKaVW/ | building.dots | transcribed |
| R3-07 | /p/DfQFRzlAOqi/ | igorcarvalhorodrigues | transcribed |
| R3-08 | /p/DfQ63-CT6gi/ | matheusgomes | transcribed |
| R3-09 | /p/DfNppuykm7W/ | - | unavailable (empty media response) |
| R3-10 | /p/DfMhyC7Ma31/ | dododididaw | transcribed (meme, no signal) |
| R3-11 | /p/DfFzQl5MwBk/ | augustoiago.js | transcribed |

Transcripts: `.devin/scratch/reels-3/transcripts/*.json` (whisper.cpp, pt).
One extra carousel slot (`saved/prog/17993301052493757`) resolved to the
collection page itself - artifact, not a reel.

## Verdicts vs bundle (178 skills)

- **R3-02 fabiano2** - 60s AI news: OpenVQ (context/memory DB for agents),
  Google Artemis (prompt -> mobile automation via MCP), Bonside-2 27B
  ternary (272k ctx, local-capable), AWS background-agent inbox.
  -> EVAL: candidate notes for memory lane, MCP/mobile lane, ai-tools
  model watchlist, background-agent inbox (adjacent to sentinel/afk-loop).
- **R3-03 lowcodepedro** - trending repos pt2: PonyTeio surgical rewrite
  (keep existing, optimize rest, token savings), Cloudflare security-audit
  skill, VoiceStudio local voice clone/dubbing (600+ langs).
  -> COVERED: surgical-rewrite = lean-code minimal-diff ethos;
  CF audit = security-audit-cf; VoiceStudio = existing C4-voicestudio-path
  handoff. Add reference note only.
- **R3-04 tecajudabr** - JPEG XL (.jxl): smaller than JPEG/WebP, alpha,
  lossless, animation, HDR, ROI, progressive decode.
  -> COVERED: `tests/test_jxl.py` + C4-media-tools-jxl handoff.
- **R3-05 eduardojcruz** - MoneyPrinterTurbo: automated dark-channel video
  pipeline (script -> stock footage -> TTS -> captions -> batch render).
  -> COVERED: `shorts-factory` is this exact pipeline. Reference impl note.
- **R3-06 building.dots** - bloc "Dia" speech-to-speech voice model
  (Jack Dorsey). No text stage; preserves emotion/pause/sarcasm; trained
  on recorded human conversation only; needs M4 Max Mac.
  -> EVAL: same category as nvidia/personaplex-7b watchlist entry. GPU/OS
  gated -> watchlist, no integration.
- **R3-07 igorcarvalho** - GlobalRow public job board (367k+ listings,
  company/sector filters, application tracking).
  -> EVAL: candidate data source for the job-apply lane (R2-02 note:
  copywriter + reviewer chain). No code needed; doc note.
- **R3-08 matheusgomes3** - Firebase one-prompt responsive site w/ theme
  selector demo. Generic vibe-coding content -> SKIP.
- **R3-09** - unavailable -> SKIP.
- **R3-10 dododididaw** - meme audio only -> SKIP.
- **R3-11 augustoiago** - dev replaced by AI doing mobile page layouts
  fast/cheap; anecdotal, no tool -> SKIP (no adoptable artifact).

## Actionable residue

1. ai-tools watchlist: add `Dia` (bloc S2S) beside PersonaPlex-7B; add
   Bonside-2 27B ternary note (local-capable reasoning model).
2. Evals doc: OpenVQ (agent memory DB), Artemis (mobile MCP), AWS
   agent-inbox, VoiceStudio (TTS backend for voicebox), GlobalRow (job
   board source), MoneyPrinterTurbo (shorts-factory reference impl).
All are notes/evals - no new skill required.
