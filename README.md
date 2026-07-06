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

Swap via config — like Flow's TTS providers.

## Quick start

```bash
git clone https://github.com/OpenX-Inc/clay.git && cd clay
uv sync --extra postprocess

cp config/config.example.toml config/config.toml   # set your GPU backend URL

# image → game-ready GLB, 60k tris
clay generate --image nganya.png --format glb --target-tris 60000
```

## Editions

- **Open-source headless core** (this repo) — CLI/API, no UI. Self-hostable from day one.
- **OpenX Clay (managed cloud)** — `openx-clay.stanl.ink`, coming later. Same pipeline, zero infra.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). MIT licensed.

Built by [OpenX-Inc](https://github.com/OpenX-Inc). 🏺
