#!/usr/bin/env python3
"""Walk-forward audit for the balanced execution policy shadow fields."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import daily_watchlist_overview as dwo


BUY_ACTIONS = {"BUY CANDIDATE", "STRONG CONTINUATION"}
RISK_STATES = {"BULL_TRAP", "DISTRIBUTION"}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_local_frames() -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for path in sorted(Path(".").glob("watchlist_*_1y.csv")):
        ticker = path.stem.removeprefix("watchlist_").removesuffix("_1y").replace("_", ".")
        frame = pd.read_csv(path)
        if {"date", "open", "high", "low", "close", "volume"}.issubset(frame.columns):
            frames[ticker] = frame
    return frames


def load_exported_frames(path: Path) -> dict[str, pd.DataFrame]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            value = json.loads(line)
            rows.extend(value if isinstance(value, list) else [value])
    frame = pd.DataFrame(rows)
    required = {"ticker", "date", "open", "high", "low", "close", "volume"}
    assert_true(required.issubset(frame.columns), "exported OHLCV fields are incomplete")
    return {
        str(ticker): group.drop(columns=["ticker"]).sort_values("date").reset_index(drop=True)
        for ticker, group in frame.groupby("ticker")
    }


def future_path(rows: list[dict], index: int, sessions: int = 5) -> list[dict]:
    return rows[index + 1 : index + 1 + sessions]


def return_pct(start: object, end: object) -> float | None:
    start_value = dwo.numeric_or_none(start)
    end_value = dwo.numeric_or_none(end)
    if start_value is None or end_value is None or start_value <= 0:
        return None
    return (float(end_value) / float(start_value) - 1) * 100


def replay(frames: dict[str, pd.DataFrame]) -> list[dict]:
    benchmarks = {ticker: frames[ticker] for ticker in ("SPY", "QQQ", "SMH") if ticker in frames}
    observations: list[dict] = []
    for ticker, frame in sorted(frames.items()):
        if ticker in {"SPY", "QQQ", "SMH"}:
            continue
        rows = dwo.build_behavior_history(ticker, frame, days=30, benchmark_frames=benchmarks)
        rows = sorted(rows, key=lambda item: str(item.get("date") or ""))
        for index, row in enumerate(rows):
            future = future_path(rows, index)
            if len(future) < 5:
                continue
            five_day_return = return_pct(row.get("close"), future[-1].get("close"))
            next_bar = future[0]
            zone_low = dwo.numeric_or_none(row.get("entry_zone_low"))
            zone_high = dwo.numeric_or_none(row.get("entry_zone_high"))
            next_low = dwo.numeric_or_none(next_bar.get("low"))
            next_high = dwo.numeric_or_none(next_bar.get("high"))
            zone_filled = (
                zone_low is not None
                and zone_high is not None
                and next_low is not None
                and next_high is not None
                and next_low <= zone_high
                and next_high >= zone_low
            )
            observations.append({
                **row,
                "five_day_return_pct": five_day_return,
                "next_day_zone_filled": zone_filled,
            })
    return observations


def rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def summarize(observations: list[dict]) -> dict:
    opportunities = [
        row for row in observations
        if str(row.get("setup") or "NONE") != "NONE"
        and row.get("five_day_return_pct") is not None
        and float(row["five_day_return_pct"]) >= 5.0
    ]
    current_buys = [row for row in observations if str(row.get("action")) in BUY_ACTIONS]
    shadow_buys = [row for row in observations if str(row.get("shadow_action")) in BUY_ACTIONS]
    current_captured = sum(1 for row in opportunities if str(row.get("action")) in BUY_ACTIONS)
    shadow_captured = sum(1 for row in opportunities if str(row.get("shadow_action")) in BUY_ACTIONS)
    current_recall = rate(current_captured, len(opportunities))
    shadow_recall = rate(shadow_captured, len(opportunities))
    recall_improvement = (
        shadow_recall - current_recall
        if current_recall is not None and shadow_recall is not None
        else None
    )

    current_losses = sum(1 for row in current_buys if float(row["five_day_return_pct"]) <= -3.0)
    shadow_losses = sum(1 for row in shadow_buys if float(row["five_day_return_pct"]) <= -3.0)
    current_loss_rate = rate(current_losses, len(current_buys))
    shadow_loss_rate = rate(shadow_losses, len(shadow_buys))
    loss_rate_change = (
        shadow_loss_rate - current_loss_rate
        if current_loss_rate is not None and shadow_loss_rate is not None
        else None
    )

    risk_rows = [
        row for row in observations
        if str(row.get("operator_state") or "").upper() in RISK_STATES
        or dwo.row_float(row, "bull_trap_score") >= 58.0
        or dwo.row_float(row, "distribution_score") >= 55.0
    ]
    current_risk_avoidance = rate(
        sum(1 for row in risk_rows if str(row.get("action")) not in BUY_ACTIONS),
        len(risk_rows),
    )
    shadow_risk_avoidance = rate(
        sum(1 for row in risk_rows if str(row.get("shadow_action")) not in BUY_ACTIONS),
        len(risk_rows),
    )
    shadow_fill_rate = rate(sum(1 for row in shadow_buys if row["next_day_zone_filled"]), len(shadow_buys))

    slices: dict[str, Counter] = defaultdict(Counter)
    for row in shadow_buys:
        slices["personality"][str(row.get("personality_type") or "UNKNOWN")] += 1
        slices["setup"][str(row.get("setup") or "NONE")] += 1
        slices["market"][str(row.get("market_permission") or "UNKNOWN")] += 1
        slices["buy_type"][str(row.get("shadow_buy_type") or "NONE")] += 1

    guardrails = {
        "recall_improvement_at_least_20pp": recall_improvement is not None and recall_improvement >= 0.20,
        "loss_rate_increase_at_most_5pp": loss_rate_change is not None and loss_rate_change <= 0.05,
        "absolute_5d_loss_rate_below_35pct": shadow_loss_rate is not None and shadow_loss_rate <= 0.35,
        "risk_avoidance_not_lower": (
            current_risk_avoidance is not None
            and shadow_risk_avoidance is not None
            and shadow_risk_avoidance >= current_risk_avoidance
        ),
        "next_day_fill_rate_at_least_50pct": shadow_fill_rate is not None and shadow_fill_rate >= 0.50,
    }
    return {
        "observations": len(observations),
        "opportunities": len(opportunities),
        "current_buy_count": len(current_buys),
        "shadow_buy_count": len(shadow_buys),
        "current_opportunity_recall": current_recall,
        "shadow_opportunity_recall": shadow_recall,
        "recall_improvement": recall_improvement,
        "current_loss_rate": current_loss_rate,
        "shadow_loss_rate": shadow_loss_rate,
        "loss_rate_change": loss_rate_change,
        "current_risk_avoidance": current_risk_avoidance,
        "shadow_risk_avoidance": shadow_risk_avoidance,
        "shadow_next_day_fill_rate": shadow_fill_rate,
        "shadow_slices": {key: dict(value) for key, value in slices.items()},
        "guardrails": guardrails,
        "passed": all(guardrails.values()),
    }


def audit_counterfactual_contract() -> None:
    prior = {
        "ticker": "TEST",
        "date": "2026-06-01",
        "action": "SETUP FORMING",
        "setup": "PULLBACK BUY",
        "close": 100,
        "entry_zone_low": 99,
        "entry_zone_high": 101,
        "stop_est": 95,
        "target_est": 108,
        "market_permission": "MIXED",
        "ticker_permission": "INSUFFICIENT",
        "walk_forward_permission": "INSUFFICIENT",
        "risk_permission": "ALLOW",
        "personality_setup_allowed": "NO",
        "shadow_policy_allowed": "NO",
        "shadow_hard_blockers": [],
    }
    future = [
        {"date": f"2026-06-{day:02d}", "open": 100, "high": 101 + day, "low": 99, "close": 100 + day}
        for day in range(2, 12)
    ]
    outcome = dwo.score_signal_horizon(prior, future)
    assert_true(outcome["outcome_learnable"] is True, "soft uncertainty must remain execution-learnable")
    assert_true(outcome["counterfactual_outcome"] == "MISSED_OPPORTUNITY", "profitable blocked setup must be identified")
    assert_true(outcome["gate_evaluation"] == "GATE_FALSE_REJECTION", "missed opportunity must audit the old gate")
    assert_true(outcome["counterfactual_return_10d_pct"] != "", "ten-session counterfactual return must be retained")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ohlcv-jsonl", type=Path)
    args = parser.parse_args()
    audit_counterfactual_contract()
    frames = load_exported_frames(args.ohlcv_jsonl) if args.ohlcv_jsonl else load_local_frames()
    assert_true(all(ticker in frames for ticker in ("SPY", "QQQ", "SMH")), "benchmark cache is incomplete")
    observations = replay(frames)
    result = summarize(observations)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["passed"]:
        raise SystemExit("Shadow policy guardrails did not pass; do not promote it to production.")


if __name__ == "__main__":
    main()
