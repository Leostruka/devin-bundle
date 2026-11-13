---
name: ghidra
description: Use when analyzing raw firmware images (ARM/Thumb embedded), dumped flash, or binaries without symbols - importing at a custom base address, seeding function discovery, and dumping decompiled output + xrefs for offline study via Ghidra headless.
triggers: [user, model]
allowed-tools: [read, exec, write, edit]
---

# Ghidra headless firmware RE

Validated on Ghidra 12.1.4 + OpenJDK 25, Windows. Target: nRF52810 Cortex-M4 Thumb app slice (Minew ESL tag), but applies to any raw bin.

## When

- Raw firmware `.bin` (no ELF headers, no symbols) needs decompilation.
- Need repeatable dumps of decompiled functions + xrefs to answer "who calls X", "what reads offset Y in ctx".
- Capstone-level disasm is not enough (literal-pool indirection, computed refs, argument tracking).

## Install / locate

- Ghidra has no winget package. Download the release zip from GitHub `NationalSecurityAgency/ghidra`, extract somewhere stable, e.g. `tools/ghidra`.
- Needs JDK 17+ on PATH.
- Headless binary: `<ghidra>/support/analyzeHeadless.bat` (Windows) / `analyzeHeadless` (Linux).

## Hard-won facts (do not relearn)

1. **Ghidra 12 has no Jython.** `.py` post-scripts fail with "Ghidra was not started with PyGhidra". Write analysis scripts in **Java** (`GhidraScript` subclass) - they run directly.
2. **Raw import needs manual context.** A bare app-slice `.bin` has no vector table, so auto-analysis finds ~zero functions. You must:
   - Import with explicit base address (e.g. app at `0x19000` after bootloader).
   - Set Thumb mode: `setRegisterValue` / context register `TMode=1` on the whole image range before disassembly.
   - Seed known function addresses, or auto-analysis stays blind.
3. **Linear sweep `disassemble()` per halfword is too slow** (flow analysis per call). Instead: generate a seed list from **Capstone BL/B.W targets** (one pass in Python over the bin) plus known entry points, then let Ghidra's `disassemble` expand by control flow. ~213 seeds -> full coverage in seconds.
4. **RAM matters.** Create the RAM memory block (e.g. `0x20000000`-`0x2003ffff`) or the decompiler cannot resolve `ldr` into ctx structures. Catch `MemoryConflictException` - the block may already exist.
5. **Match the binary to the dump.** Decompiled addresses are meaningless across firmware versions. Record which `.bin` produced which `gh_dump.txt`; re-scan constants (e.g. `movw #0xca01`) in the SAME file.
6. **Ghidra misreads `ldr/str` literal-pool pairs as arrays.** `DAT_0001f334` looked like a 10-u32 table but was `{fn_ptr, param}` pairs - verify suspicious "tables" by dumping raw bytes and checking for Thumb function pointers (odd addresses into code).
7. `analyzeHeadless <projdir> <projname> -import <bin> -processor <lang> -cspec <c> -postScript <script> [args] -scriptPath <dir>` - processor for Cortex-M4 Thumb LE: `ARM:LE:32:v7` (v8 for M33+).

## Workflow that worked

```bat
support\analyzeHeadless.bat ghproj esl -import fw.bin ^
  -processor ARM:LE:32:v7 -postScript GhDump.java -scriptPath . -deleteProject
```

Script skeleton (Java):
- `setRegisterValue` TMode=1 over `[imgStart, imgStart+len)`.
- Add RAM block via `getMemory().createInitializedBlock("ram", toAddr(0x20000000), size, (byte)0, monitor, false)` (or `createUninitializedBlock`).
- Read seed addresses from `seeds.txt` (capstone-generated BL targets), `disassemble(addr)` each.
- For each target function: `getFunctionAt`, `DecompInterface.openProgram`, `decompileFunction(fn, 60, monitor)`, print `getDecompiledFunction().getC()`.
- Print xrefs: `getReferencesTo(addr)` / `getReferencesFrom`.
- Print `cmp`/`movw` sites matching interesting immediates.

Capstone seed generator (python):

```python
from capstone import *
data = open('fw.bin','rb').read(); base = 0x19000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
seeds = set()
for off in range(0, len(data)-4, 2):
    for i in md.disasm(data[off:off+4], base+off, 2):
        if i.mnemonic in ('bl','blx','b','b.w') and i.op_str.startswith('#0x'):
            t = int(i.op_str[1:],16)
            if base <= t < base+len(data): seeds.add(t)
open('seeds.txt','w').write('\n'.join(hex(s) for s in sorted(seeds)))
```

## Analysis recipes that paid off

- **Find a message consumer**: producers `FUN_x(msg_id, sub, buf, len)` are easy; consumers live in other tasks. Grep disasm for `cmp rX, #<msgid>` clusters - the real dispatcher compares several IDs in one function. Do not trust the first `movs r0,#id` (that is a producer).
- **Follow ctx offsets, not names**: pick a struct offset (e.g. `ctx+0x118`), grep all disasm touching it - that is how you find readers/writers when there are no xrefs (literal pools).
- **Odd-value table entries**: `0x196f5` in a "param table" = Thumb func ptr (low bit). Dump code there; tiny `movs r0,#N; bx lr` getters reveal the slot is a callback column, not data.
- **Distinguish "committed" vs "rendered" on hardware**: protocol ack != visual effect. Correlate each hypothesis test with a physical observation (flash, LED, pixels) before recording conclusions.

## Outputs to keep

- `gh_dump.txt`: decompiled functions + xrefs + cmp-site index, checked next to the `.bin` it came from.
- `seeds.txt`: reproducible function seed list.
- Project notes doc: dispatcher table, msg-type map, ctx offsets, hardware-confirmed behaviors vs hypotheses. Date each section; mark superseded interpretations instead of deleting them.

## Cascade

- `binary-triage`: cheap static triage first; Ghidra is the escalation.
- `re-binary`: managed RE via rea-ops when its engine covers the artifact.
- `firmware-probe`: extraction (binwalk/EMBA) before RE.
