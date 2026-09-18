"""media-tools effects package — grainrad parity."""

from . import (ascii_fx, blockify, contour, crosshatch, dithering, dots,
               edge_detection, halftone, noise_field, pixel_sort, threshold,
               voronoi, wave_lines)

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
    "pixelSort": pixel_sort.apply,
    "waveLines": wave_lines.apply,
    "noiseField": noise_field.apply,
    "voronoi": voronoi.apply,
}


def apply(name, img, params):
    return EFFECTS[name](img, **params)
