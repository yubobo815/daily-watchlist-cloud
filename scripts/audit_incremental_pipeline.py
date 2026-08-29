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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from weekly_retry_gate import retry_decision


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
        "take_profit_1": 107,
        "target_est": 110,
        "close": 102,
        "score": 80,
        "freshness_block": "NO",
    }


def audit_incremental_settlement() -> None:
    bars = pd.DataFrame(
        [
            {"date": f"2026-07-0{day}", "open": 102, "high": 106 if day == 2 else 108 if day < 6 else 111, "low": 100, "close": 105 if day == 2 else 106 if day < 6 else 110, "volume": 1000}
            for day in range(2, 7)
        ]
    )
    outcome = scanner.build_incremental_signal_outcomes([sample_signal()], {"TEST": bars}, pd.DataFrame())
    assert len(outcome) == 1 and outcome.iloc[0]["outcome_label"] == "WORKING"
    assert outcome.iloc[0]["signal_run_date"] == "2026-07-01"
    assert outcome.iloc[0]["evaluation_run_date"] == "2026-07-06", "learning must continue from TP1 through the frozen further target"
    assert scanner.build_incremental_signal_outcomes([sample_signal()], {"TEST": bars}, outcome).empty
    frozen = scanner.freeze_final_signal_history(
        [{**sample_signal(), "action": "BUY CANDIDATE"}],
        [{**sample_signal(), "action": "SETUP FORMING", "prediction_state": "FINAL"}],
        30,
    )
    assert frozen[-1]["action"] == "SETUP FORMING" and frozen[-1]["prediction_state"] == "FINAL"
    rebuilt = scanner.rebuild_canonical_signal_outcomes(outcome, {"TEST": bars})
    assert len(rebuilt) == 1 and rebuilt.iloc[0]["outcome_label"] == outcome.iloc[0]["outcome_label"]
    assert rebuilt.iloc[0]["prior_take_profit_1"] == 107

    # The raised stop after TP1 is part of the frozen execution plan. Losing it
    # makes a later rebuild settle the same signal on a different date.
    managed_signal = {
        **sample_signal(),
        "post_tp1_stop": 104,
        "shadow_hard_blockers": ["manual safety block"],
        "shadow_policy_allowed": "NO",
        "hard_exit_pressure": "NO",
        "confirmed_break": "NO",
        "volatility_regime": "NORMAL",
        "distance_from_ref_zone_atr": 0.5,
    }
    managed_bars = pd.DataFrame([
        {"date": "2026-07-02", "open": 100, "high": 108, "low": 99.5, "close": 107, "volume": 1000},
        {"date": "2026-07-03", "open": 105, "high": 106, "low": 103, "close": 104, "volume": 1000},
        {"date": "2026-07-06", "open": 104, "high": 106, "low": 103, "close": 105, "volume": 1000},
        {"date": "2026-07-07", "open": 105, "high": 107, "low": 104, "close": 106, "volume": 1000},
        {"date": "2026-07-08", "open": 106, "high": 108, "low": 105, "close": 107, "volume": 1000},
    ])
    managed = scanner.build_incremental_signal_outcomes(
        [managed_signal], {"TEST": managed_bars}, pd.DataFrame()
    )
    managed_rebuilt = scanner.rebuild_canonical_signal_outcomes(
        managed, {"TEST": managed_bars}
    )
    assert managed.iloc[0]["prior_post_tp1_stop"] == 104
    assert managed.iloc[0]["evaluation_run_date"] == "2026-07-03"
    assert managed_rebuilt.iloc[0]["evaluation_run_date"] == "2026-07-03"
    assert scanner.calibration_parity_report(
        managed, managed_rebuilt, {"TEST": "2026-06-01"}
    )["passed"] is True
    frozen_fields = (
        "prior_post_tp1_stop",
        "prior_freshness_block",
        "prior_shadow_hard_blockers",
        "prior_shadow_policy_allowed",
        "prior_hard_exit_pressure",
        "prior_confirmed_break",
        "prior_volatility_regime",
        "prior_distance_from_ref_zone_atr",
    )
    managed_row = managed.iloc[0].to_dict()
    typed = {
        key: managed_row.get(key)
        for key in ("signal_run_date", "evaluation_run_date", "ticker", "outcome_label")
    }
    persisted = {
        **typed,
        "payload": scanner.compact_payload(managed_row, typed, max_bytes=2048),
    }
    round_tripped = scanner.merge_payload_row(persisted)
    assert all(round_tripped.get(key) == managed_row.get(key) for key in frozen_fields)

    alias_signal = {**sample_signal(), "ticker": "BRK.B"}
    alias_outcome = scanner.build_incremental_signal_outcomes(
        [alias_signal], {"BRK-B": bars}, pd.DataFrame()
    )
    alias_rebuilt = scanner.rebuild_canonical_signal_outcomes(
        alias_outcome, {"BRK-B": bars}
    )
    assert len(alias_outcome) == 1 and len(alias_rebuilt) == 1
    assert scanner.calibration_parity_report(
        alias_outcome, alias_rebuilt, {"BRK.B": "2026-06-01"}
    )["passed"] is True

    # Rows read from Supabase include the publication date as run_date. It
    # must never replace the actual historical market session in the identity.
    persisted_history_signal = {
        **sample_signal(),
        "run_date": "2026-08-09",
        "history_date": "2026-07-01",
    }
    persisted_outcome = scanner.build_incremental_signal_outcomes(
        [persisted_history_signal], {"TEST": bars}, pd.DataFrame()
    )
    assert persisted_outcome.iloc[0]["signal_run_date"] == "2026-07-01"
    assert scanner.signal_outcome_identity(persisted_outcome.iloc[0].to_dict())[1] == "2026-07-01"
    persisted_parity = scanner.calibration_parity_report(
        persisted_outcome,
        scanner.rebuild_canonical_signal_outcomes(persisted_outcome, {"TEST": bars}),
        {"TEST": "2026-06-01"},
    )
    assert persisted_parity["passed"] is True
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
    assert boundary_loss["sample_missing_from_rebuild"][0][0] == "OLD"
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
        if path.startswith("watchlist_publication_control?"):
            return [{"active_publication_id": "pub-complete"}]
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
    compatible = {
        "incremental_state_ready": True,
        "incremental_state_version": scanner.INCREMENTAL_STATE_VERSION,
        "learning_model_version": scanner.LEARNING_MODEL_VERSION,
    }
    assert scanner.compatible_incremental_metadata(compatible) == compatible
    assert scanner.compatible_incremental_metadata(
        {**compatible, "incremental_state_version": "incremental-state-v1"}
    ) == {}

    with tempfile.TemporaryDirectory() as directory:
        history_path = Path(directory) / "history.html"
        scanner.write_history_html(history_path)
        source = history_path.read_text()
        assert "{json.dumps(" not in source
        assert "watchlist_publication_control?select=active_publication_id" in source
        assert "publication_id=eq.${encodeURIComponent(publicationId)}" in source
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/daily-watchlist-pages.yml").read_text()
    scanner_source = (root / "daily_watchlist_overview.py").read_text()
    assert "allow_calibration_bootstrap" in workflow
    assert "use_stored_ohlcv" in workflow
    assert "force_bootstrap = bool(args.allow_calibration_bootstrap" in scanner_source
    assert '"supabase", "STORED_REPLAY"' in scanner_source
    assert "if previous_incremental_metadata and not needs_bootstrap:" in scanner_source
    assert "position_value_1k_risk = required_position_value" in scanner_source
    assert "actual_risk_dollars = suggested_position_value" in scanner_source
    daily_cron = 'cron: "17 23 * * 1-5"'
    weekly_cron = 'cron: "47 03 * * 6"'
    retry_cron = 'cron: "47 07 * * 6"'
    assert all(cron in workflow for cron in (daily_cron, weekly_cron, retry_cron))
    assert "run-name: Daily Watchlist Pages (${{ github.event.schedule" in workflow
    assert 'cron: "17 23 * * 1-4"' not in workflow
    assert 'cron: "17 23 * * 5"' not in workflow
    assert '--refresh-mode "${{ steps.time_gate.outputs.refresh_mode }}"' in workflow
    assert '${{ steps.time_gate.outputs.stored_ohlcv_arg }}' in workflow
    assert "parity must never be bypassed implicitly" in scanner_source
    assert workflow.index("Mark Supabase publication validated") < workflow.index("Deploy immutable Pages artifact")
    assert workflow.index("Verify deployed Pages publication") < workflow.index("Activate Supabase publication")
    assert "build-publication:" in workflow and "deploy-pages:" in workflow and "verify-and-activate:" in workflow
    assert "restore-pages-after-failed-activation:" in workflow
    assert 'EVENT_SCHEDULE: ${{ github.event.schedule }}' in workflow
    weekly_gate_start = workflow.index('if [ "$EVENT_SCHEDULE" = "47 03 * * 6" ]')
    retry_gate_start = workflow.index('if [ "$EVENT_SCHEDULE" = "47 07 * * 6" ]')
    default_gate_start = workflow.index("# Scheduled jobs can start well after", retry_gate_start)
    weekly_gate = workflow[weekly_gate_start:retry_gate_start]
    retry_gate = workflow[retry_gate_start:default_gate_start]
    default_gate = workflow[default_gate_start:workflow.index("      - name: Set up Python", default_gate_start)]
    assert 'echo "run=true" >> "$GITHUB_OUTPUT"' in weekly_gate
    assert 'echo "refresh_mode=weekly_rebuild" >> "$GITHUB_OUTPUT"' in weekly_gate
    assert 'echo "stored_ohlcv_arg=--stored-ohlcv-only" >> "$GITHUB_OUTPUT"' in weekly_gate
    assert "scripts/weekly_retry_gate.py" in retry_gate
    assert 'if [ "$retry_decision" != "retry" ]' in retry_gate
    assert 'echo "run=false" >> "$GITHUB_OUTPUT"' in retry_gate
    assert 'echo "run=true" >> "$GITHUB_OUTPUT"' in retry_gate
    assert 'echo "refresh_mode=weekly_rebuild" >> "$GITHUB_OUTPUT"' in retry_gate
    assert 'echo "stored_ohlcv_arg=--stored-ohlcv-only" >> "$GITHUB_OUTPUT"' in retry_gate
    assert 'echo "run=true" >> "$GITHUB_OUTPUT"' in default_gate
    assert 'echo "refresh_mode=daily" >> "$GITHUB_OUTPUT"' in default_gate
    assert "github.run_id || 'publication'" in workflow


def audit_weekly_retry_selector() -> None:
    current = {
        "id": 200,
        "event": "schedule",
        "status": "in_progress",
        "conclusion": None,
        "created_at": "2026-08-29T13:21:14Z",
        "display_title": "Daily Watchlist Pages (47 07 * * 6)",
    }
    daily = {
        "id": 100,
        "event": "schedule",
        "status": "completed",
        "conclusion": "failure",
        "created_at": "2026-08-28T23:17:00Z",
        "display_title": "Daily Watchlist Pages (17 23 * * 1-5)",
    }
    delayed_same_day_daily = {
        "id": 101,
        "event": "schedule",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-08-29T04:09:04Z",
        "display_title": "Daily Watchlist Pages (17 23 * * 1-5)",
    }

    def decide(status: str, conclusion) -> str:
        primary = {
            "id": 150,
            "event": "schedule",
            "status": status,
            "conclusion": conclusion,
            "created_at": "2026-08-29T10:25:44Z",
            "display_title": "Daily Watchlist Pages (47 03 * * 6)",
        }
        return retry_decision(
            {"workflow_runs": [current, daily, delayed_same_day_daily, primary]}, "200"
        )[0]

    assert decide("completed", "success") == "skip"
    assert decide("queued", None) == "skip"
    assert decide("in_progress", None) == "skip"
    for conclusion in ("failure", "cancelled", "timed_out", "startup_failure", "stale", "action_required"):
        assert decide("completed", conclusion) == "retry"
    assert retry_decision(
        {"workflow_runs": [current, daily, delayed_same_day_daily]}, "200"
    )[0] == "retry"

    # Before run-name tagging, choose the most recently started run. This is
    # the exact delayed-schedule ordering from the 2026-08-29 incident.
    legacy_primary = {
        "id": 151,
        "event": "schedule",
        "status": "completed",
        "conclusion": "failure",
        "created_at": "2026-08-29T10:25:44Z",
    }
    legacy_daily = {
        key: value
        for key, value in delayed_same_day_daily.items()
        if key != "display_title"
    }
    legacy_current = {key: value for key, value in current.items() if key != "display_title"}
    decision, reason = retry_decision(
        {"workflow_runs": [legacy_current, legacy_daily, legacy_primary]}, "200"
    )
    assert decision == "retry"
    assert "151" in reason


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
        if path.startswith("watchlist_publication_control"):
            return [{"active_publication_id": "publication-ok"}]
        if path.startswith("watchlist_refresh_runs"):
            return [{"publication_id": "publication-ok", "status": "ok", "payload": {}}]
        return [candidate]

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
    audit_weekly_retry_selector()
    audit_artifact_integrity()
    audit_provider_circuit()
    print({"incrementalPipelineUAT": "ok", "cases": 8})


if __name__ == "__main__":
    main()
