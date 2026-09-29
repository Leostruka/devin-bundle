# Manual de instalação: stack 3D gratuita

Stack recomendada pela pesquisa (`.devin/research/3d-tools-comparison.md`),
autocontida e gratuita: **Blender + ComfyUI-3D-Pack + OpenUSD +
trimesh/PyMeshLab + Godot**.

Legenda de status nesta máquina (verificado):
`[OK]` instalado e testado | `[GPU]` precisa NVIDIA/CUDA | `[USER]` passo manual pendente.

## Resumo de estado nesta máquina

| Componente | Estado | Versão |
|---|---|---|
| Blender | [OK] | 5.2.1 LTS (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`) |
| ComfyUI (server) | [OK] CPU | 0.37.0 em `~/ComfyUI`, venv `.venv`, torch 2.14.0+cpu |
| ComfyUI-3D-Pack (nodes) | [GPU] | clonado em `~/ComfyUI/custom_nodes/`; não importa sem CUDA |
| trimesh | [OK] | 5.1.0 (python do sistema) |
| pymeshlab | [OK] | 2025.7.post1 |
| usd-core (`pxr`) | [OK] | 26.8 |
| open3d | [USER] | opcional, `pip install open3d` |
| Godot | [OK] | 4.7.2 (`godot` no PATH) |
| scipy | [USER] | opcional; ativa `fix_normals` no meshops (`pip install scipy`) |
| checkpoints de modelos | [USER] | requerem espaço em disco (5-15GB cada) e GPU para uso prático |

## 1. Blender

```powershell
winget install BlenderFoundation.Blender
# ou https://www.blender.org/download/
```

Verificar:

```bash
python extensions/blender-operator/wrapper.py --self-test
python extensions/blender-operator/wrapper.py launch
python extensions/blender-operator/wrapper.py exec "bpy.app.version_string"
python extensions/blender-operator/wrapper.py kill
```

Sem GPU: Cycles roda em CPU (lento); EEVEE precisa de GPU com OpenGL.
Nesta máquina (Intel UHD 630) prefira `BLENDER_WORKBENCH` ou Cycles
com poucos samples para verificação.

## 2. ComfyUI + ComfyUI-3D-Pack

### ComfyUI server

```bash
git clone https://github.com/comfyanonymous/ComfyUI ~/ComfyUI
cd ~/ComfyUI && python -m venv .venv

# CPU-only (esta máquina):
./.venv/Scripts/python.exe -m pip install torch torchvision \
  --index-url https://download.pytorch.org/whl/cpu
# Com NVIDIA: troque o index por .../whl/cu124 e use o build GPU do torch.

./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe main.py --cpu --port 8188   # --cpu só sem GPU
```

Verificar:

```bash
python extensions/comfyui-operator/wrapper.py status
```

### ComfyUI-3D-Pack

```bash
git clone https://github.com/MrForExample/ComfyUI-3D-Pack \
  ~/ComfyUI/custom_nodes/ComfyUI-3D-Pack
cd ~/ComfyUI && ./.venv/Scripts/python.exe -m pip install \
  -r custom_nodes/ComfyUI-3D-Pack/requirements.txt
```

**Requisito duro: GPU NVIDIA + CUDA toolkit (nvcc).** O pack importa
`nvdiffrast`, `spconv-cu126`, `nerfacc`, `slangtorch` e rasterização
gaussiana, todos CUDA-only e sem wheel para CPU. Sem GPU NVIDIA o pack
aparece como `IMPORT FAILED` no log; o ComfyUI continua funcionando
para workflows 2D.

Em máquina COM GPU: instale o requirements completo; `nvdiffrast` vem
do git (`git+https://github.com/NVlabs/nvdiffrast.git`) e compila com
nvcc.

Sem GPU mas querendo gerar 3D: use os repos dos modelos direto
(TRELLIS, TripoSG, InstantMesh), alguns rodam em CPU lentamente, ou
uma máquina/cloud com GPU. Ver `skills/ai3d-gen/SKILL.md`.

### Checkpoints de modelo

Os workflows precisam de pesos em `~/ComfyUI/models/` (hunyuan3d,
trellis, etc.). Baixe do Hugging Face conforme a skill `ai3d-gen`.
Cada modelo ocupa 5-15GB; nesta máquina (2GB livres) use drive externo
e aponte `--extra-model-paths-config` ou symlink.

## 3. Bibliotecas de mesh (mesh-utils)

```bash
pip install trimesh pymeshlab usd-core
# opcionais:
pip install scipy   # habilita fix_normals (connected components)
pip install open3d  # point clouds e análise avançada
```

Verificar:

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

Verificar:

```bash
godot --version
godot --headless --path <proj> --check-only --script tool.gd
```

`godot_console` também é instalado (mostra stdout no Windows).

## 5. Ordem de verificação completa (smoke)

```bash
python extensions/mesh-utils/meshops.py doctor            # deps python
python extensions/comfyui-operator/wrapper.py status      # server up?
python extensions/blender-operator/wrapper.py --self-test # blender
godot --version                                           # godot
```

## Limites conhecidos desta máquina

- Sem NVIDIA: 3D-Pack indisponível; ComfyUI 2D e Blender rodam em CPU.
- Disco C: ~2GB livres. Checkpoints de modelo exigem outro volume.
- RAM 16GB total: modelos 3D grandes (Hunyuan3D-2 tem ~6GB) ficam
  apertados em CPU.
