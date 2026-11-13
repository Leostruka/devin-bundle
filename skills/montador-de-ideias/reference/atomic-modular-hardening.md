# Atomic & Modular Hardening and Optimization Matrix

## Purpose

Ensure every idea assembled by `montador-de-ideias` is engineered for extreme robustness (hardening) and peak efficiency (optimization) at two distinct scales: **Atomic Level** (the smallest unit of execution/data) and **Modular Level** (the composition of subsystems and boundaries).

## 1. Atomic Level (Functions, Data Types, Inputs, Queries, Prompts, Syscalls)

### 1.1 Atomic Hardening Checklist

Every atomic unit in the specification must enforce:
1. **Parse, Don't Validate**: untrusted inputs (CLI args, JSON payloads, web responses, user text, file paths) are parsed into strict, immutable types at the entry boundary; raw strings/dicts never propagate inward.
2. **Minimize Contact Surface (`sec-needs`)**: every line of code and every input field is attack surface. Strip unused fields, sanitize paths against traversal (`..`, symlink escapes), and bound string/payload lengths.
3. **Safe File & Output Semantics**:
   - User-named output paths (`--out`, `-o`, `dst`) refuse to overwrite existing files unless `--force` is explicitly passed (`O_EXCL` / pre-flight check, exit code 2).
   - Atomic writes via temp-file + rename when state corruption on crash is possible.
   - Explicit `encoding="utf-8"` on all text I/O and `errors="replace"` on subprocess streams.
4. **Timeouts & Resource Bounds**: zero unbounded network calls, regexes, loops, or subprocesses; every external operation declares an explicit timeout and max-bytes ceiling.
5. **Secret & Side-Channel Hygiene**:
   - Never log, print, or serialize secrets, tokens, or raw credentials in error traces.
   - Constant-time comparison (`hmac.compare_digest`) for tokens/hashes/signatures to prevent timing side-channels.
6. **Deterministic Error Taxonomy**: every failure returns a typed error envelope (`{"ok": false, "error": ..., "code": ...}`) and exits non-zero; zero silent `except: pass`.

### 1.2 Atomic Optimization Checklist

Every hot-path atomic unit must specify:
1. **Algorithmic Complexity Floor**: state time and space complexity ($O(1)$, $O(\log n)$, $O(n)$); ban accidental $O(n^2)$ scans, repeated regex compilations, or redundant AST/JSON parses.
2. **Zero-Waste Memory & I/O**: stream or chunk large inputs instead of loading whole files into memory; reuse buffers/connections; avoid intermediate copies.
3. **Stdlib-First & Native Acceleration (ADR-003)**:
   - Prefer zero-dependency stdlib primitives over heavy third-party packages.
   - When an atomic operation is CPU-bound, latency-critical (<10ms), or memory-intensive, specify a Rust `PyO3` (`abi3`) extension crate with a clean Python fallback.
4. **Token & Prompt Density (for AI-native units)**: compress schemas, support `--detail brief|compact|full` output tiers, and eliminate redundant prose in agent-consumed outputs.

---

## 2. Modular Level (Subsystems, Seams, APIs, Storage, Multi-Agent Flows)

### 2.1 Modular Hardening Checklist

Every module and inter-module boundary must enforce:
1. **Deep Modules & Narrow Seams**: modules expose a minimal, stable contract and encapsulate all internal state, retry logic, and platform quirks.
2. **Least Privilege & Network Isolation**: each service, worker, or subagent receives only the exact permissions, tools, and file scopes required for its contract (private VPC/localhost by default; public endpoints require explicit justification and auth).
3. **Fail-Closed Gates & Circuit Breakers**:
   - When a validator, guard, or upstream dependency fails or abstains, default to `BLOCKED` / deny - never silently promote unverified state.
   - Bound retry loops (e.g., max 2 rework cycles before escalating to the human operator).
4. **Provenance & Contract Envelopes (Envelope v2)**:
   - Inter-module and CLI JSON outputs carry `api_version: 2` and `meta.answered_by: {bundle, wrapper}` plus content hashes (`sha256` / `sha8`) of upstream inputs so stale or drifted state is detected immediately.
5. **Blast-Radius Isolation**:
   - Writing workers operate in isolated git worktrees or sandboxed containers.
   - Append-only state ledgers ensure crashes never corrupt historical progress.

### 2.2 Modular Optimization Checklist

Every subsystem topology must specify:
1. **Critical-Path Compression**: identify the longest sequential chain in the DAG; parallelize independent nodes (capped at 1-3 concurrent subagents to control token/compute cost).
2. **Batch Perceive-Act-Verify Cycles**: collapse chatty multi-round IPC, N+1 DB queries, or screenshot-per-click loops into batched atomic transactions.
3. **Lazy Enablement & Progressive Disclosure**: load heavy plugins, MCP servers, models, or reference docs only when their trigger predicate fires; keep cold-start near zero.
4. **Idempotent Caching & Content-Addressed Skip**: if an artifact exists and its `upstream_hashes` match current inputs, skip recomputation in $O(1)$.
