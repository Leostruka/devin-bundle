# ADR 003: Hybrid Rust–Python extensions (`extensions/rust-core/`)

## Status

Accepted

## Context

Bundle extensions (`computer-use`, `media-tools`) are pure Python. That fits
orchestration, CLI glue, and JSON parsing, but Python is the bottleneck for
sub-millisecond latency, CPU-bound kernels, and work needing strict memory
safety. The Rust toolchain is optional on user machines, so compiled
extensions must degrade gracefully: never required, never installed by force.

## Decision

A Cargo workspace at `extensions/rust-core/`; each crate under `crates/` is
one importable Python module built with PyO3 (`cdylib`). Demo crate:
`fast-math` (`fast_sum`, `primes_below`). Golden path is dependency-free:

```
cargo build --release          # → target/release/
# stage artifact for import:
#   Windows: fast_math.dll        → fast_math.pyd
#   Linux:   libfast_math.so      → fast_math.so
#   macOS:   libfast_math.dylib   → fast_math.so
```

`maturin` (`pyproject.toml` per crate, `maturin develop` in a venv) is the
optional wheel path; the installers use `cargo build` + rename because it
needs no Python packaging tooling. `install.ps1`/`install.sh` detect `cargo`:
absent → non-blocking warning, continue; present → build at the installed
copy (`$DEVIN_HOME/extensions/rust-core/`) so `target/` never ships in the
bundle. Crates pin `pyo3` with `abi3-py39` + `extension-module`: one build
imports on every Python ≥ 3.9.

## Rules for future sessions

**Choose Python** for CLI entry points, JSON/text parsing, orchestration,
gluing skills/hooks/extensions, and anything whose bottleneck is I/O or
process spawn.

**Choose Rust** for CPU-bound kernels (image/tensor transforms, parsing
megabytes of structured data, compression), sub-millisecond interactive work
(input injection, hot paths in `computer-use`), direct OS API access (Win32,
procfs), and anywhere memory-safety guarantees matter.

**PyO3 playbook:**

- Keep `#[pyfunction]`s thin — convert Python types at the boundary, run
  plain Rust inside. Signature `fn f(py: Python<'_>, ...) -> T` with owned
  types (`Vec<f64>` in, `Vec<u64>` out), never `PyObject` plumbing.
- Release the GIL on work > ~1 ms: wrap the body in `py.detach(|| ...)`
  (see `primes_below`).
- No async/tokio inside extensions — Python owns the event loop.
- Return `PyResult<T>` and let panics surface as Python exceptions; do not
  catch-and-print inside Rust.
- Borrow checker triage: keep functions small and take owned values at the
  seam — clone at the boundary instead of threading lifetimes across FFI.
  If a signature needs a lifetime beyond `'py`, shrink the function.
- Add `#[pyclass]` only for stateful handles; stateless kernels stay
  functions.
- New crate = `cargo new crates/<name> --lib` + `crate-type = ["cdylib"]` +
  `pyo3` dep with `abi3-py39,extension-module`. The workspace glob
  (`members = ["crates/*"]`) picks it up — no registry edits.

## Review gate for crate PRs (checklist)

Derived from the rust-anything gate pattern (evidence
`.devin/research/media-osint-20261127/cards/nRlqH4izAU8.md`: record real
behavior, replay, diff, gate; 91.9% byte-identical over 17k recorded cases
in the source project). Every PR touching `crates/` fills this checklist
in the PR body or review thread; a crate PR without it does not merge:

1. `cargo fmt --check` clean.
2. `cargo clippy -- -D warnings` clean (warnings as errors, not noise).
3. Zero `unwrap()`/`panic!` outside tests; grep the diff, justify any
   exception inline.
4. `unsafe` audit: every `unsafe` block carries a justification comment;
   report the count even when zero.
5. Size cap: compiled artifact within 3x of the baseline it replaces, or
   the PR argues why the growth buys measured performance.
6. Behavior match: replay recorded real inputs through the Rust kernel
   and diff outputs against the Python/JS reference. Byte-identical is
   the target where semantics allow; semantic divergences (example from
   evidence: UTF-16 `indexOf` counts emoji as two units in JS) must be
   enumerated, not discovered by users.
7. FFI cost: bridge crossings can regress tiny hot functions (observed in
   source evidence). Any kernel under ~1 ms of work per call needs a
   before/after bench in the PR; if the crossing costs more than the
   kernel saves, stay in Python.

## Consequences

- Users without cargo get a warning and keep all Python functionality.
- `target/` and staged `.pyd`/`.so`/`.dylib` are excluded from install
  hashing/copying and git — they are derived, never shipped.
- `Cargo.lock` is committed for reproducible builds.
- Existing Python extensions stay Python; rewrite only when a measured
  bottleneck justifies it.
