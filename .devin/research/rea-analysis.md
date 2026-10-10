# REA analysis: morluto/rea

Source: <https://github.com/morluto/rea> v4.1.0 (npm `rea-agents`), MIT, cloned
read-only to `.devin/scratch/rea-repo` on 2026-10-06. Node 22+/24/26 MCP server
+ CLI (stdio). 126 tools.

## 1. Architecture

Layered TypeScript monorepo (`turbo`, `vitest`, `oxlint/oxfmt`). Diagram source:
`docs/architecture.mermaid` in the clone.

| Layer | Path | Role |
|---|---|---|
| Entry | `scripts/rea.mjs` → `src/cli.ts`, `src/main.ts` | One dispatcher: `rea mcp` (stdio server) or one-shot CLI commands |
| Adapter | `src/server/` | MCP request translation, tool registration, toolResult shaping |
| Application | `src/application/` | Shared CLI/MCP workflows; `SessionProviderRouter` + `BinarySession` = one immutable deep binding per target; `AnalysisProviderRegistry` = deterministic selection, no silent fallback |
| Contracts | `src/contracts/` | Zod schemas for every caller-visible input/output + shared error schema (`errorSchemas.ts` → generated catalog) |
| Domain | `src/domain/` | Pure side-effect-free modules: evidence, comparisons, application graphs |
| Providers | `src/{hopper,ghidra,ida,android,firmware,browser,dotnet,artifacts,native,windows,reference,process}/` | Engine-specific adapters |
| Process foundation | `src/process/` + `native/windows/` | Owned process groups, run-token auth, deadlines, cancellation, bounded stdout/stderr, TERM→KILL cleanup; Windows: Job Objects, private DACLs, NTFS path admission (Node-API addon) |
| Evaluation | `src/evaluation/` + `tests/` | Session transcript scoring; vitest lanes: domain/services/adapters/boundary/mcp-boundary/acceptance |

Data flow: `Agent → REA (CLI|MCP) → target-bound session router → provider
registry → deep provider (Hopper/Ghidra/IDA) or disjoint aux providers
(artifacts, browser CDP, dotnet, android-JADX, firmware, process capture) →
target`.

## 2. Tool catalog (126 tools, 11 families)

| Family | Count | Examples |
|---|---:|---|
| Native inspection | 41 | `procedure_pseudo_code`, `procedure_assembly`, `search_strings`, `xrefs`, `batch_decompile` |
| Investigation workflows | 14 | `binary_overview`, function dossiers, feature traces, call graphs, Swift/ObjC discovery |
| Native macOS utilities | 7 | Mach-O metadata, code signatures, plists, Swift demangling (no Hopper launch) |
| Artifact graph | 5 | directory/ZIP/APK/IPA/ASAR inventory, IB/asset-catalog extraction |
| Managed PE/CLI (.NET) | 7 | identity, metadata, CIL instructions, native deps, build compare |
| Firmware | 2 | `inspect_firmware_regions`, `extract_firmware` (caller-supplied binwalk/unblob, Linux) |
| Android APK | 5 | manifest, class search, member inventory, method decompile (headless JADX) |
| Browser observation | 9 | CDP page structure, network metadata, scripts, source maps, screenshots |
| Electron analysis | 5 | renderer observation, static map, static/runtime reconciliation |
| JavaScript runtime | 2 | V8 Inspector discovery, script locations, exec-context events |
| Workspace/observation | 21 | sessions, evidence bundles, comparisons, open-question tracking |

Design rules (`docs/tool-design.md`): task shapes: `inspect`, `search`/`list`,
`trace`, `compare`, `workflow`, `observe`/`capture`; primitives over mega-tools;
provider-neutral names; strict object inputs; "missing evidence is unknown, not
empty or false"; read-only/mutation/process/fs/network effects declared in the
contract.

## 3. Bridges to analysis engines

| Provider | Mechanism | Boundary |
|---|---|---|
| Hopper | `bridge/hopper_bridge.py` runs *inside* Hopper's Python; NDJSON over authenticated private Unix socket; launch managed by `src/hopper/` | macOS/Linux; demo mode OK; one request at a time; annotations supported |
| Ghidra | `bridge/ghidra/ReaGhidraBridge.java` packaged `HeadlessScript`; strict NDJSON; temp projects, serial API queue, 330s first-query startup deadline | Linux/macOS full (25 read-only ops + atomic annotations); Windows x64 P0: native PE on NTFS only, read-only, Job Objects + DACLs |
| IDA | adapts upstream `ida-pro-mcp`; live GUI binding or owned headless database | bring-your-own IDA license |
| Android | headless JADX JAR (caller-supplied) via owned stdio | static APK only; Linux verified |
| Firmware | owned `binwalk`/`unblob` processes, report normalization, private extraction dir | Linux |
| Browser | CDP over literal loopback to an already-running Chrome-family browser; Playwright capture | passive observation, no navigation/JS exec |
| Native macOS | direct Mach-O/plist/demangle without an engine launch | macOS |

## 4. Investigation & evidence model

- **Loop:** Decompile → Understand → Recreate. REA explicitly does not claim
  original-source recovery or automatic cloning.
- **Evidence record:** artifact identity (SHA-256), provider id+version,
  deterministic locations, confidence, limitations, unresolved edges/unknowns.
  Inline results rather than opaque evidence links.
- **Reconstruction obligation ledger** (`build_reconstruction_obligation_ledger`):
  deterministic list of claims that must each close via unique owner + required
  parser/schema type + case fixtures + passing verifier of *comparable
  authority* to the original observation. Contradiction/duplication/residual
  unknowns keep closure open. Conservative: candidates generated from graph +
  capture records; absence of evidence never claims success.
- **Session state:** immutable provider binding per target, run_id per
  transition, process_lineage snapshots, `analysis_activity` for busy state,
  `cleanup_incomplete` for unverifiable shutdown.
- **Provider admission gate** (`docs/provider-evaluation.md`): capability
  matrix (supported/unsupported/degraded), per-record identity+authority+
  limitations, bounded subprocess lifetime, redacted diagnostics, shared
  fixture corpus across archs/formats, repeatable checks before any capability
  claim.

## 5. Process & security model

- All analysis local; no hosted service.
- Owned-process hygiene: deadlines, cancellation tokens propagated to
  providers, bounded IO retention, verified cleanup; "never kills a process it
  cannot prove it owns".
- Secrets redacted from diagnostics (paths/digests kept, credentials masked).
- Setup: `--dry-run` plan → approve → `--yes`; per-provider consent; backups.
- Runtime requests act on declared target + lifecycle only.

## 6. Port vs reimplement for devin-bundle

| REA piece | Decision | Why |
|---|---|---|
| MCP server registration (126 tools) | **Reject** | mcp-governance: ≤10-15 tools/server; 126 tools would flood context. Skill routing + CLI instead |
| `rea-agents` CLI (`npx`) | **Wrap** via `extensions/rea-ops/wrapper.py` | Same workflows/evidence without MCP registration; Node present on host (v26.5.0 verified); lazy; npx fetch on first use |
| Evidence record convention | **Adopt** | sha256 identity + provider + confidence + limitations + unknowns → reuse as the bundle's finding format across all domains |
| Obligation-ledger idea | **Adopt lite** | map to existing `.devin/ledgers/` gates pattern; no new machinery |
| Task-shape naming (inspect/search/trace/compare/capture) | **Adopt** | naming convention for new extension CLIs |
| Provider admission gate | **Adopt** | checklist before adding any new tool wrapper |
| Hopper/Ghidra bridge internals | **Ignore** | REA ships them; wrapping the CLI inherits them |
| JS/Electron/.NET/Android/firmware providers | **Use via CLI** | no reimplementation |
| Session/immutable-binding model | **Document only** | CLI one-shots are stateless; multi-step RE investigations record evidence in ledger instead |

## 7. Proposed bundle architecture

Gap analysis vs REA scope: REA covers native RE + JS/Electron + .NET + APK +
browser observation + firmware extraction. It does **not** cover web/injection
testing, network/server pentest, wireless, or mobile dynamic instrumentation;
those come from OSS CLI wrappers (see `red-team-domains.md`).

Proposed components (Fase 2, pending approval):

| Component | Path | Shape |
|---|---|---|
| Skill: offensive orchestration/routing | `skills/red-team/SKILL.md` | Routes a scoped engagement (target/window/ROE contract) to domain skills; evidence + ledger discipline; routing vs defensive `security` skill |
| Skill: binary/app RE | `skills/re-binary/SKILL.md` | REA-CLI workflow: route target → analyze → evidence → recreation handoff |
| Skill: web/injection | `skills/web-probe/SKILL.md` | ZAP/sqlmap/nuclei/ffuf wrappers; passive-first, active requires ROE |
| Skill: network/server | `skills/net-probe/SKILL.md` | nmap/masscan/enum/metasploit-adjacent; verify-not-exploit default |
| Skill: wireless | `skills/wireless-probe/SKILL.md` | aircrack/kismet/bettercap/proxmark/SDR; hardware + platform fields in contract |
| Skill: firmware | `skills/firmware-probe/SKILL.md` | binwalk/unblob/emba extraction+inventory (Linux/WSL noted) |
| Skill: mobile | `skills/mobile-probe/SKILL.md` | MobSF/jadx/frida static-first; dynamic needs rooted emulator |
| Extension | `extensions/rea-ops/wrapper.py` | `npx rea-agents@latest` passthrough: doctor, analyze, inspect, search, function, xrefs, trace, compare, capabilities |
| Extension | `extensions/offsec-tools/wrapper.py` | probe/wrap OSS CLIs (nmap, nuclei, sqlmap, zap-cli, aircrack-ng, binwalk, mobsf, frida) with `doctor`, `capabilities`, per-tool subcommands; tool-absent = `unknown`, never fabricated |
| Agent profile | `agents/red-team-lead.md` | persona + routing discipline + evidence standards |
| Tests | `tests/validation/test_red_team_skills.py` | token/contract tests per bundle convention |

Routing rule vs existing `security` skill: `security`/`secure-defaults-check` =
defensive audit of *our* code/config; `red-team` tree = scoped offensive
capability against *declared targets*. Cross-reference only, no edits.

Every offensive skill/extension contract carries: `target`, `window`, `roe`
fields; authorization assumed (Rule 13); destructive/irreversible actions
always require explicit per-action confirmation; no credential-harvesting
capability.

## 8. Evidence for this analysis

- `git clone --depth 1 https://github.com/morluto/rea` → `.devin/scratch/rea-repo`
- Read: `README.md`, `package.json`, `server.json`, `docs/architecture.mermaid`,
  `docs/tool-design.md`, `docs/mcp-contracts.md`,
  `docs/reconstruction-obligation-ledgers.md`, `docs/provider-evaluation.md`,
  `skills/reverse-engineer-anything/SKILL.md`; tree listing of `src/`,
  `bridge/`, `third_party/` (binwalk, ghidra-nativeaot, jadx-headless-mcp, unblob).
- Host check: `node --version` → v26.5.0, `npm` 12.0.1, `python` 3.14.4.
- Live verification on this host: `npx -y rea-agents@latest --version` → `4.1.0`;
  `npx -y rea-agents@latest doctor --json` → structured JSON (node 26.5.0
  healthy, win32 x64 healthy, hopper/ghidra `missing_analysis_engine` with
  remediation strings, exit 1 for unhealthy scope). Confirms the npx CLI
  wrapper path works on Windows without MCP registration or engines installed.
