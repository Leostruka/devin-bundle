# evaluate NVIDIA Personaplex-7B for the voice pipeline

status: open
priority: P3
source: reels batch-2 survey (.devin/research/2026-11-05-reels-batch2-survey.md)

## Evidence
Reel 08 (eduardocavalcanti): NVIDIA released Personaplex-7B, realtime conversational voice model, open weights, reportedly above ElevenLabs realtime. Transcript: `transcripts/08-eduardocavalcanti.json`.

## Recommendation
Eval issue: find the HF repo, check license + hardware requirements (7B realtime needs GPU), decide whether it slots into `extensions/voicebox` or `ai-tools` as a backend option. Deliverable: eval note with verdict (integrate / document-only / skip).

## Verification
`.devin/research/` eval note with license + verdict.
