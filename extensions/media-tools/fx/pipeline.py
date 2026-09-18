"""Pipeline stages — grainrad parity: adjust -> process -> effect -> postprocess -> export."""
import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps


def adjust(img, brightness=0, contrast=0, saturation=0, hue=0, sharpness=0, gamma=1.0):
    """Site ranges: b/c/s -100..100, hue 0..360, sharpness -1..1, gamma .5..2."""
    out = img.convert("RGB")
    if brightness:
        out = ImageEnhance.Brightness(out).enhance(1 + brightness / 100)
    if contrast:
        out = ImageEnhance.Contrast(out).enhance(1 + contrast / 100)
    if saturation:
        out = ImageEnhance.Color(out).enhance(1 + saturation / 100)
    if hue:
        hsv = np.asarray(out.convert("HSV"), dtype=np.uint8).copy()
        hsv[..., 0] = (hsv[..., 0].astype(np.int32) + round(hue * 255 / 360)) % 256
        out = Image.fromarray(hsv, "HSV").convert("RGB")
    if sharpness:
        out = ImageEnhance.Sharpness(out).enhance(1 + sharpness)
    if gamma != 1.0:
        lut = [min(255, round((i / 255) ** (1 / gamma) * 255)) for i in range(256)]
        out = out.point(lut * 3)
    return out


def process(img, invert=False, brightness_map=1.0, edge_enhance=0, blur=0.0,
            quantize=0, shape_match=0.0):
    """Site 'Processing' section."""
    out = img.convert("RGB")
    if invert:
        out = ImageOps.invert(out)
    if brightness_map != 1.0:
        out = ImageEnhance.Brightness(out).enhance(brightness_map)
    if blur > 0:
        out = out.filter(ImageFilter.GaussianBlur(blur * 4))
    if quantize > 0:
        out = out.quantize(colors=max(2, int(quantize))).convert("RGB")
    if edge_enhance > 0:
        edges = out.filter(ImageFilter.FIND_EDGES)
        out = Image.blend(out, ImageChops.add(out, edges), min(1.0, edge_enhance))
    if shape_match > 0:
        # edge-preserving smooth approximation (site uses shape matching)
        smooth = out.filter(ImageFilter.SMOOTH_MORE)
        out = Image.blend(out, smooth, min(1.0, shape_match))
    return out


def postprocess(img, bloom=None, grain=None, chromatic=None, scanlines=None,
                vignette=None, seed=0):
    """Each arg None or dict of params. bloom: threshold/soft/intensity/radius;
    grain: intensity/size/speed; chromatic: offset(px); scanlines: opacity/spacing;
    vignette: intensity."""
    out = img.convert("RGB")
    w, h = out.size
    if bloom:
        t = bloom.get("threshold", 0.7)
        soft = bloom.get("soft", 0.2)
        amt = bloom.get("intensity", 1.0)
        rad = bloom.get("radius", 8)
        gray = np.asarray(out.convert("L"), dtype=np.float32) / 255.0
        mask = np.clip((gray - t) / max(soft, 1e-3), 0, 1)
        glow = np.asarray(out, dtype=np.float32) * mask[..., None]
        glow = Image.fromarray(glow.astype(np.uint8)).filter(ImageFilter.GaussianBlur(rad))
        out = ImageChops.screen(out, ImageEnhance.Brightness(glow).enhance(amt))
    if grain:
        rng = np.random.default_rng(seed)
        size = max(1, int(grain.get("size", 1)))
        noise = rng.normal(0, grain.get("intensity", 0.2) * 60,
                           (h // size, w // size)).astype(np.float32)
        noise = np.asarray(Image.fromarray(noise).resize((w, h), Image.BILINEAR))
        arr = np.asarray(out, dtype=np.float32) + noise[..., None]
        out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if chromatic:
        off = int(chromatic.get("offset", 2))
        r, g, b = out.split()
        r = ImageChops.offset(r, off, 0)
        b = ImageChops.offset(b, -off, 0)
        out = Image.merge("RGB", (r, g, b))
    if scanlines:
        sp = max(2, int(scanlines.get("spacing", 3)))
        op = scanlines.get("opacity", 0.3)
        arr = np.asarray(out, dtype=np.float32)
        arr[::sp] *= 1 - op
        out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if vignette:
        strength = vignette.get("intensity", 0.5)
        y, x = np.mgrid[0:h, 0:w]
        d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
        mask = np.clip(1 - strength * np.clip(d - 0.5, 0, 1) ** 2 * 2, 0, 1)
        out = Image.fromarray((np.asarray(out, dtype=np.float32) * mask[..., None]).astype(np.uint8))
    return out
