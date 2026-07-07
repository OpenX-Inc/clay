<div align="center">

# Clay

### OpenX Clay — Meshy/Rodin, but yours.

Open-source, self-hostable **image / text → game-ready 3D assets**. Feed it an
image (or a prompt); get back a clean mesh with PBR textures — remeshed to your
poly budget, UV-unwrapped, exported as GLB/FBX. You own everything.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/OpenX-Inc/clay/actions/workflows/ci.yml/badge.svg)](https://github.com/OpenX-Inc/clay/actions/workflows/ci.yml)

</div>

---

## What it does

```
image / text  →  3D generation (open models)  →  game-ready post-processing  →  GLB / FBX
```

Raw AI meshes are unusable in games — 500k-tri blobs with messy UVs. **Clay's job
is the post-processing**: remesh/decimate to a target tri-count, clean UVs, pack
PBR maps, and export in a real game format. Clay ships **game-ready assets, not
blobs**.

## The 3D sibling to [Flow](https://github.com/OpenX-Inc/flow)

Same ethos: an **orchestrator** (runs anywhere) that talks to a **swappable GPU
backend** over one HTTP contract, a **pluggable model-provider registry**, and
**agent + MCP** surfaces over a single tool registry — all headless and
config-driven.

```
┌───────────────────────────────┐        ┌──────────────────────────────┐
│      ORCHESTRATOR (any box)    │  HTTP  │       GPU BACKEND (cloud)     │
│  providers → generate →        │───────▶│  TRELLIS-2 / Hunyuan3D /      │
│  post-process → export         │        │  Hi3DGen  (Modal/RunPod/self) │
└───────────────────────────────┘        └──────────────────────────────┘
```

## Models (pluggable)

| Provider | License | Role |
|----------|---------|------|
| TRELLIS-2 | MIT | primary |
| Hunyuan3D-2.1 | — | alt |
| Hi3DGen | — | alt |

Swap via config — like Flow's TTS providers. Providers are metadata descriptors
in the orchestrator; the actual model inference runs on the GPU backend.

> **Honest status:** the orchestrator, the game-ready post-processing (the
> differentiator), `clay deploy`, and the agent + MCP surfaces are implemented
> and tested. Model inference is **GPU-gated** — it needs a deployed backend
> with weights + a CUDA device. TRELLIS-2 image-to-3D is wired against its
> documented pipeline; other providers/modes fail *visibly* (a clear error),
> never with fake output.

## Game-ready asset tools

Beyond `generate`, Clay ships general-purpose asset tools — each surfaced
everywhere: a **registry tool** (so the **agent + MCP** get it for free), a
**CLI subcommand**, and an **opt-in `generate` flag** that folds the stage into a
run. The default `generate` (image/text → mesh) is unchanged; stages only run
when asked.

| Tool | Does | Engine |
|------|------|--------|
| `export_fbx` | mesh → FBX (meshes + UVs + skeleton) | Blender |
| `make_collision` | convex/box/simplified/compound (VHACD) collider | trimesh (CPU) |
| `make_lods` | LOD chain at descending ratios | trimesh (CPU) |
| `retopo_asset` | clean quad topology + re-unwrap | Blender (Quadriflow) |
| `bake_normals` | high→low tangent-space normal (+AO) bake | Blender (Cycles) |
| `rig_asset` | auto-rig: humanoid/quadruped/**vehicle**/generic → skinned/parented FBX | Blender |
| `generate_material` | tiling PBR material set + `material.json` | GPU (pluggable provider) |
| `texture_asset` | UV-aware (re)texture / livery / skin (+ decals) | GPU (pluggable provider) |
| `generate_variations` | N seed-varied generations | shape provider |

```bash
# opt-in stages fold into a generate run:
clay generate --image van.png --rig --rig-type vehicle --with-lods --collision

# or run any capability standalone:
clay rig van.glb --type vehicle          # → body + per-wheel bones/sockets
clay collision prop.glb --kind compound   # → VHACD collider
clay material --kind facade --prompt "Nairobi CBD glass facade"
```

Blender-backed tools use a headless Blender (set `CLAY_BLENDER` / `[blender].path`)
and **fail visibly** if it's absent; GPU model tools (material/texture) are
**GPU-gated** — pluggable providers per category, honest errors until a backend
is deployed. Pure-geometry steps (collision, LODs) are CPU-only.

## Deploy the GPU backend

Generation needs a GPU backend — the open-source server in
[`src/clay/gpu_backend/`](src/clay/gpu_backend/). It exposes one base64 HTTP
contract (`POST /generate/image-to-3d|text-to-3d`, `/remesh`, `/texture`,
`GET /health`) that the orchestrator consumes, whether it runs on Modal, RunPod,
a self-hosted box, or your own cloud.

> A provider token **is not enough on its own** — the backend has to be
> *deployed* into your account first. That deploy is what produces the endpoint
> URL your jobs route to.

```bash
uv sync --extra gpu && pip install modal && modal token new   # one-time Modal auth

# Deploy as a NAMED instance (stand up several — an A100 pool, an H100 pool…)
clay deploy modal --name clay-gpu-a100 --gpu A100-80GB
# → prints the base URL, e.g. https://<workspace>--clay-gpu-a100.modal.run
```

Put that URL in `[gpu_backend].url`. Deploy defaults live in the `[deploy]`
section of your config; CLI flags override them. Modal auth can be passed
per-invocation (`--modal-token-id/--modal-token-secret`, scoped to that deploy
only). `clay deploy aws` / `clay deploy gcp` print the concrete manual steps —
they never fake a deployment.

**Self-hosted / RunPod:** run the same app directly and point `[gpu_backend].url`
at it:

```bash
uvicorn clay.gpu_backend.server:app --host 0.0.0.0 --port 8000
```

## Agent + MCP (one tool registry)

Beyond the CLI, Clay ships an **agent** (an LLM that drives the tools) and an
**MCP server** — both over the *same* tool registry (`generate_asset`,
`remesh_asset`, `list_assets`, `list_providers`), so behavior never drifts.

```bash
# Chat with the agent (default model: kimi via NVIDIA build)
export CLAY_NVIDIA_API_KEY="nvapi-..."
clay agent -m "generate a low-poly sword from sword.png at 20k tris"

# Or expose the same tools to external coding agents over MCP
export CLAY_MCP_TOKEN="your-secret"
clay mcp                       # http://127.0.0.1:8770/mcp  (Claude Code, Cursor, Codex)
```

- **Connect Claude Code:** `claude mcp add --transport http clay http://127.0.0.1:8770/mcp`
- The agent + MCP server are dependency-light and self-hostable; `remesh_asset`
  runs on CPU, `generate_asset` needs the deployed GPU backend.
- Configure under `[agent]` / `[mcp]` — see `config/config.example.toml`.

## Commands

| Command | What it does |
|---------|--------------|
| `clay generate` | image/text → game-ready asset (opt-in: `--collision --with-lods --retopo --bake --rig --material --texture`) |
| `clay export-fbx` | convert a mesh to FBX (Blender) |
| `clay collision` | build a physics collider (convex/box/simplified/compound) |
| `clay lods`     | build an LOD chain |
| `clay retopo`   | quad retopology (Blender Quadriflow) |
| `clay bake`     | high→low normal (+AO) bake (Blender) |
| `clay rig`      | auto-rig per profile — humanoid/quadruped/vehicle/generic (Blender) |
| `clay material` | tiling PBR material set (GPU-gated) |
| `clay texture`  | UV-aware (re)texture a mesh (GPU-gated) |
| `clay variations` | N seed-varied generations |
| `clay deploy`   | deploy the GPU backend as a named instance |
| `clay agent` / `clay mcp` | agent REPL / MCP server over the tool registry |
| `clay providers`| list the model providers |

## Quick start

```bash
git clone https://github.com/OpenX-Inc/clay.git && cd clay
uv sync --extra postprocess

cp config/config.example.toml config/config.toml   # set your GPU backend URL

# Validate the plan with no backend / GPU needed
clay generate --prompt "a low-poly treasure chest" --dry-run

# image → game-ready GLB, 60k tris (needs a deployed backend)
clay generate --image nganya.png --format glb --target-tris 60000
```

## Editions

- **Open-source headless core** (this repo) — CLI/API, no UI. Self-hostable from day one.
- **OpenX Clay (managed cloud)** — `openx-clay.stanl.ink`, coming later. Same pipeline, zero infra.

| | Self-Hosted (this repo) | OpenX Clay (managed) |
|--|--|--|
| **Setup** | You deploy, you manage | We handle everything |
| **GPU** | Your own (Modal, RunPod, …) | Ours |
| **Cost** | GPU rental only | Pay per asset |
| **Best for** | Developers, studios, high-volume | Teams who want zero infra |

## Roadmap

- [x] Orchestrator → GPU-backend HTTP contract
- [x] Game-ready post-processing — decimate to tri budget, UV unwrap, GLB/OBJ export
- [x] Pluggable model-provider registry (TRELLIS-2 / Hunyuan3D / Hi3DGen)
- [x] GPU backend (FastAPI contract) + parameterized Modal deploy
- [x] Agent + MCP over one tool registry
- [x] TRELLIS-2 inference — image-to-3D validated on GPU (real textured GLBs)
- [x] FBX export + rig / retopo / normal-bake (headless Blender engine)
- [x] Colliders (VHACD/convex) · LOD chains · seed variations
- [x] Material + texture endpoints + pluggable provider categories (GPU-gated)
- [ ] Hunyuan3D-2.1 + Hi3DGen runtimes; wire material/texture models
- [ ] AWS + GCP first-class backend deploy
- [~] OpenX Clay managed service — later

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). MIT licensed.

Built by [OpenX-Inc](https://github.com/OpenX-Inc). 🏺
