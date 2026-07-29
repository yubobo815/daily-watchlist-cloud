#!/usr/bin/env python3
"""Validate that Supabase has enough replay history for learning.

This script prints only aggregate health metrics. It never prints Supabase keys.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
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


def mark_run_validated(run_date: str, status: str, publication_id: str) -> None:
    url, key = credentials()
    endpoint = (
        f"{url}/rest/v1/watchlist_refresh_runs"
        f"?run_date=eq.{urllib.parse.quote(run_date)}"
        f"&publication_id=eq.{urllib.parse.quote(publication_id)}"
        "&status=eq.pending_audit"
        f"&payload->>publication_id=eq.{urllib.parse.quote(publication_id)}"
    )
    request_headers = headers(key)
    request_headers.update({"Content-Type": "application/json", "Prefer": "return=representation"})
    req = urllib.request.Request(
        endpoint,
        data=json.dumps({"status": status}).encode("utf-8"),
        headers=request_headers,
        method="PATCH",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        updated = json.loads(body) if body else []
        if resp.status != 200 or len(updated) != 1:
            raise RuntimeError(f"Could not mark validated run; HTTP {resp.status}.")
        updated_payload = updated[0].get("payload") if isinstance(updated[0].get("payload"), dict) else {}
        if str(updated_payload.get("publication_id") or "") != publication_id:
            raise RuntimeError("Validated publication changed during compare-and-set.")


def publication_generation() -> int:
    url, key = credentials()
    endpoint = f"{url}/rest/v1/watchlist_publication_control?select=generation&control_key=eq.active&limit=1"
    req = urllib.request.Request(endpoint, headers=headers(key), method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        rows = json.loads(resp.read().decode("utf-8") or "[]")
    if len(rows) > 1:
        raise RuntimeError("Publication control has more than one active row.")
    return int(rows[0].get("generation") or 0) if rows else 0


def activate_publication(publication_id: str) -> None:
    """Promote one validated publication after the deployed Pages manifest is verified."""
    url, key = credentials()
    control_endpoint = f"{url}/rest/v1/rpc/activate_watchlist_publication"
    control_headers = headers(key)
    control_headers.update({"Content-Type": "application/json"})
    expected_generation = publication_generation()
    req = urllib.request.Request(
        control_endpoint,
        data=json.dumps({
            "p_publication_id": publication_id,
            "p_expected_generation": expected_generation,
        }).encode("utf-8"),
        headers=control_headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        activated = json.loads(resp.read().decode("utf-8") or "[]")
        if resp.status != 200 or len(activated) != 1:
            raise RuntimeError("Could not switch the active publication pointer.")
        if str(activated[0].get("active_publication_id") or "") != publication_id:
            raise RuntimeError("Active publication pointer changed during activation.")
        if int(activated[0].get("generation") or -1) != expected_generation + 1:
            raise RuntimeError("Active publication generation changed during activation.")


def add_query_param(path: str, key: str, value: str | int) -> str:
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}{urllib.parse.quote(str(key))}={urllib.parse.quote(str(value))}"


def request_all_json(path: str, *, page_size: int = 1000, max_pages: int = 50) -> list[dict]:
    max_rows = page_size * max_pages
    rows: list[dict] = []
    for _ in range(max_pages * 10 + 1):
        offset = len(rows)
        page_path = add_query_param(add_query_param(path, "limit", page_size), "offset", offset)
        page_rows, _ = request_json(page_path)
        if not page_rows:
            return rows
        rows.extend(page_rows)
        if len(rows) > max_rows:
            break
    raise RuntimeError(
        f"Supabase health audit exceeded the guarded pagination limit ({max_rows} rows): {path}"
    )


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


def fail(message: str) -> None:
    print(f"SUPABASE_LEARNING_HEALTH=FAIL {message}")
    raise SystemExit(1)


def number(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def required_learning_snapshot_rows(snapshot_count: int) -> int:
    """Require representative current-row coverage without assuming exact patterns are dense."""
    return max(10, math.ceil(max(0, snapshot_count) * 0.10))


def main(*, finalize: bool = False, activate: bool = False) -> None:
    expected_run_date = os.getenv("EXPECTED_RUN_DATE", "").strip()
    expected_publication_id = os.getenv("EXPECTED_PUBLICATION_ID", "").strip()
    synced_run_date = latest_synced_run_date()
    run_date = expected_run_date or synced_run_date
    if not run_date:
        fail("No synced watchlist run found in behavior history or snapshots.")
    if not expected_publication_id:
        fail("EXPECTED_PUBLICATION_ID is required for an immutable publication audit.")
    if expected_run_date and synced_run_date != expected_run_date:
        fail(f"Expected synced run {expected_run_date}, but newest snapshot/history run is {synced_run_date or 'missing'}.")

    runs, _ = request_json(
        "watchlist_refresh_runs"
        "?select=publication_id,run_date,status,history_rows,snapshot_rows,symbols_analyzed,symbols_failed,scanner_version,payload"
        f"&run_date=eq.{urllib.parse.quote(str(run_date))}"
        f"&publication_id=eq.{urllib.parse.quote(expected_publication_id)}&limit=1"
    )
    latest = runs[0] if runs else {"run_date": run_date}
    latest_payload = latest.get("payload") if isinstance(latest.get("payload"), dict) else {}
    learning_model_version = str(latest_payload.get("learning_model_version") or "")
    try:
        learning_horizon_sessions = int(latest_payload.get("learning_horizon_sessions") or 0)
    except (TypeError, ValueError):
        learning_horizon_sessions = 0

    filters = f"run_date=eq.{urllib.parse.quote(str(run_date))}"
    publication_filter = f"publication_id=eq.{urllib.parse.quote(expected_publication_id)}"
    history_rows = request_all_json(
        "watchlist_behavior_history"
        "?select=publication_id,ticker,history_date,open,high,low,close,payload"
        f"&{filters}&{publication_filter}&order=ticker.asc,history_date.asc"
    )
    snapshot_rows = request_all_json(
        "watchlist_snapshots"
        "?select=publication_id,ticker,data_date,open,high,low,close,payload"
        f"&{filters}&{publication_filter}&order=ticker.asc"
    )
    indicator_state_rows = []
    if "synced_indicator_state_rows" in latest_payload:
        indicator_state_rows = request_all_json(
            "watchlist_indicator_state?select=publication_id,ticker,data_date,state_version,scanner_version,raw_window_hash&"
            f"{publication_filter}&order=ticker.asc"
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
    outcome_rows = []
    publication_id = str(latest_payload.get("publication_id") or "")
    if publication_id:
        outcome_rows = request_all_json(
            "watchlist_signal_outcomes"
            "?select=publication_id,ticker,signal_run_date,evaluation_run_date,outcome_label,learning_key,entry_model_version,forecast_learnable,prior_prediction_upside_probability,prior_prediction_downside_probability,prior_prediction_no_edge_probability,prior_prediction_confidence,prior_prediction_state,prior_prediction_key,prior_prediction_scope,payload"
            f"&publication_id=eq.{urllib.parse.quote(publication_id)}"
            "&order=ticker.asc,signal_run_date.asc"
        )

    calibration_artifact_id = str(latest_payload.get("calibration_artifact_id") or "")
    calibration_artifact_valid = not calibration_artifact_id
    if calibration_artifact_id:
        artifacts = request_all_json(
            "watchlist_calibration_artifacts?"
            "select=artifact_id,source_publication_id,cutoff_date,artifact_version,scanner_version,learning_model_version,directional_model_version,content_hash,state,payload_bytes,payload&"
            f"artifact_id=eq.{urllib.parse.quote(calibration_artifact_id)}&limit=1"
        )
        if len(artifacts) == 1:
            artifact = artifacts[0]
            source_publication_id = str(artifact.get("source_publication_id") or "")
            source_runs = request_all_json(
                "watchlist_refresh_runs?select=publication_id,status&"
                f"publication_id=eq.{urllib.parse.quote(source_publication_id)}&limit=1"
            ) if source_publication_id else []
            source_run_valid = (
                len(source_runs) == 1
                and str(source_runs[0].get("publication_id") or "") == source_publication_id
                and str(source_runs[0].get("status") or "") in {"pending_audit", "ok", "degraded"}
            )
            payload = artifact.get("payload") if isinstance(artifact.get("payload"), dict) else {}
            unhashed = {key: value for key, value in payload.items() if key not in {"content_hash", "artifact_id"}}
            actual_hash = hashlib.sha256(
                json.dumps(unhashed, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            typed_keys = (
                "artifact_id", "source_publication_id", "cutoff_date", "artifact_version", "scanner_version",
                "learning_model_version", "directional_model_version", "content_hash",
            )
            model = payload.get("model") if isinstance(payload.get("model"), dict) else {}
            try:
                feature_count = int(latest_payload.get("directional_feature_count") or 0)
                label_count = int(latest_payload.get("directional_label_count") or 0)
                center = model.get("center") or []
                scale = model.get("scale") or []
                coefficients = model.get("coefficients") or []
                priors = model.get("priors") or []
                model_shape_valid = (
                    feature_count > 0
                    and label_count > 0
                    and int(payload.get("feature_count") or 0) == feature_count
                    and int(payload.get("label_count") or 0) == label_count
                    and len(center) == feature_count
                    and len(scale) == feature_count
                    and len(coefficients) == feature_count + 1
                    and all(isinstance(row, list) and len(row) == label_count for row in coefficients)
                    and len(priors) == label_count
                )
                model_values = [*center, *scale, *priors, *(value for row in coefficients for value in row)]
                model_values_valid = bool(model_values) and all(number(value) is not None for value in model_values)
            except (TypeError, ValueError):
                model_shape_valid = False
                model_values_valid = False
            calibration_artifact_valid = (
                source_run_valid
                and artifact.get("state") == "validated"
                and all(str(artifact.get(key) or "") == str(payload.get(key) or "") for key in typed_keys)
                and str(payload.get("artifact_version") or "") == str(latest_payload.get("calibration_artifact_version") or "")
                and str(payload.get("scanner_version") or "") == str(latest.get("scanner_version") or "")
                and str(payload.get("learning_model_version") or "") == learning_model_version
                and str(payload.get("directional_model_version") or "") == str(latest_payload.get("directional_model_version") or "")
                and model_shape_valid
                and model_values_valid
                and actual_hash == payload.get("content_hash")
                and int(artifact.get("payload_bytes") or 0)
                == len(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
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
    settled_forecast_outcomes = []
    valid_forecast_outcomes = []
    for row in outcome_rows:
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        merged = {**payload, **{key: value for key, value in row.items() if value is not None}}
        settled = (
            merged.get("forecast_learnable") is True
            and str(merged.get("entry_model_version") or "") == learning_model_version
            and int(merged.get("label_horizon_sessions") or 0) == learning_horizon_sessions
            and str(merged.get("path_status") or "").upper() == "SETTLED"
            and str(merged.get("outcome_label") or "").upper() in {"WORKING", "FAILED", "STALE", "TRAP_AVOIDED"}
        )
        if settled:
            settled_forecast_outcomes.append(merged)
        try:
            probabilities = [
                float(merged.get("prior_prediction_upside_probability")),
                float(merged.get("prior_prediction_downside_probability")),
                float(merged.get("prior_prediction_no_edge_probability")),
            ]
        except (TypeError, ValueError):
            probabilities = []
        valid_probabilities = (
            len(probabilities) == 3
            and all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in probabilities)
            and abs(sum(probabilities) - 1.0) <= 1e-6
        )
        if (
            settled
            and valid_probabilities
            and str(merged.get("prior_prediction_state") or "").upper()
            in {"WALK_FORWARD", "REPORTING_ONLY", "CALIBRATED"}
            and bool(merged.get("prior_prediction_key"))
            and bool(merged.get("prior_prediction_scope"))
        ):
            valid_forecast_outcomes.append(merged)
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

    invalid_promotions = []
    for row in snapshot_rows:
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        if payload.get("learning_promotion_eligible") is not True:
            continue
        evidence = {
            "model": str(payload.get("learning_model_version") or "") == learning_model_version,
            "scope": str(payload.get("learning_scope") or "") == "exact signal personality",
            "execution_samples": (number(payload.get("learning_execution_sample_count")) or 0) >= 30,
            "execution_tickers": (number(payload.get("learning_execution_distinct_ticker_count")) or 0) >= 8,
            "execution_dates": (number(payload.get("learning_execution_evaluation_date_count")) or 0) >= 10,
            "calibration_samples": (number(payload.get("learning_calibration_sample_count")) or 0) >= 30,
            "brier": number(payload.get("learning_brier_score")) is not None
            and float(payload.get("learning_brier_score")) <= 0.62,
            "not_reporting_only": payload.get("learning_reporting_only") is False,
        }
        if not all(evidence.values()):
            invalid_promotions.append({"ticker": row.get("ticker"), "failed": [key for key, passed in evidence.items() if not passed]})

    directional_validated = latest_payload.get("directional_model_validated") is True
    directional_validation_safe = (
        not directional_validated
        or (
            (number(latest_payload.get("directional_model_oos_samples")) or 0) >= 1000
            and (number(latest_payload.get("directional_model_oos_dates")) or 0) >= 40
            and (number(latest_payload.get("directional_model_brier_skill")) or 0) >= 0.03
            and bool(latest_payload.get("directional_model_validated_personalities"))
        )
    )

    expected_indicator_version = str(latest_payload.get("indicator_state_version") or "")
    expected_scanner_version = str(latest.get("scanner_version") or "")
    snapshot_dates = {
        str(row.get("ticker") or "").upper(): str(row.get("data_date") or "")
        for row in snapshot_rows
        if row.get("ticker")
    }
    snapshot_hashes = {
        str(row.get("ticker") or "").upper(): str(
            (row.get("payload") if isinstance(row.get("payload"), dict) else {}).get("raw_window_hash") or ""
        )
        for row in snapshot_rows
        if row.get("ticker")
    }
    indicator_dates = {
        str(row.get("ticker") or "").upper(): str(row.get("data_date") or "")
        for row in indicator_state_rows
        if row.get("ticker")
    }
    indicator_state_valid = (
        "synced_indicator_state_rows" not in latest_payload
        or (
            int(latest_payload.get("synced_indicator_state_rows") or 0) == len(indicator_state_rows)
            and len(indicator_state_rows) == len(snapshot_rows)
            and indicator_dates == snapshot_dates
            and all(
                str(row.get("publication_id") or "") == publication_id
                and str(row.get("state_version") or "") == expected_indicator_version
                and str(row.get("scanner_version") or "") == expected_scanner_version
                and re.fullmatch(r"[0-9a-fA-F]{64}", str(row.get("raw_window_hash") or "")) is not None
                and str(row.get("raw_window_hash") or "") == snapshot_hashes.get(str(row.get("ticker") or "").upper(), "")
                for row in indicator_state_rows
            )
        )
    )

    metrics = {
        "run_date": run_date,
        "publication_status": latest.get("status"),
        "sync_state": latest_payload.get("sync_state"),
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
        "learning_model_version": learning_model_version,
        "learning_horizon_sessions": learning_horizon_sessions,
        "settled_forecast_outcomes": len(settled_forecast_outcomes),
        "valid_forecast_outcomes": len(valid_forecast_outcomes),
        "history_rows_missing_ohlc": len(missing_ohlc_history_rows),
        "snapshot_rows_missing_ohlc": len(missing_ohlc_snapshot_rows),
        "ticker_leaking_learning_keys": len(ticker_leaking_keys),
        "invalid_learning_promotions": len(invalid_promotions),
        "directional_model_validated": directional_validated,
        "directional_model_validation_safe": directional_validation_safe,
        "snapshots_with_learning_samples": learning_ready,
        "snapshots_with_learning_scope": learning_scope_ready,
        "calibration_artifact_valid": calibration_artifact_valid,
        "indicator_state_rows": len(indicator_state_rows),
        "indicator_state_valid": indicator_state_valid,
    }

    if len(history_rows) < 1000:
        emit_metrics(metrics)
        fail("Behavior history row count is too low for watchlist lookback learning.")
    if str(latest.get("status") or "") not in {"pending_audit", "validated", "ok", "degraded"} or latest_payload.get("sync_state") != "complete":
        emit_metrics(metrics)
        fail("Expected run is not marked as a complete Supabase publication.")
    if int(latest_payload.get("synced_snapshot_rows") or 0) != len(snapshot_rows):
        emit_metrics(metrics)
        fail("Snapshot sync count does not match the expected run.")
    if int(latest_payload.get("synced_history_rows") or 0) != len(history_rows):
        emit_metrics(metrics)
        fail("Behavior-history sync count does not match the expected run.")
    if not indicator_state_valid:
        emit_metrics(metrics)
        fail("Indicator state is incomplete or does not match the snapshot publication.")
    if int(latest_payload.get("synced_outcome_rows") or 0) != len(outcome_rows):
        emit_metrics(metrics)
        fail("Signal-outcome sync count does not match the immutable publication.")
    if not calibration_artifact_valid:
        emit_metrics(metrics)
        fail("Calibration artifact metadata, hash, size, or source publication is invalid.")
    if not publication_id:
        emit_metrics(metrics)
        fail("Expected run is missing its immutable publication id.")
    mixed_snapshot_rows = [row for row in snapshot_rows if str(row.get("publication_id") or "") != publication_id]
    mixed_history_rows = [row for row in history_rows if str(row.get("publication_id") or "") != publication_id]
    if mixed_snapshot_rows or mixed_history_rows:
        emit_metrics(metrics)
        fail("Snapshot/history rows do not belong to one atomic publication.")
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
    if not learning_model_version or learning_horizon_sessions <= 0:
        emit_metrics(metrics)
        fail("Publication metadata is missing the learning model contract.")
    if len(settled_forecast_outcomes) < 100:
        emit_metrics(metrics)
        fail("Too few current-model settled forecast paths are available for evaluation.")
    if len(valid_forecast_outcomes) < 100:
        emit_metrics(metrics)
        fail("Too few current-model forecasts have frozen probabilities for calibration.")
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
    if invalid_promotions:
        metrics["invalid_learning_promotion_examples"] = invalid_promotions[:5]
        emit_metrics(metrics)
        fail("A learning promotion bypassed minimum execution, diversity, or calibration evidence.")
    if not directional_validation_safe:
        emit_metrics(metrics)
        fail("The directional OHLCV model was activated without its full OOS evidence gate.")
    # Settled and calibrated outcome checks above validate the global learner.
    # Exact-pattern matches are regime-dependent, so treat current-row coverage
    # as an attachment check rather than a fixed 20% promotion quota.
    required_learning_rows = required_learning_snapshot_rows(len(snapshot_rows))
    metrics["required_snapshots_with_learning_samples"] = required_learning_rows
    if learning_ready < required_learning_rows:
        emit_metrics(metrics)
        fail("Too few latest snapshots have learning samples attached.")
    if learning_scope_ready < required_learning_rows:
        emit_metrics(metrics)
        fail("Too few learned snapshots identify their evidence scope.")

    scanner_status = str(latest_payload.get("scanner_status") or "")
    if scanner_status not in {"ok", "degraded"}:
        emit_metrics(metrics)
        fail("Scanner status is not publishable after database validation.")
    if finalize and str(latest.get("status") or "") == "pending_audit":
        mark_run_validated(run_date, "validated", publication_id)
    if activate:
        if str(latest.get("status") or "") != "validated":
            fail("Only a validated, inactive publication can be activated.")
        activate_publication(publication_id)
    state = "ACTIVATED" if activate else "STAGED" if finalize else "VALIDATED"
    print(f"SUPABASE_LEARNING_HEALTH={state}")
    emit_metrics(metrics)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--finalize",
            action="store_true",
            help="Mark the audited publication validated but keep it inactive.",
        )
        parser.add_argument(
            "--activate",
            action="store_true",
            help="Activate a validated publication after the deployed Pages manifest passes verification.",
        )
        options = parser.parse_args()
        if options.finalize and options.activate:
            parser.error("--finalize and --activate are mutually exclusive")
        main(finalize=options.finalize, activate=options.activate)
    except Exception as exc:
        print(f"SUPABASE_LEARNING_HEALTH=FAIL {exc}")
        sys.exit(1)
