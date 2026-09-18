"""media-tools effects package — grainrad parity."""

from . import ascii_fx

EFFECTS = {
    "ascii": ascii_fx.apply,
}


def apply(name, img, params):
    return EFFECTS[name](img, **params)
