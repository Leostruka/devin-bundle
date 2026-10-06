# Install guide: free 3D stack

Stack recommended by the research (`.devin/research/3d-tools-comparison.md`),
self-contained and free: **Blender + ComfyUI-3D-Pack + OpenUSD +
trimesh/PyMeshLab + Godot**.

Status legend:
`[OK]` installed and tested | `[GPU]` requires NVIDIA/CUDA | `[USER]` manual step pending.

In the commands below, `<comfyui-dir>` is the directory where you clone
ComfyUI (any local folder of your choice).

## Component checklist

| Component | Typical state | Notes |
|---|---|---|
| Blender | [OK] | Install via winget or blender.org; any recent LTS works |
| ComfyUI (server) | [OK] CPU / [GPU] | Works CPU-only; GPU build preferred when NVIDIA exists |
| ComfyUI-3D-Pack (nodes) | [GPU] | Fails to import without CUDA; ComfyUI 2D still works |
| trimesh | [OK] | `pip install trimesh` |
| pymeshlab | [OK] | `pip install pymeshlab` |
| usd-core (`pxr`) | [OK] | `pip install usd-core` |
| open3d | [USER] | optional, `pip install open3d` |
| Godot | [OK] | Install via winget or godotengine.org; needs `godot` on PATH |
| scipy | [USER] | optional; enables `fix_normals` in meshops (`pip install scipy`) |
| model checkpoints | [USER] | need disk space (5-15GB each) and a GPU for practical use |

## 1. Blender

```powershell
winget install BlenderFoundation.Blender
# or https://www.blender.org/download/
```

Verify:

```bash
python extensions/blender-operator/wrapper.py --self-test
python extensions/blender-operator/wrapper.py launch
python extensions/blender-operator/wrapper.py exec "bpy.app.version_string"
python extensions/blender-operator/wrapper.py kill
```

Without a GPU: Cycles runs on CPU (slow); EEVEE needs a GPU with OpenGL.
On integrated graphics prefer `BLENDER_WORKBENCH` or Cycles
with few samples for verification.

## 2. ComfyUI + ComfyUI-3D-Pack

### ComfyUI server

```bash
git clone https://github.com/comfyanonymous/ComfyUI <comfyui-dir>
cd <comfyui-dir> && python -m venv .venv

# CPU-only:
./.venv/Scripts/python.exe -m pip install torch torchvision \
  --index-url https://download.pytorch.org/whl/cpu
# With NVIDIA: swap the index for .../whl/cu124 and use the GPU torch build.
# (On Linux/macOS the venv python is at ./.venv/bin/python.)

./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe main.py --cpu --port 8188   # --cpu only without a GPU
```

Verify:

```bash
python extensions/comfyui-operator/wrapper.py status
```

### ComfyUI-3D-Pack

```bash
git clone https://github.com/MrForExample/ComfyUI-3D-Pack \
  <comfyui-dir>/custom_nodes/ComfyUI-3D-Pack
cd <comfyui-dir> && ./.venv/Scripts/python.exe -m pip install \
  -r custom_nodes/ComfyUI-3D-Pack/requirements.txt
```

**Hard requirement: NVIDIA GPU + CUDA toolkit (nvcc).** The pack imports
`nvdiffrast`, `spconv-cu126`, `nerfacc`, `slangtorch` and gaussian-splat
rasterization, all CUDA-only with no CPU wheel. Without an NVIDIA GPU the
pack shows as `IMPORT FAILED` in the log; ComfyUI keeps working
for 2D workflows.

On a machine WITH a GPU: install the full requirements; `nvdiffrast` comes
from git (`git+https://github.com/NVlabs/nvdiffrast.git`) and compiles with
nvcc.

Without a GPU but wanting to generate 3D: use the model repos directly
(TRELLIS, TripoSG, InstantMesh) - some run slowly on CPU - or
a GPU machine/cloud. See `skills/ai3d-gen/SKILL.md`.

### Model checkpoints

Workflows need weights under `<comfyui-dir>/models/` (hunyuan3d,
trellis, etc.). Download from Hugging Face per the `ai3d-gen` skill.
Each model takes 5-15GB; on low-disk machines use an external drive
and point `--extra-model-paths-config` or a symlink at it.

## 3. Mesh libraries (mesh-utils)

```bash
pip install trimesh pymeshlab usd-core
# optional:
pip install scipy   # enables fix_normals (connected components)
pip install open3d  # point clouds and advanced analysis
```

Verify:

```bash
python extensions/mesh-utils/meshops.py doctor
python -c "import trimesh; trimesh.creation.icosphere().export('t.obj')"
python extensions/mesh-utils/meshops.py info t.obj
python extensions/mesh-utils/meshops.py convert t.obj t.glb
python extensions/mesh-utils/meshops.py clean t.obj t_clean.obj
```

## 4. Godot

```powershell
winget install GodotEngine.GodotEngine
```

Verify:

```bash
godot --version
godot --headless --path <proj> --check-only --script tool.gd
```

`godot_console` is also installed (shows stdout on Windows).

## 5. Full verification order (smoke)

```bash
python extensions/mesh-utils/meshops.py doctor            # python deps
python extensions/comfyui-operator/wrapper.py status      # server up?
python extensions/blender-operator/wrapper.py --self-test # blender
godot --version                                           # godot
```

## Known limits to check on your machine

- No NVIDIA: 3D-Pack unavailable; ComfyUI 2D and Blender run on CPU.
- Disk space: model checkpoints need 5-15GB each; plan a volume with room.
- RAM: large 3D models (Hunyuan3D-2 is ~6GB) are tight on CPU
  with 16GB or less.
