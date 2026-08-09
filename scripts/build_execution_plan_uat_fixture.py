#!/usr/bin/env python3
"""Build a deterministic static site fixture for execution-plan browser UAT."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from build_pages_data import build, parse_args


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "output" / "execution-plan-uat"
FIXTURES = ROOT / "output" / ".execution-plan-uat-fixtures"


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    if FIXTURES.exists():
        shutil.rmtree(FIXTURES)
    SITE.mkdir(parents=True)
    FIXTURES.mkdir()
    shutil.copy2(ROOT / "index.html", SITE / "index.html")
    shutil.copy2(ROOT / "ticker.html", SITE / "ticker.html")
    shutil.copytree(ROOT / "assets", SITE / "assets")

    plan = {
        "execution_plan_id": "uat-plan-2026-08-03",
        "execution_plan_model_version": "daily-ohlcv-plan-v1",
        "execution_plan_status": "ARMED",
        "execution_plan_signal_date": "2026-08-03",
        "execution_plan_last_evaluation_date": "2026-08-04",
        "execution_plan_age_sessions": 1,
        "execution_plan_valid_sessions": 2,
        "execution_plan_setup": "PULLBACK BUY",
        "execution_plan_style": "PULLBACK LIMIT",
        "execution_plan_personality": "COMPOUNDER",
        "execution_plan_volatility_regime": "NORMAL",
        "execution_plan_zone_low": 100,
        "execution_plan_zone_high": 105,
        "execution_plan_stop": 96,
        "execution_plan_target": 120,
        "execution_plan_source_close": 110,
        "execution_plan_fill_est": "",
        "execution_plan_risk_pct": 8.57,
        "execution_plan_reason_code": "AWAITING_ENTRY",
        "execution_plan_summary": "The frozen entry condition has not been reached.",
        "execution_plan_events": "[]",
    }
    latest = {
        "ticker": "TEST",
        "name": "Test Compounder",
        "date": "2026-08-04",
        "run_date": "2026-08-04",
        "action": "SETUP FORMING",
        "setup": "PULLBACK BUY",
        "close": 109,
        "day_change_pct": -0.9,
        "score": 68,
        "adjusted_score": 68,
        "freshness_block": "NO",
        "freshness_status": "FRESH",
        "operator_state": "NEUTRAL",
        "volume_state": "NEUTRAL",
        **plan,
    }
    history = [
        {**latest, "date": "2026-07-29", "action": "WATCH TREND", "close": 104, "day_change_pct": 0.4},
        {**latest, "date": "2026-07-30", "action": "SETUP FORMING", "close": 106, "day_change_pct": 1.9},
        {**latest, "date": "2026-07-31", "action": "SETUP FORMING", "close": 108, "day_change_pct": 1.9},
        {**latest, "date": "2026-08-03", "action": "BUY CANDIDATE", "close": 110, "day_change_pct": 1.9},
        latest,
    ]
    latest_path = FIXTURES / "latest.csv"
    history_path = FIXTURES / "history.csv"
    metadata_path = FIXTURES / "metadata.json"
    write_csv(latest_path, [latest])
    write_csv(history_path, history)
    metadata_path.write_text(json.dumps({
        "publication_id": "execution-plan-uat",
        "run_date": "2026-08-04",
        "status": "ok",
        "latest_data_date": "2026-08-04",
        "symbols_analyzed": 1,
        "symbols_total": 1,
    }), encoding="utf-8")
    args = parse_args()
    args.latest = str(latest_path)
    args.history = str(history_path)
    args.metadata = str(metadata_path)
    args.output = str(SITE / "data")
    build(args)
    shutil.rmtree(FIXTURES)
    print(SITE)


if __name__ == "__main__":
    main()
