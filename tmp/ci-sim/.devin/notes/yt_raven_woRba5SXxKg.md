# yt woRba5SXxKg -- Raven GUI library (C + Vulkan)

Source: https://youtu.be/woRba5SXxKg (Oscar Soirey, 88s, 2026-10-22)
Upstream: https://github.com/oscar-soirey/Raven -- docs
https://oscar-soirey.github.io/Raven/

## Conteudo

Screen-recording demo, sem narracao (whisper: BLANK_AUDIO x3).
Descricao: GUI library escrita do zero em C e Vulkan, estetica
"glass", cross-platform, API leve. Tutorial valido para v0.1.3 --
API ainda instavel por declaracao do autor.

## Veredito: avaliado e rejeitado para o bundle (rastrear apenas)

- `extensions/craft-bridge/ui_dsl` ja renderiza HUDs/forms em HTML --
  zero deps nativas, roda em qualquer browser/webview.
- Um backend Raven exigiria renderer Vulkan + bindings C para
  beneficio marginal neste caso de uso.
- Maturidade 0.1.x, API instavel -- revisit apenas se surgiu
  necessidade real de HUD nativo fora de browser.

## Efeito colateral (bug encontrado na extracao)

`extensions/asr/transcribe.py` quebrado no Windows: `_find_binary`
nao procurava em `_cache/Release/` e caia em `which("main")` ->
`main.CPL` do system32 (WinError 193). `_model_path` rejeitava a
soletragem `ggml-base`. Corrigido + regressoes em
tests/test_animation_pipeline.py.
