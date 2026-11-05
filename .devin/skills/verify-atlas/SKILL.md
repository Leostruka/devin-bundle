---
name: verify-atlas
description: Use when changing the GitHub Pages atlas (site/src/*, site/build.py, data inputs like manifest/CHANGELOG) and a real end-to-end proof is needed that the built site actually works - boot, tabs, skill cards, REPL, palette. Project-local verification skill generated via create-verification-skill.
disable-model-invocation: true
---

# Verify: devin-bundle atlas

The atlas is a static single-page app at `site/dist/` (built by `site/build.py` from manifest/skills/agents/hooks/ADRs/CHANGELOG). No backend; "launch" = serve dist over HTTP because fetch of the embedded app still wants a real origin for some checks.

## Launch

```bash
python site/build.py                 # rebuild dist from live data
python -m http.server 8737 -d site/dist &   # serve on 8737
```

Ready when `curl -s http://localhost:8737/` returns the index HTML containing `id="term"`. Teardown: kill the spawned http.server PID (job control), never `pkill python`.

## Doctor

- `curl -s http://localhost:8737/ | grep -c 'DEVIN BUNDLE'` >= 1 -> server is ours and built.
- `python -c "import json;d=json.load(open('manifest.json'));print(d['skill_count'])"` should equal the count rendered in the boot stats line - mismatch means dist is stale (rebuild).

## Drive

Harness = headless Edge/Chrome screenshot + DOM assertions via `curl` (no Playwright dep in this repo):

```bash
# DOM assertions (no browser needed)
curl -s http://localhost:8737/app.js | grep -c 'logoSwap\|startRepl'   # feature code present
curl -s http://localhost:8737/ | grep -o 'data-skill="[^"]*"' | wc -l   # skill cards rendered server-side? (they are client-side; check DATA payload instead)

# visual proof
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless --screenshot=proof.png --window-size=1600,1000 --virtual-time-budget=9000 http://localhost:8737/
```

Prefer DOM/grep assertions on the served files for logic checks; use the screenshot only as visual evidence of the boot/tab render.

## Evidence

- Proof artifacts go to `.devin/scratch/verify-atlas/<run>/` (screenshots + the DOM-grep output saved to `checks.txt`).
- A proof = feature exercised through the real user path (boot renders -> tab switch -> REPL command), not "the file exists". Record action AND resulting state.

## Cleanup

- Kill the http.server you started (job PID). Never kill by name.
- Remove the run dir ONLY if empty of evidence; evidence always survives teardown.

## Feature map

See `features/README.md` - top features: boot-sequence, tab-navigation, repl-commands, skill-modal, command-palette.
