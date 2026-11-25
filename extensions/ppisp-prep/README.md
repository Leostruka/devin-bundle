# ppisp-prep

Photometric QC + NVIDIA PPISP integration prep for reconstruction
pipelines (ai3d-gen/gsplat intake).

- `photo_qc.py`: go/correct/recapture verdict on a capture series
  (exposure / WB / vignette spread). Pure CPU, any Python 3.11+.
- `ppisp_runner.py`: doctor/smoke/run over the upstream checkout.
  Upstream is a LIBRARY (no train.py); `run` errors
  `integration_required` until the reconstruction-loop integration is
  wired into a pipeline. `smoke` runs upstream's own pytest suite.
- `synth_harness.py`: synthetic held-out validation of the
  integration thesis (gsplat + ppisp training loop, controlled
  corruption, novel-view PSNR gate). Needs the CUDA env below.

## CUDA environment (WSL2 userland recipe, verified 2026-11-25)

Windows-native build is blocked (torch cpp_extension needs MSVC;
vswhere shows zero VS installations on the reference host). WSL2 is
the supported path: GPU passes through, gcc builds the extensions, no
admin rights needed anywhere. Measured on RTX 3050 Laptop (sm_86):

1. venv without pip (no sudo for python3.x-venv):
   `python3 -m venv --without-pip ~/.venvs/ppisp` then bootstrap with
   `get-pip.py` (https://bootstrap.pypa.io/get-pip.py).
2. torch from the cu129 index (exact nvcc pairing):
   `pip install --index-url https://download.pytorch.org/whl/cu129 torch`
   (py3.10 caps at torch 2.13; use a newer python for newer torch).
   Plus `pip install numpy matplotlib ninja pytest gsplat`.
   ninja's binary must be on PATH (venv bin) for gsplat's JIT build.
3. CUDA toolkit userland, ~42MB instead of the 5.8GB runfile: download
   these .debs from
   `https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/`
   and extract with `dpkg-deb -x <deb> ~/cuda-12.9`:
   - `cuda-nvcc-12-9` (driver, cudafe++, ptxas). pip
     `nvidia-cuda-nvcc-cu12` is NOT a substitute (no nvcc binary)
   - `cuda-crt-12-9` (crt/host_config.h etc.; separate package!)
   - `cuda-nvvm-12-9` (nvvm/bin/cicc; nvcc fails without it)
   - `cuda-cudart-dev-12-9` + `cuda-cudart-12-9` (dev ships the .so
     symlink, the runtime package ships libcudart.so.12 itself)
   - `cuda-cccl-12-9`, `cuda-driver-dev-12-9`
4. Env for builds: `CUDA_HOME=~/cuda-12.9/usr/local/cuda-12.9`,
   PATH prepended with `$CUDA_HOME/bin` and the venv bin,
   `LD_LIBRARY_PATH=$CUDA_HOME/targets/x86_64-linux/lib`,
   `TORCH_CUDA_ARCH_LIST=8.6` (match the GPU).
5. Build upstream: clone `nv-tlabs/ppisp` (Apache-2.0) and
   `pip install . --no-build-isolation` in the venv. Validate:
   `python ppisp_runner.py smoke` or upstream `pytest tests` directly
   (235/235 green measured).

Shell gotchas (Windows host driving WSL): MSYS rewrites `/mnt/...`
paths (use `MSYS_NO_PATHCONV=1`), nested quoting eats `$vars` (write
script files and execute them instead), strip CR from Windows-written
scripts (`sed -i 's/\r//'`).

## Evidence ledger

- 2026-11-25: upstream pytest 235/235 on RTX 3050 (WSL2).
- 2026-11-25 synth_harness held-out matrix (novel-view PSNR delta vs
  baseline, positive = ppisp better; raw = scene cleanliness,
  corrected = controller-inference output):
  - strong corruption (expo U(0.7,1.4), wb +-10%, vig 0.35), seeds
    A/B/C/D: corrected +2.12 / +1.39 / +2.30 / +2.59 (mean +2.10,
    min +1.39, 3/4 over the 2dB gate, ALL positive), raw +1.14 /
    +1.31 / +2.22 / +1.82 - reliable win.
  - control (no corruption): raw +0.30, corrected +1.07 - does not
    hurt clean training.
  - realistic mild drift (expo U(0.9,1.1), wb +-3%, vig 0.15), seeds
    A/B/C: corrected +0.80 / -1.20 / +1.64 (mean +0.41, one negative)
    - high variance, benefit NOT reliable at mild drift.
  Consequence: wire PPISP correction for strong appearance variation
  (mixed devices, changing light, large photo_qc spread); mild uniform
  drift is a seed lottery. Note CUDA splatting backward uses atomics,
  so same-config reruns vary by ~0.2dB - exact bit-reproduction is
  impossible by construction.
  Protocol + jsons: `.devin/scratch/si-20261125/synth_ppisp_*.json`
  (scratch is ephemeral; numbers duplicated in the session ledger).
- photo_qc calibration on VISION (5 devices):
  `.devin/scratch/prnu-vision/photoqc-calibration-2026-11-25.json`.
