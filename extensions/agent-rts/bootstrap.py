#!/usr/bin/env python3
"""bootstrap - one-time setup for extensions/agent-rts.

Creates .venv next to this script and fetches the pinned Three.js vendor
files into web/vendor/ (skipped when already present or --offline).
The server itself is stdlib-only; the venv exists for optional extras
listed in requirements.txt.

  bootstrap.py [--offline] [--no-venv]
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
THREE_VER = "0.160.0"
CDN = "https://unpkg.com/three@" + THREE_VER
# path inside the npm package -> path under web/vendor/
VENDOR_FILES = {
    "build/three.module.js": "three.module.js",
    "examples/jsm/loaders/GLTFLoader.js": "jsm/loaders/GLTFLoader.js",
    "examples/jsm/postprocessing/Pass.js": "jsm/postprocessing/Pass.js",
    "examples/jsm/postprocessing/EffectComposer.js":
        "jsm/postprocessing/EffectComposer.js",
    "examples/jsm/postprocessing/RenderPass.js":
        "jsm/postprocessing/RenderPass.js",
    "examples/jsm/postprocessing/ShaderPass.js":
        "jsm/postprocessing/ShaderPass.js",
    "examples/jsm/postprocessing/MaskPass.js":
        "jsm/postprocessing/MaskPass.js",
    "examples/jsm/postprocessing/OutputPass.js":
        "jsm/postprocessing/OutputPass.js",
    "examples/jsm/postprocessing/SSAOPass.js":
        "jsm/postprocessing/SSAOPass.js",
    "examples/jsm/shaders/CopyShader.js": "jsm/shaders/CopyShader.js",
    "examples/jsm/shaders/SSAOShader.js": "jsm/shaders/SSAOShader.js",
    "examples/jsm/shaders/OutputShader.js": "jsm/shaders/OutputShader.js",
    "examples/jsm/math/SimplexNoise.js": "jsm/math/SimplexNoise.js",
    "examples/jsm/utils/BufferGeometryUtils.js":
        "jsm/utils/BufferGeometryUtils.js",
}


def make_venv():
    venv = os.path.join(HERE, ".venv")
    if os.path.isdir(venv):
        print("venv: exists")
        return
    subprocess.check_call([sys.executable, "-m", "venv", venv])
    print("venv: created at " + venv)


def fetch(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "agent-rts"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    with open(dest, "wb") as f:
        f.write(data)
    return len(data)


def vendor(offline):
    vdir = os.path.join(HERE, "web", "vendor")
    marker = os.path.join(vdir, "VERSION.json")
    if os.path.isfile(marker):
        try:
            with open(marker, encoding="utf-8") as f:
                if json.load(f).get("three") == THREE_VER:
                    print("vendor: three.js " + THREE_VER + " already present")
                    return
        except Exception:
            pass
    if offline:
        print("vendor: --offline, skipped (web client needs vendor files)")
        return
    got = {}
    for src, dst in VENDOR_FILES.items():
        out = os.path.join(vdir, dst)
        if os.path.isfile(out):
            continue
        try:
            n = fetch(CDN + "/" + src, out)
            got[dst] = n
            print("vendor: %s (%d bytes)" % (dst, n))
        except Exception as e:
            print("vendor: FAILED %s: %s" % (src, e))
    os.makedirs(vdir, exist_ok=True)
    with open(marker, "w", encoding="utf-8") as f:
        json.dump({"three": THREE_VER, "files": got}, f, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--no-venv", action="store_true")
    args = ap.parse_args()
    if not args.no_venv:
        make_venv()
    vendor(args.offline)
    print("bootstrap done. Run: python extensions/agent-rts/server.py")


if __name__ == "__main__":
    main()
