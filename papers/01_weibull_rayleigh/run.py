#!/usr/bin/env python3
"""Benchmark runner for Paper 01: Weibull & Rayleigh estimation via AnemoCore."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import yaml

DEFAULT_DATASET_CANDIDATES = [
    Path("/Users/chatchawichchaihong/Documents/ecowind-benchmarks/data/synthetic_open/synthetic_weibull_v1.yaml"),
    Path("/Users/chatchawichchaihong/Documents/AnemoCore/crates/anemocore/data/synthetic_weibull_v1.yaml"),
]


def resolve_dataset_path(explicit_dataset: str | None, repo_root: Path) -> Path:
    if explicit_dataset:
        cand = Path(explicit_dataset)
        if cand.exists():
            return cand.resolve()
        rel = (repo_root / explicit_dataset).resolve()
        if rel.exists():
            return rel

    for path in DEFAULT_DATASET_CANDIDATES:
        if path.exists():
            return path.resolve()

    raise FileNotFoundError("Could not locate synthetic_weibull_v1.yaml in default paths.")


def extract_wind_speeds(payload: Any) -> list[float]:
    """Extract numeric wind speed samples flexibly from YAML structures."""
    if isinstance(payload, dict):
        for key in ("wind_speed", "wind_speeds", "speeds", "samples", "data", "values"):
            if key in payload and isinstance(payload[key], list):
                vals = [float(x) for x in payload[key] if isinstance(x, (int, float))]
                if vals:
                    return vals
        if "k" in payload and "c" in payload:
            k = float(payload["k"])
            c = float(payload["c"])
            n = int(payload.get("n", 256))
            return [
                c * ((-math.log(1.0 - (i + 0.5) / n)) ** (1.0 / k))
                for i in range(max(n, 16))
            ]
    elif isinstance(payload, list):
        vals = [float(x) for x in payload if isinstance(x, (int, float))]
        if vals:
            return vals

    raise ValueError("Unable to extract valid numeric wind speed samples from YAML payload.")


def fallback_weibull_and_qmc(speeds: list[float], n_qmc: int = 256) -> dict[str, Any]:
    mean_v = sum(speeds) / len(speeds)
    var_v = sum((x - mean_v) ** 2 for x in speeds) / len(speeds)
    std_v = math.sqrt(max(var_v, 1e-12))
    k_est = max((std_v / max(mean_v, 1e-9)) ** (-1.086), 0.5)
    c_est = mean_v / math.gamma(1.0 + 1.0 / k_est)
    cubic_mean = (c_est**3) * math.gamma(1.0 + 3.0 / k_est)
    return {
        "backend": "python_math_fallback",
        "k": round(k_est, 6),
        "c": round(c_est, 6),
        "qmc_cubic_expectation": round(cubic_mean, 6),
        "n_qmc": n_qmc,
    }


def run_benchmark(paper_id: str, dataset_arg: str | None, repo_root: Path) -> dict[str, Any]:
    dataset_path = resolve_dataset_path(dataset_arg, repo_root)
    with dataset_path.open("r", encoding="utf-8") as f:
        raw_yaml = yaml.safe_load(f)

    speeds = extract_wind_speeds(raw_yaml)
    n_qmc = 256

    t0 = time.perf_counter()
    try:
        import anemocore as ac  # type: ignore

        k_val, c_val = ac.fit_weibull(speeds)
        qmc_cubic = ac.qmc_weibull_cubic(float(k_val), float(c_val), n_qmc)
        metrics = {
            "backend": "anemocore_pyo3",
            "k": round(float(k_val), 6),
            "c": round(float(c_val), 6),
            "qmc_cubic_expectation": round(float(qmc_cubic), 6),
            "n_qmc": n_qmc,
        }
    except Exception as exc:  # pragma: no cover
        metrics = fallback_weibull_and_qmc(speeds, n_qmc=n_qmc)
        metrics["fallback_reason"] = str(exc)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "paper_id": paper_id,
        "dataset_path": str(dataset_path),
        "sample_count": len(speeds),
        "compute_ms": round(elapsed_ms, 3),
        "metrics": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Paper 01 Weibull benchmark.")
    parser.add_argument("--paper-id", default="P01", help="Paper identifier.")
    parser.add_argument("--dataset", default=None, help="Dataset name or path.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    result = run_benchmark(args.paper_id, args.dataset, repo_root)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
