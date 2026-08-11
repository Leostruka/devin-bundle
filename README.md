# devin-bundle

Export + instalador do Devin — análogo ao `opencode export`/install, mas voltado para o Devin CLI.
Empacota **só as skills que o Devin usa de fato** + as **regras consolidadas** que você definiu,
e restaura tudo no destino correto via um único comando.

## O que tem dentro

```
devin-bundle/
├── AGENTS.md          # regras consolidadas (4 seções, Devin-focused)
├── manifest.json      # lista das skills + origem + propósito
├── install.ps1        # instalador Windows (PowerShell)
├── install.sh         # instalador Linux/WSL/macOS (bash)
├── README.md          # este arquivo
└── skills/            # 14 skills copiadas in-loco
    ├── brainstorming/
    ├── context7/
    ├── find-skills/
    ├── gh/
    ├── git-helper/
    ├── graphify/
    ├── memory-bridge/
    ├── requesting-code-review/
    ├── self-extend/
    ├── systematic-debugging/
    ├── test-driven-development/
    ├── tool-and-skill-discovery/
    ├── using-superpowers/
    └── writing-plans/
```

## Regras consolidadas (AGENTS.md)

1. **No AI signatures** — nunca citar/assinar Devin em commits, PRs, releases, docs, código.
2. **Skill self-maintenance** — skills são vivas: atualizar, criar, podar. É assim que o Devin vira especialista em qualquer coisa.
3. **Skill/tool discovery** — descobrir e invocar skills no início de tarefas não-triviais.
4. **graphify trigger** — `/graphify` ativa o skill graphify antes de tudo.

## Instalar

### Windows (PowerShell)
```powershell
cd devin-bundle
.\install.ps1              # instala (pula se já igual)
.\install.ps1 -DryRun      # só mostra o que faria
.\install.ps1 -Force       # sobrescreve diferenças sem perguntar
```
Destino: `%APPDATA%\devin\` → `skills\`, `AGENTS.md`

### Linux / WSL / macOS (bash)
```bash
cd devin-bundle
chmod +x install.sh
./install.sh               # instala
./install.sh --dry-run     # só mostra
./install.sh --force       # sobrescreve
```
Destino: `${XDG_CONFIG_HOME:-~/.config}/devin/` → `skills/`, `AGENTS.md`

## O que o instalador faz

1. Cria o diretório `devin/` no local correto da plataforma (se faltar).
2. Copia `AGENTS.md` consolidado sobre o existente (com `-Force` se diferente).
3. Copia cada skill em `skills/<nome>/` para o destino.
   - Se a skill já existe e é idêntica (hash) → pula.
   - Se existe e difere → só sobrescreve com `-Force`/`--force`.
   - Se não existe → instala.
4. Imprime resumo: quantas instaladas, atualizadas, inalteradas.

## Versionar / sincronizar máquinas

Este repo é um repo Git normal:
```powershell
cd devin-bundle
git init
git add -A
git commit -m "initial devin bundle"
git remote add origin <seu-repo>
git push -u origin main
```

Na outra máquina:
```bash
git clone <seu-repo> devin-bundle
cd devin-bundle
./install.sh --force   # ou install.ps1 -Force no Windows
```

## Atualizar o bundle

Para regenerar a partir da máquina fonte depois de mudar skills/regras:
1. Edite os skills em `skills/` diretamente, ou substitua as pastas.
2. Edite `AGENTS.md` se as regras mudarem.
3. Atualize `manifest.json` se adicionou/removeu skills.
4. `git add -A && git commit -m "update bundle" && git push`

O instalador é idempotente — rodar de novo só atualiza o que mudou (com `-Force`).
