# Plano: devin-N com suporte a múltiplos projetos

> Para agentes de implementação: usar `/grilling` já concluído; próximo passo é `/writing-plans` ou `/planning-pipeline` após aprovação deste conceito.

## Problem Statement

O `devin-N.ps1` atual seleciona **um único workspace** e abre **1 a 4 instâncias dentro desse mesmo projeto**, usando Git worktrees para isolar as instâncias quando são mais de uma. Isso limita o usuário a trabalhar em um único projeto por execução do launcher.

O usuário quer poder trabalhar em **até 4 projetos diferentes** em uma única execução, e usar worktrees **apenas quando 2 ou mais instâncias abrirem no mesmo projeto**.

## Solution

Trocar o fluxo de "selecionar 1 projeto + escolher N instâncias" por um fluxo de "selecionar projetos até atingir 4 instâncias", onde cada projeto pode ter 1 ou mais instâncias.

Fluxo resumido:

1. Apresentar menu para selecionar o primeiro projeto via `Select-FolderTerminal`.
2. Perguntar quantas instâncias para aquele projeto, **capadas pela quantidade restante** (ex: se já selecionou 1, só pode mais 3).
3. Se 1 instância no projeto: usa o diretório do projeto diretamente.
4. Se >1 instância no mesmo projeto: cria worktrees `.worktrees/instancia-{a,b,c,d}` dentro daquele projeto.
5. Cada instância seleciona sua própria branch (pode ser a mesma ou diferente dentro de um projeto).
6. Perguntar se o usuário quer adicionar outro projeto, até 4 instâncias totais.
7. Layout de janelas permanece 1/2/3/4 baseado no número total de instâncias.
8. Ao encerrar, limpa worktrees e branches criadas por projeto.

## User Stories

1. Como usuário, quero abrir até 4 projetos diferentes lado a lado, para trabalhar entre bases de código distintas sem trocar de janela.
2. Como usuário, quero abrir 2 instâncias no mesmo projeto com branches diferentes, para trabalhar em paralelo sem conflitos.
3. Como usuário, quero que worktrees sejam criados apenas quando 2+ instâncias usam o mesmo projeto, evitando overhead desnecessário.

## Implementation Decisions

### Estrutura de dados

Substituir o controle único de workspace por uma coleção `$projetos`:

```powershell
$projetos = @(
    [PSCustomObject]@{
        Path = 'C:\caminho\projeto-a'
        Count = 2
        Worktrees = @('...\instancia-a', '...\instancia-b')
        Branches = @('branch-a', 'branch-b')
    }
)
```

E manter `$instancias` como lista plana de instâncias com: Label, ProjectPath, WorktreePath (ou `$null` se direto), Branch.

### Worktrees por projeto

- Para cada projeto com `Count > 1`:
  - Criar `.worktrees/instancia-{letra}` dentro do próprio projeto.
  - As letras devem ser globalmente únicas A-D, não por projeto, para simplificar o mapeamento de layout.
- Para projeto com `Count == 1`:
  - `WorktreePath = $null`; usa `ProjectPath` diretamente.

### Seleção de branches

- A função `Select-BranchTerminal` é chamada uma vez por **instância**, não por projeto.
- Se o projeto tem 2 instâncias, ambas podem escolher branches distintas.
- **Restrição:** duas instâncias do mesmo projeto não podem usar a mesma branch. O seletor deve filtrar branches já escolhidas para o mesmo projeto.
- Se uma instância for criar uma nova branch (`devin-new`) em um projeto que já tem outras branches, o usuário deve escolher qual branch servirá de base para a nova.

### Layout de janelas

- Reutilizar a grade existente (`$grid`) com 1/2/3/4 posições.
- As instâncias são preenchidas em ordem A, B, C, D.
- Não agrupar por projeto; o layout é por instância.

### Cleanup

- Percorrer cada projeto e remover worktrees criados por ele.
- Restaurar branches originais em projetos com modo de 1 instância que trocaram de branch.
- Chamar `git worktree prune` por projeto.

### Integração com UX seletores

- Não alterar `devin-session-launcher.ps1` nem `Show-TerminalList`, a menos que seja necessário para a nova etapa de seleção de quantidade por projeto.
- O novo fluxo de seleção de projeto e quantidade deve usar `Show-TerminalList`.

## Testing Decisions

1. Teste manual com 1 projeto + 1 instância (modo direto).
2. Teste manual com 1 projeto + 2 instâncias (worktree no mesmo projeto).
3. Teste manual com 2 projetos + 1 instância cada (sem worktree).
4. Teste manual com 4 projetos + 1 instância cada.
5. Teste manual com 2 projetos: 1 com 1 instância, 1 com 3 instâncias.
6. Verificar cleanup de worktrees e branches ao encerrar.
7. Rodar `python audit.py` e `python -m pytest` antes do push.

## Out of Scope

- Lista de projetos recentes/favoritos (ideia interessante, mas requer design separado para não quebrar o fluxo atual).
- Persistência de configuração entre execuções.
- Mudanças em `Show-TerminalList` fora do necessário para este fluxo.
- Alteração do layout de janelas (mantém 1/2/3/4).
