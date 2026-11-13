# Rune spike - agent-rendered UI loop (R12 -> issue #570)

Fonte: reel louis_rlee DfnKmAPIoAW ("Roon" = Rune, anomalyco/rune, MIT, pre-release pin dev rev).
Clone: .devin/scratch/rune-spike (gitignored scratch, nao commitar o repo).

## Resultado do spike (Windows, Intel Iris Xe, wgpu/Dx12)

| Passo | Comando | Resultado |
|---|---|---|
| Build | `cargo run -p hello` | 2m05s primeiro build (debug) |
| Render headless | `hello --snap hello.png --scene on` | PNG 320x200 ok, gpu init ~100ms warm |
| Input scripted | `hello --snap t.png --script tap.json --at mark:after` | tap alterou estado (12 inst vs 11, glyph "on") |
| Element tree | `hello --tree tree.json --snap t.png` | JSON a11y: role/name/bounds/actions por elemento |

## Por que importa pro bundle

- Mesmo contrato do `cu_agent_desktop` (a11y tree > pixels), mas em BUILD-TIME: o agente escreve a UI, renderiza, le a tree, clica scripted, e itera - sem SO/GUI real e sem screenshot polling.
- design-iteration-loop eval (.devin/evals/) ganha um target concreto e deterministico: UI renderiza igual toda vez, tree e JSON comparavel.
- computer-use: `Runtime::with_text` = percepcao headless identica ao padrao que ja adotamos (issue #427).

## Caveats

- Pre-release: pin `rev` do branch dev; API pode mudar.
- Headless nao substitui validacao em device real (dynAImyx review nota o mesmo).
- Rust toolchain 1.99.1 auto-instalada pelo rust-toolchain.toml do repo.

## Recomendacao

Spike validado. Adocao real = quando houver uma UI nativa para construir (ex.: front-end local do busybar/laya dashboard). Manter issue fechada com este doc como evidencia; reabrir se surgir caso de uso de UI.
