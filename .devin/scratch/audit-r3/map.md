# audit-r3 -- round 3 map

Scope: media-tools, craft-bridge, remotion-render, ai-tools CLIs,
computer-use mains, scripts hooks -- unbounded reads, unguarded JSON,
untyped CLI errors.

| # | Issue | Priority | Status | Gate |
|---|-------|----------|--------|------|
| 01 | custom_presets.json corrompido derrubava built-ins | P2 | resolved | test_media_intent.py |
| 02 | 3 CLIs emitiam traceback em input ilegivel | P3 | resolved | 3 test files |

Falsos positivos descartados: prompt_compiler.main ja envolve
load_draft; cu_dom_picker tem reads bounded + erros tipados; sc_cli
usa _reply/InvalidRequest; context-budget le arquivos confiaveis com
erro tipado; sc_process tem timeout + fail-closed.
