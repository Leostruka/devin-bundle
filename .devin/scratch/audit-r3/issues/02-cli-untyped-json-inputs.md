# 02 - CLIs devem emitir erro tipado em JSON de entrada ilegivel

Status: claimed
Priority: P3
Type: cli-ux
Blocked by: none

## Contexto

Tres entry points fazem `json.loads(Path(...).read_text())` no main sem
tratamento, saindo como traceback em arquivo ausente/invalido:

- `extensions/craft-bridge/scene_manifest.py:main` (manifest) e
  `load_ops_map` com path customizado.
- `extensions/remotion-render/render.py:main` (plan).
- `extensions/ai-tools/abliterator.py` (index.json em load_safetensors).

Mesma classe do R1-01 (ffprobe) e R2-03 (compact.py).

## Impacto

Uso erroneo do CLI -> traceback ilegivel em vez de
`{"ok": false, "error": ...}` + exit != 0, quebrando o contrato de
envelope JSON usado pelos demais entry points do bundle.

## Reproducao

`python scene_manifest.py nao-existe.json` -> FileNotFoundError com
traceback; idem render.py com plan inexistente.

## Aceite

- [ ] Os tres mains convertem OSError/JSONDecodeError em
  `{"ok": false, "error": ...}` + exit 2.
- [ ] load_ops_map com path invalido cai para _DEFAULT_OPS ou erro
  tipado (escolha documentada).
- [ ] Sucesso continua emitindo o mesmo envelope JSON.
- [ ] Gate: regressao cobrindo os tres CLIs com entrada inexistente.

## Answer

Resolved. Regressions in tests/test_media_intent.py,
test_craft_bridge.py, test_animation_pipeline.py,
test_local_inference.py. Suite: 94 passed.
