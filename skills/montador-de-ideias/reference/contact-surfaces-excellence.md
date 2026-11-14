# Contact Surfaces Excellence: Facilitar, Resolver, Impressionar, Ser Intuitivo

## Purpose

A contact surface is any boundary where a user, developer, operator, or agent touches the product: GUI, CLI, API/SDK, configuration file, onboarding flow, error message, notification, or documentation. In `montador-de-ideias`, every contact surface must be explicitly inventoried and engineered against four non-negotiable imperatives: **Facilitar, Resolver, Impressionar, e Ser Intuitivo**.

## The 4 Imperatives Matrix

| Imperative | Engineering Definition | Measurable Bar | Anti-Pattern (Forbidden) |
|---|---|---|---|
| **1. Facilitar** (Frictionless Convenience) | Eliminate setup ceremony, manual configuration, and cognitive tax between intent and result. | Time-to-Value (TTV) <= 60s (CLI/tool) or <= 3 clicks (UI); zero required config files for the default happy path. | Requiring the user to read 5 pages of docs, edit 3 YAML files, or pass 8 mandatory flags before the first successful run. |
| **2. Resolver** (End-to-End Resolution) | Solve the complete root problem, including edge cases and recovery, without dumping half-finished output on the user. | 100% of common failure modes emit root cause + exact copy-pasteable remediation command; zero dead-end states. | Returning partial/raw data that requires the user to write glue scripts, or emitting generic errors like `Invalid input` / `Error 500`. |
| **3. Impressionar** (Craft, Speed & Delight) | Deliver responsiveness, visual/structural clarity, and capability depth that feel a generation ahead of market alternatives. | Perceived feedback <= 100ms (Doherty threshold); Web Vitals LCP <= 2.5s, INP <= 200ms, CLS <= 0.1; crisp typography/ASCII/JSON ergonomics. | Sluggish unbuffered output, generic AI-slop UI templates, layout shifts, or verbose walls of unstructured text. |
| **4. Ser Intuitivo** (Zero-Manual Mental Model) | Align the interface with the user's existing mental model so the right action is obvious and mistakes are prevented by design (poka-yoke). | First-time user completes primary journey without external docs; 10/10 Nielsen heuristics pass; destructive actions require explicit `--confirm` / preview diff. | Hidden modes, surprising side effects, inconsistent verb/flag naming, or destructive defaults without dry-run preview. |

## Contact Surface Inventory Template

For every project assembled by `montador-de-ideias`, enumerate all active surfaces and fill this specification table:

| Surface | Target Actor (Human / Agent) | Como Vai Facilitar (TTV & Steps) | Como Vai Resolver (End-to-End Outcome & Error Recovery) | Como Vai Impressionar (Speed, Craft, Delighter) | Como Sera Intuitivo (Mental Model & Poka-Yoke) |
|---|---|---|---|---|---|
| **Onboarding / First Run** | Human / Dev | One-command install + auto-doctor check; <= 60s to first result. | Auto-detects environment gaps and offers exact fix commands. | Instant diagnostic summary with clear status badges. | Zero config required for default local workflow. |
| **Primary Interface (UI / CLI / API)** | Human / Agent | Sensible defaults; progressive flags (`--detail brief\|compact\|full`). | Executes full workflow and verifies output integrity automatically. | Sub-100ms feedback; structured deterministic output. | Verb-first grammar matching domain mental model; `--dry-run` support. |
| **Error & Edge Recovery** | Human / Agent | Pinpoints exact file/line/field that failed. | Provides copy-pasteable recovery command or safe rollback. | Clean, structured error card/JSON without noisy stack dumps. | Fails closed before any partial destructive side effect. |

## Verification via Excellence Gate

In downstream implementation (`project-orchestrator` G5), every contact surface declared here is verified not just by unit tests, but by walking and recording the real user path (`computer-use` `record.py` for GUI or terminal path walkthrough for CLI/API) and reviewing frame-by-frame against the 4 imperatives above.
