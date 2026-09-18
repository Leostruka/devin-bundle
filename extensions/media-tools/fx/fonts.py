from PIL import ImageFont

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
