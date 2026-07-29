#!/usr/bin/env python3
"""Deterministic regression checks for bounded database learning storage."""

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import daily_watchlist_overview as scanner


def assert_ohlcv_window() -> None:
    assert scanner.OHLCV_RETENTION_BARS == 400
    assert scanner.OHLCV_MIN_READY_BARS == scanner.OHLCV_RETENTION_BARS

    requested = []
    newest = dt.date(2026, 7, 16)
    rows = [
        {
            "data_date": str(newest - dt.timedelta(days=offset)),
            "open": 100 + offset,
            "high": 101 + offset,
            "low": 99 + offset,
            "close": 100.5 + offset,
            "adjclose": 100.5 + offset,
            "volume": 1_000_000 + offset,
            "data_provider": "audit",
        }
        for offset in range(400)
    ]
    original_select = scanner.supabase_select
    scanner.supabase_select = lambda path: requested.append(path) or rows
    try:
        frame = scanner.load_ohlcv_from_supabase("NVDA")
    finally:
        scanner.supabase_select = original_select

    assert "order=data_date.desc" in requested[0]
    assert "limit=400" in requested[0]
    assert len(frame) == 400
    assert frame["date"].is_monotonic_increasing
    assert frame.iloc[-1]["date"].date() == newest


def assert_payload_compaction() -> None:
    row = {
        "publication_id": "audit-publication",
        "ticker": "NVDA",
        "date": "2026-07-16",
        "action": "WATCH",
        "adjusted_score": 61,
        "learning_scope": "personality",
        "empty_value": "",
    }
    typed = {
        "publication_id": row["publication_id"],
        "ticker": row["ticker"],
        "data_date": row["date"],
        "action": row["action"],
    }
    payload = scanner.compact_payload(row, typed, aliases=("date",), max_bytes=8192)
    assert payload == {"adjusted_score": 61, "learning_scope": "personality"}
    merged = scanner.merge_payload_row({**typed, "action": None, "payload": {**payload, "action": "BUY"}})
    assert merged["action"] == "BUY", "null typed columns must not erase payload fallbacks"
    assert merged["adjusted_score"] == 61
    assert merged["date"] == "2026-07-16"

    repeated_plan = "Execution blocked until the current market-data session is available."
    near_limit = {
        "core_evidence": "x" * (scanner.SUPABASE_HISTORY_PAYLOAD_MAX_BYTES - 325),
        "anti_signal_plan": repeated_plan,
        "execution_plan": repeated_plan,
        "freshness_plan": repeated_plan,
        "next_day_plan": repeated_plan,
        "freshness_block": "YES",
        "execution_fill_probability": 0.895,
        "execution_fill_sample_count": 15,
    }
    raw_bytes = len(json.dumps(near_limit, separators=(",", ":")).encode("utf-8"))
    assert raw_bytes > scanner.SUPABASE_HISTORY_PAYLOAD_MAX_BYTES
    compacted = scanner.compact_payload(
        {
            **near_limit,
            "raw_window_hash": "a" * 64,
            "indicator_state_version": scanner.INDICATOR_STATE_VERSION,
            "execution_fill_model_version": scanner.LEARNING_MODEL_VERSION,
        },
        {},
        aliases=scanner.SUPABASE_HISTORY_PAYLOAD_ALIASES,
        max_bytes=scanner.SUPABASE_HISTORY_PAYLOAD_MAX_BYTES,
    )
    compacted_bytes = len(json.dumps(compacted, separators=(",", ":")).encode("utf-8"))
    assert compacted_bytes <= scanner.SUPABASE_HISTORY_PAYLOAD_MAX_BYTES
    assert "anti_signal_plan" in compacted
    assert "execution_plan" not in compacted
    assert "freshness_plan" in compacted
    assert "next_day_plan" not in compacted
    assert compacted["execution_fill_probability"] == 0.895
    assert compacted["execution_fill_sample_count"] == 15
    assert "raw_window_hash" not in compacted
    assert "indicator_state_version" not in compacted
    assert "execution_fill_model_version" not in compacted

    overflow_payload = scanner.compact_payload(
        {
            "action": "SETUP FORMING",
            "operator_plan": "x" * 7000,
            "anti_signal_plan": "Keep core risk context.",
        },
        {"action": "SETUP FORMING"},
        max_bytes=128,
    )
    assert "operator_plan" not in overflow_payload
    assert overflow_payload["anti_signal_plan"] == "Keep core risk context."

    distinct_plans = scanner.deduplicate_payload_narratives({
        "operator_plan": "Operator pressure is neutral.",
        "operator_state_plan": "Accumulation remains constructive.",
    })
    assert set(distinct_plans) == {"operator_plan", "operator_state_plan"}

    try:
        scanner.compact_payload({"large": "x" * 20}, {}, max_bytes=10)
    except ValueError:
        pass
    else:
        raise AssertionError("oversized payloads must fail closed")


def assert_capacity_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    guard = (root / "scripts/database_capacity_guard.sh").read_text()
    workflow = (root / ".github/workflows/daily-watchlist-pages.yml").read_text()
    schema = (root / "supabase_schema.sql").read_text()

    for contract in (
        "readonly WARNING_BYTES=175000000",
        "readonly STAGING_LIMIT_BYTES=220000000",
        "readonly HARD_LIMIT_BYTES=250000000",
        "readonly MAX_TICKERS=250",
        "readonly OHLCV_BARS_PER_TICKER=400",
        "readonly OHLCV_MAX_ROWS=100000",
        "readonly LEARNING_SESSIONS=100",
        "readonly CALIBRATION_MAX_ARTIFACTS=8",
        "readonly CALIBRATION_MAX_BYTES=8000000",
        "readonly MAX_STAGED_PUBLICATION_BYTES=85000000",
        "readonly OHLCV_MAX_BYTES=65000000",
        "readonly BEHAVIOR_MAX_BYTES=40000000",
        "readonly OUTCOME_MAX_BYTES=45000000",
        "ohlcv_growth_reserve + MAX_STAGED_PUBLICATION_BYTES",
        "record_storage_metrics",
        "evaluation_run_date not in",
        "delete from public.watchlist_learning_state",
        "delete from public.watchlist_indicator_state",
        "delete from public.watchlist_calibration_artifacts",
        "select source_publication_id from public.watchlist_calibration_artifacts",
        "active_publication_id = :'publication_id'",
        "control.previous_publication_id",
    ):
        assert contract in guard, contract
    assert "scripts/database_capacity_guard.sh prepare" in workflow
    assert "scripts/database_capacity_guard.sh staged" in workflow
    assert "scripts/database_capacity_guard.sh finalize" in workflow
    assert "scripts/database_capacity_guard.sh rollback" in workflow
    assert workflow.index("Reserve Supabase publishing headroom") < workflow.index("Refresh watchlist")
    assert workflow.index("Enforce staged database ceiling") < workflow.index("Deploy to GitHub Pages")
    assert "drop constraint if exists watchlist_snapshots_pkey" not in schema
    assert "drop constraint if exists watchlist_behavior_history_pkey" not in schema
    assert "create table if not exists public.watchlist_learning_state" in schema
    assert "create table if not exists public.watchlist_indicator_state" in schema
    assert "create table if not exists public.watchlist_calibration_artifacts" in schema
    assert "payload_bytes > 0 and payload_bytes <= 2097152" in schema
    assert "watchlist_snapshots_payload_bytes" in schema
    assert "watchlist_outcomes_payload_bytes" in schema
    scanner_source = (root / "daily_watchlist_overview.py").read_text()
    assert "estimate_supabase_publication_bytes" in scanner_source
    assert scanner_source.index("estimated_publication_bytes = estimate_supabase_publication_bytes") < scanner_source.index("supabase_upsert_refresh_run([publishing_metadata])")
    estimate = scanner.estimate_supabase_publication_bytes([{"payload": "x" * 1000}])
    assert 5_000_000 < estimate < scanner.SUPABASE_MAX_STAGED_PUBLICATION_BYTES


if __name__ == "__main__":
    assert_ohlcv_window()
    assert_payload_compaction()
    assert_capacity_contract()
    print("Database capacity audit passed: compact payloads, 400-bar OHLCV, 100-session learning baseline, and transactional guards verified.")
