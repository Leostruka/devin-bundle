# Five-stage cognitive flow

Stage protocols. Each stage consumes the previous stage's artifact and
produces the next one's input. The workbench manifest (Stage 3) is the
contract the 32-cycle loop (Stage 4) executes against; nothing skips
ahead.

## Stage 1: Radar and Hunt

- **Sources**: direct (project domain) + surrounding/adjacent
  (tools, papers, repos, releases, community signal). Both halves are
  mandatory; adjacent finds are where leverage hides.
- **Output**: the indexed raw dossier (dossie). Every entry carries:
  tag `[direct|adjacent]`, source, date, one-line relevance, and a
  link or path.
- **Density rule**: structured notes only, no prose paragraphs. The
  dossier is Stage 2's input; if Stage 2 cannot triage from it, the
  hunt failed.
- **Executor hints**: `agent-reach` for credential-free channels,
  `scheduled-turns` for recurring hunts (morning radar), `web_search`
  for targeted lookups.

## Stage 2: Triage, benefit calc, Jobs conception

- **Triage**: score each dossier item by real benefit (technical ROI +
  experience ROI) against the current project state. Kill weak items
  here; Stage 3 only sees survivors.
- **Steve Jobs filter** (experience first, technology second):
  1. *Human purpose*: how does this solve the person's problem or ease
     their life with an unforgettable, intuitive experience that has
     unique personality?
  2. *Creative reverse engineering*: only after the ideal experience
     is defined, map the technology: what already exists ready-made?
     What exists in the surroundings (adjacent tech) to adapt or
     reuse? What must be invented from zero?
- **Design bar carried forward**: impeccable base, perfect hardening,
  absurd security (zero-trust), hardware-level optimization, complete
  metrics.
- **Output**: ranked opportunities + chosen direction + experience
  spec detailed enough for Stage 3 to plan against.

## Stage 3: Workbench manifest

Evolve approved ideas into an executable technical plan and declare
the workbench: exactly which tools, skills, MCPs, scripts,
compilers, and analyzers go on the bench and how they operate
together.

**Focus lock (anti-drift)**: the manifest opens with `objetivo_primario`
(the non-negotiable mission) versus `objetivos_secundarios` (derived
or punctual tasks that serve the bigger goal). Armored separation:
every secondary entry names the primary it serves, and secondary tasks
may never displace the primary objective. `regras_e_decisoes` records
the business/architecture rules and the rationale, so a fresh session
can resume without re-deriving decisions.

Schema (YAML):

```yaml
workbench:
  janela_horario: "HH:MM-HH:MM block or sprint window"
  perfil_ativo: "foco-novidades | foco-qualidade-produto | foco-interno | foco-externo [+ combo]"
  objetivo_primario: "the non-negotiable mission"
  objetivos_secundarios:
    - "derived task that serves objetivo_primario"
  ferramentas_na_bancada:
    - "tool/skill/MCP/script/compiler/analyzer + its role"
  regras_e_decisoes:
    - "business/architecture rule or decision rationale"
```

Persist the manifest under the target project's `.devin/` so it
survives compaction; the calendar events only point at it.

## Stage 4: 32-cycle loop

Minimum >=32 consecutive disciplined iterations on the bench
deliverable. Four batteries of 8:

| Battery | Cycles | Focus |
|---|---|---|
| 1 | 1-8 | Core functionality |
| 2 | 9-16 | UI/UX and edge cases |
| 3 | 17-24 | Hardware/performance/metrics |
| 4 | 25-32+ | Hardening/security/regression |

Each cycle runs: implement -> test (unit, integration, mutation,
fuzzing, hardware stress, UI/UX edges as applicable) -> validate
metrics -> harden -> fix -> micro-optimize. No deliverable leaves
Stage 4 before the >=32-cycle matrix completes with full approval.

Per-cycle log format:

```
cycle: N/32+  battery: B
change: <what was implemented or fixed>
tests: <commands run + result>
metrics: <before -> after where measurable>
verdict: pass | fix-needed | blocked
artifact: <commit sha / file / evidence path>
```

Track cycles in the SDD ledger or `.devin/ledgers/<task>.md`. `gates`
enforces that every completion claim cites fresh evidence; a cycle
without a logged verdict does not count toward the 32.

## Stage 5: Close

- **Living docs**: update README, skill docs, and runbooks to match
  reality; stale docs are bugs.
- **Versioning integrity**: atomic commits, PRs, issues, ADRs through
  the git/github workflow skills; high-precision history is the audit
  trail.
- **Open-Minded Scrum self-evaluation**: run the questions below,
  record answers in the ledger.
- **Re-plan**: feed findings back into the macro calendar for the next
  cycle; adjust profile allocations and block lengths from measured
  bottlenecks, not vibes.

## Open-Minded Scrum self-evaluation questions

- Did the block produce the artifact its spec promised? Cite evidence.
- Which stage consumed the most time relative to its value? Where was
  the friction?
- Did secondary tasks displace the `objetivo_primario`? How should the
  armor improve?
- Which tools on the bench underperformed, and which were missing?
- What did the radar miss that a surrounding/adjacent source would
  have caught?
- What one routine change (profile mix, block length, handoff format)
  would make the next window measurably better?
- Are the 32 cycles real verification events or padded repeats?
  Evidence per battery, or it did not happen.
