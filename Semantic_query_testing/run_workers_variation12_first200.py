#!/usr/bin/env python3
"""
Runs a 200-item semantic-query worker batch.

This is CI-safe: no external services are required.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
import json
from pathlib import Path


def process_query(index: int) -> dict:
    # Lightweight deterministic workload for CI validation.
    query = f"semantic query #{index}"
    score = len(query) % 10
    return {"id": index, "query": query, "score": score}


def main() -> int:
    total_items = 200
    max_workers = 12

    print(
        f"Running semantic worker batch: total_items={total_items}, max_workers={max_workers}"
    )

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_query, i) for i in range(1, total_items + 1)]
        for future in as_completed(futures):
            results.append(future.result())

    print(f"Completed {len(results)} semantic query tasks successfully.")
    score_counts = Counter(item["score"] for item in results)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    results_path = output_dir / "results.json"
    summary = {
        "total_items": len(results),
        "max_workers": max_workers,
        "score_counts": dict(sorted(score_counts.items())),
    }
    results_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    max_count = max(score_counts.values()) if score_counts else 1
    chart_lines = [f"Semantic Worker Result (n={len(results)})", ""]
    for score in sorted(score_counts):
        count = score_counts[score]
        bar_len = max(1, round((count / max_count) * 40))
        chart_lines.append(f"Score {score:>2} | {'#' * bar_len} ({count})")

    chart_path = output_dir / "results_chart.txt"
    chart_path.write_text("\n".join(chart_lines) + "\n", encoding="utf-8")
    print(f"Wrote artifacts: {results_path} and {chart_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
