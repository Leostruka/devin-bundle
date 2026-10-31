"""Backend-specific weight/expert offloading argv builder.

Real flags only, verified against upstream sources — no generic "speed"
claims:

- bitnet.cpp (microsoft/BitNet): CPU-first by design. run_inference.py
  always passes `-ngl 0`; the official BitNet b1.58 models are dense
  ternary LLMs with no MoE experts, so expert offloading is rejected.
- llama.cpp (ggml-org): `-ngl N` layers on GPU, `--cpu-moe` keeps all MoE
  expert weights in system RAM, `--n-cpu-moe N` keeps the experts of the
  first N layers on CPU, `--override-tensor "pattern=CPU"` forces named
  tensors to a buffer type (common/arg.cpp, PRs #14992/#15077).

`build_argv` returns the flag suffix to append to the backend's CLI, or
raises ValueError for an unsupported backend, a dense-model MoE request,
or a malformed override pattern. Stdlib only.
"""
import json
import sys

_BACKENDS = ("bitnet.cpp", "llama.cpp")

_BUFFERS = ("CPU", "CUDA0", "CUDA1", "CUDA2", "CUDA3")


def _check_int(name, value, lo):
    if not isinstance(value, int) or isinstance(value, bool) \
            or value < lo:
        raise ValueError(f"{name} must be an integer >= {lo}")


def _check_override(pattern):
    if "=" not in pattern:
        raise ValueError(
            f"--override-tensor needs 'regex=buffer', got {pattern!r}")
    buf = pattern.rsplit("=", 1)[1].strip()
    if buf not in _BUFFERS:
        raise ValueError(f"unknown buffer type {buf!r} in {pattern!r}")


def build_argv(backend, model_is_moe=False, n_gpu_layers=None, cpu_moe=False,
               n_cpu_moe=None, override_tensors=None):
    """Return the offloading flag suffix for `backend`.

    Raises ValueError on unknown backend, MoE flags for a dense model, or
    malformed --override-tensor values.
    """
    if backend not in _BACKENDS:
        raise ValueError(f"unsupported backend {backend!r}; "
                         f"supported: {_BACKENDS}")
    if backend == "bitnet.cpp":
        if cpu_moe or n_cpu_moe or override_tensors:
            raise ValueError(
                "bitnet.cpp is CPU-first and BitNet b1.58 is a dense model: "
                "expert offloading flags do not apply")
        if n_gpu_layers is not None:
            _check_int("n_gpu_layers", n_gpu_layers, 0)
            if n_gpu_layers != 0:
                raise ValueError(
                    "bitnet.cpp runs CPU-only: n_gpu_layers must be 0")
        return ["-ngl", "0"]
    if (cpu_moe or n_cpu_moe) and not model_is_moe:
        raise ValueError("MoE offloading flags require a mixture-of-experts "
                         "model; dense models gain nothing and misplace "
                         "weights")
    if cpu_moe and n_cpu_moe is not None:
        raise ValueError("use --cpu-moe or --n-cpu-moe, not both")
    argv = []
    if n_gpu_layers is not None:
        _check_int("n_gpu_layers", n_gpu_layers, 0)
        argv += ["-ngl", str(n_gpu_layers)]
    if cpu_moe:
        argv.append("--cpu-moe")
    elif n_cpu_moe is not None:
        _check_int("n_cpu_moe", n_cpu_moe, 1)
        argv += ["--n-cpu-moe", str(n_cpu_moe)]
    for pat in override_tensors or []:
        _check_override(pat)
        argv += ["--override-tensor", pat]
    return argv


def main():
    """argv builder CLI: emit the flag suffix as JSON."""
    import argparse
    ap = argparse.ArgumentParser(description="offloading flag builder")
    ap.add_argument("--backend", required=True, choices=_BACKENDS)
    ap.add_argument("--model-is-moe", action="store_true")
    ap.add_argument("--ngl", type=int, dest="n_gpu_layers")
    ap.add_argument("--cpu-moe", action="store_true")
    ap.add_argument("--n-cpu-moe", type=int)
    ap.add_argument("--override-tensor", action="append",
                    dest="override_tensors", default=[])
    args = ap.parse_args()
    try:
        argv = build_argv(args.backend, model_is_moe=args.model_is_moe,
                          n_gpu_layers=args.n_gpu_layers,
                          cpu_moe=args.cpu_moe, n_cpu_moe=args.n_cpu_moe,
                          override_tensors=args.override_tensors)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)
    print(json.dumps({"ok": True, "argv": argv}))


if __name__ == "__main__":
    main()
