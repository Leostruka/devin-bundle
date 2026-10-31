"""vLLM TPU held-out batch runner and optional local serving wrapper.

Two entry points, both honest about hardware:

- `run_tpu_batch` executes a finite batch over a frozen manifest validated
  by `heldout_batch.load_manifest`, using vLLM's offline Python API
  (`from vllm import LLM, SamplingParams`; `llm.generate(prompts, sp)`)
  per the current vLLM TPU docs (tpu-inference / vllm-tpu). jax and vllm
  are imported lazily inside the function; without TPU hardware it
  returns `backend_unavailable` and exits honestly.
- `serve` optionally launches `vllm serve` bound to 127.0.0.1 on a bounded
  port — the documented default is a public unauthenticated listener,
  which is not acceptable, so the host flag is forced private and cannot
  be overridden by extra flags.

No cloud job submission, no TPU VM creation, no hardware claims. Stdlib
only at module scope.
"""
import argparse
import hashlib
import json
import subprocess
import sys

_BIND_HOST = "127.0.0.1"
_PORT_MIN, _PORT_MAX = 1024, 65535
_ALLOWED_EXTRA = frozenset()


def check_tpu():
    """Report TPU availability via jax; honest failure when absent."""
    try:
        import jax
    except ImportError:
        return {"ok": False, "backend": "vllm-tpu",
                "backend_unavailable": True,
                "error": "jax not installed — run on a TPU VM with "
                         "vllm-tpu installed"}
    try:
        devices = jax.devices()
    except Exception as e:
        return {"ok": False, "backend": "vllm-tpu",
                "backend_unavailable": True,
                "error": f"jax.devices() failed: {e}"}
    tpus = [d for d in devices if "tpu" in str(d).lower()
            or "TpuDevice" in type(d).__name__]
    if not tpus:
        return {"ok": False, "backend": "vllm-tpu",
                "backend_unavailable": True,
                "error": f"no TPU devices found: {devices}"}
    return {"ok": True, "backend": "vllm-tpu",
            "backend_unavailable": False,
            "devices": [str(d) for d in tpus]}


def run_tpu_batch(entries, model, max_tokens=128, temperature=0.0,
                  tensor_parallel_size=1, max_model_len=2048,
                  download_dir="/tmp"):
    """Finite held-out batch via vLLM's offline API on real TPU.

    `entries` must come from heldout_batch.load_manifest (verified bytes
    bound at load). Returns deterministic records sorted by id. Without
    TPU or vllm installed, returns backend_unavailable — never a mock.
    """
    check = check_tpu()
    if not check["ok"]:
        return check
    try:
        from vllm import LLM, SamplingParams
    except ImportError:
        return {"ok": False, "backend": "vllm-tpu",
                "backend_unavailable": True,
                "error": "vllm not installed — install vllm-tpu on the "
                         "TPU VM"}
    if max_tokens < 1 or temperature < 0.0 or tensor_parallel_size < 1:
        return {"ok": False, "backend": "vllm-tpu",
                "backend_unavailable": False,
                "error": "invalid generation bounds"}
    ordered = sorted(entries, key=lambda x: x["id"])
    prompts = [e["_data"].decode("utf-8", errors="replace")
               for e in ordered]
    llm = LLM(model=model, tensor_parallel_size=tensor_parallel_size,
              max_model_len=max_model_len, download_dir=download_dir)
    sp = SamplingParams(max_tokens=max_tokens, temperature=temperature)
    outs = llm.generate(prompts, sp)
    n_out = len(outs) if isinstance(outs, (list, tuple)) else -1
    if n_out != len(ordered):
        return {"ok": False, "backend": "vllm-tpu",
                "backend_unavailable": False,
                "error": "incomplete_results: backend returned "
                         f"{n_out} outputs for {len(ordered)} prompts",
                "manifest_entries": len(ordered), "results": []}
    results = []
    for e, o in zip(ordered, outs):
        try:
            text = "".join(c.text for c in o.outputs)
        except AttributeError:
            results.append({"id": e["id"], "ok": False,
                            "input_sha256": e["sha256"],
                            "error": "malformed_output"})
            continue
        results.append({
            "id": e["id"], "ok": True, "input_sha256": e["sha256"],
            "output_sha256": hashlib.sha256(text.encode()).hexdigest()})
    return {"ok": all(r["ok"] for r in results), "backend": "vllm-tpu",
            "backend_unavailable": False,
            "manifest_entries": len(ordered), "results": results}


def build_serve_command(model, port=8080, tensor_parallel_size=1,
                        max_model_len=2048, download_dir="/tmp",
                        extra_flags=None):
    """argv for `vllm serve`, always bound to 127.0.0.1 on a high port."""
    if not (_PORT_MIN <= port <= _PORT_MAX):
        raise ValueError(f"port {port} outside {_PORT_MIN}-{_PORT_MAX}")
    if tensor_parallel_size < 1 or max_model_len < 1:
        raise ValueError("tensor_parallel_size and max_model_len must be "
                         ">= 1")
    extra = list(extra_flags or [])
    if not isinstance(extra_flags or [], (list, tuple)):
        raise TypeError("extra_flags must be a list/tuple of strings")
    for f in extra:
        if not isinstance(f, str):
            raise ValueError("extra_flags must be strings")
        if f.split("=", 1)[0] not in _ALLOWED_EXTRA:
            raise ValueError(
                f"extra flag {f!r} is not in the allowlist; the "
                "localhost binding and serving contract cannot be "
                "overridden")
    argv = ["vllm", "serve", model,
            "--host", _BIND_HOST,
            "--port", str(port),
            "--download_dir", download_dir,
            "--tensor-parallel-size", str(tensor_parallel_size),
            "--max-model-len", str(max_model_len)]
    argv.extend(extra)
    return argv


def serve(model, port=8080, tensor_parallel_size=1, max_model_len=2048,
          download_dir="/tmp", timeout=None):
    """Verify TPU, then exec `vllm serve` bound to localhost."""
    check = check_tpu()
    if not check["ok"]:
        return check
    argv = build_serve_command(model, port, tensor_parallel_size,
                               max_model_len, download_dir)
    try:
        proc = subprocess.run(argv, shell=False, timeout=timeout)
    except FileNotFoundError:
        return {"ok": False, "backend": "vllm-tpu",
                "backend_unavailable": True,
                "error": "vllm executable not found on PATH"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "backend": "vllm-tpu",
                "backend_unavailable": False, "timed_out": True,
                "error": "vllm serve exceeded timeout"}
    return {"ok": proc.returncode == 0, "backend": "vllm-tpu",
            "backend_unavailable": False, "exit_code": proc.returncode}


def main():
    ap = argparse.ArgumentParser(
        description="vLLM TPU held-out batch / local serve")
    ap.add_argument("--manifest", help="frozen held-out manifest to run")
    ap.add_argument("--data-root")
    ap.add_argument("--model")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--tensor-parallel-size", type=int, default=1)
    ap.add_argument("--max-model-len", type=int, default=2048)
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--download-dir", default="/tmp")
    ap.add_argument("--serve", action="store_true",
                    help="launch localhost-bound vllm serve instead")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    if args.check_only:
        print(json.dumps(check_tpu()))
        return
    if args.serve:
        if not args.model:
            ap.error("--model required with --serve")
        print(json.dumps(serve(args.model, args.port,
                               args.tensor_parallel_size,
                               args.max_model_len, args.download_dir)))
        return
    if not (args.manifest and args.model):
        ap.error("--manifest and --model required for batch")
    import heldout_batch as hb
    try:
        entries = hb.load_manifest(args.manifest, args.data_root)
    except hb.ManifestError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        raise SystemExit(2)
    res = run_tpu_batch(entries, args.model, args.max_tokens,
                        tensor_parallel_size=args.tensor_parallel_size,
                        max_model_len=args.max_model_len,
                        download_dir=args.download_dir)
    print(json.dumps(res))
    raise SystemExit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
