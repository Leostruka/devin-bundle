# Plan: Four research fronts -> implementation (2026-09-26)

Source research (read first):
- `.devin/research/bundle-capability-map.md` (F1 recon)
- `.devin/research/scrapling-integration.md` (F2, 67 sources)
- `.devin/research/host-input-routing.md` (F3, 115 sources)
- `.devin/research/heyclicky-eval.md` (F4, 50 sources)
- `.devin/research/spec-driven-development.md` (F5, 80 sources)

## Goal

Add scraping capability (Scrapling), host-side scoped input + ghost overlay
(F3/F4 lessons), and close the two real SDD gaps (analyze/converge) - without
duplicating existing capability, without breaking invariants.

## Global Constraints (invariants - every slice preserves)

- No host `SendInput`/InputInjector on background paths (steals user focus) [F3 §2].
- No journal hooks (blocks real input; dead on Win11) [F3 §4].
- No auto-exec from model output; Laya `assist` stays gated on E-evals.
- New deps live behind extension `requirements.txt` + install-time consent; hooks stay stdlib-only.
- `pytest tests` green + `audit.py` 0 errors before push; main is protected (PR + CI).
- Scoped channels are teleport-only: `fast` semantics; `human`/`smooth` stay on
  host+guest paths where a real cursor exists.
- Every user-facing decision cites a verified fact from the research files.

## Front ownership (one capability = one owner - zero conflicts)

| Capability | Owner | NOT elsewhere |
|---|---|---|
| Web scraping/fetch/parse | F2 `scrape-tools` | not in media-tools/ai-tools |
| Host scoped input | F3 `cu_scope` inside computer-use | not a new extension |
| Ghost cursor + annotations | F3-S5/S6 (`cu_overlay`) | not a motion profile; not an extension |
| Spec pipeline gaps | F5 templates + 2 skills | not spec-kit install |

F4 (heyclicky) produces NO plan - it feeds decisions into F3 (overlay) and is
closed: macOS-only product, click mechanism undisclosed [F4 §5].

## F2 - `extensions/scrape-tools/` (Scrapling tiered)

Decision: adopt **parser + `Fetcher`(curl_cffi) tier first**; browser tiers
(Dynamic/Stealthy) behind opt-in flag - they need ~300-600MB first-run
`scrapling install` [F2 §6,§9]. Do NOT register Scrapling's MCP server now
(mcp-governance: audit tool-count first; SKILL.md exists for future).

- [ ] S1 `extensions/scrape-tools/` skeleton + `requirements.txt`
        (`scrapling[fetchers]>=0.4.15,<0.5` pin. Fetcher/curl_cffi lives
        in the extra, not core [F2 §6]; pip wheels incl. playwright/
        patchright packages land now, browser binaries still gated by S5).
        0.x churn documented [F2 §7].
        Gate: `pip install -r` into .venv; `python -c "import scrapling"`.
- [ ] S2 `parse.py <file|-> --css|--xpath [--first]` - offline, parser-only,
        zero network, stdlib-shaped JSON out. Gate: parses fixture HTML;
        exits!=0 on bad selector; works with no fetchers extra installed
        (parser is core-tier [F2 §6]).
- [ ] S3 `scrape.py <url> --css|--xpath [--impersonate chrome]
        [--json]` - Fetcher+curl_cffi path; JSON {status,url,nodes[]}.
        Gate: mock-free live test against httpbin-style target documented
        manually (opt-in, not CI); SSRF-safe redirects on [F2 §3].
- [ ] S4 `--adaptive` flag wiring `auto_save/adaptive` with SQLite storage
        under env-namespaced dir (reuse `CU_STATE_ROOT` pattern? no -
        own `.devin/scrape-tools/storage/`; keep isolation). Gate:
        save -> rename class in fixture -> relocate finds element [F2 §4].
- [ ] S5 Browser tiers: `--browser` rejected with
        `feature_off:browser_tier_not_installed` until user runs
        `python -m scrapling.cli.install` themselves (consent, offline-by-
        default violated otherwise). Gate: error is honest, JSON-shaped.
- [ ] S6 USAGE.md + skill `scrape-tools` (when-to-use rules; forbidden:
        credential scraping, auth-bypass crawling). Gate: audit.py 0 errors.
- [ ] S7 tests: parser contract, scrape JSON shape, adaptive roundtrip,
        browser-gate error. Gate: `pytest tests` +N green.

NON-GOALS: spiders framework, ProxyRotator, MCP server, Rust port [F2 §9];
any "undetectable" claim (disproven [F2 §8]); scraping inside VM path.

## F3 - Scoped host input + ghost overlay (computer-use)

New CLI axes inside `extensions/computer-use/` (decided in thread):
`--channel host|env|scope|uia|cdp` (default host, back-compat) and
`--cursor real|ghost` + `--overlay-capture visible|hidden`.
`env` is a universe selector, not a delivery channel: `--channel env`
requires the existing `--env ID` registry path; `host|scope|uia|cdp`
reject `--env`. Naming: `cu_target.py` already owns "target" for env
resolution. `cu_scope.py` resolves *window targets* (HWND) instead;
keep the two meanings distinct in code and docs.

- [ ] S1 `cu_scope.py` - channel dispatcher + window-target resolution
        (HWND by title/class/pid; conhost vs Win32 detection).
        Gates: resolve notepad->Edit child HWND, not frame [F3 §1];
        unit test on fixture HWND tree.
- [ ] S2 PostMessage keyboard path: WM_CHAR/WM_KEYDOWN to child control;
        report `delivered` honestly (delivery != effect [F3 §1]).
        Gates: types into real Notepad while user keeps focus (manual
        live gate); unit test for message construction + honesty shape.
- [ ] S3 WriteConsoleInput path for conhost (AttachConsole + CONIN$ +
        INPUT_RECORD incl. mouse events) [F3 §7].
        Gates: sends ENTER to a real cmd.exe background window (manual);
        unit test for INPUT_RECORD construction.
- [ ] S4 UIA channel: Invoke/Value/Scroll patterns via comtypes UIA
        (the cu_hints/cu_terminal pattern, already pinned; NO pywinauto,
        new deps need approval); `--force-renderer-accessibility` note
        for Chromium targets [F3 §3].
        Gates: invokes a real button on occluded window (manual); unit
        test via comtypes seam (test_cu_uia_actions.py style).
- [ ] S5 `cu_overlay.py` - ghost cursor: WS_EX_LAYERED|TRANSPARENT|
        NOACTIVATE topmost window; sprite + bezier fly-to-target;
        `--overlay-capture hidden` applies WDA_EXCLUDEFROMCAPTURE
        (opt-in; default visible) [F4 §4; user decision]. Win10 2004+;
        hidden also blinds the agent's own mss captures: the ghost never
        appears in --verify evidence frames (they read target rect,
        not the overlay). Document in S10.
        Gate: overlay visible on screen, zero input reach (WS_EX_TRANSPARENT).
- [ ] S6 Annotation layer (same window): box+label+arrow primitives driven
        by UIA geometry; used by --verify/dry-run preview.
        Gate: renders box over target rect without focus steal.
- [ ] S7 CDP channel: reuse cu_browser `BrowserClient`/`_cdp_client`
        (loopback-pinned; dispatchMouseEvent + insertText exist). Add
        `Input.dispatchKeyEvent` for non-text keys (insertText can't
        send Enter). Agent-launched/attached browsers only; document
        launch flag needed [F3 §8].
        Gate: click works in headless AND headed Chromium (manual).
- [ ] S8 Wire `--channel` into mouse.py/type_text.py: scoped channels reject
        `--profile` other than fast (no cursor -> no motion profile;
        human/smooth remain on host+env only).
        Gate: `--channel scope --profile human` errors clearly.
- [ ] S9 Held-out proof: scoped input delivered to target app while a real
        user input stream is untouched (extend test_cu_env_boundaries style;
        live gate documented like C16).
- [ ] S10 USAGE.md: channel ladder (PostMessage->UIA->CDP->RDP/VM fallback),
        honest failure matrix per app class [F3 §9]; no "works everywhere"
        claims. Fix stale `uiautomation` mention at USAGE.md:28 (dep was
        removed; comtypes is the UIA path).

NON-GOALS: SendInput scoping (impossible [F3 §2]); virtual HID per-app
(structurally impossible [F3 §5]); games/anti-cheat targets (documented dead
ends, defer to RDP/VM); journal hooks; CreateDesktop tricks; automatic
foreground theft as "fallback"; Clicky-style voice/agent persona (F4 says
borrow overlay+native-channels only).

## F5 - SDD gaps (process layer)

Decision: patch the two real gaps; do NOT install spec-kit (80% duplicate
[F5 §7]).

- [ ] S1 Plan template: add "Spec (what/why, tech-agnostic, user stories,
        acceptance criteria)" front-matter before Tech Stack in
        `skills/planning/modes/plan-doc.md` (header block, Tech Stack ~:79).
        Repo skills go live only after `install.ps1` re-export to
        %APPDATA%\devin\skills; include that step in the slice.
        Gate: new plan generated with block; old plans untouched.
- [ ] S2 `analyze` - `scripts/spec-consistency.py` (stdlib-only): reads a
        plan file + ARCHITECTURE_MANIFEST + related ADRs + `.devin/ledgers/`
        (NOT root `ledgers/`, which holds audit reports); reports cross-artifact
        mismatches (files named in plan that don't exist, constraint
        violations declared then broken, unchecked boxes after "done"
        claims). Read-only, JSON out. Parse leniently: plan-doc `**Files:**`
        blocks are machine-checkable; prose-slice plans (like this one)
        get best-effort extraction, not silence.
        Gate: run on this plan file -> reports clean or lists real diffs;
        unit tests on fixture plans.
- [ ] S3 `converge` - step in `finishing-a-development-branch`: diff
        delivered code vs plan+ledger, append residual tasks to the plan
        instead of silent drift (documented failure mode [F5 §6]).
        Gate: on a completed slice, produces "converged" or new open items.

NON-GOALS: EARS notation; specs/NNN/ dirs; branch-per-spec; tasks.md file;
Tessl/spec-as-source (least proven [F5 §1]); Kiro-style 3-file spec.

## Dependency map

```
F2  independent (greenfield extension)
F3  S1-S4 channels -> S5-S6 overlay uses same HWND/geometry plumbing
    S7 CDP independent of S2-S4
    S9 needs S2+ done
F5  S2 analyze SHOULD run on this very plan before F2/F3 start (dogfood)
F4  closed - inputs already folded into F3 S5/S6
```

## Cross-conflict check (final)

- F2 and F3 touch zero same files (new dirs both, disjoint).
- F3 changes only computer-use internals; `--env` QMP path untouched
  (scoped = complement host-side, per constraint).
- F5 S2 is a script + template edit; zero overlap with extensions.
- One dep each: scrapling (F2), comtypes UIA (F3 S4, already pinned in
  requirements.txt), nothing new for F5.
- No plan claims unverified capability; UNVERIFIED markers propagate from
  research into gates (e.g., WriteConsoleInput mouse focus gating is
  documented UNVERIFIED [F3 gaps]).

## Human checkpoints inside the plan

- F2 S5: browser-tier install = explicit user action, never automated.
- F3 S2-S4,S7: each channel's live gate is manual (real window + real user
  present) - deterministic tests cover plumbing, honesty covers effect.
- F3 S9 held-out proof with a human physically typing during scoped input.
- Before ANY slice: this plan reviewed and approved (SDD spec-first level -
  matches measured-adoption reality, most teams spec-first [F5 §6]).
