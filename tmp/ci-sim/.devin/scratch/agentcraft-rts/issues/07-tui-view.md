# 07 - TUI view

Status: resolved
Blocked by: 01

## Objetivo

Cliente terminal (Textual ou stdlib) falando o mesmo protocolo WS: `/status`, `/agents`, `/decisions`, `/answer`, `/feed`. Referência: `npm run tui` do foreman. Serve como view mínima quando browser não convém e como cliente de teste do protocolo.

## Gate

gate: TUI conecta, lista frota e responde decisão de teste.
expect: mesmas operações da UI web funcionam via TUI.
evidence: transcript capturado.
