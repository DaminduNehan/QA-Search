#!/usr/bin/env python3
"""Run minimum-should-match queries and generate results sheet + dashboard."""

from __future__ import annotations

import csv
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get(
    "BASE_URL",
    "https://search-api-wurthbaer-qa.search-villvay.workers.dev/search",
)
INPUT_JSON = Path(__file__).resolve().parent / "minimum_should_match.json"
OUT_CSV = Path(__file__).resolve().parent / "minimum_should_match_results.csv"
OUT_JSON = Path(__file__).resolve().parent / "minimum_should_match_results.json"
OUT_HTML = Path(__file__).resolve().parent / "minimum_should_match_dashboard.html"

REQUEST_TIMEOUT_S = int(os.environ.get("REQUEST_TIMEOUT_S", "30"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
RETRY_BACKOFF_S = float(os.environ.get("RETRY_BACKOFF_S", "0.8"))
REQUEST_DELAY_S = float(os.environ.get("REQUEST_DELAY_S", "0.12"))
PAGE_SIZE = int(os.environ.get("PAGE_SIZE", "24"))


def fetch_total_for_query(query: str) -> tuple[int, str]:
    params = {
        "page": "1",
        "query": query,
        "isFilterByBrand": "false",
        "pageSize": str(PAGE_SIZE),
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("accept", "application/json")
    req.add_header(
        "user-agent",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    )

    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
                payload = json.loads(resp.read().decode("utf-8", errors="replace"))
            summary = payload.get("summary") if isinstance(payload, dict) else {}
            total = int((summary or {}).get("total") or 0)
            return total, ""
        except Exception as e:  # noqa: BLE001
            last_error = str(e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_S * attempt)
    return 0, last_error


def build_dashboard(rows: list[dict], summary: dict) -> str:
    zeros = [r for r in rows if int(r.get("no_of_results", 0)) == 0]
    non_zeros = [r for r in rows if int(r.get("no_of_results", 0)) > 0]
    rows_json = json.dumps(rows, ensure_ascii=False)
    zeros_json = json.dumps(zeros, ensure_ascii=False)
    non_zero_json = json.dumps(non_zeros, ensure_ascii=False)
    summary_json = json.dumps(summary, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Minimum Should Match Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; color: #111; }}
    h1 {{ margin-bottom: 8px; }}
    .cards {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 14px 0; }}
    .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 10px 14px; min-width: 170px; }}
    .tabs button {{ margin-right: 8px; padding: 8px 10px; border: 1px solid #bbb; background: #f5f5f5; border-radius: 6px; cursor: pointer; }}
    .tabs button.active {{ background: #111; color: #fff; border-color: #111; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ border: 1px solid #ddd; padding: 7px 8px; text-align: left; font-size: 13px; }}
    th {{ background: #f6f6f6; }}
    .zero {{ color: #b91c1c; font-weight: 700; }}
    .ok {{ color: #047857; font-weight: 700; }}
  </style>
</head>
<body>
  <h1>Minimum Should Match - Query Results</h1>
  <div id="meta"></div>
  <div class="cards" id="cards"></div>
  <div class="tabs">
    <button id="btnZero" class="active">No Results (0)</button>
    <button id="btnAll">All Queries</button>
    <button id="btnNonZero">Queries with Results (>0)</button>
  </div>
  <table>
    <thead>
      <tr>
        <th>query</th>
        <th>no_of_results</th>
        <th>status</th>
        <th>error</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <script>
    const rows = {rows_json};
    const zeroRows = {zeros_json};
    const nonZeroRows = {non_zero_json};
    const summary = {summary_json};
    const meta = document.getElementById("meta");
    meta.innerText = "API: " + summary.api_base + " | Generated: " + summary.generated_at;

    const cards = document.getElementById("cards");
    [
      ["Total Queries", summary.total_queries],
      ["No Results (0)", summary.zero_result_queries],
      ["With Results (>0)", summary.non_zero_queries],
      ["Errors", summary.error_queries]
    ].forEach(([k, v]) => {{
      const d = document.createElement("div");
      d.className = "card";
      d.innerHTML = "<div><strong>" + k + "</strong></div><div style='font-size:22px;margin-top:4px;'>" + v + "</div>";
      cards.appendChild(d);
    }});

    function render(data) {{
      const tb = document.getElementById("tbody");
      tb.innerHTML = "";
      data.forEach(r => {{
        const tr = document.createElement("tr");
        const n = Number(r.no_of_results || 0);
        const status = n === 0 ? "<span class='zero'>NO RESULT</span>" : "<span class='ok'>HAS RESULT</span>";
        tr.innerHTML = `
          <td>${{r.query || ""}}</td>
          <td>${{n}}</td>
          <td>${{status}}</td>
          <td>${{r.error || ""}}</td>
        `;
        tb.appendChild(tr);
      }});
    }}

    const btnZero = document.getElementById("btnZero");
    const btnAll = document.getElementById("btnAll");
    const btnNonZero = document.getElementById("btnNonZero");
    function activate(btn) {{
      [btnZero, btnAll, btnNonZero].forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    }}
    btnZero.onclick = () => {{ activate(btnZero); render(zeroRows); }};
    btnAll.onclick = () => {{ activate(btnAll); render(rows); }};
    btnNonZero.onclick = () => {{ activate(btnNonZero); render(nonZeroRows); }};
    render(zeroRows);
  </script>
</body>
</html>
"""


def main() -> None:
    if not INPUT_JSON.exists():
        raise SystemExit(f"Missing input file: {INPUT_JSON}")

    payload = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    queries = payload.get("queries") if isinstance(payload, dict) else None
    if not isinstance(queries, list):
        raise SystemExit("minimum_should_match.json must contain a 'queries' list.")

    rows: list[dict] = []
    for i, qv in enumerate(queries, start=1):
        query = str(qv or "").strip()
        if not query:
            continue
        total, err = fetch_total_for_query(query)
        rows.append(
            {
                "query": query,
                "no_of_results": total,
                "error": err,
            }
        )
        print(f"[{i}/{len(queries)}] {query} -> {total}", flush=True)
        time.sleep(REQUEST_DELAY_S)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["query", "no_of_results"])
        writer.writeheader()
        for r in rows:
            writer.writerow({"query": r["query"], "no_of_results": r["no_of_results"]})

    zero_count = sum(1 for r in rows if int(r.get("no_of_results", 0)) == 0)
    err_count = sum(1 for r in rows if str(r.get("error") or "").strip())
    summary = {
        "api_base": BASE_URL,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_queries": len(rows),
        "zero_result_queries": zero_count,
        "non_zero_queries": len(rows) - zero_count,
        "error_queries": err_count,
        "columns": ["query", "no_of_results"],
    }
    result_payload = {"summary": summary, "results": rows}
    OUT_JSON.write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_HTML.write_text(build_dashboard(rows, summary), encoding="utf-8")

    print(f"Saved CSV : {OUT_CSV}", flush=True)
    print(f"Saved JSON: {OUT_JSON}", flush=True)
    print(f"Saved HTML: {OUT_HTML}", flush=True)


if __name__ == "__main__":
    main()

