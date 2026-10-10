"""prnu — noise-residual extraction, reference building, PCE scoring.

PRNU (photo-response non-uniformity): every sensor stamps a fixed
spatial noise pattern on its captures; synthetic images have none.

Residual = image - denoised(image). Preferred denoiser is a wavelet
shrinkage (PyWavelets, Mihcak/BDWT family); when pywt is absent we fall
back to a Gaussian estimate via Pillow — weaker but deterministic and
dependency-free.

PCE (peak-to-correlation-energy): normalized cross-correlation of the
query residual against a camera reference pattern over all circular
shifts; the squared peak divided by the mean correlation energy
outside the peak neighborhood. Goljan's empirical discrimination band
is ~50-60; treat thresholds as dataset-calibrated, never universal.
"""
from __future__ import annotations

import numpy as np


def load_gray(path):
    """Load image as float64 grayscale in [0, 1]."""
    from PIL import Image
    with Image.open(path) as im:
        arr = np.asarray(im.convert("L"), dtype=np.float64)
    return arr / 255.0


def _denoise_gauss(arr, radius=1.0):
    from PIL import Image, ImageFilter
    im = Image.fromarray(np.clip(arr * 255.0, 0, 255).astype(np.uint8))
    out = im.filter(ImageFilter.GaussianBlur(radius=radius))
    return np.asarray(out, dtype=np.float64) / 255.0


def _denoise_wavelet(arr):
    import pywt  # optional
    coeffs = pywt.wavedec2(arr, "db8", level=2)
    sigma = np.median(np.abs(coeffs[-1][0])) / 0.6745 or 1e-6
    thr = sigma * np.sqrt(2 * np.log(arr.size))
    new = [coeffs[0]] + [tuple(pywt.threshold(c, thr, mode="soft")
                               for c in lvl) for lvl in coeffs[1:]]
    return pywt.waverec2(new, "db8")[:arr.shape[0], :arr.shape[1]]


def residual(arr, method="auto"):
    """High-frequency noise residual candidate (fingerprint)."""
    if method in ("auto", "wavelet"):
        try:
            return arr - _denoise_wavelet(arr)
        except ImportError:
            if method == "wavelet":
                raise
    return arr - _denoise_gauss(arr)


def build_reference(arrays, method="auto"):
    """Average residuals of N same-shape captures from one device.

    arrays: iterable of float64 images (identical shape required —
    crop/resize upstream before calling).
    """
    acc = None
    n = 0
    for a in arrays:
        r = residual(a, method=method)
        acc = r if acc is None else acc + r
        n += 1
    if not n:
        raise ValueError("empty image set")
    return acc / n


def _norm(arr):
    a = arr.astype(np.float64) - arr.mean()
    s = a.std()
    return a / s if s > 0 else a


def pce(res, ref, peak_win=11):
    """Peak-to-correlation-energy of residual vs reference pattern."""
    if res.shape != ref.shape:
        raise ValueError(f"shape mismatch {res.shape} vs {ref.shape}")
    r = _norm(res)
    k = _norm(ref)
    corr = np.fft.ifft2(np.fft.fft2(r) * np.conj(np.fft.fft2(k))).real
    peak = int(np.argmax(corr))
    py_, px_ = np.unravel_index(peak, corr.shape)
    mask = np.ones(corr.shape, dtype=bool)
    h, w = corr.shape
    ys = (py_ + np.arange(-peak_win // 2, peak_win // 2 + 1)) % h
    xs = (px_ + np.arange(-peak_win // 2, peak_win // 2 + 1)) % w
    mask[np.ix_(ys, xs)] = False
    denom = corr[mask]
    energy = float(np.mean(denom ** 2)) if denom.size else 0.0
    if energy <= 0:
        return 0.0
    return float(corr[py_, px_] ** 2 / energy)


def residual_energy(res):
    """Std of the residual — abstain signal when below the noise floor
    of the denoiser (flat or heavily recompressed input)."""
    return float(np.asarray(res).std())
