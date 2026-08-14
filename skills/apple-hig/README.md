# Família de Skills Apple HIG

Catálogo da família `apple-hig` — auditoria e implementação de UI desktop **WPF + WebView2** (dashboard/settings do BackupEmail) seguindo Apple Human Interface Guidelines adaptadas para Windows (1pt ≈ 1px em DPI 96).

## Skills

| Skill | Papel | Triggers | Fatia do checklist |
|---|---|---|---|
| `apple-hig` | **Orquestrador** — pipeline completo de design review 52/52 | "design review", "auditoria de UI", "refazer o dashboard", "refazer as settings", "relatório HIG", "está nos padrões da Apple?", "52 itens" | 51–52 (transversais) + consolidação |
| `hig-foundations` | Tipografia, Cor, Spacing/Layout, Shapes, Ícones, Motion | "tipografia", "cor", "grade 8px", "radius", "motion", "espaçamento", "ícone", "tokens", "grid" | 1–25 |
| `hig-writing` | UX Copy, rótulos de botões, mensagens de erro | "copy", "texto de botão", "rótulo", "mensagem de erro", "capitalização", "UX writing" | 49–50 (+ copy de 34, 47) |
| `hig-alerts` | Alertas, sheets, popovers, tooltips, destrutivas | "alerta", "modal", "confirmação", "destrutivo", "sheet", "tooltip", "diálogo" | 33–38 |
| `hig-feedback` | Feedback, Progresso, Notificações, Empty States | "feedback", "progresso", "loading", "spinner", "toast", "notificação", "pause", "empty state" | 26–32, 47 |
| `hig-settings-navigation` | Settings, Navegação, Botões, Menus/Teclado, Toolbars | "settings", "atalho", "navegação", "botões", "menu", "teclado", "toolbar", "tabela", "undo" | 44–48 |
| `hig-accessibility` | Acessibilidade, Plataforma desktop, Focus, Privacy, Onboarding, Help | "acessibilidade", "contraste", "focus", "foco", "screen reader", "privacy", "onboarding", "help" | 39–43 |

## Relação entre skills

- **Ordem fixa do pipeline** (orquestrador): foundations → writing → alerts → feedback → settings-navigation → accessibility.
- **Itens co-ocupados**: `34` (copy → hig-writing; dono hig-alerts) · `47` (empty states → hig-feedback; referenciado por hig-settings-navigation) · `51–52` (dono: apple-hig). Cada número conta **uma única vez** no total 52.
- Cada skill audita **apenas a própria fatia**; não re-auditar o que outra skill já auditou.

## Uso

- **Review completo**: rode `apple-hig` (carrega `references/app-context.md`, roda as 6 skills, executa `scripts/audit-design.mjs`, consolida relatório 52/52 com score por categoria).
- **Problema pontual**: use a skill do domínio diretamente ("tipografia", "alerta", "settings", "acessibilidade", ...) sem rodar o pipeline inteiro.

## Estrutura

```
apple-hig/
├── SKILL.md                  # orquestrador
├── README.md                 # este catálogo
├── references/
│   ├── app-context.md        # seção 20 (mapeamento BackupEmail) + lacunas do app
│   └── checklist-master.md   # índice canônico dos 52 itens com donos
└── scripts/
    └── audit-design.mjs      # verificador determinístico (Node puro)
hig-foundations/ hig-writing/ hig-alerts/ hig-feedback/
hig-settings-navigation/ hig-accessibility/   # 1 SKILL.md + references cada
```

## Fontes de verdade

- `D:\Envio\Project\BackupEmail\docs\HIG-REFERENCIA.md` (20 seções + checklist 52 itens).
- `D:\Envio\Project\BackupEmail\docs\HIG-LACUNAS.md` (18 lacunas priorizadas).
- HIG oficial: developer.apple.com/design/human-interface-guidelines.
