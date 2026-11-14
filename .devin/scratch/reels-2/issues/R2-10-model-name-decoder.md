# HF model-name anatomy decoder micro-skill

status: resolved
priority: P3
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Reel 10 (leikauskas): 14-word model names decode as maker / size / training claims / scores / surgical mods (abliteration) / packaging-quant. Heretic = the abliteration tool; we already ship `ai-tools` abliterator. Transcript: `transcripts/10-leikauskas.json`.

## Recommendation
Micro addition to `ai-tools` SKILL.md (or a `model-card-reader` reference file): a decode table so a filename like `Qwen3.8-27B-turbo-fable-coldfusion-735-882-heretic` reads as vendor/size/claims/scores/mod/pack. Feeds `hf-model-eval` decisions (pick the right quant/variant).

## Verification
Section exists in ai-tools doc; decode example matches reel anatomy.

## Answer

Decoder table added to `skills/ai-tools/SKILL.md` (maker/size/claims/scores/mod/packaging) with the heretic->abliterator link.
