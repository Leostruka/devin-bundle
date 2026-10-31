"""CPU-first bitnet.cpp subprocess adapter.

Wraps the upstream `microsoft/BitNet` inference contract: the compiled
`llama-cli` binary (build/bin/llama-cli, or build/bin/Release/llama-cli.exe
on Windows) invoked as

    llama-cli -m MODEL.gguf -n N_PREDICT -t THREADS -p PROMPT \\
              -ngl 0 -c CTX_SIZE --temp TEMPERATURE

`-ngl 0` pins all layers to CPU — bitnet.cpp runs ternary 1.58-bit models
on CPU/RAM with no VRAM. Source: github.com/microsoft/BitNet,
run_inference.py. Newer llama-cli builds default to interactive chat, so
non-conversation runs pass `-st` and stdin is /dev/null — the process can
never block on a prompt.

Stdlib only. JSON on stdout. Honest `backend_unavailable` errors when the
binary or GGUF weights are not present locally — nothing is downloaded and
no external endpoint is contacted.

  python bitnet_adapter.py --model models/.../ggml-model-i2_s.gguf \\
      --binary build/bin/llama-cli -p "prompt"
  python bitnet_adapter.py --self-test   # offline contract checks
"""
import argparse
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_N_PREDICT = 128
DEFAULT_THREADS = 2
DEFAULT_CTX_SIZE = 2048
DEFAULT_TEMPERATURE = 0.8
DEFAULT_TIMEOUT_S = 120.0
DEFAULT_MAX_PROMPT_BYTES = 8192
MAX_INT_BOUND = 1 << 20
MAX_CANDIDATES = 8
MAX_TIMEOUT_S = 3600.0
_ID_RE = re.compile(r"^[A-Za-z0-9_.:\-]{1,64}$")
_JSON_RE = re.compile(r"\{[^{}]*\}")
_ALLOWED_EXTRA = frozenset()


@dataclass
class BitNetConfig:
    binary: Path
    model: Path
    n_predict: int = DEFAULT_N_PREDICT
    threads: int = DEFAULT_THREADS
    ctx_size: int = DEFAULT_CTX_SIZE
    temperature: float = DEFAULT_TEMPERATURE
    timeout: float = DEFAULT_TIMEOUT_S
    max_prompt_bytes: int = DEFAULT_MAX_PROMPT_BYTES
    conversation: bool = False
    extra_flags: list = field(default_factory=list)


def find_binary(build_dir):
    """Locate the compiled llama-cli inside a bitnet.cpp build tree."""
    build_dir = Path(build_dir)
    candidates = [
        build_dir / "bin" / "llama-cli",
        build_dir / "bin" / "Release" / "llama-cli.exe",
        build_dir / "bin" / "llama-cli.exe",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def _check_bound(name, value, lo, hi):
    if not isinstance(value, int) or isinstance(value, bool) \
            or not (lo <= value <= hi):
        raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")


def _check_extra_flags(flags):
    """Closed allowlist: only explicitly verified-safe extras pass.

    The allowlist is empty — no flag, positional, or `flag=value` form may
    extend the pinned CPU/model/prompt/context contract. flags must be a
    list/tuple of strings.
    """
    if not isinstance(flags, (list, tuple)):
        raise TypeError("extra_flags must be a list/tuple of strings")
    for f in flags:
        if not isinstance(f, str):
            raise ValueError("extra_flags must be strings")
        if f.split("=", 1)[0] not in _ALLOWED_EXTRA:
            raise ValueError(
                f"extra flag {f!r} is not in the allowlist; the "
                "model/prompt/CPU/context contract cannot be overridden")


def _check_path_arg(name, value):
    if not isinstance(value, (str, Path)) or not str(value) \
            or "\x00" in str(value):
        raise ValueError(f"{name} must be a non-empty path string")


def build_command(cfg, prompt):
    """Build the llama-cli argv per the upstream run_inference.py contract."""
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    if "\x00" in prompt:
        raise ValueError("prompt contains NUL")
    _check_path_arg("binary", cfg.binary)
    _check_path_arg("model", cfg.model)
    if len(prompt.encode("utf-8", errors="replace")) > cfg.max_prompt_bytes:
        raise ValueError("prompt exceeds max_prompt_bytes")
    _check_bound("n_predict", cfg.n_predict, 1, MAX_INT_BOUND)
    _check_bound("threads", cfg.threads, 1, MAX_INT_BOUND)
    _check_bound("ctx_size", cfg.ctx_size, 1, MAX_INT_BOUND)
    _check_bound("max_prompt_bytes", cfg.max_prompt_bytes, 1, MAX_INT_BOUND)
    if not isinstance(cfg.timeout, (int, float)) \
            or not math.isfinite(cfg.timeout) \
            or not (0 < cfg.timeout <= MAX_TIMEOUT_S):
        raise ValueError(
            f"timeout must be finite in (0, {MAX_TIMEOUT_S}]")
    if not (0.0 <= cfg.temperature <= 2.0):
        raise ValueError("temperature out of range [0.0, 2.0]")
    _check_extra_flags(cfg.extra_flags)
    argv = [
        str(cfg.binary),
        "-m", str(cfg.model),
        "-n", str(cfg.n_predict),
        "-t", str(cfg.threads),
        "-p", prompt,
        "-ngl", "0",
        "-c", str(cfg.ctx_size),
        "--temp", str(cfg.temperature),
    ]
    if cfg.conversation:
        argv.append("-cnv")
    else:
        argv.append("-st")
    argv.extend(cfg.extra_flags)
    return argv


def _unavailable(reason):
    return {"ok": False, "backend": "bitnet.cpp", "backend_unavailable": True,
            "error": reason}


def run(prompt, cfg):
    """Execute llama-cli. Never raises; returns a JSON-able result dict."""
    try:
        _check_path_arg("binary", cfg.binary)
        _check_path_arg("model", cfg.model)
        binary = Path(cfg.binary)
        model = Path(cfg.model)
    except (ValueError, TypeError) as e:
        return {"ok": False, "backend": "bitnet.cpp",
                "backend_unavailable": False, "error": str(e)}
    if sys.platform == "win32" \
            and binary.suffix.lower() in (".bat", ".cmd"):
        return {"ok": False, "backend": "bitnet.cpp",
                "backend_unavailable": False,
                "error": "refusing .bat/.cmd backend path: batch files "
                         "run through cmd.exe even with shell=False; use "
                         "a native executable"}
    if not binary.is_file():
        return _unavailable(f"llama-cli binary not found: {binary}")
    if not model.is_file():
        return _unavailable(f"GGUF model not found: {model}")
    try:
        argv = build_command(cfg, prompt)
    except (ValueError, TypeError) as e:
        return {"ok": False, "backend": "bitnet.cpp",
                "backend_unavailable": False, "error": str(e)}
    try:
        proc = subprocess.run(argv, shell=False, stdin=subprocess.DEVNULL,
                              capture_output=True, encoding="utf-8",
                              errors="replace", timeout=cfg.timeout)
    except ValueError as e:
        return {"ok": False, "backend": "bitnet.cpp",
                "backend_unavailable": False,
                "error": f"malformed argv: {e}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "backend": "bitnet.cpp",
                "backend_unavailable": False, "timed_out": True,
                "error": f"process exceeded {cfg.timeout}s timeout"}
    except OSError as e:
        return _unavailable(f"cannot execute {binary}: {e}")
    if proc.returncode != 0:
        return {"ok": False, "backend": "bitnet.cpp",
                "backend_unavailable": False,
                "error": f"llama-cli exit {proc.returncode}: "
                         f"{proc.stderr.strip()[:500]}"}
    return {"ok": True, "backend": "bitnet.cpp",
            "backend_unavailable": False,
            "output": _clean_output(proc.stdout.strip(), prompt)}


def _valid_ids(candidates):
    if not isinstance(candidates, list) \
            or not (1 <= len(candidates) <= MAX_CANDIDATES):
        return None
    ids = []
    for c in candidates:
        if not isinstance(c, dict) or not isinstance(c.get("id"), str):
            return None
        if not _ID_RE.match(c["id"]):
            return None
        ids.append(c["id"])
    if len(set(ids)) != len(ids):
        return None
    return ids


_FOOTER_RE = re.compile(r"\[\s*Prompt:|^Exiting\.\.\.|^>$", re.MULTILINE)


def _clean_output(output, prompt):
    """Extract generated text from llama-cli's framed stdout.

    Only the `> <prompt>` echo line is consumed — text after it is kept
    verbatim, so a generation that repeats the prompt is preserved. Known
    timing footer (`[ Prompt: ... t/s | ... ]`, `Exiting...`, bare `>`)
    is stripped. Output without recognizable framing is returned as-is.
    """
    echo = "> " + prompt
    idx = output.find(echo)
    if idx < 0:
        return output
    tail = output[idx + len(echo):]
    cut = _FOOTER_RE.search(tail)
    if cut:
        tail = tail[:cut.start()]
    return tail.strip()


def _generation_tail(output, prompt):
    tail = output
    idx = output.find("> " + prompt)
    if idx >= 0:
        tail = output[idx + len(prompt) + 2:]
    return tail


def suggest(prompt, candidates, cfg):
    """Typed suggestion/abstain wrapper over `run`.

    Candidates must be 1-8 dicts with unique safe "id" strings. The model
    is asked to answer with JSON {"choice": "<id>"}. Only the output tail
    after the echoed prompt is parsed, so an echoed prompt can never be
    consumed as the recommendation. A suggestion requires the parsed
    choice to be exactly one candidate ID; anything else abstains.
    `authority` is always False — a local model suggestion never overrides
    the deterministic policy, and no raw confidence or raw model text is
    surfaced on rejection.
    """
    ids = _valid_ids(candidates)
    if ids is None:
        return {"type": "abstain", "authority": False,
                "reason": "invalid candidates: need 1-8 entries with "
                          "unique safe ids"}
    listing = "\n".join(f'- "{i}"' for i in ids)
    query = (f"{prompt}\n\nPick exactly one of these candidate IDs:\n"
             f"{listing}\n\nAnswer ONLY with JSON: {{\"choice\": \"<id>\"}}")
    r = run(query, cfg)
    if not r["ok"]:
        out = {"type": "abstain", "authority": False,
               "reason": r["error"]}
        if r.get("backend_unavailable"):
            out["backend_unavailable"] = True
        return out
    tail = _generation_tail(r["output"], query)
    matches = _JSON_RE.findall(tail)
    if not matches:
        return {"type": "abstain", "authority": False,
                "reason": "no JSON object in model output"}
    try:
        parsed = json.loads(matches[-1])
    except json.JSONDecodeError:
        return {"type": "abstain", "authority": False,
                "reason": "malformed JSON in model output"}
    choice = parsed.get("choice")
    if choice in ids:
        return {"type": "suggestion", "authority": False, "choice": choice}
    return {"type": "abstain", "authority": False,
            "reason": "model choice is not a candidate ID"}


def _self_test():
    cfg = BitNetConfig(binary="b", model="m", n_predict=1, threads=1,
                       ctx_size=8, temperature=0.0)
    argv = build_command(cfg, "p")
    assert argv[1:3] == ["-m", "m"] and argv[argv.index("-ngl") + 1] == "0"
    assert argv[argv.index("-p") + 1] == "p"
    r = run("x", BitNetConfig(binary="missing", model="missing"))
    assert r["ok"] is False and r["backend_unavailable"]
    for bad in (dict(max_prompt_bytes=2), dict(timeout=-1),
                dict(n_predict=0), dict(extra_flags=["-ngl"])):
        try:
            build_command(BitNetConfig(binary="b", model="m", **bad),
                          "xxxx")
            raise AssertionError(f"bound not enforced: {bad}")
        except (ValueError, TypeError):
            pass
    print(json.dumps({"ok": True, "self_test": True}))


def main():
    ap = argparse.ArgumentParser(description="bitnet.cpp CPU adapter")
    ap.add_argument("--binary", help="path to llama-cli")
    ap.add_argument("--model", help="path to GGUF model")
    ap.add_argument("-p", "--prompt")
    ap.add_argument("-n", "--n-predict", type=int, default=DEFAULT_N_PREDICT)
    ap.add_argument("-t", "--threads", type=int, default=DEFAULT_THREADS)
    ap.add_argument("-c", "--ctx-size", type=int, default=DEFAULT_CTX_SIZE)
    ap.add_argument("-temp", "--temperature", type=float,
                    default=DEFAULT_TEMPERATURE)
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _self_test()
        return
    if not args.binary or not args.model or not args.prompt:
        ap.error("--binary, --model and -p are required")
    cfg = BitNetConfig(binary=args.binary, model=args.model,
                       n_predict=args.n_predict, threads=args.threads,
                       ctx_size=args.ctx_size, temperature=args.temperature,
                       timeout=args.timeout)
    print(json.dumps(run(args.prompt, cfg)))


if __name__ == "__main__":
    main()
