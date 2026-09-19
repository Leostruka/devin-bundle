# rust-core

Hybrid Rust–Python extension layer for the devin bundle. Cargo workspace where
each crate under `crates/` is one compiled Python module ("micro-extension").
Python stays the orchestration layer; Rust carries CPU-bound, memory-tight, or
OS-adjacent kernels. Rules: `.devin/adr/003-hybrid-rust-python-extensions.md`.

## Build

Requires `cargo`/`rustc` (optional — install scripts skip silently without it).

```sh
cargo build --release          # artifacts in target/release/
```

Then rename the artifact so Python can import it:

| Platform | artifact                    | import name        |
| -------- | --------------------------- | ------------------ |
| Windows  | `target/release/fast_math.dll`       | `fast_math.pyd` |
| Linux    | `target/release/libfast_math.so`     | `fast_math.so`  |
| macOS    | `target/release/libfast_math.dylib`  | `fast_math.so`  |

The install scripts do this automatically. With `maturin` installed,
`maturin develop` inside a crate dir works too.

## Use

```python
import sys
sys.path.insert(0, "<devin-home>/extensions/rust-core")
import fast_math
fast_math.fast_sum([1.0, 2.0, 3.0])   # 6.0
fast_math.primes_below(20)            # [2, 3, 5, 7, 11, 13, 17, 19]
```

## Add a new micro-extension

1. `cargo new crates/<name> --lib` (or copy `crates/fast-math`).
2. `[lib] crate-type = ["cdylib"]`, `name = "<python_module_name>"`.
3. `pyo3` dep with `abi3-py39` + `extension-module` features.
4. Workspace picks it up via `members = ["crates/*"]`.
