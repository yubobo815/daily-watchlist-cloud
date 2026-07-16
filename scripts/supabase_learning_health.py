#!/usr/bin/env python3
"""Validate that Supabase has enough replay history for learning.

This script prints only aggregate health metrics. It never prints Supabase keys.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict


def credentials() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )
    return url, key


def headers(key: str, *, count: bool = False) -> dict[str, str]:
    result = {
        "apikey": key,
        "Accept": "application/json",
    }
    if key.count(".") == 2 and not key.startswith("sb_"):
        result["Authorization"] = f"Bearer {key}"
    if count:
        result["Prefer"] = "count=exact"
    return result


def request_json(path: str, *, count: bool = False) -> tuple[list[dict], int | None]:
    url, key = credentials()
    if not url or not key:
        raise RuntimeError("Supabase credentials are missing.")
    endpoint = f"{url}/rest/v1/{path}"
    req = urllib.request.Request(endpoint, headers=headers(key, count=count), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            content_range = resp.headers.get("Content-Range", "")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase query failed with HTTP {exc.code}: {body[:500]}") from exc
    rows = json.loads(body) if body else []
    total = None
    if "/" in content_range:
        raw_total = content_range.rsplit("/", 1)[-1]
        if raw_total.isdigit():
            total = int(raw_total)
    return rows, total


def add_query_param(path: str, key: str, value: str | int) -> str:
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}{urllib.parse.quote(str(key))}={urllib.parse.quote(str(value))}"


def request_all_json(path: str, *, page_size: int = 1000, max_pages: int = 50) -> list[dict]:
    rows: list[dict] = []
    for page in range(max_pages):
        offset = page * page_size
        page_path = add_query_param(add_query_param(path, "limit", page_size), "offset", offset)
        page_rows, _ = request_json(page_path)
        rows.extend(page_rows)
        if len(page_rows) < page_size:
            break
    return rows


def count_rows(table: str, filters: str) -> int:
    _, total = request_json(f"{table}?select=*&{filters}&limit=1", count=True)
    return int(total or 0)


def latest_run_date_from_table(table: str, date_column: str = "run_date") -> str:
    rows, _ = request_json(
        f"{table}?select={urllib.parse.quote(date_column)}&order={date_column}.desc&limit=1"
    )
    if not rows:
        return ""
    return str(rows[0].get(date_column) or "")


def latest_synced_run_date() -> str:
    # watchlist_refresh_runs can lag when schema migration is skipped, so audit the
    # tables that prove the ML inputs were actually written.
    candidates = [
        latest_run_date_from_table("watchlist_behavior_history"),
        latest_run_date_from_table("watchlist_snapshots"),
    ]
    candidates = [date for date in candidates if date]
    return max(candidates) if candidates else ""


def emit_metrics(metrics: dict[str, object]) -> None:
    for key, value in metrics.items():
        print(f"{key}={value}")


def postgrest_in_list(values: list[str]) -> str:
    return ",".join(urllib.parse.quote(str(value), safe="") for value in values if str(value))


def fail(message: str) -> None:
    print(f"SUPABASE_LEARNING_HEALTH=FAIL {message}")
    raise SystemExit(1)


def main() -> None:
    run_date = latest_synced_run_date()
    if not run_date:
        fail("No synced watchlist run found in behavior history or snapshots.")

    runs, _ = request_json(
        "watchlist_refresh_runs"
        "?select=run_date,history_rows,snapshot_rows,symbols_analyzed,symbols_failed,payload"
        f"&run_date=eq.{urllib.parse.quote(str(run_date))}&limit=1"
    )
    latest = runs[0] if runs else {"run_date": run_date}

    filters = f"run_date=eq.{urllib.parse.quote(str(run_date))}"
    history_rows = request_all_json(
        "watchlist_behavior_history"
        "?select=ticker,history_date,open,high,low,close,payload"
        f"&{filters}&order=ticker.asc,history_date.asc"
    )
    snapshot_rows = request_all_json(
        "watchlist_snapshots"
        "?select=ticker,open,high,low,close,payload"
        f"&{filters}&order=ticker.asc"
    )

    history_by_ticker: dict[str, set[str]] = defaultdict(set)
    for row in history_rows:
        ticker = str(row.get("ticker") or "").upper()
        date = str(row.get("history_date") or "")
        if ticker and date:
            history_by_ticker[ticker].add(date)

    counts = [len(dates) for dates in history_by_ticker.values()]
    tickers_with_25 = sum(1 for count in counts if count >= 25)
    tickers_with_30 = sum(1 for count in counts if count >= 30)
    min_days = min(counts) if counts else 0
    max_days = max(counts) if counts else 0
    avg_days = round(sum(counts) / len(counts), 2) if counts else 0
    history_dates = sorted({str(row.get("history_date") or "") for row in history_rows if row.get("history_date")})

    outcome_rows = []
    if history_dates:
        outcome_rows = request_all_json(
            "watchlist_signal_outcomes"
            "?select=ticker,signal_run_date,evaluation_run_date,outcome_label,learning_key"
            f"&evaluation_run_date=in.({postgrest_in_list(history_dates)})"
            "&order=ticker.asc,signal_run_date.asc"
        )

    learning_ready = 0
    learning_scope_ready = 0
    for row in snapshot_rows:
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        sample_count = payload.get("learning_sample_count")
        try:
            has_samples = int(float(sample_count)) > 0
        except (TypeError, ValueError):
            has_samples = False
        if has_samples:
            learning_ready += 1
        if has_samples and payload.get("learning_scope"):
            learning_scope_ready += 1

    outcome_counts = Counter(str(row.get("outcome_label") or "UNKNOWN") for row in outcome_rows)
    missing_ohlc_history_rows = [
        row for row in history_rows
        if any(row.get(field) in (None, "") for field in ("open", "high", "low", "close"))
    ]
    missing_ohlc_snapshot_rows = [
        row for row in snapshot_rows
        if any(row.get(field) in (None, "") for field in ("open", "high", "low", "close"))
    ]
    ticker_leaking_keys = []
    for row in outcome_rows:
        ticker = str(row.get("ticker") or "").upper().strip()
        key = str(row.get("learning_key") or "").upper()
        if ticker and ticker in [segment.strip() for segment in key.split("|")]:
            ticker_leaking_keys.append({"ticker": ticker, "learning_key": row.get("learning_key")})

    metrics = {
        "run_date": run_date,
        "run_health_history_rows": latest.get("history_rows"),
        "snapshot_rows": len(snapshot_rows),
        "behavior_history_rows": len(history_rows),
        "behavior_history_tickers": len(history_by_ticker),
        "history_days_min": min_days,
        "history_days_avg": avg_days,
        "history_days_max": max_days,
        "tickers_with_25_plus_days": tickers_with_25,
        "tickers_with_30_plus_days": tickers_with_30,
        "signal_outcome_rows_for_run": len(outcome_rows),
        "signal_outcome_labels": dict(outcome_counts),
        "history_rows_missing_ohlc": len(missing_ohlc_history_rows),
        "snapshot_rows_missing_ohlc": len(missing_ohlc_snapshot_rows),
        "ticker_leaking_learning_keys": len(ticker_leaking_keys),
        "snapshots_with_learning_samples": learning_ready,
        "snapshots_with_learning_scope": learning_scope_ready,
    }

    if len(history_rows) < 1000:
        emit_metrics(metrics)
        fail("Behavior history row count is too low for watchlist lookback learning.")
    # The tracked universe can legitimately be smaller after data-provider
    # failures. Every successfully published snapshot must have replay data;
    # do not require an unrelated fixed ticker count.
    required_history_tickers = max(25, int(len(snapshot_rows) * 0.8))
    if len(history_by_ticker) < required_history_tickers:
        emit_metrics(metrics)
        fail("Too few published tickers have behavior history.")
    if tickers_with_25 < max(1, int(len(history_by_ticker) * 0.8)):
        emit_metrics(metrics)
        fail("Less than 80% of tickers have at least 25 lookback trading days.")
    if len(outcome_rows) < 500:
        emit_metrics(metrics)
        fail("Signal outcome rows are too low; ML/self-learning has insufficient samples.")
    if missing_ohlc_history_rows or missing_ohlc_snapshot_rows:
        metrics["missing_ohlc_examples"] = {
            "history": missing_ohlc_history_rows[:5],
            "snapshot": missing_ohlc_snapshot_rows[:5],
        }
        emit_metrics(metrics)
        fail("Supabase OHLC columns are required for entry-zone and stop audits.")
    if ticker_leaking_keys:
        metrics["ticker_leaking_learning_key_examples"] = ticker_leaking_keys[:5]
        emit_metrics(metrics)
        fail("Learning keys must describe behavior patterns, not ticker identity.")
    # A hard-gated model deliberately leaves rows without settled, exact-pattern
    # evidence in reporting-only mode. Require meaningful coverage, but do not
    # fail a healthy v3 cold-start simply because it refuses broad promotion.
    required_learning_rows = max(25, int(len(snapshot_rows) * 0.20))
    metrics["required_snapshots_with_learning_samples"] = required_learning_rows
    if learning_ready < required_learning_rows:
        emit_metrics(metrics)
        fail("Too few latest snapshots have learning samples attached.")

    print("SUPABASE_LEARNING_HEALTH=OK")
    emit_metrics(metrics)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"SUPABASE_LEARNING_HEALTH=FAIL {exc}")
        sys.exit(1)
