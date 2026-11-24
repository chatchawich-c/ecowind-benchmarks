import argparse
import json
import os
import subprocess
import sys
import time
import resource
from pathlib import Path

def load_manifest(manifest_path):
    import yaml
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data

def filter_papers(papers, only=None, dataset=None, tier=None):
    result = []
    # Accept a comma‑separated list for --only (e.g. "P07,P31,P33")
    only_ids = set()
    if only:
        only_ids = {pid.strip() for pid in only.split(',') if pid.strip()}
    for paper in papers:
        if only_ids and paper.get("id") not in only_ids:
            continue
        if dataset is not None and dataset not in paper.get("dataset"):
            continue
        if tier is not None and paper.get("tier") != tier:
            continue
        result.append(paper)
    return result

def run_paper(paper, timeout, out_dir):
    start = time.time()
    # Determine benchmark command
    if "entrypoint" in paper:
        entry_path = Path(__file__).resolve().parent.parent / paper["entrypoint"]
        cmd = ["python3", str(entry_path), "--paper-id", paper.get("id")]
    else:
        cmd = ["python3", "-c", f"print('Running {paper.get('id')}')"]
    # Run the command normally to capture its output
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        exit_code = proc.returncode
        stdout = proc.stdout.decode()
        stderr = proc.stderr.decode()
    except subprocess.TimeoutExpired:
        exit_code = -1
        stdout = ""
        stderr = "timeout"
    # Use /usr/bin/time -l to get accurate max RSS for the child process on macOS
    time_cmd = ["/usr/bin/time", "-l"] + cmd
    try:
        time_proc = subprocess.run(
            time_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        import re
        rss_match = re.search(r"maximum resident set size\s*\(kbytes\):\s*(\d+)", time_proc.stderr.decode())
        rss_kb = int(rss_match.group(1)) if rss_match else 0
    except Exception:
        rss_kb = 0
    peak_rss_mib = rss_kb / 1024.0
    duration = time.time() - start
    return {
        "paper_id": paper.get("id"),
        "status": "success" if exit_code == 0 else "failure",
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "peak_rss_mib": round(peak_rss_mib, 2),
        "within_rss_budget": peak_rss_mib <= 150.0,
        "duration_s": round(duration, 2),
    }

def main():
    parser = argparse.ArgumentParser(description="Run ECOWind benchmarks with filtering and resource tracking.")
    parser.add_argument("--only", help="Run only the specified paper ID")
    parser.add_argument("--dataset", help="Filter papers by dataset name")
    parser.add_argument("--tier", help="Filter papers by tier (e.g., basic, full)")
    parser.add_argument("--out", default="results/benchmark_summary.json", help="Path to write JSON summary")
    parser.add_argument("--timeout", type=int, default=300, help="Per‑paper timeout in seconds")
    args = parser.parse_args()

    manifest_path = Path(__file__).resolve().parents[1] / "manifest" / "papers_66.yaml"
    if not manifest_path.is_file():
        sys.exit(f"Manifest not found: {manifest_path}")
    manifest = load_manifest(manifest_path)
    papers = manifest.get("papers", [])
    selected = filter_papers(papers, only=args.only, dataset=args.dataset, tier=args.tier)
    if not selected:
        sys.exit("No papers matched the given filters.")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = []
    for paper in selected:
        result = run_paper(paper, timeout=args.timeout, out_dir=out_path.parent)
        summary.append(result)
        # Enforce RSS budget per paper
        if result["peak_rss_mib"] > 150.0:
            print(f"Warning: paper {paper.get('id')} exceeded RSS budget ({result['peak_rss_mib']} MiB)")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Benchmark summary written to {out_path}")

if __name__ == "__main__":
    main()
