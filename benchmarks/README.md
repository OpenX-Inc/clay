# Clay Benchmarks

Real generation + game-ready post-processing on Modal. These run the **actual
shipped code** (`clay.gpu_backend.runtime` + `clay.postprocess`), so they both
validate the end-to-end loop and record timing / triangle-reduction / cost data.
Failures are recorded per-case and never faked.

## Setup

```bash
uv sync --extra gpu --extra postprocess
pip install modal && modal token new        # one-time Modal auth
```

Drop single-object images into `benchmarks/assets/` matching the `image` fields
in `cases/default.json` (e.g. `chair.png`, `character.png`, `prop.png`) and a
`pot.png` for the smoke test. Clean, centered product/render shots of one
object work best.

## Run

```bash
# 1) Smoke test — one image, proves the loop before spending on the matrix
modal run benchmarks/run_benchmark.py

# 2) Full suite — the case matrix (several benchmarks)
modal run benchmarks/run_benchmark.py::suite
```

Tune with env vars:

| Var | Default | Meaning |
|-----|---------|---------|
| `CLAY_BENCH_GPU`   | `A100-80GB` | Modal GPU type |
| `CLAY_BENCH_RATE`  | `1.90`      | USD/hr for the cost estimate |
| `CLAY_BENCH_CASES` | `benchmarks/cases/default.json` | case matrix file |

## Output

- `results/suite-results.json` — full metrics per case
- `results/RESULTS.md` — a readable table (raw→final tris, reduction, time, cost)
- `results/samples/<case>.glb` — the generated game-ready meshes

## What each case measures

- **Generation time** — model inference on the GPU (per provider).
- **Post-process time** — decimate to budget + UV unwrap + export.
- **Reduction ratio** — how much the game-ready step shrinks the raw blob.
- **Cost** — GPU seconds × rate. The `chair-5k/20k/60k` sweep isolates the
  post-processing differentiator on a single raw mesh.
