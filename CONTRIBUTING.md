# Contributing to Clay

Thanks for helping build Clay — open-source, game-ready 3D generation.

## Setup

```bash
uv sync --extra postprocess --extra dev
```

## Workflow

- **Atomic commits.** One logical change per commit (ideally one function/method).
- **Conventional Commits** — we use [release-please](https://github.com/googleapis/release-please), so prefixes drive versioning:
  - `feat:` → minor bump, `fix:` → patch, `feat!:`/`fix!:` → major, plus `docs:`, `test:`, `chore:`, `refactor:`.
- **CI must be green per push** — `ruff check src tests` and `pytest -q`. Fix before moving on.
- Keep the **core headless and config-driven** (TOML + Pydantic). Don't bake in the managed cloud.

## Run checks locally

```bash
ruff check src tests
pytest -q
```

## Architecture

- `clay/config.py`, `clay/schemas.py` — config + data models.
- `clay/providers/` — pluggable model-provider registry (TRELLIS-2, Hunyuan3D, Hi3DGen).
- `clay/generator.py` — orchestrator → GPU backend over the HTTP contract.
- `clay/postprocess.py` — remesh/decimate, UV unwrap, PBR, export (the differentiator).
- `clay/pipeline.py`, `clay/cli.py` — end-to-end + CLI.
- `clay/gpu_backend/`, `clay/deploy/` — the swappable backend + parameterized deploys.
- `clay/tools/`, `clay/agent/`, `clay/mcp_server/` — one tool registry, two surfaces.

## License

By contributing, you agree your contributions are licensed under the MIT License.
