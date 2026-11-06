# micro-interactions: quantified motion spec into frontend-design

status: resolved
priority: P2
source: reels batch-4 survey (.devin/research/2026-11-06-reels-batch4-survey.md)

## Evidence
charles.unemployed reel = concrete UI motion spec. frontend-design currently has no motion section (grep: no easing/transition/ms).

## Task
Add a Motion checklist section to skills/frontend-design/SKILL.md: ease-out for entrances, dropdowns 150-250ms, stagger list rows 30ms, scale buttons 0.97 on press, stretch moving knobs 12%, popovers start scale 0.95, transitions to/from trigger not center, exits ~20% shorter than entrances, crossfade icons scale+blur, rubber-band past drag bounds, shared layoutId across shared objects, no spring bounce for everyday UI.

## Answer

Added quantified micro-interaction spec to skills/frontend-design/SKILL.md after the motion paragraph (easings, 150-250ms dropdowns, 30ms stagger, .97 press, -20% exits, trigger-origin, layoutId).
