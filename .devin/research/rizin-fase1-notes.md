# Rizin - notas Fase 1 (fontes primarias)

Todas as fontes consultadas em 2026-10-14 via GitHub API / raw / PyPI.

## Repositorio e licenca

- Repo: github.com/rizinorg/rizin, branch `dev`, ~4.0k stars, 30.8k commits. Licenca LGPL-3.0/GPL-3.0 (About page).
- Fork do radare2; "usability, features and cleanliness" (README.md).
- Build: meson >=0.55 (README.md "How to build").

## Arvore raiz (api.github.com/repos/rizinorg/rizin/contents/)

- `binrz/` frontends CLI, `librz/` subsistemas, `subprojects/` deps meson, `test/`, `doc/`, `sys/`, `dist/`.

## Subsistemas librz (contents/librz, 29 dirs)

arch, bin, config, cons, core, crypto, debug, demangler, diff, egg, flag, hash,
il, include, inquiry, io, lang, magic, main, mark, reg, search, sign, socket,
syscall, type, util.

Notas: `arch` unifica asm/analysis; `il` = Rizin IL (herdeiro do ESIL);
`sign` = assinaturas FLIRT; `lang` = plugins de linguagem.

## Frontends binrz (contents/binrz)

rizin, rz-ar, rz-asm, rz-ax, rz-bin, rz-diff, rz-find, rz-gg, rz-hash,
rz-run, rz-sign, rz-test (+ man pages).

Funcoes por README.md:
- rz-bin: info de formatos binarios
- rz-ar: lista/extrai arquivos .a/.lib
- rz-asm: assembler/disassembler CLI
- rz-diff: compara binarios (raw ou analisados)
- rz-hash: hashes e crypto
- rz-gg: gerador de shellcode "eggs" p/ exploitation
- rz-find: busca padroes/bitmasks
- rz-sign: cria/converte/parseia assinaturas FLIRT
- rz-ax: calculadora/conversor numerico
- rz-run: define ambiente/args p/ processo debugado

## Subprojects relevantes (contents/subprojects)

- Disasm engines: capstone v4, v5, v6, next; zydis; libdemangle.
- Debug remoto/Windows: rzgdb (cliente GDB), rzw32dbg_wrap (debug Win32 nativo),
  rzwinkd (kernel debug Windows), rzqnx, ptrace-wrap.
- Outros: sigdb (wrap p/ FLIRT db), rizin-grammar-c, rizin-shell-parser,
  rizin-math-parser, tree-sitter, softfloat, yxml, xxhash, nettle, pcre2,
  compressao (zstd, lz4, liblzma, libzip, mspack).

## Plataformas e arquiteturas (README.md)

- OS: Windows 7+, macOS/iOS, Linux, *BSD, Android, QNX, Solaris, Haiku, Hurd.
- ~50 arquiteturas: x86/x64, ARM/ARM64, RISC-V, PPC, MIPS, SPARC, s390, AVR,
  m68k, Z80, 8051, TMS320, Hexagon, Xtensa, VAX, wasm/Dalvik/Java bytecode etc.
- Formatos: PE/PE+, ELF, Mach-O, COFF, XBE, DEX, MDMP (minidump Windows),
  DMP (pagedump), UEFI/BIOS, dyldcache, WASM, roms GB/NDS/3DS etc.

## Decompilers (repos separados, plugins)

- rz-ghidra (github.com/rizinorg/rz-ghidra, ativo push 2026-10-12): decompiler
  Ghidra + Sleigh disassembler, self-contained C++, comandos `pdg`/`pdgj`
  (JSON). Build cmake ou via rz-pm; nao esta no core.
- jsdec = "rz-dec" (github.com/rizinorg/jsdec, BSD-3, push 2026-07-27):
  pseudo-C ate em asm artesanal, comandos `pdd`/`pddj`/`pdda`. Plugin meson
  separado.
- rz-retdec: plugin RetDec, ativo.

## Debugger e emulacao

- book.rizin.re src/debugger/intro.md: debuggers sao IO plugins; URIs
  `dbg:///prog`, `gdb://host:port`; backends nativos p/ Linux/Windows/macOS/BSD;
  comandos `d?` (breakpoints, ESIL watchpoints `de`, core dump `dg`, injecao
  `dx`, Windows process cmds `dW`).
- Book tem revdebug.md (reverse debugging), heap.md, windows_messages.md.
- analysis/emulation.md (ESIL/RZIL), analysis/signatures.md (FLIRT),
  analysis/graphs.md, types.md, vtables.md, syscalls.md.

## Scripting / headless (github.com/rizinorg/rz-pipe README, PyPI rzpipe)

- API = wrapper sobre `rz_core_cmd_str()`: envia comando string, recebe texto;
  recomendado `cmdj` (saida JSON, quase todo comando rizin tem variante `j`).
- Backends: spawn `rizin -q0` via pipe, RZPIPE_IN/OUT env, TCP, HTTP, RAP.
- Linguagens: Python (rzpipe 0.6.2 no PyPI), Go, Haskell, OCaml, Rust, Ruby,
  Racket.

## Distribuicao Windows (releases/latest = v0.9.1)

- rizin-windows-shared64-v0.9.1.zip (11.7 MB)
- rizin-windows-static-v0.9.1.zip (115 MB)
- rizin_installer-v0.9.1-x86_64.exe (9.4 MB) + x86
- static x86_64 tarball, Android, macOS pkg, src tarball.
- Empacotamento: rizin-win-installer repo; plugins via rz-pm (rizin-pm).

## Plugins extras relevantes p/ lane ofensiva

- rz-libyara: core plugin YARA (criar/parsear/aplicar regras).
- rz-frida: integracao Frida p/ Rizin/Cutter (instrumentacao dinamica).
- rz-asm-llvm: assembler via LLVM (arquivado 2022).
- sigdb: database FLIRT (data repo, parado desde 2023).
- rizin-extras: plugins da comunidade.

## Pendente verificar (Fase 2/3)

- Se jsdec vem pre-instalado nos zips/installers Windows (README nao afirma).
- Cobertura real do rzwinkd (kernel debug) vs uso da lane.
- rz-diff modo grafado (diff de funcoes analisadas) vs diff raw.
