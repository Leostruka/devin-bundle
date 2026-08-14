# Checklist de Design Review — Índice Canônico (52 itens)

> Fonte: `docs/HIG-REFERENCIA.md` (checklist de 52 itens). Este arquivo é o **índice canônico**: cada item tem um **dono** (skill que o audita). Nunca rode o bloco inteiro dentro de uma skill — cada skill usa apenas a própria fatia (3–8 itens no corpo; fatias completas nos references).

## TOC por categoria

- [Tipografia (1–6)](#tipografia) — dono: hig-foundations (typography.md)
- [Cor & contraste (7–11)](#cor--contraste) — dono: hig-foundations (color.md)
- [Layout (12–18)](#layout) — dono: hig-foundations (layout.md)
- [Shapes & ícones (19–21)](#shapes--ícones) — dono: hig-foundations (shapes.md / icons.md)
- [Motion (22–25)](#motion) — dono: hig-foundations (motion.md)
- [Feedback & loading (26–32)](#feedback--loading) — dono: hig-feedback (feedback.md)
- [Alertas (33–38)](#alertas) — dono: hig-alerts (alerts.md)
- [Acessibilidade (39–43)](#acessibilidade) — dono: hig-accessibility (accessibility.md)
- [Settings & navegação (44–48)](#settings--navegação) — dono: hig-settings-navigation (settings-navigation.md) [47 co-dono hig-feedback]
- [Consistência (49–52)](#consistência) — dono: hig-writing (49–50) / apple-hig orquestrador (51–52)

## Legenda de donos

| Sigla | Skill | Fatia |
|---|---|---|
| F | hig-foundations | 1–25 |
| W | hig-writing | 49–50 (+copy de 34, 47) |
| A | hig-alerts | 33–38 |
| FB | hig-feedback | 26–32, 47 |
| SN | hig-settings-navigation | 44–48 |
| AC | hig-accessibility | 39–43 |
| OR | apple-hig (orquestrador) | 51–52 |

## Tipografia

| # | Item | Dono |
|---|---|---|
| 1 | Nenhum texto < 11px em conteúdo normal | F |
| 2 | Escala limitada a 5–7 estilos em tokens; nenhum font-size arbitrário inline | F |
| 3 | Corpo line-height ≥1.4; títulos ≥1.2 | F |
| 4 | Hierarquia por peso+tamanho, não só cor | F |
| 5 | Títulos grandes no topo; metadata 11–12px | F |
| 6 | Zoom escalável (rem), sem maximum-scale restritivo | F |

## Cor & contraste

| # | Item | Dono |
|---|---|---|
| 7 | Textos ≥4.5:1 (AA) em light e dark; grande/bold ≥3:1 | F |
| 8 | Nenhum feedback só com cor | F |
| 9 | Cores semânticas com variantes dark | F |
| 10 | Dark testado com Increase Contrast/Reduce Transparency | F |
| 11 | Destrutiva usa vermelho + rótulo explícito, nunca só cor | F |

## Layout

| # | Item | Dono |
|---|---|---|
| 12 | Grade 4/8px; sem valores arbitrários | F |
| 13 | Margens de página ≥20px | F |
| 14 | Forms com label/controle em colunas; gap 8px | F |
| 15 | Seções ≥12px | F |
| 16 | Texto descritivo ~60ch | F |
| 17 | Responsivo ~800px e ~400px | F |
| 18 | Nada crítico no rodapé | F |

## Shapes & ícones

| # | Item | Dono |
|---|---|---|
| 19 | Raios consistentes (8/10/10px) | F |
| 20 | Ícones mesmo stroke (1.5–2px) | F |
| 21 | Botões de ícone com aria-label/tooltip | F |

## Motion

| # | Item | Dono |
|---|---|---|
| 22 | Durações 120/200/300ms; nada >500ms sem propósito | F |
| 23 | Reduced-motion desativa zoom/scale/spin (mantém fades) | F |
| 24 | Nada piscando em loop sem controle | F |
| 25 | Transições transform/opacity | F |

## Feedback & loading

| # | Item | Dono |
|---|---|---|
| 26 | Todo loading tem saída (cancelar/timeout/retry) | FB |
| 27 | Spinner só para não-quantificável; barra para o resto | FB |
| 28 | Nenhum progresso falso | FB |
| 29 | Sucesso confirmado só para ações significativas | FB |
| 30 | Erros com causa + ação; nunca só "Erro 1234" | FB |
| 31 | Toasts não bloqueiam; auto-dismiss + fechar | FB |
| 32 | aria-live/aria-busy corretos | FB |

## Alertas

| # | Item | Dono |
|---|---|---|
| 33 | Alertas só para crítico/acionável; nada no startup | A |
| 34 | Título ≤2 linhas; botões 1–2 palavras com verbo | A |
| 35 | Nenhum "OK" em ação destrutiva | A |
| 36 | Destrutivo com Cancel; estilo de perigo | A |
| 37 | Enter default; Esc cancela; foco capturado | A |
| 38 | Nenhum modal sobre modal | A |

## Acessibilidade

| # | Item | Dono |
|---|---|---|
| 39 | Alvos ≥44px (touch)/≥28px (mouse) | AC |
| 40 | Foco visível em tudo | AC |
| 41 | Tab order lógico; teclado completo | AC |
| 42 | `<label>` associado; obrigatórios indicados | AC |
| 43 | Ícones decorativos aria-hidden; tabelas com cabeçalhos | AC |

## Settings & navegação

| # | Item | Dono |
|---|---|---|
| 44 | Settings por atalho (Ctrl+,) + botão; último pane restaurado | SN |
| 45 | Navegação com estado atual (`aria-current`) | SN |
| 46 | Salvar explícito OU automático, nunca ambos | SN |
| 47 | Empty states com explicação + ação | FB (co: SN) |
| 48 | Atalhos documentados | SN |

## Consistência

| # | Item | Dono |
|---|---|---|
| 49 | Botões começam com verbo; capitalização consistente | W |
| 50 | Sem palavras desnecessárias; copy revisada | W |
| 51 | Estado do backup cor+ícone+texto, nunca só cor | OR |
| 52 | Alertas nunca para pura informação | OR |

## Nota de consolidação

Itens **co-ocupados**: `47` (dono primário FB/Empty States; SN referencia no contexto de listas) e `34` (dono A; W audita apenas o copy dos rótulos). No relatório final do orquestrador, cada número conta **uma única vez** (evidência combinada) para totalizar 52.
