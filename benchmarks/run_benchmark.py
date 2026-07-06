"""OpenX Clay benchmark — real generation + game-ready post-processing on Modal.

This runs the **actual shipped code** (``clay.gpu_backend.runtime.generate`` +
``clay.postprocess.PostProcessor``), so it validates the whole loop end-to-end
*and* records timing / triangle / cost data. Nothing here is faked: if a model
path isn't wired or an API differs, the case records the error and the suite
keeps going.

Usage (after ``modal token new``):

    modal run benchmarks/run_benchmark.py            # single smoke case
    modal run benchmarks/run_benchmark.py::suite     # full matrix (several)

Tune via env: ``CLAY_BENCH_GPU`` (default A100-80GB),
``CLAY_BENCH_RATE`` (USD/hr for the cost estimate, default 1.90).
"""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path

import modal

GPU = os.environ.get("CLAY_BENCH_GPU", "A100-80GB")
RATE_USD_HR = float(os.environ.get("CLAY_BENCH_RATE", "1.90"))

app = modal.App("openx-clay-benchmark")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "libgl1", "libglib2.0-0")
    .pip_install(
        "torch>=2.6.0",
        "transformers>=4.50.0",
        "diffusers>=0.33.0",
        "accelerate>=1.5.0",
        "trimesh>=4.5.0",
        "xatlas>=0.0.9",
        "fast-simplification>=0.1.7",
        "pygltflib>=1.16.0",
        "pillow",
        "numpy",
    )
    .run_commands("pip install git+https://github.com/microsoft/TRELLIS.git")
    .add_local_python_source("clay")
)

volume = modal.Volume.from_name("clay-bench-weights", create_if_missing=True)


@app.function(image=image, gpu=GPU, volumes={"/models": volume}, timeout=1800)
def bench_case(case: dict, image_bytes: bytes | None = None) -> dict:
    """Run one case through the real runtime + post-processor. Returns metrics.

    On any failure, returns ``{ok: False, error: ...}`` with the timings captured
    so far — the case fails *visibly*, the suite continues.
    """
    import tempfile

    from clay.config import PostprocessConfig
    from clay.gpu_backend import runtime
    from clay.postprocess import PostProcessor
    from clay.schemas import Generated3DAsset

    provider = case.get("provider", "trellis2")
    mode = case.get("mode", "image")
    target_tris = int(case.get("target_tris", 60000))
    fmt = case.get("format", "glb")

    t0 = time.time()
    try:
        image_b64 = base64.b64encode(image_bytes).decode() if image_bytes else None
        raw_bytes, raw_tris = runtime.generate(
            provider, mode, image_b64=image_b64, prompt=case.get("prompt")
        )
        t_gen = time.time()

        tmp = Path(tempfile.mkdtemp(prefix="clay_bench_"))
        raw_path = tmp / "raw.glb"
        raw_path.write_bytes(raw_bytes)
        asset = Generated3DAsset(
            path=str(raw_path), format="glb", triangles=raw_tris, provider=provider
        )

        pp = PostProcessor(PostprocessConfig(
            target_tris=target_tris, unwrap_uvs=case.get("unwrap_uvs", True),
            format=fmt, pbr=case.get("pbr", True),
        ))
        out_path = tmp / f"final.{fmt}"
        result = pp.process(asset, out_path=str(out_path))
        t_post = time.time()

        final_bytes = Path(result.path).read_bytes()
        return {
            "ok": True,
            "name": case.get("name", "case"),
            "provider": provider,
            "mode": mode,
            "target_tris": target_tris,
            "format": fmt,
            "raw_triangles": raw_tris,
            "final_triangles": result.triangles,
            "reduction_ratio": round(1 - result.triangles / raw_tris, 3) if raw_tris else 0.0,
            "generation_time_s": round(t_gen - t0, 1),
            "postprocess_time_s": round(t_post - t_gen, 1),
            "total_gpu_time_s": round(t_post - t0, 1),
            "output_size_kb": round(len(final_bytes) / 1024, 1),
            "mesh_bytes": final_bytes,
        }
    except Exception as err:  # noqa: BLE001 — record the failure, don't crash the suite
        return {
            "ok": False,
            "name": case.get("name", "case"),
            "provider": provider,
            "error": f"{type(err).__name__}: {err}",
            "elapsed_s": round(time.time() - t0, 1),
        }


def _load_image(case: dict) -> bytes | None:
    if case.get("mode") == "text" or not case.get("image"):
        return None
    path = Path("benchmarks/assets") / case["image"]
    if not path.exists():
        raise FileNotFoundError(f"benchmark image not found: {path}")
    return path.read_bytes()


def _record(result: dict, results_dir: Path) -> dict:
    """Save the mesh (if any) and strip bytes from the metrics record."""
    samples = results_dir / "samples"
    samples.mkdir(parents=True, exist_ok=True)
    metrics = {k: v for k, v in result.items() if k != "mesh_bytes"}
    if result.get("ok") and result.get("mesh_bytes"):
        out = samples / f"{result['name']}.{result['format']}"
        out.write_bytes(result["mesh_bytes"])
        metrics["sample"] = str(out)
        metrics["estimated_cost_usd"] = round(
            result["total_gpu_time_s"] / 3600 * RATE_USD_HR, 4
        )
    return metrics


@app.local_entrypoint()
def main():
    """Single smoke case — proves the loop before spending on a full matrix."""
    results_dir = Path("benchmarks/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    case = {"name": "smoke", "mode": "image", "provider": "trellis2",
            "image": "smoke.png", "target_tris": 20000, "format": "glb"}

    print(f"🏺 Clay benchmark — {case['name']} on {GPU}")
    try:
        img = _load_image(case)
    except FileNotFoundError as err:
        print(f"✗ {err}\n  Drop an object image at benchmarks/assets/smoke.png first.")
        return

    result = bench_case.remote(case, img)
    metrics = _record(result, results_dir)
    (results_dir / "smoke-result.json").write_text(json.dumps(metrics, indent=2))

    if metrics["ok"]:
        print(f"✓ raw {metrics['raw_triangles']} → {metrics['final_triangles']} tris "
              f"({metrics['reduction_ratio']:.0%} reduction) in "
              f"{metrics['total_gpu_time_s']}s · ~${metrics['estimated_cost_usd']}")
    else:
        print(f"✗ FAILED (visible): {metrics['error']}")


@app.local_entrypoint()
def suite():
    """Run the full case matrix (several benchmarks) and write an aggregate report."""
    results_dir = Path("benchmarks/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    cases_file = Path(os.environ.get("CLAY_BENCH_CASES", "benchmarks/cases/default.json"))
    cases = json.loads(cases_file.read_text())["cases"]

    print(f"🏺 Clay benchmark suite — {len(cases)} cases on {GPU}")
    records = []
    for case in cases:
        try:
            img = _load_image(case)
        except FileNotFoundError as err:
            records.append({"ok": False, "name": case.get("name"), "error": str(err)})
            print(f"  ✗ {case.get('name')}: {err}")
            continue
        result = bench_case.remote(case, img)
        metrics = _record(result, results_dir)
        records.append(metrics)
        if metrics["ok"]:
            print(f"  ✓ {metrics['name']}: {metrics['raw_triangles']}→"
                  f"{metrics['final_triangles']} tris, {metrics['total_gpu_time_s']}s, "
                  f"~${metrics['estimated_cost_usd']}")
        else:
            print(f"  ✗ {metrics['name']}: {metrics['error']}")

    (results_dir / "suite-results.json").write_text(json.dumps(records, indent=2))
    _write_markdown(records, results_dir / "RESULTS.md")
    ok = sum(1 for r in records if r.get("ok"))
    print(f"\n{ok}/{len(records)} cases passed → benchmarks/results/RESULTS.md")


def _write_markdown(records: list[dict], path: Path) -> None:
    lines = [
        "# Clay Benchmark Results", "",
        f"GPU: `{GPU}` · rate: ${RATE_USD_HR}/hr", "",
        "| Case | Provider | Raw → Final tris | Reduction | Gen (s) | Post (s) | "
        "Total (s) | Size (KB) | Cost | Status |",
        "|------|----------|------------------|-----------|---------|----------|"
        "-----------|-----------|------|--------|",
    ]
    for r in records:
        if r.get("ok"):
            lines.append(
                f"| {r['name']} | {r['provider']} | "
                f"{r['raw_triangles']} → {r['final_triangles']} | "
                f"{r['reduction_ratio']:.0%} | {r['generation_time_s']} | "
                f"{r['postprocess_time_s']} | {r['total_gpu_time_s']} | "
                f"{r['output_size_kb']} | ${r['estimated_cost_usd']} | ✓ |"
            )
        else:
            lines.append(
                f"| {r.get('name', '?')} | {r.get('provider', '?')} | — | — | — | — | "
                f"— | — | — | ✗ {r.get('error', 'failed')[:40]} |"
            )
    path.write_text("\n".join(lines) + "\n")
