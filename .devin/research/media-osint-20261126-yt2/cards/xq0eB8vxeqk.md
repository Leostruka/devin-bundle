# Card: xq0eB8vxeqk - UI hill-climbing, multi-model council, and MCP evals

URL: https://www.youtube.com/watch?v=xq0eB8vxeqk | channel: Theo - t3.gg | date: 20261103

VISUAL: `frames/xq0eB8vxeqk_05.jpg`/`_06.jpg` show the initiating X criticism, `/goal` prompt, T3 Code UI, `t3dotgg/tstack`, and the `council` skill. `_08.jpg` shows delegate reviews and Gemini failure notes. `_10.jpg`/`_14.jpg` show annotated before/after UI screenshots, arrows explaining changes, and council round tables. `_12.jpg`/`_16.jpg` show category scoring matrices comparing T3 Code, Claude Code, and Codex. `_17.jpg` shows cost dashboards: roughly 956.1M tokens, $401.21, 17.6h. `_18.jpg`/`_20.jpg` show PRs and side-by-side design diffs. `_22.jpg` shows the MCP audit prompt and merged eval PR. `_23.jpg` shows token/context reductions of 52% and 78%.

CITED: T3 Code (`pingdotgg/t3code`), tstack (`t3dotgg/tstack`), council skill, Claude Opus, GPT Sol/Codex, Muse, Gemini, Magic Patterns/MagicOS sponsor, `/goal`, computer-use screenshots, MCP tool-use eval. External verification: `external/t3code_README.md`, `external/tstack_README.md`, `external/tstack_council_SKILL.md`, `external/t3code_evals_README.md`, `external/github_repo_snapshot.json`. T3 Code exists, MIT, 80,152 stars; tstack exists, MIT, 4,390 stars; council source verified; evals package and PR #24635 verified by search result.

CLAIMS: Creator claims about 18 hours, five models, 30+ review rounds, and roughly $400 total cost. Scores rose from roughly 6-7/10 to 9.5-10/10, but these are LLM-judge scores and highly prompt/context sensitive; the creator himself notes non-determinism and possible target leakage. Stronger evidence is the merged eval PR: 88 fake threads, real failure cases, controls, baseline comparison, multiple samples, source-imported prompts/schemas, no user data, cost accounting. Token reductions of 52%/78% are creator-reported but tied to the eval narrative.

PAIN-VOCAB: UI "not very pleasant looking"; models produce "slop or the exact same three templates"; "turning it into a hill climb"; same screenshot can receive different scores; target leakage: subagents knowing the score may influence scores; MCP tool descriptions bloating context (`captions.md` lines 217-249, 277-281, 482-488, 804-816, 1055-1059).

BUNDLE-RELEVANCE: Strong validation plus refinement of existing `impeccable`, `arena`, `agent-eval`, `mcp-governance`, and `continuous-improvement`. The bundle already warns against ungrounded LLM judges and has reference-bar scoring. Missing/underdeveloped pieces: multi-provider council protocol, comparative incumbent screenshots in the judging packet, round/score/cost ledgers, target hiding from judges, staged cheap-to-expensive reviewer escalation, and source-derived MCP behavior evals with controls before compressing tool descriptions.

EVIDENCE-QUALITY: observed=18 self-reported=9 unverified=2
