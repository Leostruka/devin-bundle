---
name: hig-writing
description: Use quando o usuário pedir para revisar ou escrever o texto da UI WebView2 (dashboard/settings do BackupEmail) seguindo Apple HIG. WHAT: audita a fatia 49–50 do checklist (e o copy de 34 e 47) com evidência arquivo:linha — botões começam com verbo ("Executar Backup", nunca "OK"), capitalização consistente, copy enxuta sem interjeições, mensagens de erro com causa + como corrigir posicionadas ao lado do campo. WHEN: triggers "copy", "texto de botão", "rótulo", "mensagem de erro", "capitalização", "UX writing". NÃO use para: estrutura de alerta/modal (botões e foco) — use hig-alerts; decisão de progresso/loading — use hig-feedback; acessibilidade/leitor de tela — use hig-accessibility; tamanhos e fontes — use hig-foundations.
version: 1.0.0
family: apple-hig
target: wpf-webview2
---

# HIG Writing — UX Copy

Copy da UI (checklist 49–50 + copy de 34 e 47). O texto errado quebra a percepção do app mesmo com visual perfeito.

## Quando usar

- Revisar/escrever rótulos de botões, títulos, mensagens de erro, placeholders, empty states.
- Definir padrão de capitalização (title case vs sentence case) e tom.
- Corrigir mensagem de erro que "culpa o usuário" ou não diz como corrigir.

## Quando NÃO usar

- Estrutura do alerta (ordem de botões, foco, `role="alertdialog"`) → `hig-alerts`.
- Progresso/loading/empty states (estrutura e ações) → `hig-feedback`.
- Contraste/leitor de tela → `hig-accessibility`.
- Tipografia/tamanhos → `hig-foundations`.

## Contexto obrigatório

Leia **references/app-context.md** (o app é pt-BR; estado do backup usa cor+ícone+texto). Leia **references/writing.md** (seção 8 + lacuna 13) — carrega os valores; este corpo só tem princípios.

## Domínios

| Domínio | Reference | Fatia do checklist |
|---|---|---|
| Rótulos e botões | `references/writing.md` | 49 |
| Copy enxuta e tom | `references/writing.md` | 50 |
| Copy de alertas (rótulos) | `references/writing.md` | 34 (copy) |
| Copy de empty states | `references/writing.md` | 47 (copy) |
| Mensagens de erro | `references/writing.md` | 30 (copy) + lacuna 13 |

## Princípios

- Seja claro; reduza ao necessário; leia em voz alta.
- **Verbos em botões** ("Executar Backup", "Salvar Alterações") — nunca "OK" em ação destrutiva.
- Sem interjeições ("Ops!", "Oops!"); sem "por favor/desculpe" genéricos.
- Capitalização consistente (title case OU sentence case, nunca misturar).
- Erro: título = problema concreto; corpo = causa + solução ("Verifique sua rede e tente novamente").
- Erro exibido **perto do problema**, instruindo **como corrigir** — não o que está errado ("Use apenas letras no nome" > "Não use números").
- Toast de sucesso: verbo passado ("Backup concluído").

## Guardrails

- NUNCA "OK"/"Sim"/"Não" em ação destrutiva — use verbo + objeto ("Excluir destino").
- NUNCA "Click here" (screen readers leem rótulo, não a instrução).
- NUNCA "Erro 1234" sem causa e ação.
- NUNCA culpar o usuário ("Você digitou errado") — diga como corrigir.
- NUNCA interjeições nem "we/estamos" ("Não foi possível carregar o conteúdo" > "Estamos com problemas...").

## Exemplos

- **Bom**: botão `Executar Backup` / `Salvar Alterações` (verbo primeiro, sentence case pt-BR).
- **Ruim**: botão `OK` ou `Confirmar` genérico em ação destrutiva.
- **Bom**: erro de campo — `"Use apenas letras no nome"` (instrução positiva, adjacente ao campo).
- **Ruim**: `"Nome inválido"` ou `"Erro 400"` (o que está errado, sem como corrigir).
- **Bom**: empty state — `"Nenhum backup ainda — execute o primeiro backup para proteger seus PSTs."`
- **Ruim**: empty state — `"Sem dados."` (sem explicação nem próximo passo).

## Checklist do domínio

- **[49] Botões começam com verbo; capitalização consistente** — PASS: todos os rótulos acionáveis iniciam com verbo no infinitivo → verificação: leitura de todos os `<button>`/`<a>`; padrão único de capitalização. Fonte: HIG Writing.
- **[50] Sem palavras desnecessárias; copy revisada** — PASS: nenhuma interjeição, "por favor", "você precisa", dupla negativa → verificação: busca textual. Fonte: HIG Writing.
- **[34-copy] Botões do alerta 1–2 palavras com verbo, sem pontuação** — PASS: rótulos curtos ("Excluir", "Cancelar", "Ver tudo") → verificação: leitura do modal. Fonte: HIG Alerts (copy).
- **[47-copy] Empty state explica + próximo passo acionável** — PASS: título + texto + CTA → verificação: leitura da tabela vazia. Fonte: HIG Empty States.
- **[30-copy] Erros com causa + ação** — PASS: mensagem diz o problema e o que fazer → verificação: leitura dos painéis de erro. Fonte: HIG Writing / Error Messages.

## Failure modes

- Rótulo bonito mas ambíguo ("Prosseguir" sem destino).
- Misturar title case e sentence case na mesma tela.
- Erro longo demais (deve caber em 1–2 linhas) ou vago demais ("Algo deu errado").

## Related Skills

- `hig-alerts` — estrutura do alerta; esta skill fornece o copy dos rótulos (34).
- `hig-feedback` — esta skill fornece o copy de empty states (47) e erros.
- `apple-hig` — consolida 49–50 no relatório 52/52.
