#!/usr/bin/env python3
"""Execute the publication health state machine against bounded fixtures."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os

import supabase_learning_health as health


RUN_DATE = "2026-07-17"
PUBLICATION_ID = "pub-test"
MODEL_VERSION = "five-session-r-risk-v5"


def fixture_rows(*, invalid_promotion: bool = False, learning_rows: int = 40):
    history = [
        {
            "ticker": f"T{ticker:02d}",
            "history_date": f"2026-06-{day:02d}",
            "open": 100,
            "high": 102,
            "low": 99,
            "close": 101,
            "publication_id": PUBLICATION_ID,
            "payload": {},
        }
        for ticker in range(40)
        for day in range(1, 31)
    ]
    snapshots = []
    for ticker in range(40):
        payload = {
            "learning_sample_count": 30 if ticker < learning_rows else 0,
            "learning_scope": "exact signal personality" if ticker < learning_rows else "none",
            "learning_promotion_eligible": False,
            "raw_window_hash": "a" * 64,
        }
        if invalid_promotion and ticker == 0:
            payload["learning_promotion_eligible"] = True
        snapshots.append({
            "publication_id": PUBLICATION_ID,
            "ticker": f"T{ticker:02d}", "data_date": RUN_DATE,
            "open": 100, "high": 102, "low": 99, "close": 101,
            "payload": payload,
        })
    outcomes = []
    prediction_key = "SETUP FORMING|PULLBACK BUY|BALANCED|ACCUMULATION|NONE"
    for index in range(500):
        payload = {
            "label_horizon_sessions": 5,
            "path_status": "SETTLED",
        }
        outcomes.append({
            "publication_id": PUBLICATION_ID,
            "ticker": f"T{index % 40:02d}",
            "signal_run_date": "2026-06-01",
            "evaluation_run_date": "2026-06-08",
            "outcome_label": "WORKING" if index % 2 else "STALE",
            "learning_key": prediction_key,
            "entry_model_version": MODEL_VERSION,
            "forecast_learnable": True,
            "prior_prediction_upside_probability": 0.5,
            "prior_prediction_downside_probability": 0.25,
            "prior_prediction_no_edge_probability": 0.25,
            "prior_prediction_confidence": 0.5,
            "prior_prediction_state": "WALK_FORWARD",
            "prior_prediction_key": prediction_key,
            "prior_prediction_scope": "exact signal personality",
            "payload": payload,
        })
    return history, snapshots, outcomes


def run_fixture(
    *,
    finalize: bool,
    invalid_promotion: bool = False,
    learning_rows: int = 40,
    integrity_state: str = "legacy",
    source_run_status: str = "ok",
) -> int:
    history, snapshots, outcomes = fixture_rows(
        invalid_promotion=invalid_promotion,
        learning_rows=learning_rows,
    )
    run = {
        "publication_id": PUBLICATION_ID,
        "run_date": RUN_DATE,
        "status": "pending_audit",
        "history_rows": len(history),
        "snapshot_rows": len(snapshots),
        "scanner_version": "scanner-test",
        "payload": {
            "publication_id": PUBLICATION_ID,
            "sync_state": "complete",
            "scanner_status": "ok",
            "synced_snapshot_rows": len(snapshots),
            "synced_history_rows": len(history),
            "synced_outcome_rows": len(outcomes),
            "learning_model_version": MODEL_VERSION,
            "learning_horizon_sessions": 5,
            "directional_model_validated": False,
        },
    }
    indicator_rows = []
    artifact = None
    source_run = {"publication_id": "weekly-source", "status": source_run_status}
    if integrity_state != "legacy":
        indicator_rows = [
            {
                "publication_id": PUBLICATION_ID,
                "ticker": row["ticker"],
                "data_date": "2026-07-16" if integrity_state == "bad_indicator" and index == 0 else row["data_date"],
                "state_version": "indicator-test",
                "scanner_version": "scanner-test",
                "raw_window_hash": "b" * 64 if integrity_state == "bad_indicator_hash" and index == 0 else "a" * 64,
            }
            for index, row in enumerate(snapshots)
        ]
        feature_count = 2
        label_count = 3
        artifact_payload = {
            "source_publication_id": source_run["publication_id"],
            "artifact_version": "artifact-test",
            "scanner_version": "scanner-test",
            "learning_model_version": MODEL_VERSION,
            "directional_model_version": "directional-test",
            "feature_count": feature_count,
            "label_count": label_count,
            "cutoff_date": RUN_DATE,
            "metrics": {"passed": False},
            "model": {
                "center": [0.0] * feature_count,
                "scale": [1.0] * feature_count,
                "coefficients": [[0.0] * label_count for _ in range(feature_count + 1)],
                "priors": [1 / label_count] * label_count,
                "sample_count": 100,
            },
            "train_sample_count": 100,
        }
        if integrity_state == "bad_artifact":
            artifact_payload["model"]["center"] = [0.0]
        digest = hashlib.sha256(
            json.dumps(artifact_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        artifact_payload["content_hash"] = digest
        artifact_payload["artifact_id"] = f"artifact-{digest[:12]}"
        artifact = {
            **{key: artifact_payload[key] for key in (
                "artifact_id", "source_publication_id", "cutoff_date", "artifact_version", "scanner_version",
                "learning_model_version", "directional_model_version", "content_hash",
            )},
            "state": "validated",
            "payload_bytes": len(json.dumps(artifact_payload, sort_keys=True, separators=(",", ":")).encode()),
            "payload": artifact_payload,
        }
        run["payload"].update({
            "synced_indicator_state_rows": len(indicator_rows),
            "indicator_state_version": "indicator-test",
            "calibration_artifact_id": artifact_payload["artifact_id"],
            "calibration_artifact_version": "artifact-test",
            "directional_model_version": "directional-test",
            "directional_feature_count": feature_count,
            "directional_label_count": label_count,
        })
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
        if path.startswith("watchlist_indicator_state"):
            return indicator_rows
        if path.startswith("watchlist_calibration_artifacts"):
            return [artifact] if artifact else []
        if path.startswith("watchlist_refresh_runs"):
            return [source_run]
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
    assert health.required_learning_snapshot_rows(185) == 19
    assert health.required_learning_snapshot_rows(250) == 25
    assert health.required_learning_snapshot_rows(40) == 10
    assert run_fixture(finalize=False) == 0, "validation must not expose the staged publication"
    assert run_fixture(finalize=True) == 1, "finalization must perform exactly one CAS promotion"
    assert run_fixture(finalize=False, learning_rows=10) == 0, "representative sparse learning coverage must publish"
    assert run_fixture(finalize=False, integrity_state="valid") == 0, "current integrity contract must publish"
    assert run_fixture(finalize=False, integrity_state="valid", source_run_status="validated") == 0, (
        "activation must accept an artifact after its source run enters the validated state"
    )
    try:
        run_fixture(finalize=False, learning_rows=9)
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("insufficient current-row learning coverage must fail closed")
    try:
        run_fixture(finalize=False, invalid_promotion=True)
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("an under-evidenced promotion must fail closed")
    for integrity_state in ("bad_indicator", "bad_indicator_hash", "bad_artifact"):
        try:
            run_fixture(finalize=False, integrity_state=integrity_state)
        except SystemExit as exc:
            assert exc.code == 1
        else:
            raise AssertionError(f"{integrity_state} must fail closed")
    original_request = health.request_json
    health.request_json = lambda *_args, **_kwargs: ([{}] * 1000, None)
    try:
        try:
            health.request_all_json("watchlist_behavior_history?select=*", max_pages=2)
        except RuntimeError:
            pass
        else:
            raise AssertionError("health audit must fail closed at its pagination guard")
    finally:
        health.request_json = original_request

    original_control = health.publication_control
    original_credentials = health.credentials
    original_urlopen = health.urllib.request.urlopen
    controls = iter((("prior-publication", 7), (PUBLICATION_ID, 8)))
    health.publication_control = lambda: next(controls)
    health.credentials = lambda: ("https://example.supabase.co", "test-key")
    health.urllib.request.urlopen = lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError("lost response"))
    try:
        health.activate_publication(PUBLICATION_ID)
    finally:
        health.publication_control = original_control
        health.credentials = original_credentials
        health.urllib.request.urlopen = original_urlopen

    health.publication_control = lambda: ("prior-publication", 7)
    health.assert_publication_inactive(PUBLICATION_ID)
    health.publication_control = lambda: (PUBLICATION_ID, 8)
    try:
        health.assert_publication_inactive(PUBLICATION_ID)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Pages rollback must stop when the candidate publication is active")
    finally:
        health.publication_control = original_control
    print({"supabaseLearningHealthAudit": "ok", "cases": 13})


if __name__ == "__main__":
    main()
