#!/usr/bin/env python3
"""Build deterministic, versioned static data for the GitHub Pages app."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
MAX_TICKER_HISTORY_ROWS = 30
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")
# The ticker view needs the full current snapshot, but the watchlist only needs
# enough data to rank, explain, and open a trade plan. Keeping those separate
# prevents every daily publication from growing with diagnostics intended for
# a single-stock page.
WATCHLIST_FIELDS = frozenset(
    """
    action anti_signal_level buy_tier buy_type policy_version legacy_action close data_date date day_change_pct
    entry_est entry_zone_high entry_zone_low entry_zone_plan execution_fill_probability
    execution_fill_state extension_state freshness_block freshness_status
    market_permission name next_day_bias next_day_plan notes operator_pressure
    operator_state personality_setup_allowed position_value_1k_risk suggested_position_value actual_risk_dollars post_tp1_stop
    prediction_confidence prediction_state risk_pct_to_stop risk_permission run_date
    score setup stop_est take_profit_1 take_profit_1_reduce_pct target_est ticker
    ticker_permission volume_state walk_forward_permission
    execution_priority
    execution_regime relative_strength_20d_pct relative_strength_leader
    shadow_action shadow_buy_type shadow_policy_allowed shadow_readiness_score
    shadow_position_size_factor shadow_decision_explanation
    execution_plan_id execution_plan_model_version execution_plan_status
    execution_plan_signal_date execution_plan_last_evaluation_date
    execution_plan_age_sessions execution_plan_valid_sessions execution_plan_setup
    execution_plan_style execution_plan_personality execution_plan_volatility_regime
    execution_plan_zone_low execution_plan_zone_high execution_plan_stop
    execution_plan_target execution_plan_source_close execution_plan_fill_est
    execution_plan_final_target execution_plan_entry_date execution_plan_risk_pct
    execution_plan_post_tp1_stop execution_plan_management_sessions
    execution_plan_reason_code execution_plan_summary execution_plan_events
    execution_plan_previous_id execution_plan_previous_status execution_plan_previous_date
    """.split()
)

RUN_INFO_FIELDS = frozenset(
    """
    earliest_data_date history_rows latest_data_date learning_history_rows
    live_access_message live_access_ok notes run_date scanner_version status
    symbols_analyzed symbols_failed symbols_stale_cache symbols_total
    """.split()
)

# These fields support the current trade plan and its explanation on a ticker
# page. Scanner-only calibration diagnostics remain in Supabase rather than
# being repeated in every browser download.
TICKER_SNAPSHOT_FIELDS = WATCHLIST_FIELDS | frozenset(
    """
    active_protective_stop adaptive_mode adjusted_score anti_signal_plan buyer_score
    contextual_overlay contextual_plan data_provider data_provider_status
    distance_from_ref_zone_pct entry_quality_label event_risk execution_fill_sample_count
    execution_plan execution_priority execution_style feedback_plan feedback_quality
    last_outcome_label last_outcome_reason learning_adjustment
    learning_distinct_ticker_count learning_evaluation_date_count learning_model_version
    learning_baseline_sample_count learning_baseline_evaluation_date_count learning_baseline_weight
    learning_plan learning_promotion_eligible learning_promotion_state
    learning_reporting_only learning_sample_count market_context model_version
    next_day_bias_score operator_plan operator_pressure_score operator_state_plan
    operator_state_score prediction_downside_probability prediction_horizon_sessions
    prediction_model_version prediction_no_edge_probability prediction_upside_probability
    profit_stage psychology reason_codes seller_score signal_quality transition_label
    transition_score volatility_regime
    shadow_hard_blockers shadow_cautions shadow_readiness_trend shadow_readiness_entry
    shadow_readiness_momentum shadow_readiness_volume_demand shadow_readiness_relative_strength
    shadow_readiness_market shadow_readiness_history execution_regime_efficiency_20d
    execution_regime_trend_votes_5d relative_strength_score
    legacy_signal_stage legacy_adjusted_score legacy_position_size_factor
    legacy_suggested_position_value legacy_actual_risk_dollars
    """.split()
)

# Thirty history rows are rendered as a concise timeline. Its calculations do
# not need verbose plans, learning notes, or per-row model diagnostics.
HISTORY_FIELDS = frozenset(
    """
    action adjusted_score buyer_score close data_date date day_change_pct high low name open
    operator_pressure operator_state reason_codes run_date score setup ticker
    seller_score volume_state
    shadow_action shadow_buy_type shadow_readiness_score shadow_policy_allowed
    buy_type policy_version legacy_action
    execution_plan_id execution_plan_model_version execution_plan_status
    execution_plan_signal_date execution_plan_last_evaluation_date
    execution_plan_age_sessions execution_plan_valid_sessions execution_plan_setup
    execution_plan_style execution_plan_personality execution_plan_volatility_regime
    execution_plan_zone_low execution_plan_zone_high execution_plan_stop
    execution_plan_target execution_plan_source_close execution_plan_fill_est
    execution_plan_final_target execution_plan_entry_date execution_plan_risk_pct
    execution_plan_post_tp1_stop execution_plan_management_sessions
    execution_plan_reason_code execution_plan_summary execution_plan_events
    execution_plan_previous_id execution_plan_previous_status execution_plan_previous_date
    """.split()
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latest", default="daily_watchlist_overview_latest.csv")
    parser.add_argument("--history", default="watchlist_behavior_history_latest.csv")
    parser.add_argument("--metadata", default="daily_watchlist_run_metadata_latest.json")
    parser.add_argument("--output", default="public/data")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required CSV does not exist: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        # Older publishers nested a complete second copy of each row here.
        return [
            {key: value for key, value in row.items() if key and key != "payload"}
            for row in reader
        ]


def read_metadata(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Required metadata does not exist: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Metadata must be a JSON object: {path}")
    return value


def project_row(row: dict[str, str], fields: frozenset[str]) -> dict[str, str]:
    return {key: value for key, value in row.items() if key in fields}


def project_run_info(metadata: dict[str, Any]) -> dict[str, Any]:
    """Publish a stable operational summary, not arbitrary scanner diagnostics."""
    run_info = {key: metadata[key] for key in RUN_INFO_FIELDS if key in metadata}
    stale_blocks = metadata.get("payload", {}).get("stale_execution_blocks")
    if stale_blocks is not None:
        run_info["payload"] = {"stale_execution_blocks": stale_blocks}
    return run_info


def required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Metadata field {field!r} is required")
    return text


def safe_segment(value: str) -> str:
    """Return a stable path segment without trusting source-controlled values."""
    if SAFE_SEGMENT_RE.fullmatch(value) and value not in {".", ".."}:
        return value
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-") or "item"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{stem[:64]}-{digest}"


def row_ticker(row: dict[str, str], source: str) -> str:
    ticker = str(row.get("ticker") or "").strip().upper()
    if not ticker:
        raise ValueError(f"{source} contains a row without a ticker")
    row["ticker"] = ticker
    return ticker


def row_date(row: dict[str, str]) -> str:
    return str(row.get("history_date") or row.get("date") or row.get("run_date") or "")


def stable_row_key(row: dict[str, str]) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def file_integrity(path: Path) -> dict[str, int | str]:
    content = path.read_bytes()
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def site_file_inventory(site_root: Path, data_files: set[str]) -> dict[str, dict[str, int | str]]:
    """Hash every deployable file outside the immutable payload inventory."""
    inventory: dict[str, dict[str, int | str]] = {}
    for path in sorted(item for item in site_root.rglob("*") if item.is_file()):
        relative = path.relative_to(site_root).as_posix()
        if relative == "data/manifest.json" or relative.removeprefix("data/") in data_files:
            continue
        inventory[relative] = file_integrity(path)
    return inventory


def build(args: argparse.Namespace) -> dict[str, Any]:
    latest_rows = read_csv(Path(args.latest))
    history_rows = read_csv(Path(args.history))
    metadata = read_metadata(Path(args.metadata))
    publication_id = required_text(metadata.get("publication_id"), "publication_id")
    run_date = required_text(metadata.get("run_date"), "run_date")

    latest_by_ticker: dict[str, dict[str, str]] = {}
    for row in latest_rows:
        ticker = row_ticker(row, "latest CSV")
        if ticker in latest_by_ticker:
            raise ValueError(f"Latest CSV contains duplicate ticker: {ticker}")
        latest_by_ticker[ticker] = row

    history_by_ticker: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in history_rows:
        history_by_ticker[row_ticker(row, "history CSV")].append(row)

    # The publication contract is the current watchlist. Historical rows for a
    # ticker that is no longer present must not create a phantom manifest entry.
    tickers = sorted(latest_by_ticker)
    ticker_segments: dict[str, str] = {}
    used_segments: dict[str, str] = {}
    for ticker in tickers:
        segment = safe_segment(ticker)
        collision_key = segment.casefold()
        if collision_key in used_segments and used_segments[collision_key] != ticker:
            raise ValueError(
                f"Ticker path collision: {ticker!r} and {used_segments[collision_key]!r}"
            )
        used_segments[collision_key] = ticker
        ticker_segments[ticker] = segment

    output = Path(args.output)
    publication_segment = safe_segment(publication_id)
    run_relative = Path("runs") / publication_segment
    run_output = output / run_relative
    if run_output.exists():
        shutil.rmtree(run_output)
    ticker_output = run_output / "tickers"

    sorted_latest = [
        project_row(latest_by_ticker[ticker], WATCHLIST_FIELDS)
        for ticker in sorted(latest_by_ticker)
    ]
    latest_payload = {
        "schema_version": SCHEMA_VERSION,
        "publication_id": publication_id,
        "run_date": run_date,
        "runInfo": project_run_info(metadata),
        "rows": sorted_latest,
    }
    write_json(run_output / "latest.json", latest_payload)

    ticker_paths: dict[str, str] = {}
    for ticker in tickers:
        rows = sorted(
            (project_row(row, HISTORY_FIELDS) for row in history_by_ticker.get(ticker, [])),
            key=lambda row: (row_date(row), stable_row_key(row)),
            reverse=True,
        )[:MAX_TICKER_HISTORY_ROWS]
        relative_path = run_relative / "tickers" / f"{ticker_segments[ticker]}.json"
        ticker_paths[ticker] = relative_path.as_posix()
        write_json(
            output / relative_path,
            {
                "schema_version": SCHEMA_VERSION,
                "publication_id": publication_id,
                "run_date": run_date,
                "ticker": ticker,
                "snapshot": (
                    project_row(latest_by_ticker[ticker], TICKER_SNAPSHOT_FIELDS)
                    if ticker in latest_by_ticker
                    else None
                ),
                "historyRows": rows,
                "runInfo": project_run_info(metadata),
            },
        )

    latest_relative = (run_relative / "latest.json").as_posix()
    files = {latest_relative: file_integrity(output / latest_relative)}
    for ticker, relative_path in ticker_paths.items():
        files[relative_path] = {**file_integrity(output / relative_path), "ticker": ticker}
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "publication_id": publication_id,
        "run_date": run_date,
        "latest_path": latest_relative,
        "ticker_base_path": (run_relative / "tickers").as_posix(),
        "ticker_count": len(tickers),
        "ticker_paths": ticker_paths,
        "files": files,
        "site_files": site_file_inventory(output.parent, set(files)),
    }
    # The mutable pointer is written last so readers never see a partial publication.
    write_json(output / "manifest.json", manifest)
    return manifest


def main() -> None:
    manifest = build(parse_args())
    print(
        f"Published {manifest['ticker_count']} tickers for "
        f"{manifest['publication_id']} to {manifest['latest_path']}"
    )


if __name__ == "__main__":
    main()
