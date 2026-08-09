#!/usr/bin/env python3
"""UAT contract tests for frozen daily BUY execution plans."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from execution_plan_state import apply_execution_plan_lifecycle, create_execution_plan, evaluate_execution_plan
from scripts.build_pages_data import HISTORY_FIELDS, TICKER_SNAPSHOT_FIELDS, WATCHLIST_FIELDS


def signal(**overrides):
    row = {
        "ticker": "TEST",
        "date": "2026-08-03",
        "action": "BUY CANDIDATE",
        "setup": "PULLBACK BUY",
        "execution_style": "PULLBACK LIMIT",
        "personality_type": "COMPOUNDER",
        "volatility_regime": "NORMAL",
        "open": 109,
        "high": 111,
        "low": 108,
        "close": 110,
        "entry_zone_low": 100,
        "entry_zone_high": 105,
        "stop_est": 96,
        "target_est": 120,
        "freshness_block": "NO",
    }
    row.update(overrides)
    return row


def bar(date, **overrides):
    row = {
        "ticker": "TEST",
        "date": date,
        "action": "SETUP FORMING",
        "operator_state": "NEUTRAL",
        "open": 108,
        "high": 111,
        "low": 106,
        "close": 109,
        "freshness_block": "NO",
    }
    row.update(overrides)
    return row


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def audit_creation_and_immutability():
    plan = create_execution_plan(signal())
    require(plan and plan["execution_plan_status"] == "ARMED", "BUY SETUP must arm a plan")
    require(create_execution_plan(signal(action="SETUP FORMING")) is None, "BUILDING must not create a plan")
    require(create_execution_plan(signal(execution_style="NONE")) is None, "unknown execution styles must fail closed")
    first_target = create_execution_plan(signal(take_profit_1=116, target_est=125))
    require(first_target["execution_plan_target"] == 116, "the frozen first target must prefer TP1")
    require(first_target["execution_plan_final_target"] == 125, "the farther target must remain separately auditable")
    next_plan = evaluate_execution_plan(plan, bar("2026-08-04"))
    require(next_plan["execution_plan_status"] == "ARMED", "untouched two-session pullback must remain armed")
    require(next_plan["execution_plan_zone_low"] == 100, "frozen zone must not move with today's signal")


def audit_pullback_paths():
    plan = create_execution_plan(signal())
    filled = evaluate_execution_plan(plan, bar("2026-08-04", open=104, high=108, low=102, close=106))
    require(filled["execution_plan_status"] == "MODEL_FILLED", "open inside pullback zone must establish modeled entry")
    require(filled["execution_plan_fill_est"] == 104, "open inside zone must use open as fill")
    stopped = evaluate_execution_plan(plan, bar("2026-08-04", open=104, high=108, low=95, close=97))
    require(stopped["execution_plan_status"] == "STOPPED", "known entry at open followed by stop must be stopped")
    ambiguous = evaluate_execution_plan(plan, bar("2026-08-04", open=108, high=111, low=95, close=101))
    require(ambiguous["execution_plan_status"] == "AMBIGUOUS", "intraday entry and stop order must not be invented")
    gap = evaluate_execution_plan(plan, bar("2026-08-04", open=99, high=106, low=98, close=104))
    require(gap["execution_plan_status"] == "INVALIDATED", "open below pullback zone must invalidate")


def audit_breakout_paths():
    plan = create_execution_plan(signal(
        setup="BREAKOUT BUY", execution_style="BREAKOUT TRIGGER",
        entry_zone_low=111, entry_zone_high=113, stop_est=105, target_est=125,
    ))
    require(plan["execution_plan_valid_sessions"] == 1, "breakout plan must expire after one future session")
    filled = evaluate_execution_plan(plan, bar("2026-08-04", open=109, high=116, low=108, close=114))
    require(filled["execution_plan_status"] == "MODEL_FILLED", "breakout high crossing trigger must fill")
    require(filled["execution_plan_fill_est"] == 111, "breakout must fill at trigger, not band high")
    chase = evaluate_execution_plan(plan, bar("2026-08-04", open=114, high=118, low=113, close=116))
    require(chase["execution_plan_reason_code"] == "OPENED_ABOVE_MAX_ENTRY", "gap above band must not be chased")


def audit_profit_management():
    plan = create_execution_plan(signal(take_profit_1=112, target_est=120, post_tp1_stop=107))
    filled = evaluate_execution_plan(plan, bar("2026-08-04", open=104, high=108, low=102, close=107))
    first_target = evaluate_execution_plan(filled, bar("2026-08-05", open=109, high=113, low=108, close=112))
    require(first_target["execution_plan_status"] == "TP1_HIT", "TP1 must raise protection without terminating the plan")
    final_target = evaluate_execution_plan(first_target, bar("2026-08-06", open=114, high=121, low=110, close=120))
    require(final_target["execution_plan_status"] == "TARGET_HIT", "the further target must remain tracked after TP1")


def audit_expiry_rerun_and_projection():
    plan = create_execution_plan(signal())
    first = evaluate_execution_plan(plan, bar("2026-08-04"))
    rerun = evaluate_execution_plan(first, bar("2026-08-04"))
    require(rerun["execution_plan_age_sessions"] == 1, "same-session rerun must be idempotent")
    expired = evaluate_execution_plan(first, bar("2026-08-05"))
    require(expired["execution_plan_status"] == "EXPIRED", "unfilled pullback must expire after its validity window")
    current = bar("2026-08-04", action="AVOID", entry_zone_low=80, entry_zone_high=82)
    projected = apply_execution_plan_lifecycle([current], [{**signal(), **plan}])[0]
    require(projected["execution_plan_zone_low"] == 100, "today's AVOID must not rewrite yesterday's plan")
    recovered = apply_execution_plan_lifecycle(
        [bar("2026-08-05")],
        [{**signal(), **plan}],
        {"TEST": [bar("2026-08-04", open=104, high=108, low=102, close=106), bar("2026-08-05")]},
    )[0]
    require(recovered["execution_plan_status"] == "MODEL_FILLED", "recovery must evaluate a missed intermediate session")
    require(recovered["execution_plan_fill_est"] == 104, "recovery must retain the intermediate session's modeled touch price")
    old_breakout = create_execution_plan(signal(
        setup="BREAKOUT BUY", execution_style="BREAKOUT TRIGGER",
        entry_zone_low=115, entry_zone_high=117, stop_est=104, target_est=125,
    ))
    replacement_signal = signal(date="2026-08-04", setup="PULLBACK BUY", execution_style="PULLBACK LIMIT")
    replaced = apply_execution_plan_lifecycle([replacement_signal], [{**signal(), **old_breakout}])[0]
    require(replaced["execution_plan_signal_date"] == "2026-08-04", "a plan expiring today must not hide today's new BUY SETUP")
    require(replaced["execution_plan_previous_status"] == "EXPIRED", "same-day replacement must retain its predecessor terminal state")


def audit_missing_data_and_hard_risk():
    plan = create_execution_plan(signal())
    missing = evaluate_execution_plan(plan, bar("2026-08-04", low=""))
    require(missing["execution_plan_reason_code"] == "DATA_UNAVAILABLE", "incomplete OHLC must fail closed")
    malformed = evaluate_execution_plan(plan, bar("2026-08-04", high=100, low=110))
    require(malformed["execution_plan_reason_code"] == "DATA_UNAVAILABLE", "internally inconsistent OHLC must fail closed")
    risk = evaluate_execution_plan(plan, bar("2026-08-04", operator_state="DISTRIBUTION"))
    require(risk["execution_plan_reason_code"] == "HARD_RISK_CONFIRMED", "confirmed distribution before entry must invalidate")
    touched_risk = evaluate_execution_plan(plan, bar("2026-08-04", open=104, high=108, low=102, operator_state="DISTRIBUTION"))
    require(touched_risk["execution_plan_status"] == "INVALIDATED", "confirmed hard risk must take priority over a same-day touch")


def audit_publication_contract():
    required = {
        "execution_plan_id", "execution_plan_status", "execution_plan_signal_date",
        "execution_plan_zone_low", "execution_plan_zone_high", "execution_plan_stop",
        "execution_plan_target", "execution_plan_reason_code",
    }
    require(required <= WATCHLIST_FIELDS, "watchlist publication must include the frozen plan")
    require(required <= TICKER_SNAPSHOT_FIELDS, "ticker publication must include the frozen plan")
    require(required <= HISTORY_FIELDS, "history publication must preserve the lifecycle across refreshes")


def main():
    audit_creation_and_immutability()
    audit_pullback_paths()
    audit_breakout_paths()
    audit_profit_management()
    audit_expiry_rerun_and_projection()
    audit_missing_data_and_hard_risk()
    audit_publication_contract()
    print("Execution-plan UAT passed.")


if __name__ == "__main__":
    main()
