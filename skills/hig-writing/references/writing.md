# Writing / UX Copy (checklist 49–50) — HIG seção 8 + lacuna 13

> Aplica-se ao copy dos rótulos dos itens 30, 34 e 47 (a estrutura é de cada skill dona).

## Fatia do checklist

| # | Item | PASS |
|---|---|---|
| 49 | Botões começam com verbo; capitalização consistente | rótulos com verbo no início; padrão único de capitalização |
| 50 | Sem palavras desnecessárias; copy revisada | sem interjeições, "por favor", "você precisa" |

## Princípios

- Seja claro; reduza ao necessário; leia em voz alta.
- **Verbos em botões** ("Send" > "Let's do it!"). Evite "Click here" (screen readers).
- Sem interjeições ("Oops!", "Uh-oh"); sem "please/sorry" genéricos.
- Capitalização consistente (title case ou sentence case, não misture).
- Empty states: explique + próximo passo acionável; não mostre info crucial.

## Valores

- Alerta: título 1–2 linhas; botões 1–2 palavras, verbos, sem pontuação ("View All", "Delete").
- Fluxos: "Continue"/"Next", "Done" no fim.

## Aplicação web (pt-BR)

- Botões começam com verbo: "Executar Backup", "Salvar Alterações". Nunca "OK" em ação destrutiva.
- Erro: título = problema concreto; corpo = causa + solução ("Verifique sua rede e tente novamente").
- Toast de sucesso: verbo passado ("Backup concluído").

## Lacuna 13 — Error Messages (PARCIAL)

HIG oficial (`/writing`):
- Exiba o erro **perto do problema**; **não culpe o usuário**; deixe claro **como corrigir**.
- "Escolha uma senha com pelo menos 8 caracteres" > "Senha muito curta".
- Sem interjeições; evite "nós/estamos" ("Não foi possível carregar o conteúdo" > "Estamos com problemas...").

**BackupEmail**: posicionamento adjacente ao campo + falar como corrigir (não o que está errado) nos formulários de settings.

## Exemplos pt-BR

- Campo de senha: erro → `"Use pelo menos 8 caracteres com letras e números"` (positivo, ao lado do campo). Ruim: `"Senha inválida"`.
- Destrutiva: rótulo `"Excluir destino"` com `"Cancelar"`. Ruim: `"OK"`.
- Sucesso: `"Configurações salvas"`. Ruim: `"Salvo com sucesso!!! ✓"`.

## Fontes

HIG Writing, HIG Error Messages (`/writing`), lacuna 13.
