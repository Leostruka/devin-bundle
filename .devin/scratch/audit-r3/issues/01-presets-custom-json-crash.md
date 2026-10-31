# 01 - custom_presets.json corrompido nao deve derrubar presets built-in

Status: claimed
Priority: P2
Type: robustness
Blocked by: none

## Contexto

`extensions/media-tools/presets.py:_load_custom` faz
`json.loads(CUSTOM_FILE.read_text())` sem tratamento. `list_presets`
sempre chama `_load_custom`, e `get_preset` consulta custom quando o
nome nao e built-in.

## Impacto

Um `custom_presets.json` invalido (truncado, JSON quebrado) lanca
JSONDecodeError em TODA consulta de preset -- incluindo nomes built-in
via `list_presets` e `--list-presets` do grainrad. Um arquivo
user-writable corrompido derruba funcionalidade que nao depende dele.
Mesma classe do R1-03 (memory note ilegivel).

## Reproducao

Escrever `{bad` em custom_presets.json e chamar
`presets.list_presets()` -> JSONDecodeError traceback.

## Aceite

- [ ] _load_custom retorna {} (ou fallback seguro) em OSError/JSONDecodeError.
- [ ] list_presets continua funcionando com custom corrompido.
- [ ] Erro de parse e diagnostico visivel (stderr ou campo), nao silencioso.
- [ ] Gate: regressao com custom_presets.json invalido.

## Answer

Resolved. Regressions in tests/test_media_intent.py,
test_craft_bridge.py, test_animation_pipeline.py,
test_local_inference.py. Suite: 94 passed.
