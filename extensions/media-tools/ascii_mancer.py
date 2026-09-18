#!/usr/bin/env python3
"""ascii_mancer — merged ASCII art generator (Detailed + Blocks, screen blend).

Pipeline: image -> grayscale -> dense ASCII layer + block ASCII layer ->
screen blend f(A,B) = 1 - (1-A)*(1-B) -> PNG.

CLI prints JSON to stdout: {"ok": true, "path": ...} or {"ok": false, "error": ...}.
"""
import argparse
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

DETAILED_CHARS = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
BLOCK_CHARS = " ░▒▓█"

FONT_CANDIDATES = ["consola.ttf", "Consolas.ttf", "cour.ttf", "Courier New.ttf", "courbd.ttf"]


def load_font(cell):
    """Font sized so glyph advance ~= cell px (dense tiling like grainrad)."""
    probe = "MW@"
    for name in FONT_CANDIDATES:
        try:
            size = cell * 2
            font = ImageFont.truetype(name, size)
            adv = font.getlength(probe) / len(probe)
            if adv > 0:
                return ImageFont.truetype(name, max(1, round(size * cell * 1.05 / adv)))
            return font
        except OSError:
            continue
    try:
        return ImageFont.load_default(cell)
    except TypeError:
        return ImageFont.load_default()


def render_layer(gray, charset, cell, font):
    """Render one ASCII layer as a float array in [0,1] (white glyphs on black)."""
    h, w = gray.shape
    cols = max(1, w // cell)
    rows = max(1, h // cell)
    small = Image.fromarray((gray * 255).astype(np.uint8)).resize(
        (cols, rows), Image.BILINEAR
    )
    lum = np.asarray(small, dtype=np.float32) / 255.0
    idx = (lum * (len(charset) - 1)).astype(np.int32)
    img = Image.new("L", (cols * cell, rows * cell), 0)
    draw = ImageDraw.Draw(img)
    for r in range(rows):
        y = r * cell
        for c in range(cols):
            draw.text((c * cell, y), charset[idx[r, c]], fill=255, font=font)
    return np.asarray(img, dtype=np.float32) / 255.0


def screen(a, b):
    return 1.0 - (1.0 - a) * (1.0 - b)


def mance(src, out_path, cell_detail=8, cell_block=16):
    gray = np.asarray(src.convert("L"), dtype=np.float32) / 255.0
    detailed = render_layer(gray, DETAILED_CHARS, cell_detail, load_font(cell_detail))
    blocks = render_layer(gray, BLOCK_CHARS, cell_block, load_font(cell_block))
    h = min(detailed.shape[0], blocks.shape[0])
    w = min(detailed.shape[1], blocks.shape[1])
    merged = screen(detailed[:h, :w], blocks[:h, :w])
    Image.fromarray((merged * 255).astype(np.uint8)).save(out_path)
    return out_path


def self_test(out_path):
    y, x = np.mgrid[0:480, 0:640]
    grad = np.exp(-(((x - 320) ** 2 + (y - 240) ** 2) / 2.0 / 140.0**2))
    diag = ((x + y) % 80 < 40).astype(np.float32) * 0.35
    arr = np.clip(grad + diag, 0, 1)
    img = Image.fromarray((arr * 255).astype(np.uint8))
    mance(img, out_path)
    with Image.open(out_path) as chk:
        chk.verify()


def main():
    p = argparse.ArgumentParser(description="Merged ASCII art generator (screen blend).")
    p.add_argument("--input", help="Input image path")
    p.add_argument("--output", help="Output PNG path")
    p.add_argument("--self-test", action="store_true", help="Run synthetic self-test")
    p.add_argument("--cell-detail", type=int, default=8)
    p.add_argument("--cell-block", type=int, default=16)
    args = p.parse_args()
    try:
        if args.self_test:
            out = args.output or "ascii_mancer_selftest.png"
            self_test(out)
            print(json.dumps({"ok": True, "path": out}))
            return 0
        if not args.input or not args.output:
            print(json.dumps({"ok": False, "error": "missing --input/--output (or --self-test)"}))
            return 2
        with Image.open(args.input) as src:
            mance(src, args.output, args.cell_detail, args.cell_block)
        print(json.dumps({"ok": True, "path": args.output}))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
