#!/usr/bin/env python3
"""Offline UAT for daily incremental state and weekly rebuild contracts."""

from datetime import datetime
from pathlib import Path
import sys
import tempfile
import hashlib
import json
from zoneinfo import ZoneInfo

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daily_watchlist_overview as scanner


def frame(start: str, periods: int, base: float = 100.0) -> pd.DataFrame:
    dates = pd.bdate_range(start, periods=periods)
    return pd.DataFrame(
        {
            "date": dates,
            "open": [base + index for index in range(periods)],
            "high": [base + index + 2 for index in range(periods)],
            "low": [base + index - 2 for index in range(periods)],
            "close": [base + index + 1 for index in range(periods)],
            "adjclose": [base + index + 1 for index in range(periods)],
            "volume": [1_000_000 + index for index in range(periods)],
        }
    )


def audit_ohlcv_modes() -> None:
    stored = frame("2024-01-02", 400)
    original_hash = scanner.ohlcv_window_hash(stored)
    corrected = stored.copy()
    corrected.loc[corrected.index[-1], "close"] += 0.01
    assert scanner.ohlcv_window_hash(corrected) != original_hash
    overlap_start = stored.iloc[-10]["date"]
    live = frame(str(overlap_start.date()), 12, base=500.0)
    calls, writes = [], []
    originals = scanner.load_ohlcv_from_supabase, scanner.fetch_chart, scanner.persist_ohlcv_to_supabase
    scanner.load_ohlcv_from_supabase = lambda _ticker: stored.copy()

    def fetch(_ticker, years, refresh, provider_circuit=None):
        calls.append((years, refresh))
        return scanner.attach_data_provider(live.copy(), "polygon", "LIVE_OK")

    scanner.fetch_chart = fetch
    scanner.persist_ohlcv_to_supabase = lambda _ticker, rows: writes.append(rows.copy())
    try:
        daily = scanner.load_or_refresh_ohlcv("TEST", years=2, refresh=True)
        assert calls[-1][0] == scanner.OHLCV_INCREMENTAL_YEARS
        assert len(daily) == scanner.OHLCV_RETENTION_BARS
        assert daily["date"].is_monotonic_increasing and daily["date"].is_unique
        assert 1 <= len(writes[-1]) <= len(live)
        assert daily.attrs["data_provider"] == "polygon"

        scanner.load_or_refresh_ohlcv("TEST", years=2, refresh=True, force_full=True)
        assert calls[-1][0] == 2
        assert len(writes[-1]) == scanner.OHLCV_RETENTION_BARS
    finally:
        scanner.load_ohlcv_from_supabase, scanner.fetch_chart, scanner.persist_ohlcv_to_supabase = originals


def sample_signal() -> dict:
    return {
        "ticker": "TEST",
        "date": "2026-07-01",
        "action": "BUY CANDIDATE",
        "setup": "PULLBACK BUY",
        "personality_type": "BALANCED",
        "operator_state": "ACCUMULATION",
        "anti_signal_level": "NONE",
        "market_permission": "ALLOW",
        "ticker_permission": "ALLOW",
        "risk_permission": "ALLOW",
        "walk_forward_permission": "ALLOW",
        "personality_setup_allowed": True,
        "entry_zone_low": 99,
        "entry_zone_high": 101,
        "entry_est": 100,
        "stop_est": 95,
        "target_est": 110,
        "close": 102,
        "score": 80,
        "freshness_block": "NO",
    }


def audit_incremental_settlement() -> None:
    bars = pd.DataFrame(
        [
            {"date": f"2026-07-0{day}", "open": 102, "high": 108 if day < 6 else 111, "low": 100, "close": 106 if day < 6 else 110, "volume": 1000}
            for day in range(2, 7)
        ]
    )
    outcome = scanner.build_incremental_signal_outcomes([sample_signal()], {"TEST": bars}, pd.DataFrame())
    assert len(outcome) == 1 and outcome.iloc[0]["outcome_label"] == "WORKING"
    assert scanner.build_incremental_signal_outcomes([sample_signal()], {"TEST": bars}, outcome).empty
    frozen = scanner.freeze_final_signal_history(
        [{**sample_signal(), "action": "BUY CANDIDATE"}],
        [{**sample_signal(), "action": "SETUP FORMING", "prediction_state": "FINAL"}],
        30,
    )
    assert frozen[-1]["action"] == "SETUP FORMING" and frozen[-1]["prediction_state"] == "FINAL"
    rebuilt = scanner.rebuild_canonical_signal_outcomes(outcome, {"TEST": bars})
    assert len(rebuilt) == 1 and rebuilt.iloc[0]["outcome_label"] == outcome.iloc[0]["outcome_label"]
    legacy = outcome.copy()
    legacy.loc[legacy.index[0], "entry_model_version"] = ""
    assert scanner.calibration_parity_report(legacy, legacy, {"TEST": "2026-06-01"})["incremental_settled"] == 0
    replay_starts = {"TEST": "2026-06-01", "NEW": "2026-06-01", "OLD": "2026-06-01"}
    assert scanner.calibration_parity_report(outcome, outcome, replay_starts)["passed"] is True
    changed = outcome.copy()
    changed.loc[changed.index[0], "outcome_label"] = "FAILED"
    assert scanner.calibration_parity_report(outcome, changed, replay_starts)["passed"] is False
    additive = outcome.copy()
    extra = outcome.iloc[0].copy()
    extra["ticker"] = "NEW"
    extra["signal_run_date"] = "2026-07-02"
    extra["evaluation_run_date"] = "2026-07-08"
    additive = pd.concat([additive, pd.DataFrame([extra])], ignore_index=True)
    additive_report = scanner.calibration_parity_report(outcome, additive, replay_starts)
    assert additive_report["passed"] is True and additive_report["newly_available"] == 1
    incomplete_incremental = pd.concat([outcome, additive.assign(evaluation_run_date=outcome.iloc[0]["evaluation_run_date"])])
    incomplete_report = scanner.calibration_parity_report(incomplete_incremental, outcome, replay_starts)
    assert incomplete_report["passed"] is False and incomplete_report["missing_from_rebuild"] == 1
    earliest = outcome.copy()
    earliest.loc[earliest.index[0], "ticker"] = "OLD"
    earliest.loc[earliest.index[0], "signal_run_date"] = "2026-06-01"
    earliest.loc[earliest.index[0], "evaluation_run_date"] = outcome.iloc[0]["evaluation_run_date"]
    boundary_loss = scanner.calibration_parity_report(
        pd.concat([earliest, outcome], ignore_index=True), outcome, replay_starts
    )
    assert boundary_loss["passed"] is False and boundary_loss["missing_from_rebuild"] == 1
    preserved = scanner.preserve_failed_ticker_history(
        [{"ticker": "TEST", "date": "2026-07-02"}],
        {"TEST": [sample_signal()], "FAIL": [{**sample_signal(), "ticker": "FAIL"}]},
        {"TEST", "FAIL"},
        30,
    )
    assert {row["ticker"] for row in preserved} == {"TEST", "FAIL"}


def audit_supabase_history_pagination() -> None:
    original_select = scanner.supabase_select
    calls = []

    def select(path):
        calls.append(path)
        offset = int(path.rsplit("offset=", 1)[1])
        remaining = max(0, 2350 - offset)
        return [{"row": index} for index in range(offset, offset + min(1000, remaining))]

    scanner.supabase_select = select
    try:
        rows = scanner.supabase_select_all(
            "watchlist_behavior_history?select=*&publication_id=eq.test&order=ticker.asc,history_date.asc"
        )
    finally:
        scanner.supabase_select = original_select

    assert len(rows) == 2350
    assert [row["row"] for row in rows] == list(range(2350))
    assert [path.rsplit("offset=", 1)[1] for path in calls] == ["0", "1000", "2000", "2350"]
    assert all("order=ticker.asc,history_date.asc" in path for path in calls)

    for total, expected_calls in ((999, 2), (1000, 2), (1001, 3), (2000, 3), (2001, 4)):
        boundary_calls = []

        def boundary_select(path, row_count=total):
            boundary_calls.append(path)
            offset = int(path.rsplit("offset=", 1)[1])
            return [{"row": index} for index in range(offset, min(offset + 1000, row_count))]

        scanner.supabase_select = boundary_select
        try:
            boundary_rows = scanner.supabase_select_all(
                "watchlist_behavior_history?select=*&order=ticker.asc"
            )
        finally:
            scanner.supabase_select = original_select
        assert len(boundary_rows) == total and len(boundary_calls) == expected_calls

    capped_calls = []

    def capped_select(path):
        capped_calls.append(path)
        offset = int(path.rsplit("offset=", 1)[1])
        return [{"row": index} for index in range(offset, min(offset + 100, 2350))]

    scanner.supabase_select = capped_select
    try:
        capped_rows = scanner.supabase_select_all("watchlist_behavior_history?select=*&order=ticker.asc")
    finally:
        scanner.supabase_select = original_select
    assert len(capped_rows) == 2350 and len(capped_calls) == 25


def audit_daily_history_inherits_full_publication() -> None:
    original_select = scanner.supabase_select
    ticker_count = 186
    sessions = 30

    def select(path):
        if path.startswith("watchlist_refresh_runs?"):
            return [{"run_date": "2026-07-22", "publication_id": "pub-complete", "payload": {}}]
        offset = int(path.rsplit("offset=", 1)[1])
        all_rows = [
            {
                "ticker": f"T{ticker:03d}",
                "history_date": str(date.date()),
                "publication_id": "pub-complete",
                "payload": {"date": str(date.date()), "close": 100 + session},
            }
            for ticker in range(ticker_count)
            for session, date in enumerate(pd.bdate_range("2026-06-11", periods=sessions))
        ]
        return all_rows[offset : offset + 1000]

    scanner.supabase_select = select
    try:
        inherited = scanner.fetch_previous_behavior_history("2026-07-23")
    finally:
        scanner.supabase_select = original_select

    assert len(inherited) == ticker_count * sessions
    coverage = pd.DataFrame(inherited).groupby("ticker")["history_date"].nunique()
    assert len(coverage) == ticker_count and int(coverage.min()) == sessions
    tickers = [f"T{ticker:03d}" for ticker in range(ticker_count)]
    assert scanner.incremental_history_ready(inherited, tickers, sessions, len(inherited))
    partial = [row for row in inherited if int(row["ticker"][1:]) < 33]
    assert not scanner.incremental_history_ready(partial, tickers, sessions, len(inherited))


def audit_rolling_window_and_modes() -> None:
    rows = []
    for index, date in enumerate(pd.bdate_range("2026-03-02", periods=61)):
        rows.append(
            {
                **scanner.score_signal_horizon(sample_signal(), []),
                "signal_run_date": str((date - pd.Timedelta(days=7)).date()),
                "evaluation_run_date": str(date.date()),
                "ticker": f"T{index:03d}",
                "path_status": "SETTLED",
                "outcome_label": "WORKING",
                "forecast_learnable": True,
                "entry_model_version": scanner.LEARNING_MODEL_VERSION,
                "label_horizon_sessions": scanner.LEARNING_HORIZON_SESSIONS,
            }
        )
    retained = scanner.restrict_learning_outcomes_to_window(pd.DataFrame(rows), "2027-01-01", 60)
    assert retained["evaluation_run_date"].nunique() == 60
    assert retained["evaluation_run_date"].min() == rows[1]["evaluation_run_date"]
    saturday = datetime(2026, 7, 25, 10, tzinfo=ZoneInfo("Australia/Melbourne"))
    monday = datetime(2026, 7, 27, 10, tzinfo=ZoneInfo("Australia/Melbourne"))
    assert scanner.resolve_refresh_mode("auto", saturday) == "weekly_rebuild"
    assert scanner.resolve_refresh_mode("auto", monday) == "daily"

    with tempfile.TemporaryDirectory() as directory:
        history_path = Path(directory) / "history.html"
        scanner.write_history_html(history_path)
        source = history_path.read_text()
        assert "{json.dumps(" not in source
        assert "watchlist_refresh_runs?select=publication_id" in source
        assert "publication_id=eq.${encodeURIComponent(publicationId)}" in source
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/daily-watchlist-pages.yml").read_text()
    scanner_source = (root / "daily_watchlist_overview.py").read_text()
    assert "allow_calibration_bootstrap" in workflow
    assert 'cron: "17 23 * * 1-4"' in workflow and 'cron: "17 23 * * 5"' in workflow
    assert '--refresh-mode "${{ steps.time_gate.outputs.refresh_mode }}"' in workflow
    assert "parity must never be bypassed implicitly" in scanner_source
    assert workflow.index("Finalize Supabase publication") < workflow.index("Deploy to GitHub Pages")
    assert "if: always() && steps.time_gate.outputs.run == 'true' && steps.finalize_publication.outcome == 'success'" in workflow


def audit_artifact_integrity() -> None:
    feature_count = len(scanner.DIRECTIONAL_NUMERIC_FEATURES) + len(scanner.DIRECTIONAL_PERSONALITIES)
    payload = {
        "source_publication_id": "publication-ok",
        "artifact_version": scanner.CALIBRATION_ARTIFACT_VERSION,
        "scanner_version": scanner.SCANNER_VERSION,
        "learning_model_version": scanner.LEARNING_MODEL_VERSION,
        "directional_model_version": scanner.DIRECTIONAL_MODEL_VERSION,
        "feature_count": feature_count,
        "label_count": len(scanner.DIRECTIONAL_LABELS),
        "cutoff_date": "2026-07-21",
        "metrics": {"passed": False, "validated_personalities": []},
        "model": {
            "center": [0.0] * feature_count,
            "scale": [1.0] * feature_count,
            "coefficients": [[0.0] * len(scanner.DIRECTIONAL_LABELS) for _ in range(feature_count + 1)],
            "priors": [1 / 3] * len(scanner.DIRECTIONAL_LABELS),
            "sample_count": 1000,
        },
        "train_sample_count": 1000,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    payload["content_hash"] = digest
    payload["artifact_id"] = f"cal-v1-20260721-{digest[:16]}"
    candidate = {
        **{key: payload[key] for key in (
            "artifact_id", "source_publication_id", "cutoff_date", "artifact_version", "scanner_version",
            "learning_model_version", "directional_model_version", "content_hash",
        )},
        "payload_bytes": scanner.calibration_payload_bytes(payload),
        "payload": payload,
    }
    original = scanner.supabase_select

    def select(path):
        return [{"publication_id": "publication-ok", "status": "ok", "payload": {}}] if path.startswith("watchlist_refresh_runs") else [candidate]

    scanner.supabase_select = select
    try:
        assert scanner.fetch_active_calibration_artifact()["artifact_id"] == payload["artifact_id"]
        candidate["content_hash"] = "tampered"
        assert scanner.fetch_active_calibration_artifact() is None
    finally:
        scanner.supabase_select = original


def audit_provider_circuit() -> None:
    circuit = scanner.MarketDataProviderCircuit(failure_limit=2)
    circuit.record_failure("polygon", RuntimeError("Polygon HTTP 404: unknown ticker"))
    assert not circuit.is_open("polygon")
    circuit.record_failure("polygon", RuntimeError("request timed out"))
    assert not circuit.is_open("polygon")
    circuit.record_failure("polygon", RuntimeError("HTTP 429: rate limit exceeded"))
    assert circuit.is_open("polygon")


def main() -> None:
    audit_ohlcv_modes()
    audit_incremental_settlement()
    audit_supabase_history_pagination()
    audit_daily_history_inherits_full_publication()
    audit_rolling_window_and_modes()
    audit_artifact_integrity()
    audit_provider_circuit()
    print({"incrementalPipelineUAT": "ok", "cases": 7})


if __name__ == "__main__":
    main()
