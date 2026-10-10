"""scene_manifest — cross-engine scene/timeline spec -> craft commands.

Our contract (schema v1), consumed by the craft suite via bridge.py and
by animation-direction (Issue 04, which adds motion_spec + sync_range):

{
  "version": 1,
  "scenes": [
    {"id": "s1", "duration_s": 5.0,
     "layers": [
       {"type": "video", "source": "a.mp4",
        "ops": [{"op": "cut", "params": {"at_s": 2.0}}]},
       {"type": "image", "source": "b.psd",
        "ops": [{"op": "export", "params": {"format": "png"}}]}
     ]}
  ]
}

compile() routes each layer to its engine (layer.type -> app) and each
op through OPS_MAP (logical op -> app command_id). Ops absent from
OPS_MAP pass through verbatim with an `unverified` note — the app's own
registry is the authority; run `bridge.py commands <app>` to confirm a
command_id before dispatch.
"""
from __future__ import annotations

import json
from pathlib import Path

LAYER_DOMAIN = {
    "video": "filmcraft", "audio": "soundcraft",
    "image": "photocraft", "photo": "lightcraft",
    "vector": "vectorcraft", "cad": "cadcraft",
    "doc": "wordcraft", "sheet": "gridcraft",
    "slide": "deckcraft", "pdf": "pdfcraft",
}

# Logical op -> (app-agnostic) engine command id. Values are the craft
# registry ids where verified; entries here are our seam vocabulary.
OPS_MAP_PATH = Path(__file__).with_name("ops_map.json")
_DEFAULT_OPS = {
    "cut": "timeline.cut",
    "trim": "timeline.trim",
    "grade": "color.grade",
    "mix": "audio.mix",
    "export": "file.export",
    "open": "file.open",
    "save": "file.save",
    "text": "text.insert",
    "layer": "layer.add",
    "render": "render.frame",
}


def load_ops_map(path=None):
    p = Path(path) if path else OPS_MAP_PATH
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return dict(_DEFAULT_OPS)


def compile(manifest, ops_map=None):
    """Manifest -> ordered plan of engine calls.

    Returns {"ok", "plan": [{scene, layer, app, command, params,
    source}], "notes": [...]}. Never dispatches — bridge.run_command
    does that per plan step.
    """
    ops_map = ops_map or load_ops_map()
    if manifest.get("version") != 1:
        return {"ok": False, "error": "manifest version must be 1"}
    plan, notes = [], []
    for scene in manifest.get("scenes", []):
        for li, layer in enumerate(scene.get("layers", [])):
            ltype = layer.get("type")
            app = LAYER_DOMAIN.get(ltype)
            if app is None:
                notes.append(f"unrouted_layer_type:{ltype} "
                             f"(scene {scene.get('id')} layer {li})")
                continue
            ops = layer.get("ops") or [{"op": "open", "params": {}}]
            for oi, op in enumerate(ops):
                name = op.get("op")
                cmd = ops_map.get(name, name)
                step = {"scene": scene.get("id"), "layer": li,
                        "order": len(plan), "app": app,
                        "command": cmd, "params": op.get("params", {}),
                        "source": layer.get("source")}
                if name not in ops_map:
                    step["unverified"] = True
                    notes.append(f"unverified_op:{name}->{cmd} on {app} "
                                 "confirm via `bridge.py commands`")
                plan.append(step)
    return {"ok": True, "plan": plan, "notes": notes}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="scene manifest compiler")
    ap.add_argument("manifest")
    args = ap.parse_args(argv)
    m = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    print(json.dumps(compile(m), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
