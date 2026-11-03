# Contract Q4: pstack backlog evaluation (read-mostly)

- Role: `researcher` (read-only; controller persists the file)
- Objective: evaluate the pstack skills NOT adopted this round plus the
  remaining vercel-labs skills, and produce an eval table the user can
  pull from later.
- Adopted already (exclude): no-comments, unslop,
  typescript-best-practices, poteto-mode (evaluated: skip, Cursor
  coupling), principle-* library (single row, not 20 rows).
- For each remaining pstack skill (architect, arena, automate-me,
  benchmark-checklist, blast-radius, bro, correct, figure-it-out, how,
  in-your-own-words, interrogate, ketchup, ketchup-video, make-bot-ui,
  poteto-help, recall, reflect, setup-pstack, sharpen, show-me-your-work,
  statechart, swarm, tdd, teach, technical-writing, why, the 4
  verification-skill generators): fetch its SKILL.md description
  (api.github.com contents or raw) and rate: ADOPT / ADAPT / SKIP /
  COVERED-BY-<bundle-skill>, one-line reason.
- Also one row each for vercel-labs extras: composition-patterns,
  react-native-skills, react-view-transitions, vercel-optimize,
  web-design-guidelines, writing-guidelines.
- Deliver content for `.devin/research/2026-11-03-pstack-backlog-eval.md`:
  intro (2 lines), eval table, short "recommended next batch" section
  (top 3-5 with reasons), sources.
- Constraints: ASCII, no U+2014, no AI signature. Return the full file
  content in your final report; do not write files.
