# 01 - Conter timeout do ffprobe dentro do contrato tipado do ingest

Status: resolved
Priority: P2
Type: reliability
Blocked by: none

## Contexto

`extensions/media-tools/playblast_ingest.py:probe()` roda ffprobe com
`timeout=60`. `subprocess.TimeoutExpired` herda de `SubprocessError` --
nao e `OSError` nem `ValueError`. `ingest_playblast` propaga e `main()`
captura apenas `(OSError, ValueError)`, logo um ffprobe travado sai como
traceback nao tratado em vez de `{"ok": false, "error": ...}` + exit 1.

## Impacto

Um ffprobe lento/travado num mp4 grande produz crash sem mensagem
estruturada -- o chamador (agente/pipeline) nao recebe erro tipado e o
ponto de falha fica ilegivel nos logs.

## Reproducao

Stub de `subprocess.run` lancando `TimeoutExpired` dentro de
`ingest_playblast` (camera.json valido + mp4 temporario): a excecao
escapa sem conversao. Verificado em shell -- `ESCAPES as TimeoutExpired`.

## Aceite

- [ ] Timeout do ffprobe vira `{"ok": false}` + exit 1 em `main`.
- [ ] Erros de execucao do ffprobe (OSError de spawn, returncode != 0,
  JSON invalido) continuam tipados.
- [ ] Sem mudanca no contrato de `probe()` para chamadores Python
  (FileNotFoundError/ValueError continuam documentados).
- [ ] Gate: `python -m pytest tests/test_camera_blocking.py -q`.

## Answer

probe() agora traduz subprocess.TimeoutExpired para ValueError("ffprobe timed out after 60s"), que ingest propaga e main() converte em {"ok": false} + exit 1. Regressao test_ingest_ffprobe_timeout_typed em test_camera_blocking.py: 70 passed.
