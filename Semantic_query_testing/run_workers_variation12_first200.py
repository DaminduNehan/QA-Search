#!/usr/bin/env python3
"""
Runs a 200-item semantic-query worker batch.

This is CI-safe: no external services are required.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
