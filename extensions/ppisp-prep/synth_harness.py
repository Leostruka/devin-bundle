"""Synthetic PPISP integration harness (held-out by construction).

Scene: random gaussians rendered by gsplat from known orbit poses.
Corruption: per-frame exposure gain + WB shift, constant vignette -
mirrors PPISP's own model split (per-frame exposure/color, per-camera
vignette) so recovery is identifiable in principle.

Two training arms, same init/seed/steps:
  baseline: plain photometric loss vs corrupted frames
  ppisp:    render -> ppisp() -> loss vs corrupted frames + reg loss

Held-out gate: novel-orbit renders compared against CLEAN gt renders.
Pass = ppisp-arm novel-view PSNR exceeds baseline by >= 2 dB.
"""
import argparse
import json
import math
import sys
from pathlib import Path

torch = None
rasterization = None

_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    """Nearest ancestor manifest.json with a "name" marker, else ""."""
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    import json as _json
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = _json.loads(
                    manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "ppisp-prep"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    if isinstance(payload, list):
        payload = {"ok": True, "items": payload}
    return json.dumps(_stamp(payload), **kw)


def _load_deps():
    """Import env-provided GPU deps lazily; return None or an error string."""
    global torch, rasterization
    if torch is None:
        try:
            import torch as torch_mod
        except ImportError as exc:
            return f"torch: {exc}"
        torch = torch_mod
    if rasterization is None:
        try:
            from gsplat import rasterization as rasterization_mod
        except ImportError as exc:
            return f"gsplat: {exc}"
        rasterization = rasterization_mod
    return None


def _dep_hint():
    return ("torch+gsplat are provided by the prepared environment, not "
            "pip-installed by the bundle - see extensions/ppisp-prep/README.md")


def doctor():
    """Offline dependency report; never starts training."""
    missing = _load_deps()
    deps = {
        "torch": {"available": torch is not None},
        "gsplat": {"available": rasterization is not None},
    }
    if torch is not None:
        deps["torch"]["version"] = getattr(torch, "__version__", "")
        deps["torch"]["cuda_available"] = bool(torch.cuda.is_available())
    payload = {
        "ok": missing is None,
        "status": "ok" if missing is None else "missing",
        "dependencies": deps,
    }
    if missing is not None:
        payload["error"] = f"missing GPU dependency ({missing})"
        payload["hint"] = _dep_hint()
    return payload


dev = "cuda"
W, H = 320, 240
N_GAUSS = 1200
N_VIEWS = 24
FOCAL = 350.0

# corruption regimes: (expo_lo, expo_span, wb_halfspan, vignette)
REGIMES = {
    "strong": (0.7, 0.7, 0.1, 0.35),
    "realistic": (0.9, 0.2, 0.03, 0.15),
    "control": (1.0, 0.0, 0.0, 0.0),
}


def orbit_poses(n, radius=3.2, height=0.0, center=(0, 0, 0)):
    mats = []
    for i in range(n):
        a = 2 * math.pi * i / n
        cx, cy, cz = center
        eye = torch.tensor([cx + radius * math.cos(a), cy + height,
                            cz + radius * math.sin(a)])
        fwd = torch.tensor([cx, cy, cz]) - eye
        fwd = fwd / fwd.norm()
        up = torch.tensor([0., 1., 0.])
        right = torch.cross(fwd, up)
        right = right / right.norm()
        up2 = torch.cross(right, fwd)
        rot = torch.stack([right, up2, -fwd], dim=0)
        m = torch.eye(4)
        m[:3, :3] = rot
        m[:3, 3] = eye
        mats.append(m)
    return torch.stack(mats)


def lookat_inv(c2w):
    rot = c2w[:3, :3].T
    t = -rot @ c2w[:3, 3]
    m = torch.eye(4)
    m[:3, :3] = rot
    m[:3, 3] = t
    return m


def intrinsic():
    return torch.tensor([[FOCAL, 0, W / 2.], [0., FOCAL, H / 2.],
                         [0., 0., 1.]])


def render(params, viewmats, K):
    means, quats, scales, opacities, colors = params
    quats = torch.nn.functional.normalize(quats, dim=-1)
    K = K.expand(viewmats.shape[0], -1, -1)
    out, _, _ = rasterization(
        means=means, quats=quats, scales=torch.exp(scales),
        opacities=torch.sigmoid(opacities), colors=colors,
        viewmats=viewmats, Ks=K, width=W, height=H,
        sh_degree=None, packed=False)
    return out  # [C, H, W, 3]


def make_gt_scene():
    means = (torch.rand(N_GAUSS, 3, device=dev) - 0.5) * 1.6
    quats = torch.randn(N_GAUSS, 4, device=dev)
    quats = quats / quats.norm(dim=-1, keepdim=True)
    scales = torch.log(torch.rand(N_GAUSS, 3, device=dev) * 0.10 + 0.06)
    opacities = torch.logit(torch.rand(N_GAUSS, device=dev) * 0.6 + 0.4)
    colors = torch.rand(N_GAUSS, 3, device=dev)
    return means, quats, scales, opacities, colors


def corrupt(clean, expo_gain, wb_shift, vig_strength):
    """clean [H,W,3] in [0,1] -> corrupted frame. Vignette radial falloff."""
    img = clean.clone() * expo_gain
    img[..., 0] = img[..., 0] * (1.0 + wb_shift)
    img[..., 2] = img[..., 2] * (1.0 - wb_shift)
    ys, xs = torch.meshgrid(torch.linspace(-1, 1, H, device=dev),
                            torch.linspace(-1, 1, W, device=dev),
                            indexing="ij")
    r2 = xs ** 2 + ys ** 2
    vig = 1.0 - vig_strength * r2
    img = img * vig.unsqueeze(-1)
    return torch.clamp(img, 0.0, 1.0)


def pixel_grid():
    ys, xs = torch.meshgrid(
        torch.arange(H, device=dev, dtype=torch.float32),
        torch.arange(W, device=dev, dtype=torch.float32),
        indexing="ij")
    return torch.stack([xs, ys], dim=-1).contiguous()


def train_arm(with_ppisp, init_params, viewmats, K, targets, steps):
    means = torch.nn.Parameter(init_params[0].clone())
    quats = torch.nn.Parameter(init_params[1].clone())
    scales = torch.nn.Parameter(init_params[2].clone())
    opacities = torch.nn.Parameter(init_params[3].clone())
    colors = torch.nn.Parameter(init_params[4].clone())
    opt = torch.optim.Adam([
        {"params": means, "lr": 0.008},
        {"params": quats, "lr": 0.005},
        {"params": scales, "lr": 0.005},
        {"params": opacities, "lr": 0.02},
        {"params": colors, "lr": 0.01},
    ])
    ppisp = None
    ppisp_opts = []
    ppisp_scheds = []
    if with_ppisp:
        from ppisp import PPISP
        ppisp = PPISP(num_cameras=1, num_frames=N_VIEWS)
        ppisp_opts = ppisp.create_optimizers()
        ppisp_scheds = ppisp.create_schedulers(ppisp_opts, steps)
    coords = pixel_grid()
    freeze_step = int(0.8 * steps)
    order = torch.randperm(N_VIEWS).tolist()
    for step in range(steps):
        vi = order[step % N_VIEWS]
        if step % N_VIEWS == 0:
            order = torch.randperm(N_VIEWS).tolist()
        rgb = render((means, quats, scales, opacities, colors),
                     viewmats[vi:vi + 1], K)[0]
        if with_ppisp:
            rgb = ppisp(rgb, coords, resolution=(W, H),
                        camera_idx=0, frame_idx=vi)
        tgt = targets[vi]
        loss = torch.nn.functional.l1_loss(rgb, tgt) + \
            ((rgb - tgt) ** 2).mean()
        if with_ppisp:
            loss = loss + ppisp.get_regularization_loss()
        opt.zero_grad(set_to_none=True)
        for o in ppisp_opts:
            o.zero_grad(set_to_none=True)
        loss.backward()
        if not (with_ppisp and step >= freeze_step):
            opt.step()
        for o in ppisp_opts:
            o.step()
        for s in ppisp_scheds:
            s.step()
    params = (means.detach(), quats.detach(), scales.detach(),
              opacities.detach(), colors.detach())
    return params, ppisp


def psnr(a, b):
    mse = ((a - b) ** 2).mean().item()
    return -10.0 * math.log10(max(mse, 1e-9))


def main():
    ap = argparse.ArgumentParser(description="synthetic ppisp held-out harness")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--init-seed", type=int, default=123)
    ap.add_argument("--regime", choices=sorted(REGIMES), default="strong")
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--out", default="synth_ppisp_result.json")
    ap.add_argument("--doctor", action="store_true",
                    help="print dependency status as JSON and exit")
    args = ap.parse_args()
    if args.doctor:
        payload = doctor()
        print(_dumps(payload, indent=1))
        sys.exit(0 if payload["ok"] else 1)
    missing = _load_deps()
    if missing is not None:
        print(_dumps({
            "ok": False,
            "status": "missing",
            "error": f"missing GPU dependency ({missing})",
            "hint": _dep_hint(),
        }, indent=1))
        sys.exit(1)
    steps = args.steps
    torch.manual_seed(args.seed)
    gt = make_gt_scene()
    K = intrinsic().to(dev).unsqueeze(0)
    c2w_train = orbit_poses(N_VIEWS, radius=3.2)
    viewmats = torch.stack([lookat_inv(m) for m in c2w_train]).to(dev)
    clean = render(gt, viewmats, K)  # [C,H,W,3]

    torch.manual_seed(7)
    expo_lo, expo_span, wb_half, vig = REGIMES[args.regime]
    expo_gains = torch.rand(N_VIEWS, device=dev) * expo_span + expo_lo
    wb_shifts = (torch.rand(N_VIEWS, device=dev) - 0.5) * 2 * wb_half
    targets = torch.stack([
        corrupt(clean[i], float(expo_gains[i]), float(wb_shifts[i]), vig)
        for i in range(N_VIEWS)])

    torch.manual_seed(args.init_seed)
    init = (
        (torch.rand(N_GAUSS, 3, device=dev) - 0.5) * 1.8,
        torch.nn.functional.normalize(torch.randn(N_GAUSS, 4, device=dev), dim=-1),
        torch.log(torch.rand(N_GAUSS, 3, device=dev) * 0.05 + 0.01),
        torch.logit(torch.rand(N_GAUSS, device=dev) * 0.2 + 0.1),
        torch.rand(N_GAUSS, 3, device=dev) * 0.4 + 0.3,
    )

    print("training baseline...", flush=True)
    base, _ = train_arm(False, init, viewmats, K, targets, steps)
    print("training ppisp arm...", flush=True)
    arm, ppisp_mod = train_arm(True, init, viewmats, K, targets, steps)

    # held-out: novel orbit (different radius + height), compare to CLEAN gt
    c2w_novel = orbit_poses(8, radius=3.8, height=0.6)
    vm_novel = torch.stack([lookat_inv(m) for m in c2w_novel]).to(dev)
    gt_novel = render(gt, vm_novel, K)
    base_novel = render(base, vm_novel, K)
    arm_novel = render(arm, vm_novel, K)

    coords = pixel_grid()
    corrected = torch.stack([
        ppisp_mod(arm_novel[i], coords, resolution=(W, H),
                  camera_idx=0, frame_idx=-1).clamp(0.0, 1.0)
        for i in range(arm_novel.shape[0])])

    res = {
        "ok": True,
        "status": "ok",
        "baseline_novel_psnr": round(psnr(base_novel, gt_novel), 3),
        "ppisp_raw_novel_psnr": round(psnr(arm_novel, gt_novel), 3),
        "ppisp_corrected_novel_psnr": round(psnr(corrected, gt_novel), 3),
    }
    res["delta_raw_db"] = round(res["ppisp_raw_novel_psnr"]
                                - res["baseline_novel_psnr"], 3)
    res["delta_corrected_db"] = round(res["ppisp_corrected_novel_psnr"]
                                      - res["baseline_novel_psnr"], 3)
    res["gate_pass"] = bool(res["delta_corrected_db"] >= 2.0)
    res["protocol"] = {
        "n_gauss": N_GAUSS, "n_views": N_VIEWS, "steps": steps,
        "protocol_v": 3, "regime": args.regime,
        "seed": args.seed, "init_seed": args.init_seed,
        "corruption": f"regime={args.regime}",
        "heldout": "novel orbit radius 3.8 height 0.6 vs training 3.2/0.0",
    }
    print(_dumps(res, indent=1))
    import os
    if os.path.exists(args.out):
        print(f"refusing to overwrite existing file: {args.out}", file=sys.stderr)
        sys.exit(2)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
