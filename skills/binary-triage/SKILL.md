---
name: binary-triage
description: Use when extracting evidence from closed binaries (DLL/SO/EXE/AAR) without heavy RE tooling - engine version, symbols, getter constants, exports, diff between builds, ctypes runtime probing. Answers in minutes what would take hours in Ghidra; escalate to re-binary/Ghidra only when static triage cannot close the question.
triggers: [user, model]
allowed-tools: [read, grep, find_file_by_name, exec]
---

# Binary Triage

Extract answers from a closed DLL/.so/.aar in minutes with light tools (strings, nm, objdump, python) before paying the cost of Ghidra/IDA. Born from a real case: proving an Android engine was generation 5.3.x incompatible with a 4.8.4.0 server via the internal FIR version.

## When to use

- Compare builds/engines of the same lib across platforms or versions ("which DLL is this Android .so equivalent to?").
- Extract an undocumented internal constant (format version, magic, fixed size) without source.
- Confirm whether a function/symbol exists in a binary that stripped exports.
- Evaluate a binary-incompatibility hypothesis (template, protocol, serialized struct) before heavy disassembly.

## Tools (cost order)

1. `strings`, `nm -D`, `objdump -T` (mingw/scoop ships all three under `~/scoop/apps/mingw/current/bin/`).
2. Python stdlib to parse ELF/PE and read bytes at offsets (snippets below, tested).
3. `sigcheck` (scoop) or PowerShell `Get-Item ... .VersionInfo` for Windows DLL/EXE FileVersion.
4. ctypes runtime probing: `Init` + `GetVersion` sometimes answer in 20 lines what takes hours statically.
5. Heavy RE only when the above does not close it: `re-binary` skill (`rea-ops` wrapper -> Hopper/Ghidra engines) or `ghidra` skill for raw firmware.
6. .NET managed: dnSpy/ILSpy/dotPeek (the assembly is not native; a native disassembler does not help).

## Steps

1. **Metadata first**: FileVersion/ProductVersion of the binary and all "siblings" (other versions, other platforms, inner .aar). In .aar, unzip: `unzip -o lib.aar -d out` and inspect `jni/<abi>/*.so`. The inner .aar/lib name sometimes leaks the real engine version (real case: wrapper "v2.0.0.8" contained `sdk-release-5.3.0.7.aar`).
2. **Symbol map**: `nm -D` (ELF) or export table (PE, snippet below). Cross-check sets between builds: identical internal symbol set = same codebase/generation. PE strips internal symbols; NDK ELFs often do not. So "symbol absent in the DLL" proves nothing; "symbol present" proves presence.
3. **Constants via 1-instruction getters**: functions like `GetXxxVersion` are usually `mov reg, imm; ret`. Find the symbol in the .so and disassemble:
   `objdump -d --start-address=<va> --stop-address=<va+16> lib.so`
   - AArch64: `MOVZ w0,#imm` = `(instr >> 5) & 0xFFFF` (e.g. `52812000` -> `0x900`).
   - x86-64: `b8 <imm32> c3` = `mov eax, imm; ret`. Scanning the whole PE for `b8(....)\xc3` finds these getters without symbols (snippet below).
4. **vaddr -> file offset**: ELF uses program headers, PE uses the section table. Ready snippets below; do not compute by hand.
5. **Runtime probe when possible**: load the DLL with ctypes, call `Init`/version function. Failed (VALIDITY_FAIL, AV, license)? Note it and go back to static; do not insist.
6. **Conclude with a delta, not a vibe**: report what differs between the binaries (internal version, symbol on only one side, struct size) and the application-level confirmation test (e.g. log the `Version` field of the API-returned header).

## Ready snippets

ELF vaddr->offset + instruction read (python stdlib):

```python
import struct
data = open('lib.so','rb').read()
e_phoff = struct.unpack('<Q', data[0x20:0x28])[0]
e_phentsize, e_phnum = struct.unpack('<HH', data[0x36:0x3a])
segs = []
for i in range(e_phnum):
    t,f,off,va,pa,fs,ms,al = struct.unpack('<IIQQQQQQ', data[e_phoff+i*e_phentsize:e_phoff+i*e_phentsize+56])
    if t == 1: segs.append((va,off,fs))
def v2o(va):
    for v,o,s in segs:
        if v <= va < v+s: return o+(va-v)
# symbol addr from: nm -D lib.so | grep Name
# instr = struct.unpack('<I', data[v2o(addr):v2o(addr)+4])[0]
```

PE export table walker (file offset of an exported function):

```python
import struct
data = open('lib.dll','rb').read()
pe = struct.unpack('<I', data[0x3c:0x40])[0]
opt = pe+24
magic = struct.unpack('<H', data[opt:opt+2])[0]
ddir = opt + (112 if magic == 0x20b else 96)
exp_rva = struct.unpack('<I', data[ddir:ddir+4])[0]
nsec = struct.unpack('<H', data[pe+6:pe+8])[0]
sec_off = opt + struct.unpack('<H', data[pe+20:pe+22])[0]
secs = [struct.unpack('<IIII', data[sec_off+i*40+8:sec_off+i*40+24]) for i in range(nsec)]
def r2o(rva):
    for vs,va,rs,rp in secs:
        if va <= rva < va+vs: return rp+(rva-va)
eo = r2o(exp_rva)
nf, nn = struct.unpack('<II', data[eo+20:eo+28])
af, an, aon = struct.unpack('<III', data[eo+28:eo+40])
for i in range(nn):
    no = r2o(struct.unpack('<I', data[r2o(an)+i*4:r2o(an)+i*4+4])[0])
    name = data[no:data.find(b'\x00', no)].decode()
    ordi = struct.unpack('<H', data[r2o(aon)+i*2:r2o(aon)+i*2+2])[0]
    frva = struct.unpack('<I', data[r2o(af)+ordi*4:r2o(af)+ordi*4+4])[0]
    print(name, 'fileoff', hex(r2o(frva)))
```

Scanner for `mov eax,imm;ret` getters across a whole PE:

```python
import re
data = open('lib.dll','rb').read()
for m in re.finditer(rb'\xb8(....)\xc3', data):
    v = int.from_bytes(m.group(1), 'little')
    print(hex(m.start()), hex(v))
# adjacent pairs of small getters (e.g. 0x100 and 0x10 side by side)
# are typically GetVersion/GetMinVersion of the same family
```

ctypes probing (Windows):

```python
import ctypes, os
os.add_dll_directory(r'C:\dir\with\deps')
d = ctypes.CDLL(r'C:\path\lib.dll')   # cdecl; WinDLL if stdcall
h = ctypes.c_ulong(0)
print(d.SomeApi_Init(ctypes.byref(h)))  # adapt to the SDK in question
```

## Anti-patterns

- Do not open Ghidra before steps 1-4: 80% of "version/format" questions die on strings + exports + getters.
- Do not conclude "function does not exist" from a missing string in PE (internal symbol stripped); look for code patterns or test at runtime.
- Do not trust the package/wrapper version; the version that matters is the inner engine's (.so/.dll).
- Do not report "probably incompatible" without a concrete delta and an API-level confirmation test.
- Do not scan the whole disk hunting RE tools; use what is on PATH, look for Ghidra once, proceed without it if absent.

## Cascade

- `debugging`: binary triage is an investigation step, not the end.
- `re-binary`: heavy RE via rea-ops (Hopper/Ghidra engines) under engagement contract.
- `ghidra`: raw firmware headless decompilation recipe.
- `security`: same tooling audits third-party binaries (supply chain).
