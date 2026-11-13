"""mesh-utils: inspect/convert/clean 3D mesh and scene files via
trimesh, PyMeshLab, or OpenUSD (pxr), whichever is installed.

Commands: doctor, info, convert, clean.
All output is JSON on stdout; errors exit 1 with {"ok": false, ...}.
Install hints are emitted per missing dependency; nothing is auto-installed.
"""
import argparse
import importlib
import json
import os
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
    return {"bundle": _bundle_version(), "wrapper": "mesh-utils"}


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



def _out(obj, code=0):
    print(_dumps(obj, indent=2, sort_keys=True))
    sys.exit(code)


def _fail(msg, **extra):
    _out({"ok": False, "error": msg, **extra}, 1)


def _probe(modname):
    try:
        m = importlib.import_module(modname)
        return getattr(m, "__version__", "installed")
    except ImportError:
        return None


INSTALL_HINTS = {
    "trimesh": "pip install trimesh",
    "pymeshlab": "pip install pymeshlab",
    "pxr": "pip install usd-core",
    "open3d": "pip install open3d",
}


def cmd_doctor():
    deps = {m: _probe(m) for m in INSTALL_HINTS}
    _out({"ok": True, "deps": deps,
          "hints": {m: INSTALL_HINTS[m] for m, v in deps.items()
                    if v is None}})


def _load(path):
    """Return (engine, mesh-or-stage). Prefers trimesh, falls back to
    pymeshlab, then pxr for USD formats."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".usd", ".usda", ".usdc", ".usdz"):
        pxr = _probe("pxr")
        if pxr is None:
            _fail("USD file but pxr not installed",
                  hint=INSTALL_HINTS["pxr"])
        from pxr import Usd
        return "pxr", Usd.Stage.Open(path)
    if _probe("trimesh"):
        import trimesh
        return "trimesh", trimesh.load(path, force="mesh")
    if _probe("pymeshlab"):
        import pymeshlab
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(path)
        return "pymeshlab", ms
    _fail("no mesh backend installed",
          hint="pip install trimesh  (or pymeshlab)")


def _info_trimesh(mesh):
    if mesh is None or getattr(mesh, "is_empty", False):
        _fail("empty or unreadable mesh")
    bounds = mesh.bounds.tolist() if mesh.bounds is not None else None
    return {"vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "watertight": bool(mesh.is_watertight),
            "bounds": bounds,
            "extents": mesh.extents.tolist()}


def _info_pymeshlab(ms):
    m = ms.current_mesh()
    return {"vertices": int(m.vertex_number()),
            "faces": int(m.face_number())}


def _info_pxr(stage):
    from pxr import UsdGeom
    prims = [p.GetPath().pathString for p in stage.Traverse()]
    mesh_prims = [p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]
    return {"prims": len(prims), "meshes": len(mesh_prims),
            "up_axis": UsdGeom.GetStageUpAxis(stage),
            "root_paths": prims[:10]}


def cmd_info(path):
    if not os.path.exists(path):
        _fail(f"file not found: {path}")
    engine, obj = _load(path)
    info = {"trimesh": _info_trimesh, "pymeshlab": _info_pymeshlab,
            "pxr": _info_pxr}[engine](obj)
    _out({"ok": True, "file": path, "engine": engine, **info})


def _check_dst(dst):
    if os.path.exists(dst):
        _fail(f"dst exists: {dst} (refusing to overwrite; "
              "pick another path or delete it first)")


def cmd_convert(src, dst):
    if not os.path.exists(src):
        _fail(f"file not found: {src}")
    _check_dst(dst)
    engine, obj = _load(src)
    if engine == "pxr":
        obj.Export(dst)
    elif engine == "trimesh":
        obj.export(dst)
    else:
        obj.save_current_mesh(dst)
    _out({"ok": True, "engine": engine, "in": src, "out": dst})


def cmd_clean(src, dst):
    """Remove unreferenced vertices, merge duplicates, fix normals."""
    if not os.path.exists(src):
        _fail(f"file not found: {src}")
    _check_dst(dst)
    engine, obj = _load(src)
    if engine == "pymeshlab":
        ms = obj
        ms.meshing_remove_unreferenced_vertices()
        ms.meshing_merge_close_vertices()
        ms.meshing_re_orient_faces_coherently()
        ms.save_current_mesh(dst)
    elif engine == "trimesh":
        obj.merge_vertices()
        obj.remove_unreferenced_vertices()
        try:
            obj.fix_normals()
            normals_fixed = True
        except Exception:
            normals_fixed = False  # needs scipy for connected components
        obj.export(dst)
        _out({"ok": True, "engine": engine, "in": src, "out": dst,
              "normals_fixed": normals_fixed})
    else:
        _fail("clean not supported for USD stages; convert first")
    _out({"ok": True, "engine": engine, "in": src, "out": dst})


def main():
    ap = argparse.ArgumentParser(prog="meshops")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    p = sub.add_parser("info")
    p.add_argument("file")
    p = sub.add_parser("convert")
    p.add_argument("src")
    p.add_argument("dst")
    p = sub.add_parser("clean")
    p.add_argument("src")
    p.add_argument("dst")
    a = ap.parse_args()

    {"doctor": cmd_doctor,
     "info": lambda: cmd_info(a.file),
     "convert": lambda: cmd_convert(a.src, a.dst),
     "clean": lambda: cmd_clean(a.src, a.dst)}[a.cmd]()


if __name__ == "__main__":
    main()
