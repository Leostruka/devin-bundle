# audit-r5 -- issue map

Fifth audit round. Scope: never-audited surfaces -- comfyui-operator
wrapper, skills/agents reference integrity, data/ consistency,
templates, mcp_server internals, install.sh remainder, unsafe-primitive
sweep (pickle/eval/TLS-off), media-tools remaining CLIs.

| # | File | Defect | Severity | Status |
|---|------|--------|----------|--------|
| 01 | `extensions/comfyui-operator/wrapper.py` | `--url`/`COMFYUI_URL` unrestricted (no loopback check; upload/submit exfil surface) | P2 | resolved |
| 02 | `extensions/comfyui-operator/wrapper.py` | `cmd_download` writes server-controlled filename unsanitized (`..\`, absolute drive -> write outside outdir on Windows) | P2 | resolved |

## Scanned, clean

- 200 SKILL.md + agents/*.md reference sweep: all script/template refs
  resolve (skill-relative layout; two apparent misses were an external
  GitHub attribution link and a POSIX venv path in docs).
- `data/*.json`: all parse; `bundle-models.json` role pins resolve to
  model ids. Parked: `aliases.swe->swe-2` points at a family id with no
  code consumer (dead data, not a defect).
- `mcp_server.py`: subprocess args passed as list (no shell),
  TimeoutExpired handled.
- `install.sh` remainder: rm -rf confined to DEVIN_HOME install dir;
  hash functions already fixed in R1.
- `validate-mermaid.py`: subprocess timeout + fail-open on missing node.
- `behavioral-nudge`, `laya-guard`, `memory-post-edit`,
  `refine-review-prompt`, `memory-stop`: fail-open contract held.
- `ascii_mancer`, `grainrad`, `update_tooooools_db`: global try ->
  typed errors.
- No `pickle`/`marshal`/`yaml.load`/`eval`/`shell=True`/`verify=False`/
  `CERT_NONE` anywhere outside .venv.
- `.devin/templates/*.json`: parse clean.
