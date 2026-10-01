# Bundle Capability Map - 2026-09-26

Recon for the 4-front research (Scrapling, host input routing, heyclicky,
spec-driven development). Maps what exists so integration proposals do not
duplicate or collide. Sources: direct read of the repo @ `a2d6f68` (main).

## 1. `extensions/computer-use/` (C00-C17, merged via PR #63)

| Module | Capability |
|---|---|
| `env.py`, `cu_env.py`, `cu_env_daemon.py` | Isolated env lifecycle: spec+digest, consent TTY, daemon-owned QEMU+QMP (AF_UNIX where it fits, else TCP+token), stop/restart/reset, `same_instance` |
| `cu_qmp.py`, `cu_qmp_backend.py` | QMP framing, request correlation, journal/dedup, recovery (`may_retry`, `cleanup` never touches host), `verify_effect` |
| `cu_capture.py`, `screenshot.py` | Framebuffer screendump via daemon, PNG+grid, `frame_sha256`, `--verify` re-observation |
| `mouse.py`, `cu_motion.py`, `type_text.py` | Guest-only keyboard/pointer: pure encoders, strict bounds, release-all on mid-chord failure |
| `cu_guest.py`, `guest/worker.py`, `cu_guest_worker.py` | virtio-serial guest worker: `text.insert`, `clipboard.get/set`, `probe.state`, `exec.run`, `dom.*`, `uia.snapshot` behind explicit capabilities |
| `cu_devices.py` | Physical device lease state machine (serial+topology identity, protected IDs); inventory is honest-empty without qualified backend |
| `cu_container.py` | Closed container profile (Xvfb+worker, no host mounts, network off) - spec+validator, live-qualified only on Linux |
| `cu_session*.py`, `browser*.py`, `cu_terminal*.py` | Host-side session dispatch, browser/terminal bindings namespaced per env |
| `cu_decision.py` | Laya shadow suggestions for UI targets (`adoptable()` gated on assist) |

Host input stack: `mss` capture + `pynput`/`SendInput`-family dispatch -
**everything targets the host session unless `--env`**. No directed-input
mechanism (no window-targeted posting, no UI Access path) exists today.

## 2. `extensions/laya-tools/` (L00-L10)

- `decision_contract.py` - closed outcomes `suggestion|abstain`, <=8 candidates, `__none__`, context echo, allowlisted state
- `laya_worker.py` + `decision_client.py` - resident stdio worker, offline-only, sha256-pinned local snapshots, selective preload, `model` pin from config
- `eval_decisions.py`, `capture_eval.py` - frozen-manifest metrics + capture helper
- Consumers (shadow-only): `cu_decision`, `media-tools/intent`, `workflow_routing`, `output_context`, `knowledge_labels`
- `assist` degrades to `shadow` without compatible calibration

## 3. Other extensions

| Extension | Capability |
|---|---|
| `system-control` | Brokered OS control: inventory, bounded exec, owned sessions, event streams, verified file copies; backends per-OS |
| `media-tools` | Media fx/presets, webcam, glb input, ascii; `intent.py` consumes Laya shadow |
| `blender-operator` | Headless Blender bridge `wrapper.py` + `blender_server.py` (TCP JSONL exec loop, full bpy) |
| `comfyui-operator` | Local ComfyUI HTTP client `wrapper.py` (status/submit/history/download/upload) |
| `mesh-utils` | `meshops.py` inspect/convert/clean via trimesh, PyMeshLab, pxr |
| `ai-tools` | `prompt_compiler.py` (golden template), `abliterator.py`, model knowledge_bases |
| `diagram-tools`, `rust-core` | diagrams; PyO3 crates (`fast_math` staged) |

## 4. Scraping / web-fetch capability in bundle

**None.** `youtube-fetcher` skill exists (yt-dlp wrapper). No extension does
HTTP fetching, HTML parsing, crawling, or anti-bot work. `webfetch`/`web_search`
are agent-tools, not bundle code. **Scrapling integration is greenfield - no
existing capability to duplicate or conflict with.** Candidate fit: new
`extensions/scrape-tools/` or inside `ai-tools` - decision deferred to research.

## 5. Input mechanism status (host side)

Prior research (`virtual-input-devices*.md`, `virtual-env-input-isolation.md`,
`sandboxie-*`) already established:

- True independent cursor/keyboard requires separate compositor/VM (hence QMP path).
- Virtual HID devices (driver-level) can exist per-device but need driver/kernel work.
- **Not yet researched here:** Windows message-level directed input
  (`PostMessage`/`SendMessage` to HWND without focus), UI Access, journal
  hooks, `SendInput` with `INPUT_HARDWARE` scoping, mouse-via-keyboard
  (MouseKeys, accessibility shortcuts). That is exactly the Fase-3 gap.

## 6. Spec-driven development in bundle

- `.devin/plans/` exists and is used (dated plan files, slices+checkboxes).
- `.devin/adr/`, `ARCHITECTURE_MANIFEST.md`, ledgers via `gates` skill.
- **No spec-kit scaffolding, no `/specify`-`/plan`-`/tasks` command flow.**
  SDD research must map onto the existing plan/ledger culture rather than
  replace it.

## 7. Invariants every plan must preserve

1. No host fallback on remote paths (dispatch != effect != conclusion).
2. No auto-execution from model output; `assist` gated on evals.
3. Offline-by-default for model paths; secrets never in repo.
4. Hooks/scripts stay stdlib-only; new deps need approval.
5. `pytest tests` green + `audit.py` 0 errors before push; main is protected.

## 8. Dependency map between the 4 fronts

```
F2 Scrapling        - greenfield extension; independent
F3 Input routing    - complements CU host path; must not touch --env/QMP path
F4 heyclicky        - evaluates product claims; feeds F3 if applicable
F5 Spec-driven dev  - process layer; governs HOW F2-F4 plans get executed
```

F5 is orthogonal (methodology); F3/F4 overlap at "mouse without focus" and
must share one decision owner (F3 owns input mechanism; F4 only feeds facts).
