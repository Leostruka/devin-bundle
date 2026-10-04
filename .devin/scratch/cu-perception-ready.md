# Nível de Esforço Obrigatório: MAX
# Perfil Operacional: Staff Engineer - Windows Systems / Computer-Use Perception

# Goal
Otimização, aceleração e aumento de precisão do computer-use em todas as frentes possíveis. Pesquisa profunda e teoricamente coerente do funcionamento geral do stack de percepção/localização, do baixo nível ao alto nível: GPU/compositor (DXGI, WGC, DWM), win32k/user32 (WinEvents), UIA/MSAA (árvore, padrões, eventos), canais semânticos por app (DOM/CDP, ConPTY, QMP), pixels (capture, OCR, template match) e decisão (hints, laya). Objetivo concreto: extrair informação do HUD e localizar elementos mais rápido e com mais precisão, qualquer que seja o meio tecnicamente viável e seguro. Para cada hipótese: evidência primária, veredicto de viabilidade, teste parametrizado com métricas, um commit checkpoint por hipótese.

# Context
Repo: bundle Devin CLI em D:\Programing\ai_workspace\devin-bundle. Branch nova feat/cu-perception; commits = checkpoints por fase/hipótese. Trabalho anterior (feat/cu-realtime, merged via PR #80) mediu: piso do runtime = 1 turno de modelo/ciclo (~9.5s p50); tool floor in-process ~0.25-1.1s; reflexos residentes: DOM ws-eval 16ms, UIA enum+invoke ~54ms, PTY link 0.33s. Docs: .devin/research/cu-realtime-{phase1,phase2,verdict,phase4}.md.

Inventário atual (verificado, não deduzir de novo - confirmar na fase 1):
- Capture: cu_capture.py seam grab(bbox, backend) com registry _BACKENDS={"mss"}; apply_delta() JÁ escrito para DXGI move/dirty rects mas sem backend; mss = GDI BitBlt por chamada (~28ms full / ~7ms region + ~175ms PNG encode).
- UIA: comtypes cru - enum FindAllBuildCache com cache request (~17-31ms focused), padrões Invoke/Value/Scroll/Text via _uia_call, uia_perform re-resolve por hwnd (falha em provider elements hwnd:null); SEM event handlers (AddAutomationEventHandler não usado).
- WinEvents/SetWinEventHook: NÃO usado em lugar nenhum (verificado).
- DXGI Desktop Duplication / Windows.Graphics.Capture / DwmRegisterThumbnail: NÃO usados.
- ETW (Microsoft-Windows-UIAutomationCore, DwmCore, etc): NÃO usado.
- OCR: Windows.Media.Ocr (winrt já vendored) só no path mintty; não é canal geral de localização texto->coords.
- Template matching / OpenCV: ausente (nenhuma dependência de visão clássica).
- Semânticos por app: CDP/BiDi (browser.py + browser_events daemon), ConPTY/TextPattern/CONOUT$ (terminal), QMP guest channel (envs), adb (android).
- Decisão: hints sidecar com session/generation; laya shadow plumbing pronto (assist gated em calibração aprovada; steady ~432ms).
- Reflexos: terminal.py link shipped; consumidor UIA/DOM residente = só protótipo em scratch (p4_probe.py).

Candidatos de hipótese pré-mapeados (a validar/parametrizar, não assumir):
1. Backend DXGI Desktop Duplication no seam cu_capture: frame-acquire sub-ms, dirty/move rects = delta grátis + wait por frame novo (evento de vídeo em vez de poll de pixels).
2. Windows.Graphics.Capture por janela (sem fullscreen), comparação vs mss/DDA.
3. WinEvents daemon (SetWinEventHook, EVENT_OBJECT_*): barramento de eventos do OS - create/destroy/focus/name/location/value change = percepção dirigida por evento em vez de enum polling.
4. UIA event handlers (automation + property-change) dentro do processo.
5. ETW como telemetria de baixo nível (provável: viável para observação, inviável como fonte operacional - decidir com evidência).
6. OCR geral região->texto+coords (Windows.Media.Ocr já vendored; rapidocr/onnx como alternativa) para conteúdo não-semântico (canvas, imagens, texto rasterizado).
7. Template matching leve (numpy, sem OpenCV se possível) para alvos puramente visuais.
8. MSAA/IAccessible legado para apps pré-UIA (fallback de cobertura, não de velocidade).
9. Precisão: DPI awareness (per-monitor v2), transforms lógico<->físico, coordenada de elemento vs hit-test real (ElementFromPoint round-trip).
10. Compositor interno DWM (surfaces, present timing) - documentar o que é API vs indocumentado/bloqueado.
Skills relevantes: computer-use, cu-realtime, system-control, gates, deep-mode. Anti reward-hacking: métrica e limiar definidos ANTES dos testes.

# Acceptance Criteria
1. Mapa teórico completo do stack de percepção/localização Windows, baixo->alto nível: cada camada com mecanismo, custo teórico, e estado de implementação no extension (existe/ausente); fontes primárias citadas
2. Inventário verificado por ferramentas do que o extension já usa por camada (sem dedução)
3. Tabela de hipóteses por camada: evidência técnica, veredicto viável/inviável, métrica prevista; camadas inviáveis documentadas com motivo (não silenciosamente puladas)
4. Cada hipótese viável testada uma a uma, parametrizada, com métricas registradas (latência de percepção, latência de localização, precisão de coordenada, custo de tokens); resultados em doc/ledger rastreável
5. Veredicto final: o que entra no extension (com seam/integração declarada) vs o que fica em scratch vs o que é inviável; thresholds: percepção >=2x mais rápida no mesmo task OU nova capacidade mensurável (ex.: wake por evento OS < poll equivalente); precisão de localização >= baseline; zero violações de segurança
6. Branch feat/cu-perception com um commit por checkpoint; gates verdes (audit 0 erros, validate-skill-format se SKILL.md mudar, pytest escopado quando código de produção mudar)

# Scope & Non-Goals
- **IN SCOPE:** Pesquisa primária profunda: docs Microsoft/MSDN, fontes primárias, probes empíricos no próprio sistema
- **IN SCOPE:** Protótipos em .devin/scratch/; integração no extension só quando hipótese passar no limiar E o design for declarado
- **IN SCOPE:** Medição comparativa contra baselines já congelados (cu_bench, s1/p4 probes)
- **IN SCOPE:** Commits checkpoint na branch feat/cu-perception
- **OUT OF SCOPE:** Modificar o binário devin-cli; modelos pagos
- **OUT OF SCOPE:** Drivers de kernel, hooks de injeção em processos alheios, internals win32k indocumentados, qualquer técnica classificável como game-hack/AV-bypass - essas são fronteira de pesquisa: documentar viabilidade/risco, NÃO implementar sem aprovação explícita
- **OUT OF SCOPE:** Reescrever CLIs existentes sem design aprovado; canais scoped/intenção consentida continuam a regra

# Execution Hints & Checkpoints
1. **Fase 1:** Mapa teórico completo (baixo->alto) + inventário verificado do extension + tabela de hipóteses por camada com evidência e viabilidade + métricas/limiares definidos. Fontes primárias para cada claim de API. Commit checkpoint. PARE e aguarde aprovação.
2. **Fase 2:** Testar hipóteses viáveis uma a uma, parametrizadas, mais impacto primeiro; um commit checkpoint por hipótese; registrar métricas comparando com baseline.
3. **Fase 3:** Veredicto: matriz camada->decisão (integra no extension com seam declarada / fica em scratch / inviável+motivo); se nenhuma atingir limiar, retorno documentado a fase 1 com aprendizados; gates verdes, commit final, reporte com evidências.
