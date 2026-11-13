"""metadata — first-pass provenance report: EXIF/XMP/C2PA.

Fast signal only. Presence of camera EXIF or a C2PA manifest is
evidence; absence is NOT evidence of synthesis — metadata dies on
screenshot and re-upload while pixel noise survives.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

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
    return {"bundle": _bundle_version(), "wrapper": "image-forensics"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    return json.dumps(_stamp(payload), **kw)




def report(path):
    """Return {has_exif, camera_make, camera_model, software,
    has_xmp, c2pa_manifest, flags}."""
    from PIL import Image
    out = {"has_exif": False, "camera_make": None, "camera_model": None,
           "software": None, "has_xmp": False, "c2pa_manifest": False,
           "flags": []}
    p = Path(path)
    try:
        with Image.open(p) as im:
            exif = im.getexif()
            if exif:
                out["has_exif"] = True
                out["camera_make"] = exif.get(271)
                out["camera_model"] = exif.get(272)
                out["software"] = exif.get(305)
            info = im.info or {}
            out["has_xmp"] = any("xmp" in str(k).lower() for k in info) \
                or "XML:com.adobe.xmp" in info
            app = info.get("XML:com.adobe.xmp") or ""
            if isinstance(app, bytes):
                app = app.decode("utf-8", "ignore")
            if "c2pa" in app.lower():
                out["c2pa_manifest"] = True
    except Exception as e:  # unreadable file -> flags carry the note
        out["flags"].append(f"unreadable:{type(e).__name__}")
        return out
    try:
        head = p.read_bytes()[:262144]
        if b"c2pa" in head or b"urn:c2pa" in head:
            out["c2pa_manifest"] = True
        low = head.lower()
        if b"photoshop" in low or b"dall-e" in low \
                or b"midjourney" in low:
            out["flags"].append("generator_string_in_container")
    except OSError:
        pass
    if out["software"] and any(
            s in str(out["software"]).lower()
            for s in ("stable diffusion", "dall-e", "midjourney",
                      "firefly", "leonardo")):
        out["flags"].append("generator_software_tag")
    if not out["has_exif"]:
        out["flags"].append("no_exif")
    return out


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print(_dumps({"ok": False,
                          "error": "usage: metadata.py <image>"}))
        raise SystemExit(2)
    print(_dumps(report(sys.argv[1]), ensure_ascii=False, indent=2))
