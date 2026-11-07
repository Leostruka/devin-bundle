# frontend-design: upload & file-state UX checklist

status: ready-for-agent
priority: P2
source: reels batch-5 survey, kairozmind DfZdE8plZ0A (adapted from designmotionhq.com/patterns/file-upload-ux)

## Evidence

Transcript (`.devin/scratch/reels-5/transcripts/DfZdE8plZ0A.txt`): "o upload que parece seguro": five interface signals that make an upload feel safe vs broken, with the same file. Primary source verified: https://designmotionhq.com/patterns/file-upload-ux ("Same file. One upload feels broken. One feels safe").

The 5 signals:
1. Dropzone reacts to drag-over, border, glow, copy shift (3 signals before drop).
2. Honest progress, percent + ETA, not a bare spinner.
3. Inline retry that keeps the file loaded, no re-select after a failure at 90%.
4. Thumbnail/type/size preview as proof of receipt.
5. Per-file progress + per-file retry in multi-file queues.

Bundle gap: `skills/frontend-design/SKILL.md` covers motion/micro-interactions (R4-02) and general principles but has no async/file-transfer state guidance.

## Task

Add a compact "Upload & file states" subsection to `skills/frontend-design/SKILL.md` (near the micro-interactions block, ~lines 68-90) encoding the 5 signals as a checklist, plus the anti-patterns (spinner-only progress, re-select after failure, silent dropzone). Cite the designmotionhq pattern page as source. Keep it terse; skill files stay lean (Rule 18).

## Acceptance

- [ ] Section present, <=15 lines, checklist form
- [ ] Source URL cited
- [ ] `python audit.py` green (skill structure checks)
