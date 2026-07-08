# Model-runtime benchmarks (GPU backend)

Real outputs from the wired model runtimes, validated on **Modal A10G**. Reproduce
with the `benchmarks/run_*.py` harnesses (`uv pip install modal` first, then
`modal run benchmarks/run_<x>.py`). Meshes (`*.glb`) are git-ignored (size) —
metrics are recorded here; the material maps are committed under `material/`.

## Shape — `trellis2` (TRELLIS-2, MIT, default)
`modal run benchmarks/run_benchmark.py::suite`

| Case | Input | Final tris | Texture | Gen time | Cost (A10G) |
|------|-------|-----------|---------|----------|-------------|
| pot | pot.png | 11,402 | 1024² PBR | ~202 s | ~$0.11 |
| chair-20k | chair.png | 7,366 | 1024² PBR | ~53 s | ~$0.028 |
| character | character.png | 19,522 | 1024² PBR | ~29 s | ~$0.015 |
| prop | prop.png | 10,287 | 1024² PBR | ~41 s | ~$0.022 |

## Shape — `hunyuan3d` (Hunyuan3D-2.1)
`modal run benchmarks/run_hunyuan.py`

| Input | Faces | Verts | Watertight | Size |
|-------|-------|-------|-----------|------|
| pot.png | 768,292 | 384,148 | ✅ | 13.8 MB |

Raw dense mesh (surface extractor `mc`); the orchestrator `PostProcessor`
decimates to the requested triangle budget.

## Material — `stablematerials` (StableMaterials, Apache-2.0)
`modal run benchmarks/run_material.py --prompt "…" --kind facade`

Prompt: *"Nairobi CBD glass office facade, seamless PBR material"* → 5 tiling maps
@ 1024² (committed under `material/`):

| Map | Character |
|-----|-----------|
| `facade_base_color.png` | seamless glass facade (windows + mullions), rich color |
| `facade_normal.png` | tangent-space (blue-dominant Z ≈ 252) |
| `facade_roughness.png` | grayscale scalar (low ≈ glossy glass) |
| `facade_metallic.png` | grayscale scalar |
| `facade_height.png` | grayscale displacement |

## Texture — `hunyuanpaint` (Hunyuan3D-Paint, NON-COMMERCIAL, self-host only)
`modal run benchmarks/run_texture.py --mesh <mesh.glb> --image <ref.png>`

| Input mesh | Ref image | Result | Texture |
|------------|-----------|--------|---------|
| pot.glb (11.4k tris) | pot.png | textured GLB | 2048² baked |

Image-conditioned re-texturing onto the mesh's UVs; output is a self-contained
GLB (OBJ+MTL+texture re-exported). **Non-commercial weights** — a self-host
option, not offered by the managed service. (Exit-time `bpy` SIGSEGV is a known
Blender-module teardown crash, after the result is returned — harmless.)

## Pending runtimes
- `hi3dgen` (Stable-X) — shape provider slot; model runtime TBD.
- Commercial-OK texture (`paint3d`/`syncmvd`) — pluggable slots, TBD.
