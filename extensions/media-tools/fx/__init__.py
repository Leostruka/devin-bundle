"""media-tools effects package — grainrad parity."""

from . import (ascii_fx, blockify, contour, crosshatch, dithering, dots,
               edge_detection, halftone, threshold)

EFFECTS = {
    "ascii": ascii_fx.apply,
    "threshold": threshold.apply,
    "blockify": blockify.apply,
    "dots": dots.apply,
    "contour": contour.apply,
    "edgeDetection": edge_detection.apply,
    "dithering": dithering.apply,
    "halftone": halftone.apply,
    "crosshatch": crosshatch.apply,
}


def apply(name, img, params):
    return EFFECTS[name](img, **params)
