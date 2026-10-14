# Rizin vs lane ofensiva do bundle: gap analysis bidirecional

Data: 2026-10-14. Spec: `.devin/scratch/optimized_ready.md`.
Notas Fase 1: `.devin/research/rizin-fase1-notes.md`.

## 1. Arquitetura rizin (fontes primarias)

- Repo `rizinorg/rizin`, branch dev, LGPL-3.0/GPL-3.0, fork radare2.
  Fonte: github.com/rizinorg/rizin (About + README.md).
- 29 subsystems em `librz/`: arch, bin, config, cons, core, crypto, debug,
  demangler, diff, egg, flag, hash, il, io, lang, magic, reg, search, sign,
  socket, syscall, type, util etc.
  Fonte: api.github.com/repos/rizinorg/rizin/contents/librz.
- 12 frontends em `binrz/`: rizin, rz-ar, rz-asm, rz-ax, rz-bin, rz-diff,
  rz-find, rz-gg, rz-hash, rz-run, rz-sign, rz-test.
  Fonte: api.github.com/repos/rizinorg/rizin/contents/binrz.
- Disasm: capstone v4/v5/v6/next + zydis via subprojects; ~50 arquiteturas
  listadas no README (x86/x64, ARM/64, RISC-V, PPC, MIPS, Hexagon, TMS320,
  Dalvik/Java/WASM bytecode...).
  Fonte: README.md + contents/subprojects.
- Formatos: PE/PE+, ELF, Mach-O, MDMP (minidump), DMP (pagedump), XBE, DEX,
  UEFI, dyldcache. Fonte: README.md "Supported File Formats".
- Decompilers: rz-ghidra (`pdg`/`pdgj`, C++ self-contained, plugin separado);
  jsdec (`pdd`/`pddj`, repo separado, BSD-3); rz-retdec. Nenhum no core.
  Fontes: github.com/rizinorg/rz-ghidra/blob/master/README.md;
  github.com/rizinorg/jsdec/blob/dev/README.md;
  github.com/rizinorg/rz-retdec.
- Debugger: IO plugins, `dbg://`, `gdb://` (rzgdb subproject), backend Win32
  nativo (rzw32dbg_wrap), kernel Windows (rzwinkd), reverse debugging
  (book src/debugger/revdebug.md), ESIL watchpoints (`de`).
  Fonte: github.com/rizinorg/book/blob/master/src/debugger/intro.md +
  api.github.com/repos/rizinorg/rizin/contents/subprojects.
- ESIL/IL: `librz/il`; book src/analysis/emulation.md.
- Scripting: rzpipe (pypi.org/project/rzpipe 0.6.2); spawn `rizin -q0`,
  `cmdj` JSON; backends env-pipe/spawn/TCP/HTTP/RAP; langs Python/Go/Rust/
  Ruby/Haskell/OCaml/Racket.
  Fonte: github.com/rizinorg/rz-pipe README + pypi.org/pypi/rzpipe/json.
- Windows dist: release v0.9.1 com rizin-windows-shared64 zip (11.7 MB),
  static zip (115 MB), installers x86/x86_64.
  Fonte: api.github.com/repos/rizinorg/rizin/releases/latest.
- Extras: rz-libyara (core plugin YARA), rz-frida, sigdb (FLIRT db),
  rz-pm (package manager). Fonte: api.github.com/orgs/rizinorg/repos.

## 2. Lane red do bundle (paths verificados)

- `skills/red-team/SKILL.md`: roteador; contrato target/window/ROE
  obrigatorio; routing table 6 dominios.
- `skills/re-binary/SKILL.md`: RE via rea-ops; fallback documentado para
  offsec-tools (capa/floss/yara/rizin/ghidra) quando engines ausentes.
- `extensions/rea-ops/wrapper.py` (201 linhas): passthrough para
  `npx rea-agents@latest`; whitelist 7 subcomandos read-only:
  analyze, inspect, search, function, xrefs, trace, compare; contrato
  obrigatorio; engines sondados por `rea doctor`.
- `extensions/offsec-tools/wrapper.py` (446 linhas): catalogo 28 tools;
  dominios net/web/wireless/firmware/mobile/re; backends native/wsl/docker;
  mode gates passive/active(+--confirm)/destructive.
  RE domain (linhas 140-155): capa, floss, yara, rizin, ghidra.
- `agents/red-team-lead.md`: perfil swe-2-max, exec, mesma disciplina de
  contrato/evidencia.
- `skills/web-probe|net-probe|wireless-probe|firmware-probe|mobile-probe`:
  escopo por dominio (OWASP web, SMB/TLS net, Wi-Fi/SDR, firmware images,
  MASVS mobile).
- Contexto: `.devin/research/rea-analysis.md` linhas 54-55 documentam
  bridges Hopper (macOS/Linux) e Ghidra (Linux/macOS full; Windows x64
  limitado); linhas 151-153: neste host, hopper/ghidra reportaram
  `missing_analysis_engine`.
- rizin ja consta no catalogo offsec-tools (wrapper.py linhas 149-151):
  bins [rizin, rz-bin], passive, native+wsl, passthrough de args crus.

## 3. Matriz capability x {rizin, bundle/red}

| Eixo | rizin | bundle/red hoje |
|---|---|---|
| Disasm/analise estatica multi-arq | ~50 archs, capstone+zydis, `pdj` JSON, rz-asm standalone | rea analyze/function depende de Hopper/Ghidra (ausentes neste host, rea-analysis.md:151); rizin passthrough cru no catalogo; ghidra headless precisa JDK |
| Decompilacao | rz-ghidra `pdgj`, jsdec `pddj`, rz-retdec (plugins separados) | rea via Ghidra engine (se instalada); jadx so p/ APK; nenhum decompiler garantido local |
| Analise dinamica/debugger | dbg://, Win32 nativo, winkd kernel, gdb client, revdebug, ESIL watchpoints | inexistente p/ binarios desktop; frida so no dominio mobile (emulador rooted) |
| Binary diffing | rz-diff raw + analisado, librz/diff | rea `compare` (engine-dependente) |
| Carving/forensics | rz-find padroes/bitmasks, magic, MDMP/DMP parsers | binwalk/unblob/emba (firmware), floss (strings); sem parser de dumps Windows |
| Signature analysis | rz-sign FLIRT create/parse/apply + sigdb | yara (pattern match), capa (capability); sem FLIRT/compiler-ID |
| Scripting/automacao | rzpipe Python cmdj, sessao persistente, projeto | wrappers one-shot por subprocesso; sem sessao stateful |
| Headless p/ agente | JSON-first (`j` em todo comando), rizin -qc, RAP/HTTP | envelopes JSON dos wrappers; rizin ja invocavel mas sem estrutura |

## 4. Gaps priorizados (impacto x esforco)

| # | Gap | Impacto | Esforco | Recomendacao |
|---|---|---|---|---|
| 1 | Estatica multi-arq garantida sem engines comerciais (Hopper ausente, Ghidra limitada no Windows) | Alto | Baixo: rizin ja esta no catalogo | ADOTAR: wrapper estruturado `extensions/rz-ops/wrapper.py` (padrao rea-ops) com presets JSON (`iIj`, `aflj`, `pdfj`, `izj`, `axtj`), mesmo contrato target/window/roe |
| 2 | Debugger Windows local (dbg:// via rzw32dbg_wrap) | Alto | Medio: semantica de mode gate (executar alvo = active) + ROE deve declarar execucao | ADOTAR como modo active no wrapper; documentar dbg:// no re-binary |
| 3 | Decompiler sem Ghidra instalada | Medio-Alto | Medio: jsdec/rz-ghidra exigem meson/cmake build ou rz-pm | ADAPTAR: sondar presenca via doctor; fallback jsdec via rz-pm quando disponivel |
| 4 | Binary diffing sem engine | Medio | Baixo: `rz-diff -j` direto | ADOTAR como fallback de `compare` quando rea reportar engine ausente |
| 5 | FLIRT/compiler-ID (rz-sign+sigdb) | Medio | Baixo-Medio | ADAPTAR: probe opcional no doctor; util p/ triagem (pular codigo de biblioteca) |
| 6 | Parser MDMP/DMP + rz-find carving | Medio-Baixo | Baixo | ADOTAR como presets do wrapper; cobre forensica de dumps que binwalk nao cobre |
| 7 | Sessao stateful (rzpipe) p/ analise multi-step | Medio | Medio: novo padrao de integracao | ADAPTAR: fase 2 do wrapper (spawn `rizin -q0` persistente) ou manter one-shot com `-qc` |
| 8 | ESIL emulacao/deobfuscacao | Medio | Baixo-Medio | ADAPTAR: presets `ae`/`aes` no wrapper |
| 9 | rz-gg eggs, rz-hash, rz-ax | Baixo | Baixo | IGNORAR: nicho exploitation; fora do escopo defensivo-padrao |
| 10 | rz-libyara, rz-frida | Baixo | - | IGNORAR: yara e frida ja cobertos no catalogo com melhor isolamento |

## 5. Veredito

Para RE local no Windows, rizin agrega tres coisas que a lane nao tem hoje:

1. Estatica multi-arq self-contained que nao depende de engine comercial
   (11.7 MB zip nativo; Hopper/Ghidra reportaram `missing_analysis_engine`
   neste host, .devin/research/rea-analysis.md:151).
2. Debugger Windows nativo + ESIL: unica via de analise dinamica de binarios
   desktop no bundle (hoje so existe frida/mobile).
3. Diffs e FLIRT sem engine: `rz-diff` e `rz-sign` substituem `rea compare`
   e adicionam compiler-ID ausente.

O que nao muda: rizin ja esta no catalogo offsec-tools (passthrough cru,
wrapper.py:149-151); web/net/wireless/firmware/mobile nao sao afetados;
rea-ops continua sendo o caminho profundo quando Hopper/Ghidra existirem.

Forma de integracao recomendada: novo `extensions/rz-ops/wrapper.py`
espelhando rea-ops (whitelist de presets JSON, contrato target/window/roe,
mode passive para estatica e active para dbg://), sem instalar nada agora;
`doctor` sonda rizin/rz-bin/jsdec/rz-ghidra/rz-diff no PATH.

## 6. Nao verificado (honest)

- Se os zips/installers Windows ja embutem jsdec (README jsdec nao afirma).
- Maturidade real do rzwinkd (kernel debug) em Windows 11 atual.
- Se `rea compare` funciona sem engine (faz diff nativo ou delega?).
