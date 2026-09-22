#!/usr/bin/env python3
"""bootstrap.py — isolated .venv installer for laya-tools.

Scoop-managed Python upgrades silently break native wheels (ABI mismatch,
e.g. torch built for python312.dll loaded by python314.dll -> WinError 126).
This script builds a strictly contained .venv next to laya_cli.py, installs
requirements through the correct PyTorch wheel index (cpu or cu124), and
runs an import + prediction smoke test.

stdlib only. Emits a single JSON object on stdout:
  {ok, steps, venv_python, torch_version, device}
Progress notes go to stderr. Exit code != 0 on any failure.

  python bootstrap.py
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV = HERE / ".venv"
REQUIREMENTS = HERE / "requirements.txt"
LAYA_CLI = HERE / "laya_cli.py"
TORCH_INDEX = {
    "cpu": "https://download.pytorch.org/whl/cpu",
    "cuda": "https://download.pytorch.org/whl/cu124",
}
MIN_PY = (3, 10)          # torch 2.x / transformers floor
NEWEST_OK = (3, 15)       # >=3.15: prefer py -3.13/-3.12 (wheel support lags)
PREDICT_TIMEOUT = int(os.environ.get("LAYA_BOOTSTRAP_TIMEOUT", "900"))

steps = []
device = "cpu"


def step(name, ok, detail=""):
    steps.append({"step": name, "ok": ok, **({"detail": detail} if detail else {})})
    return ok


def note(msg):
    print(f"[bootstrap] {msg}", file=sys.stderr)


def run(cmd, timeout=None):
    """Run cmd, return (rc, combined_output). Never raises."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=HERE)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, f"{type(e).__name__}: {e}"


def venv_python():
    """Interpreter path inside the venv for the current platform."""
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def pick_interpreter():
    """Choose the base interpreter. >=3.15 prefers py -3.13/-3.12 or
    python3.13/python3.12 on PATH; otherwise use the running interpreter."""
    cur = sys.version_info
    if cur >= NEWEST_OK:
        cands = []
        if shutil.which("py"):
            cands += [["py", "-3.13"], ["py", "-3.12"]]
        cands += [[n] for n in ("python3.13", "python3.12") if shutil.which(n)]
        for cmd in cands:
            rc, out = run(cmd + ["-c", "import sys;print(sys.version_info[:2])"])
            if rc == 0:
                return cmd
        return None
    if cur < MIN_PY:
        return None
    return [sys.executable]


def has_vcruntime():
    if os.name != "nt":
        return True
    sys32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    return (sys32 / "vcruntime140.dll").is_file()


def detect_device():
    """'cuda' if an NVIDIA GPU is present, else 'cpu'."""
    if shutil.which("nvidia-smi"):
        rc, _ = run(["nvidia-smi", "-L"], timeout=15)
        if rc == 0:
            return "cuda"
    if os.name == "nt" and shutil.which("powershell"):
        rc, out = run(["powershell", "-NoProfile", "-Command",
                       "(Get-CimInstance Win32_VideoController).Name"],
                      timeout=30)
        if rc == 0 and "nvidia" in out.lower():
            return "cuda"
    return "cpu"


def install(force=False):
    cmd = [str(venv_python()), "-m", "pip", "install"]
    if force:
        cmd += ["--force-reinstall", "--no-cache-dir"]
    cmd += ["-r", str(REQUIREMENTS), "--extra-index-url", TORCH_INDEX[device]]
    return run(cmd, timeout=1800)


def smoke():
    """import torch, laya inside the venv. Returns (ok, output)."""
    rc, out = run([str(venv_python()), "-c",
                   "import torch, laya; print(torch.__version__)"],
                  timeout=180)
    return rc == 0, out


def emit(ok, extra=None):
    out = {"ok": ok, "steps": steps,
           "venv_python": str(venv_python()),
           "torch_version": extra.get("torch_version"),
           "device": device}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.exit(0 if ok else 1)


def main():
    global device

    if not REQUIREMENTS.is_file():
        step("requirements", False, f"missing {REQUIREMENTS}")
        emit(False)

    base = pick_interpreter()
    if base is None:
        step("python_version", False,
             f"need Python >={MIN_PY[0]}.{MIN_PY[1]} and <{NEWEST_OK[0]}.{NEWEST_OK[1]} "
             f"(running {sys.version.split()[0]}); install py -3.13/-3.12")
        emit(False)
    step("python_version", True, " ".join(base))

    if not has_vcruntime():
        step("vcruntime", False,
             "vcruntime140.dll missing — run: winget install Microsoft.VCRedist.2015+.x64")
        emit(False)
    step("vcruntime", True)

    device = detect_device()
    step("gpu_detect", True, f"{device} ({'NVIDIA found' if device == 'cuda' else 'no NVIDIA GPU'})")

    if not venv_python().is_file():
        note("creating .venv ...")
        rc, out = run(base + ["-m", "venv", str(VENV)], timeout=300)
        if not step("create_venv", rc == 0, out.strip()[-400:] if rc else ""):
            emit(False)
    else:
        step("create_venv", True, "reusing existing .venv")

    note("upgrading pip in .venv ...")
    run([str(venv_python()), "-m", "pip", "install", "--upgrade", "pip"], timeout=300)

    note(f"installing requirements via {TORCH_INDEX[device]} ...")
    rc, out = install()
    if not step("install_deps", rc == 0, out.strip()[-400:] if rc else ""):
        emit(False)

    note("smoke test: import torch, laya ...")
    ok, out = smoke()
    if not ok and ("WinError 126" in out or "torch_python" in out):
        note("ABI mismatch detected — retrying with --force-reinstall --no-cache-dir ...")
        rc, out2 = install(force=True)
        step("force_reinstall", rc == 0, out2.strip()[-400:] if rc else "")
        if rc == 0:
            ok, out = smoke()
    if not step("smoke_import", ok, out.strip()[-400:] if not ok else ""):
        emit(False)

    torch_version = out.strip().splitlines()[-1].strip() if ok else None

    note("smoke predict — first run downloads ~1GB of weights from Hugging Face ...")
    # laya_cli emits pure JSON on stdout; stderr carries tqdm/warnings — parse stdout only
    try:
        p = subprocess.run([str(venv_python()), str(LAYA_CLI), "predict",
                            "--state", '{"body": "charged twice"}',
                            "--preset", "triage"],
                           capture_output=True, text=True,
                           timeout=PREDICT_TIMEOUT, cwd=HERE)
        pred_ok = p.returncode == 0 and json.loads(p.stdout).get("ok") is True
        out = p.stdout + (p.stderr or "")
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        pred_ok, out = False, f"{type(e).__name__}: {e}"
    if not step("smoke_predict", pred_ok, out.strip()[-400:] if not pred_ok else ""):
        emit(False, {"torch_version": torch_version})

    emit(True, {"torch_version": torch_version})


if __name__ == "__main__":
    main()
