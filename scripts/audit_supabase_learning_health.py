#!/usr/bin/env python3
"""Execute the publication health state machine against bounded fixtures."""

from __future__ import annotations

import contextlib
import io
import os

import supabase_learning_health as health


RUN_DATE = "2026-07-17"
PUBLICATION_ID = "pub-test"


def fixture_rows(*, invalid_promotion: bool = False):
    history = [
        {
            "ticker": f"T{ticker:02d}",
            "history_date": f"2026-06-{day:02d}",
            "open": 100,
            "high": 102,
            "low": 99,
            "close": 101,
            "payload": {"publication_id": PUBLICATION_ID},
        }
        for ticker in range(40)
        for day in range(1, 31)
    ]
    snapshots = []
    for ticker in range(40):
        payload = {
            "publication_id": PUBLICATION_ID,
            "learning_sample_count": 30,
            "learning_scope": "exact signal personality",
            "learning_promotion_eligible": False,
        }
        if invalid_promotion and ticker == 0:
            payload["learning_promotion_eligible"] = True
        snapshots.append({
            "ticker": f"T{ticker:02d}", "open": 100, "high": 102, "low": 99, "close": 101,
            "payload": payload,
        })
    outcomes = []
    for index in range(500):
        payload = {
            "publication_id": PUBLICATION_ID,
            "label_horizon_sessions": 5,
            "path_status": "SETTLED",
            "prior_prediction_upside_probability": 0.5,
            "prior_prediction_downside_probability": 0.25,
            "prior_prediction_no_edge_probability": 0.25,
            "prior_prediction_state": "WALK_FORWARD",
            "prior_prediction_key": "SETUP FORMING|PULLBACK BUY|BALANCED|ACCUMULATION|NONE",
            "prior_prediction_scope": "exact signal personality",
        }
        outcomes.append({
            "publication_id": PUBLICATION_ID,
            "ticker": f"T{index % 40:02d}",
            "signal_run_date": "2026-06-01",
            "evaluation_run_date": "2026-06-08",
            "outcome_label": "WORKING" if index % 2 else "STALE",
            "learning_key": payload["prior_prediction_key"],
            "entry_model_version": "five-session-r-risk-v4",
            "forecast_learnable": True,
            "payload": payload,
        })
    return history, snapshots, outcomes


def run_fixture(*, finalize: bool, invalid_promotion: bool = False) -> int:
    history, snapshots, outcomes = fixture_rows(invalid_promotion=invalid_promotion)
    run = {
        "publication_id": PUBLICATION_ID,
        "run_date": RUN_DATE,
        "status": "pending_audit",
        "history_rows": len(history),
        "snapshot_rows": len(snapshots),
        "payload": {
            "publication_id": PUBLICATION_ID,
            "sync_state": "complete",
            "scanner_status": "ok",
            "synced_snapshot_rows": len(snapshots),
            "synced_history_rows": len(history),
            "synced_outcome_rows": len(outcomes),
            "learning_model_version": "five-session-r-risk-v4",
            "learning_horizon_sessions": 5,
            "directional_model_validated": False,
        },
    }
    marked = []
    originals = {
        "latest_synced_run_date": health.latest_synced_run_date,
        "request_json": health.request_json,
        "request_all_json": health.request_all_json,
        "mark_run_validated": health.mark_run_validated,
    }
    health.latest_synced_run_date = lambda: RUN_DATE
    health.request_json = lambda path, count=False: ([run], None)

    def request_all(path, **_kwargs):
        if path.startswith("watchlist_behavior_history"):
            return history
        if path.startswith("watchlist_snapshots"):
            return snapshots
        if path.startswith("watchlist_signal_outcomes"):
            return outcomes
        raise AssertionError(path)

    health.request_all_json = request_all
    health.mark_run_validated = lambda *args: marked.append(args)
    os.environ["EXPECTED_RUN_DATE"] = RUN_DATE
    os.environ["EXPECTED_PUBLICATION_ID"] = PUBLICATION_ID
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            health.main(finalize=finalize)
    finally:
        for name, value in originals.items():
            setattr(health, name, value)
    return len(marked)


def main() -> None:
    assert run_fixture(finalize=False) == 0, "validation must not expose the staged publication"
    assert run_fixture(finalize=True) == 1, "finalization must perform exactly one CAS promotion"
    try:
        run_fixture(finalize=False, invalid_promotion=True)
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("an under-evidenced promotion must fail closed")
    print({"supabaseLearningHealthAudit": "ok", "cases": 3})


if __name__ == "__main__":
    main()
