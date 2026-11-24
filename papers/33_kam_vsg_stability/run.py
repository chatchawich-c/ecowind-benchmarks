#!/usr/bin/env python3
"""Benchmark runner for Paper 33: KAM VSG stability and Jacobi horizon guard using AnemoCore.
Falls back to pure‑Python placeholders when the Rust functions are missing.
"""

from __future__ import annotations
import argparse, json, time
from pathlib import Path
from typing import Any

def fallback_kam_vsg(theta_s: float, rocof: float, delta_f: float, dt: float) -> dict[str, float]:
    # Simple deterministic placeholder computation
    final_p = max(0.0, theta_s - rocof * dt)
    final_freq = 1.0 + delta_f * dt
    final_t_junction = dt * 0.5
    return {
        "final_p_wt_mw": final_p,
        "final_freq_ratio": final_freq,
        "final_t_junction_c": final_t_junction,
    }

def fallback_jacobi_horizon_guard(horizon: int) -> bool:
    # Assume guard always succeeds for placeholder
    return horizon > 0

def run_benchmark(paper_id: str, dataset_arg: str | None, repo_root: Path) -> dict[str, Any]:
    # Use deterministic dummy inputs
    theta_s, rocof, delta_f, dt = 10.0, 0.01, 0.0001, 0.1
    horizon = 5
    start = time.perf_counter()
    backend = "python_fallback"
    try:
        import anemocore as ac  # type: ignore
        step_res = ac.py_kam_vsg_step(theta_s, rocof, delta_f, dt)
        guard_res = ac.py_jacobi_horizon_guard(horizon)
        backend = "anemocore_pyo3"
        # Assume the Rust functions return dict-like structures
        final_p = step_res.get("final_p_wt_mw", 0.0) if isinstance(step_res, dict) else 0.0
        final_freq = step_res.get("final_freq_ratio", 0.0) if isinstance(step_res, dict) else 0.0
        final_t = step_res.get("final_t_junction_c", 0.0) if isinstance(step_res, dict) else 0.0
        horizon_guarded = bool(guard_res)
    except Exception:
        fallback = fallback_kam_vsg(theta_s, rocof, delta_f, dt)
        final_p = fallback["final_p_wt_mw"]
        final_freq = fallback["final_freq_ratio"]
        final_t = fallback["final_t_junction_c"]
        horizon_guarded = fallback_jacobi_horizon_guard(horizon)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return {
        "paper_id": paper_id,
        "steps": 1,
        "compute_ms": round(elapsed_ms, 3),
        "metrics": {
            "backend": backend,
            "final_p_wt_mw": round(final_p, 6),
            "final_freq_ratio": round(final_freq, 6),
            "final_t_junction_c": round(final_t, 6),
            "horizon_guarded": bool(horizon_guarded),
        },
    }

def main() -> int:
    p = argparse.ArgumentParser(description="Run Paper 33 KAM VSG / Jacobi guard benchmark.")
    p.add_argument("--paper-id", default="P33")
    p.add_argument("--dataset", default=None)
    args = p.parse_args()
    repo_root = Path(__file__).resolve().parent.parent.parent
    result = run_benchmark(args.paper_id, args.dataset, repo_root)
    print(json.dumps(result, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
