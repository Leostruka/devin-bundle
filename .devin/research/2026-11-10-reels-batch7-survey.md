# Reels batch-7 + YT batch-2 survey (2026-11-10)

28 unique links (24 reels new + 4 YouTube; batch-6 dup `DfYRPKEDSDJ` re-listed
once). Transcripts: `.devin/scratch/reels-7/transcripts/*.txt` (whisper.cpp
base; PT-BR reels legible despite accent noise), `yt-batch2/transcripts/`
(3 VTT subs + 1 whisper). External research: 7 parallel researcher subagents.

## Verdict table

| # | Link | Conteudo real | Veredito |
|---|---|---|---|
| 1 | GRlcm3wmOqs (YT) | IndyDevDan "Tiny Software Factories" L2: agentic scaffold mount (init->configure->specialize), liquid software = all surfaces agent-editable, in->near->out-of-loop via cron pulse + subagent budgets | EVAL x3 (pulse executor, subagent trace/budget, decision queue) |
| 2 | vSCYL8ySh9g (YT) | NVIDIA Dory1.0-4B looped nGPT: 20-layer shared recurrent block, k=1/2/4 loops, beats Gemma4-26B composite; k fixed at load; KV=non-looped | EVAL x2 (loop sweep on laya heldout, two-lane confidence routing) |
| 3 | DByAR5Su1Yw (YT) | Nate Herk: same improve-prompt x100 on ugly site; Sonnet plateaus r32, Opus accretion-collapse (21k LOC slop); LOC!=quality | EVAL (bounded design-iteration converge-by-gate) |
| 4 | KDyPHt4lW60 (YT) | "Capabilities overhang" showcase: Claude rebuilds ad-riddled TV, dictation-mic firmware+case, AC UI, Kindle jailbreak->dashboard, Wi-Fi 8x, drone security | EVAL light (device-automation lane doc) |
| 5 | murphmaxxing Dff39V1vpj7 | "Omega" config: Opus-5.5 orchestrates Haiku-5.5 agents, every brief carries runnable "Done when" re-checked by orchestrator, CLAUDE_AUTOCOMPACT_PCT 40-60%, self-improving skills | EVAL (done-when contract in dispatch briefs) |
| 6 | fabianocarvalhojr DfieBCtlK5q | Cherny #1 tip: give Claude a way to verify its work; loop engineering (Jun/2026); /goal grades turns with separate small model - writer never grades itself | EVAL (done-evaluator tier in afk-loop/stop-guard) |
| 7 | artofthepossible.ai DffnUDcDBCL | Felix Rieseberg (Cowork eng lead): kill persona prompts->ask-for-method, adversarial review fleet writer!=grader, MX raw access, skills half-life audit | EVAL (persona->process note + skills-debt audit step) |
| 8 | pasquadev DeWwjvyiV2_ | arXiv 2608.23550: 481 CLAUDE.md files, only 4-16% of security rules map to a built-in control; .md = write-only channel; enforcement = deny-rules + hooks + sandbox | EVAL (rules->control coverage audit - direct fit) |
| 9 | alvim_ai DfXFwwCDFMD | LGPD R$50M cap (Art.52) + Claude Code audit-questionnaire plugins (lgpd-compliance-falkzera et al): data inventory, third-party sharing | EVAL (compliance questionnaire skill - scope decision) |
| 10 | pedrohtmallet DfdYAW1xcHk | Claude Code /simplify (v2.1.63): parallel review agents over git diff - reuse/simplification/efficiency/altitude; restored after /code-review rename drama | EVAL (periodic cleanup pass in audit/prepush) |
| 11 | vibecoding.society DfcaHjbEYtq | MIT "Sparks of Weight-Space Programming": GPT-6 Astra reads+writes Qwen3.5-0.8B weights via CPU kernel; kills repetition-loop direction -> MATH 8->48%, GSM8K 14->67% | EVAL (activation-guided weight patching PoC - same mechanism as refusal ablation) |
| 12 | _dbrogle DffOrNAByFw | Balestriero+LeCun arXiv 2610.39302: 109M JEPA beats 72B LLM on representation-alignment (0.184 vs 0.154), 42x sample efficiency; LeCun AMI Labs $1B | EVAL low-pri (tiny JEPA PRH PoC - defer) |
| 13 | kem_glitch DcEBQNPNPzs | graphify (Graphify-Labs): folder->knowledge graph via tree-sitter (33 grammars, no LLM for code), edges EXTRACTED/INFERRED/AMBIGUOUS, MCP+hooks, --obsidian | EVAL (graphify query -> memory-retrieval + knowledge-label eval) |
| 14 | omarontape DfgwiprT5DN | Project Nomad: Docker offline appliance (Ollama+Qdrant, Kiwix, Kolibri, ProtoMaps) | NOTE (system appliance, not embeddable) |
| 15 | huwprosser DfXwuL0izsO | Busy Bar: LED display+Pomodoro hw, open HTTP API + busylib-py/ts, on-device JS | EVAL (focus.py->busylib push; hw-blocked live test) |
| 16 | michaelhroberson DfWJElGNZDz | Eldercare fall-detection: rolling 20s frames -> Jev decision model (Typesafe AI, ex-OpenAI Almeida) - state in, typed Choice/Score/Noul/Box out, 70-500ms hosted | EVAL (Jev as cloud tier above laya for CU perception) |
| 17 | shane.shinyobjectz DfgQMGEKGJG | raea (Render Anything Engine): Rust+Bevy+Dioxus, React/TS compositions on local GPU, raea render/play/cut/check, agent skills installer, 10-20x vs Remotion claim | EVAL (spike raea vs Remotion backend in animation-direction) |
| 18 | mr.owerthinker DfUdibshw3A | hairline (lucasmarkes): 33 interactive isometric SVG figures, pointer-reactive, ESM/React, a11y+reduced-motion | EVAL (dep+pattern ref for design-intelligence/animation-direction) |
| 19 | synsation_ DcjkR2PSkml | Build-For-Good-UX ep17: button has 6 states | EVAL group (state-coverage lint rules) |
| 20 | kabarza DeK0AFcIRhf | checkbox->switch fidelity article, squishy animation craft | EVAL group (same - motion/state vocabulary) |
| 21 | ui_motion_prompts DfbKtE6iabf | Tab Bar Part 3: 3D flips/comets/particles/slot-reel animations | EVAL group (same) |
| 22 | ui_motion_prompts DfYRPKEDSDJ | Text Field Part 2: text-field animation showcase | EVAL group (same) |
| 23 | calculusphile DejYAGbxOAM | Interview Q: 10k distributed IPs hammer login; bcrypt deliberately expensive | NOTE (conceptual security Q, no artifact) |
| 24 | lostandlucky DcCoPrCxPT_ | "Software that passes an audit is a moat" discourse | NOTE (validates audit.py thesis, nothing new) |
| 25 | graduate_ml De12iBYTUNB | backprop/gradient-descent explainer | NOTE (educational) |
| 26 | asimov.academy DfXRHe9s8kZ | PT-BR: moving-average/seasonal-naive forecast explainer | NOTE (educational; data-analyst adjacency only) |
| 27 | tejal_bk DfHOBy6gCye | music/lyrics reel (garbled loop) | NOTE |
| 28 | thatsblu3 DdXZrIMIYXM | editor "cyberspace sequence" heavy-edit showcase | NOTE (creative editing; media-tools adjacency weak) |

## Decisoes (issues a criar - milestone #14)

Grouped eval issues (dedup overlapping surfaces):

1. R7-01 pulse-executor: drain `.devin/rts/intents/*.json` due intents -> one
   afk-loop frontier step (liquid-software near-loop trigger). P2.
2. R7-02 subagent-trace-budget: dispatch records {prompt,tools,output,tokens,
   wall_time} + budget-abort flag; eval suite. P2.
3. R7-03 decision-queue: stop-guard/laya review_gate append
   `.devin/decisions.jsonl` on human-blocking stops; roadmap-board counts. P3.
4. R7-04 done-evaluator: writer!=grader - cheap-tier model grades turn-done
   in afk-loop/stop-guard (loop-verification gap). P2.
5. R7-05 done-when-contract: mandatory runnable "Done when" check in dispatch
   briefs; orchestrator re-runs check before accepting output. P2.
6. R7-06 rules-coverage-audit: map each NL rule (AGENTS.md/global_rules) ->
   deterministic control (hook/audit/permission); flag unenforced rules.
   arXiv 2608.23550 method. P2.
7. R7-07 weight-patch-poc: ai-tools PoC - activation-guided direction
   ablation on small safetensors; measure MATH/GSM8K delta (MIT weight-space
   repro, local). P3.
8. R7-08 dory-loop-eval: Dory1.0-4B GGUF loop sweep k=1/2/4 on laya heldout
   manifests; two-lane confidence routing sketch. P3 (GPU-dependent).
9. R7-09 graphify-eval: `graphify query` -> memory-retrieval hook
   (graph-before-grep); knowledge-label eval on EXTRACTED/INFERRED. P3.
10. R7-10 raea-spike: raea vs Remotion render backend in animation-direction
    (parity, speed, Windows stability, frame-check loop). P3.
11. R7-11 jev-tier-eval: Jev API as cloud decision tier above laya for
    computer-use perception classification. P4 (paid API, deferred).
12. R7-12 design-state-motion: design-intelligence rules for interactive-
    state coverage (button 6 states, switch fidelity, motion vocabulary from
    ui_motion_prompts/hairline patterns). P3.
13. R7-13 bounded-design-loop: converge-by-gate iteration (design_lint +
    look_ledger + held-out) vs fixed-count (100x failure evidence). P3.
14. R7-14 simplify-cleanup-pass: periodic code-rot pass (reuse/simplify/
    efficiency/altitude analog) in audit or prepush; or document /simplify. P4.
15. R7-15 lgpd-scope-decision: compliance questionnaire skill in-bundle or
    user-side; jurisdiction scoping. P4.
16. R7-16 skills-debt-audit: refine-loop step auditing each skill vs
    current-model limits; persona->process prompting note in authoring docs. P4.
17. R7-17 busybar-focus: focus.py -> busylib status push spec; hardware-
    blocked live test documented. P4.
18. R7-18 device-automation-lane: doc the agent->physical-device lane
    (TV/Kindle/router class); map to craft-bridge/system-control/computer-use. P4.

NOTE-only (no issue): Project Nomad, login-bots interview, audit-moat
discourse, backprop explainer, seasonal-forecast explainer, music reel,
cyberspace edit showcase, JEPA PRH (deferred - low-pri eval noted in map).

## Evidencia

- Transcripts `.devin/scratch/reels-7/transcripts/`, `yt-batch2/transcripts/`.
- Media `.devin/scratch/reels-7/media/*.mp4` (24 dl OK), yt-batch2/media wav.
- Research: 7 researcher subagents (returns embedded in issue bodies).
