"""Run isolated local-LLM batches concurrently, preserving source order."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from scrape import load_data, save_data


def validate(original, extended):
    """Reject changed source fields, missing outputs, or reordered records."""
    if len(original) != len(extended):
        raise ValueError("Output record count changed")
    for source, result in zip(original, extended):
        if any(result.get(key) != value for key, value in source.items()):
            raise ValueError("A source field or record order changed")
        for key in ("llm-generated-program", "llm-generated-university"):
            if not isinstance(result.get(key), str) or not result[key].strip():
                raise ValueError("Missing standardized name")


def run_batches(records, directory, workers, threads, batch_size=50):
    """Run child processes with isolated caches and merge only validated data.

    The thread pool only supervises processes; each process has its own model.
    A single parent writes the aggregate after all batches pass validation.
    """
    if min(workers, threads, batch_size) < 1:
        raise ValueError("Workers, threads, and batch size must be positive")
    if workers * threads > (os.cpu_count() or 1):
        raise ValueError("Requested model threads exceed logical CPU count")
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parent
    env = dict(os.environ, N_THREADS=str(threads), N_GPU_LAYERS="0")
    jobs = []
    for index, start in enumerate(range(0, len(records), batch_size)):
        batch = records[start : start + batch_size]
        folder = directory / f"batch-{index:05d}"
        folder.mkdir(exist_ok=True)
        save_data(batch, folder / "input.json")
        jobs.append((batch, folder))

    def execute(job):
        """Run and validate one isolated local-model batch subprocess."""
        batch, folder = job
        result = subprocess.run(
            [
                sys.executable,
                str(root / "clean.py"),
                "--file",
                str(folder / "input.json"),
                "--output",
                str(folder / "output.json"),
                "--llm-dir",
                str(root / "llm_hosting"),
                "--batch-size",
                str(batch_size),
            ],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode:
            raise RuntimeError(f"Batch failed: {result.stderr[-2000:]}")
        output = load_data(folder / "output.json")
        validate(batch, output)
        return output

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        groups = list(executor.map(execute, jobs))
    elapsed = time.perf_counter() - started
    merged = [record for group in groups for record in group]
    validate(records, merged)
    save_data(merged, directory / "merged.json")
    return elapsed, merged


def main():
    """Benchmark configurations or clean using explicitly chosen limits."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file", type=Path, default=Path("applicant_data.json")
    )
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    records = load_data(args.file)
    if not records:
        raise ValueError("Input is empty")
    Path("tmp").mkdir(exist_ok=True)
    directory = args.work_dir or Path(
        tempfile.mkdtemp(prefix="llm-bench-", dir="tmp")
    )
    if not args.benchmark:
        if args.output is None:
            parser.error("--output is required outside benchmark mode")
        elapsed, result = run_batches(
            records, directory, args.workers, args.threads
        )
        save_data(result, args.output)
        print(f"Validated {len(result)} records in {elapsed:.1f} seconds")
        return
    sample = records[:100]
    if len(sample) != 100:
        raise ValueError("Benchmark requires at least 100 source records")
    report = {"records": 100, "batch_size": 50, "results": []}
    report["input_sha256"] = hashlib.sha256(
        json.dumps(sample, sort_keys=True).encode()
    ).hexdigest()
    baseline = None
    print(f"Benchmark artifacts: {directory}", flush=True)
    for workers, threads in ((1, 8), (1, 12), (2, 6)):
        folder = directory / f"workers-{workers}-threads-{threads}"
        if folder.exists():
            raise ValueError(
                "Benchmark requires fresh directories, not cached results"
            )
        elapsed, result = run_batches(sample, folder, workers, threads)
        names = [
            (row["llm-generated-program"], row["llm-generated-university"])
            for row in result
        ]
        baseline = names if baseline is None else baseline
        differences = sum(a != b for a, b in zip(baseline, names))
        summary = {
            "workers": workers,
            "threads": threads,
            "seconds": round(elapsed, 3),
            "records_per_minute": round(6000 / elapsed, 2),
            "source_preserved": True,
            "name_differences_vs_baseline": differences,
        }
        report["results"].append(summary)
        save_data(report, directory / "benchmark.json")
        print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
