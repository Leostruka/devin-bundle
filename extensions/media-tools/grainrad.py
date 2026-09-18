#!/usr/bin/env python3
"""grainrad — unified effects CLI (parity with grainrad.com pipeline).

Pipeline: input -> adjust -> process -> effect -> postprocess -> export.
Prints JSON to stdout: {"ok": true, "path": ...} or {"ok": false, "error": ...}.

Params: --param k=v repeatable. Bare keys go to the effect; prefix with
adjust./process./bloom./grain./chromatic./scanlines./vignette. for pipeline stages.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx
from fx.pipeline import adjust, process, postprocess


def _coerce(v):
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    return v


def _parse_params(pairs):
    eff, adj, proc, post = {}, {}, {}, {}
    for p in pairs or []:
        k, _, v = p.partition("=")
        val = _coerce(v)
        for prefix, target in (("adjust.", adj), ("process.", proc)):
            if k.startswith(prefix):
                target[k[len(prefix):]] = val
                break
        else:
            for stage in ("bloom", "grain", "chromatic", "scanlines", "vignette"):
                if k.startswith(stage + "."):
                    post.setdefault(stage, {})[k[len(stage) + 1:]] = val
                    break
                if k == stage:
                    post.setdefault(stage, {})
                    break
            else:
                eff[k] = val
    return eff, adj, proc, post


def run(img, effect, eff_params, adj_params, proc_params, post_params, fmt=None):
    out = adjust(img, **adj_params) if adj_params else img.convert("RGB")
    if proc_params:
        out = process(out, **proc_params)
    out = fx.apply(effect, out, eff_params)
    if post_params:
        out = postprocess(out, **post_params)
    return out


def main():
    p = argparse.ArgumentParser(description="grainrad effects CLI")
    p.add_argument("--input")
    p.add_argument("--output")
    p.add_argument("--effect", default="ascii")
    p.add_argument("--format", default=None, choices=["png", "jpeg", "svg", "txt"])
    p.add_argument("--preset")
    p.add_argument("--param", action="append", default=[])
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--list-effects", action="store_true")
    p.add_argument("--list-presets", action="store_true")
    args = p.parse_args()
    try:
        if args.list_effects:
            print(json.dumps({"ok": True, "effects": sorted(fx.EFFECTS)}))
            return 0
        if args.list_presets:
            from presets import list_presets
            print(json.dumps({"ok": True, "presets": list_presets()}))
            return 0
        eff_params, adj, proc, post = _parse_params(args.param)
        if args.preset:
            from presets import get_preset
            eff_params = {**get_preset(args.preset), **eff_params}
        if args.self_test:
            import numpy as np
            y, x = np.mgrid[0:480, 0:640]
            arr = np.clip(np.exp(-(((x - 320) ** 2 + (y - 240) ** 2) / 2.0 / 140.0**2))
                          + ((x + y) % 80 < 40) * 0.35, 0, 1)
            img = Image.fromarray((arr * 255).astype(np.uint8)).convert("RGB")
            out = args.output or "grainrad_selftest.png"
        else:
            if not args.input or not args.output:
                print(json.dumps({"ok": False, "error": "missing --input/--output (or --self-test)"}))
                return 2
            img = Image.open(args.input)
            out = args.output
        if args.format in ("svg", "txt"):
            if args.effect != "ascii":
                print(json.dumps({"ok": False, "error": f"--format {args.format} requires --effect ascii"}))
                return 2
            from fx.ascii_fx import grid, to_svg, to_text
            gk = {k: eff_params[k] for k in ("scale", "spacing", "out_width", "charset", "custom_chars") if k in eff_params}
            g = grid(img.convert("RGB"), **gk)
            Path(out).write_text(
                to_svg(g, **{k: eff_params[k] for k in ("mode", "fg", "bg") if k in eff_params})
                if args.format == "svg" else to_text(g), encoding="utf-8")
        else:
            result = run(img, args.effect, eff_params, adj, proc, post)
            result.save(out)
        print(json.dumps({"ok": True, "path": out}))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
