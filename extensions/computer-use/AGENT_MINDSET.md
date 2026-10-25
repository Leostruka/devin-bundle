# GUI Automation Mindset (computer-use)

Working rules for agents driving the desktop through this extension. Adapted
from the ARTEMIS (Google) "AI Agent Testing Mindset" rules; the principles
transfer, the tooling is desktop, not Android.

### 1. The Runnable Code Principle: explore before scripting

- Deliver runnable automation with **verified interactions and explicit wait
  conditions**, never assumed click paths.
- Before authoring any scripted sequence, explore the target interactively:
  `screenshot.py --hints` to enumerate elements, probe transitions, confirm
  what a control actually does.
- **Timing discipline**: agent-driven steps carry model latency; scripted
  replay does not. Use exploration to find the path, then put deterministic
  waits (`time.sleep`, polling for the next screen state) in the deliverable.
- When a task implies a duration ("wait for the page to load"), judge whether
  exact timing is functionally critical; prefer waiting on an observable
  state (element appears, terminal quiets) over fixed sleeps.

### 2. Dynamic-first, coordinate-fallback

- Prefer **dynamic locators** wherever the toolkit supports them:
  `mouse.py click --hint <label>` and `type_text.py --via uia` survive layout
  drift and resolution changes.
- Fall back to **absolute coordinates** (verified during exploration) when
  dynamic location fails or the target has no UIA presence.
- Document coordinates relative to a landmark (window corner, grid cell) so
  the script degrades gracefully on different resolutions.

### 3. Diagnose before guessing

- When a tool fails, run `cu_diagnose` / `cu_env.py --check` first. Do not
  retry blind, and do not ask the user to poke at the environment manually
  before you have the report.
- `cu_browser.py status` reports whether a bound browser exists and which
  transport (CDP/BiDi) is live; `terminal_sessions.py` reports terminal
  health. Consult state before action.
- Layered perception, cheapest first: **UIA tree → coordinates →
  screenshot/OCR**. Escalate only when the cheaper layer can't ground the
  target.

### 4. Perceive-act-verify

- Every interaction is a cycle: observe (screenshot/hints) → act → **verify
  the effect** (screenshot or read state). Never chain actions blind unless
  the intermediate states are guaranteed transient.
- On failure, record what was observed and adapt; three consecutive failures
  on the same action means the premise is wrong: re-perceive, don't retry.

### 5. Safety on the desktop boundary

- Destructive UI actions (delete, send, pay, close-without-save) require
  explicit user confirmation regardless of how confident the targeting is.
- Type into fields, not at coordinates you haven't re-verified after focus
  changes.
- The extension operates a real screen; leave the desktop in the state the
  user expects (restore focus, dismiss dialogs you opened).
