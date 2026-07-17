import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import daily_watchlist_overview as dwo


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def row(date, action, close, **overrides):
    base = {
        "date": date,
        "action": action,
        "setup": overrides.pop("setup", "NONE"),
        "close": close,
        "score": overrides.pop("score", 60),
        "reason_codes": [],
        "next_day_bias": overrides.pop("next_day_bias", "WATCH TREND"),
        "distribution_score": overrides.pop("distribution_score", 0),
        "bull_trap_score": overrides.pop("bull_trap_score", 0),
        "short_pressure_proxy": overrides.pop("short_pressure_proxy", 0),
        "extension_state": overrides.pop("extension_state", ""),
        "adaptive_mode": overrides.pop("adaptive_mode", "POWER TREND"),
        "personality_type": overrides.pop("personality_type", "BALANCED"),
        "operator_state": overrides.pop("operator_state", "NEUTRAL"),
        "demand_control_score": overrides.pop("demand_control_score", 0),
        "absorption_score": overrides.pop("absorption_score", 0),
        "buyer_score": overrides.pop("buyer_score", 50),
        "market_permission": overrides.pop("market_permission", "ALLOW"),
        "ticker_permission": overrides.pop("ticker_permission", "ALLOW"),
        "risk_permission": overrides.pop("risk_permission", "ALLOW"),
        "walk_forward_permission": overrides.pop("walk_forward_permission", "ALLOW"),
        "personality_setup_allowed": overrides.pop("personality_setup_allowed", "YES"),
    }
    base.update(overrides)
    return base


def latest(rows):
    return dwo.enrich_signal_transitions(rows)[-1]


def audit_profit_active_does_not_force_defense():
    result = latest([
        row("D1", "BUY CANDIDATE", 100, setup="MOMENTUM BUY", score=100, next_day_bias="BULLISH CONFIRM"),
        row("D2", "WATCH TREND", 108, score=65, next_day_bias="WATCH TREND"),
    ])
    assert_true(result["contextual_overlay"] == "PROFIT ACTIVE", "open profit should be marked active")
    assert_true(result["next_day_bias"] == "WATCH TREND", "profit active must not force defensive bias")
    assert_true(result.get("execution_block") != "YES", "profit active must not block execution")


def audit_profit_protect_requires_giveback_or_supply():
    result = latest([
        row("D1", "BUY CANDIDATE", 100, setup="MOMENTUM BUY", score=100, next_day_bias="BULLISH CONFIRM"),
        row("D2", "WATCH TREND", 108, score=65, next_day_bias="WATCH TREND"),
        row("D3", "EXIT PRESSURE", 100, score=20, next_day_bias="DEFENSIVE / EXIT RISK", distribution_score=48),
    ])
    assert_true(result["contextual_overlay"] == "PROFIT PROTECT", "real giveback plus supply must trigger hard protection")
    assert_true(result["next_day_bias"] == "DEFENSIVE / EXIT RISK", "hard profit protect must be defensive")


def audit_post_exit_cooldown_sees_short_pressure():
    result = latest([
        row("D1", "EXIT PRESSURE", 100, score=20, next_day_bias="DEFENSIVE / EXIT RISK", distribution_score=60),
        row(
            "D2",
            "BUY CANDIDATE",
            107,
            setup="MOMENTUM BUY",
            score=100,
            next_day_bias="BULLISH CONFIRM",
            operator_state="MARKUP / DEMAND CONTROL",
            demand_control_score=90,
            buyer_score=80,
            short_pressure_proxy=85,
        ),
    ])
    assert_true(result["contextual_overlay"] == "POST-EXIT COOLDOWN", "short pressure must not bypass post-exit cooldown")
    assert_true(result["action"] == "SETUP FORMING", "cooldown must downgrade rebound BUY to BUILDING")
    assert_true(result["next_day_bias"] == "EXECUTION BLOCKED", "cooldown must block next-day execution")


def audit_post_exit_risk_persistence_keeps_exit_pressure():
    result = latest([
        row("D1", "EXIT PRESSURE", 213.68, score=20, next_day_bias="DEFENSIVE / EXIT RISK", seller_score=86, buyer_score=9, distribution_score=40),
        row("D2", "WAIT", 211.82, score=34, next_day_bias="NEUTRAL", seller_score=53, buyer_score=12, distribution_score=0),
        row("D3", "WAIT", 205.81, score=34, next_day_bias="NEUTRAL", seller_score=49, buyer_score=16, distribution_score=24),
    ])
    assert_true(result["contextual_overlay"] == "POST-EXIT RISK PERSISTENCE", "post-exit weakness must stay in risk mode")
    assert_true(result["action"] == "EXIT PRESSURE", "post-exit weakness must not collapse to WAIT")
    assert_true(result["next_day_bias"] == "DEFENSIVE / EXIT RISK", "post-exit weakness must keep defensive next-day bias")


def audit_post_exit_risk_persistence_allows_strong_reclaim():
    result = latest([
        row("D1", "EXIT PRESSURE", 100, score=20, next_day_bias="DEFENSIVE / EXIT RISK", seller_score=80, distribution_score=50),
        row(
            "D2",
            "SETUP FORMING",
            108,
            setup="MOMENTUM BUY",
            score=78,
            next_day_bias="BULLISH CONFIRM",
            operator_state="MARKUP / DEMAND CONTROL",
            demand_control_score=88,
            buyer_score=82,
            seller_score=5,
            distribution_score=0,
        ),
    ])
    assert_true(result.get("contextual_overlay") != "POST-EXIT RISK PERSISTENCE", "strong reclaim should not be forced back to EXIT")
    assert_true(result["action"] == "SETUP FORMING", "strong reclaim setup should remain BUILDING")


def audit_range_bound_reclaim_cannot_skip_post_exit_cooldown():
    result = latest([
        row(
            "D1",
            "EXIT PRESSURE",
            211.14,
            score=20,
            next_day_bias="DEFENSIVE / EXIT RISK",
            seller_score=80,
            distribution_score=98,
        ),
        row(
            "D2",
            "BUY CANDIDATE",
            224.36,
            setup="MOMENTUM BUY",
            score=118,
            next_day_bias="BULLISH CONFIRM",
            operator_state="MARKUP / DEMAND CONTROL",
            adaptive_mode="MEAN REVERSION",
            personality_type="RANGE_BOUND",
            demand_control_score=86,
            buyer_score=92,
            seller_score=3,
            distribution_score=0,
        ),
    ])
    assert_true(result["contextual_overlay"] == "POST-EXIT COOLDOWN", "range-bound reclaim must not skip post-exit cooldown")
    assert_true(result["action"] == "SETUP FORMING", "range-bound post-exit rebound must downgrade BUY to BUILDING")
    assert_true(result["next_day_bias"] == "EXECUTION BLOCKED", "range-bound post-exit rebound must require confirmation")


def audit_volatile_hold_has_consistent_score():
    result = latest([
        row(
            "D1",
            "EXIT PRESSURE",
            102,
            score=20,
            next_day_bias="DEFENSIVE / EXIT RISK",
            personality_type="BALANCED",
            adaptive_mode="POWER TREND",
            demand_control_score=60,
            buyer_score=60,
        ),
    ])
    assert_true(result["contextual_overlay"] == "VOLATILE TREND HOLD", "balanced power trend can qualify for volatile hold")
    assert_true(result["action"] == "WATCH TREND", "volatile hold must convert soft EXIT to WATCH")
    assert_true(float(result["adjusted_score"]) >= 50, "volatile hold WATCH must not retain a collapsed EXIT score")


def audit_behavior_history_seeds_learning():
    history_rows = [
        {**row("2026-06-01", "BUY CANDIDATE", 100, setup="MOMENTUM BUY", entry_zone_low=99, entry_zone_high=101, stop_est=97), "ticker": "MU"},
        {**row("2026-06-02", "WATCH TREND", 100.5, setup="NONE", open=100, low=99.5, high=101), "ticker": "MU"},
        {**row("2026-06-03", "WATCH TREND", 103.5, setup="NONE", open=101, low=100.5, high=104), "ticker": "MU"},
        {**row("2026-06-04", "WATCH TREND", 103, setup="NONE", open=103, low=102, high=104), "ticker": "MU"},
        {**row("2026-06-05", "WATCH TREND", 104, setup="NONE", open=103, low=102, high=105), "ticker": "MU"},
        {**row("2026-06-06", "SETUP FORMING", 103, setup="PULLBACK BUY", open=104, low=102, high=105), "ticker": "MU"},
    ]
    outcomes = dwo.build_backfilled_signal_outcomes(history_rows)
    assert_true(len(outcomes) >= 1, "behavior replay should create backfilled learning samples")
    first = outcomes.iloc[0].to_dict()
    assert_true(first["signal_run_date"] == "2026-06-01", "backfilled sample must use prior history date")
    assert_true(first["evaluation_run_date"] == "2026-06-03", "backfilled sample must settle on the bar that reaches the target")
    assert_true(first["label_horizon_sessions"] == dwo.LEARNING_HORIZON_SESSIONS, "backfilled sample must use the risk-adjusted horizon")
    assert_true(first["outcome_label"] == "WORKING", "BUY that reaches 1R before the stop should seed WORKING")
    assert_true(first["entry_filled"] is True, "BUY learning must require a next-session entry-zone fill")
    stats = dwo.build_learning_stats(outcomes)
    assert_true(bool(stats), "backfilled outcomes should feed learning stats")


def audit_unfilled_buy_is_excluded_from_learning():
    history_rows = [
        {**row("2026-06-01", "BUY CANDIDATE", 100, setup="MOMENTUM BUY", entry_zone_low=99, entry_zone_high=101, stop_est=97), "ticker": "MU"},
        {**row("2026-06-02", "WATCH TREND", 108, setup="NONE", open=107, low=106, high=109), "ticker": "MU"},
        {**row("2026-06-03", "WATCH TREND", 109, setup="NONE", open=108, low=107, high=110), "ticker": "MU"},
        {**row("2026-06-04", "WATCH TREND", 110, setup="NONE", open=109, low=108, high=111), "ticker": "MU"},
        {**row("2026-06-05", "WATCH TREND", 111, setup="NONE", open=110, low=109, high=112), "ticker": "MU"},
        {**row("2026-06-06", "WATCH TREND", 112, setup="NONE", open=111, low=110, high=113), "ticker": "MU"},
    ]
    outcomes = dwo.build_backfilled_signal_outcomes(history_rows)
    first = outcomes.iloc[0].to_dict()
    assert_true(first["outcome_label"] == "NOT_FILLED", "gap-away BUY must not be recorded as a working trade")
    assert_true(not dwo.build_learning_stats(outcomes), "unfilled BUY must not change learning weights")


def audit_ambiguous_daily_path_is_excluded_from_learning():
    prior = executable_prior()
    bars = [executable_current(open=100, high=104, low=96, close=101) for _ in range(dwo.LEARNING_HORIZON_SESSIONS)]
    outcome = dwo.score_signal_horizon(prior, bars)
    assert_true(outcome["path_status"] == "AMBIGUOUS", "same-bar entry and stop must not invent an intraday sequence")
    assert_true(outcome["outcome_learnable"] is False, "ambiguous daily path must be excluded from learning")


def audit_non_executable_signal_is_excluded_from_risk_path_learning():
    prior = row("2026-06-01", "WATCH TREND", 100, setup="NONE", ticker="MU")
    bars = [executable_current(open=100, high=104, low=98, close=102) for _ in range(dwo.LEARNING_HORIZON_SESSIONS)]
    outcome = dwo.score_signal_horizon(prior, bars)
    assert_true(outcome["path_status"] == "NON_EXECUTABLE", "v4 risk-path learning must only score planned entries")
    assert_true(outcome["outcome_learnable"] is False, "WATCH/EXIT paths without entry, stop, and target must not become v4 evidence")


def audit_defensive_learning_shows_samples_without_promotion():
    current = row("2026-06-03", "EXIT PRESSURE", 100, setup="NONE", score=20)
    current["ticker"] = "NVDA"
    current["adjusted_score"] = 20
    key = dwo.learning_key_for(current)
    outcomes = pd.DataFrame(outcome_rows(3, key))
    outcomes["prior_action"] = "EXIT PRESSURE"
    outcomes["prior_setup"] = "NONE"
    outcomes["learning_key"] = key
    outcomes["outcome_label"] = "TRAP_AVOIDED"
    outcomes["outcome_score"] = 1.0
    stats = dwo.build_learning_stats(outcomes)
    dwo.apply_learning_adjustments([current], stats)
    assert_true(current["learning_sample_count"] == 3, "defensive family samples should be visible")
    assert_true(current["learning_adjustment"] == 0.0, "successful defensive learning must not promote EXIT score")
    assert_true(float(current["adjusted_score"]) == 20.0, "EXIT adjusted score must remain unchanged by positive defense learning")


def audit_learning_lookback_supports_60_day_window():
    history_rows = [
        {**row(f"2026-06-{day:02d}", "BUY CANDIDATE", 100 + day, setup="MOMENTUM BUY"), "ticker": "MU"}
        for day in range(1, 61)
    ]
    learning_outcomes = dwo.build_backfilled_signal_outcomes(history_rows)
    assert_true(dwo.DEFAULT_LEARNING_LOOKBACK_DAYS == 60, "learning should use a broader outcome window than the displayed history")
    assert_true(len(learning_outcomes) == 59, "60 replayed days should create one outcome per prior signal")


def audit_learning_key_uses_behavior_not_ticker_identity():
    current = row(
        "2026-06-03",
        "BUY CANDIDATE",
        100,
        setup="MOMENTUM BUY",
        ticker="NVDA",
        personality_type="RANGE_BOUND",
        operator_state="MARKUP / DEMAND CONTROL",
        anti_signal_level="NONE",
    )
    key = dwo.learning_key_for(current)
    segments = key.split("|")
    assert_true("NVDA" not in segments, "learning key must not include ticker identity")
    assert_true("RANGE_BOUND" in segments, "learning key should learn personality behavior pattern")
    assert_true(key == "BUY CANDIDATE|MOMENTUM BUY|RANGE_BOUND|MARKUP / DEMAND CONTROL|NONE", "learning key shape must stay behavior-only")

    outcomes = dwo.build_backfilled_signal_outcomes([
        {**current, "date": "2026-06-03"},
        {**current, "date": "2026-06-04", "close": 103, "action": "WATCH TREND"},
    ])
    outcome_key = str(outcomes.iloc[0]["learning_key"])
    assert_true("NVDA" not in outcome_key.split("|"), "backfilled learning key must not include ticker identity")
    assert_true("RANGE_BOUND" in outcome_key.split("|"), "backfilled learning key must include personality behavior")


def audit_action_display_labels_match_product_ui():
    assert_true(dwo.ACTION_DISPLAY_LABELS["BUY CANDIDATE"] == "BUY", "BUY label must match product UI")
    assert_true(dwo.ACTION_DISPLAY_LABELS["STRONG CONTINUATION"] == "TRENDING", "continuation label must match product UI")
    assert_true(dwo.ACTION_DISPLAY_LABELS["SETUP FORMING"] == "BUILDING", "setup-forming label must match product UI")
    assert_true(dwo.ACTION_DISPLAY_LABELS["WATCH TREND"] == "WATCH", "watch label must match product UI")
    assert_true(dwo.ACTION_DISPLAY_LABELS["EXIT PRESSURE"] == "EXIT", "exit label must match product UI")
    assert_true(dwo.ACTION_DISPLAY_LABELS["WAIT / AVOID"] == "AVOID", "avoid label must match product UI")


def learning_confirmed_setup_row(**overrides):
    current = row(
        "2026-06-03",
        "SETUP FORMING",
        100,
        setup="PULLBACK BUY",
        score=78,
        next_day_bias="BULLISH CONFIRM",
        operator_state="ACCUMULATION",
        extension_state="NEAR_ZONE",
    )
    current.update({
        "adjusted_score": 84,
        "anti_signal_level": "NONE",
        "freshness_block": "NO",
        "risk_permission": "ALLOW",
        "market_permission": "ALLOW",
        "learning_sample_count": 30,
        "learning_working_rate": 0.75,
        "learning_failed_rate": 0.125,
        "learning_adjustment": 5.0,
        "learning_scope": "exact signal personality",
        "learning_distinct_ticker_count": 8,
        "learning_evaluation_date_count": 10,
        "learning_promotion_eligible": True,
        "personality_setup_allowed": "YES",
        "signal_quality": "NEXT-DAY BUILDING",
    })
    current.update(overrides)
    return current


def audit_learning_can_upgrade_building_execution_tier():
    current = learning_confirmed_setup_row()
    tier, priority, plan = dwo.buy_tier_for(current, 0)
    assert_true(tier == "BUY WATCH", "positive learning should upgrade clean BUILDING to BUY WATCH tier")
    assert_true(priority == 2, "learning-confirmed BUILDING should rank with buy-watch priority")
    assert_true("Pine confirmation" in plan, "learning upgrade must still require Pine confirmation")
    dwo.apply_buy_tiers([current])
    assert_true("learning_confirmed_setup" in current["reason_codes"], "learning upgrade should be auditable")


def audit_learning_upgrade_respects_anti_signals():
    trapped = learning_confirmed_setup_row(
        anti_signal_level="BLOCK",
        operator_state="BULL_TRAP",
        bull_trap_score=70,
    )
    tier, priority, _ = dwo.buy_tier_for(trapped, 0)
    assert_true(tier == "SETUP ONLY", "anti-signal block must prevent learning-confirmed upgrade")
    assert_true(priority == 4, "blocked learning setup must stay low execution priority")


def audit_safety_gates_preserve_raw_technical_score():
    trapped = learning_confirmed_setup_row(
        score=112,
        adjusted_score=118,
        anti_signal_level="BLOCK",
        anti_signal_score=76,
        anti_signal_plan="Bull-trap evidence blocks execution.",
        operator_state="BULL_TRAP",
        operator_pressure="DISTRIBUTION",
        bull_trap_score=76,
        distribution_score=62,
    )
    dwo.apply_anti_signal_penalty(trapped)
    assert_true(trapped["score"] == 112, "anti-signal execution policy must preserve the raw technical score")
    assert_true(trapped["adjusted_score"] <= 49, "anti-signal execution policy must cap only the adjusted rank")


def audit_freshness_gate_preserves_raw_technical_score():
    candidate = learning_confirmed_setup_row(score=96, adjusted_score=96)
    original_age = dwo.nyse_session_age
    try:
        dwo.nyse_session_age = lambda _value: 1
        dwo.apply_data_freshness_gate(candidate, "2026-07-17", set())
    finally:
        dwo.nyse_session_age = original_age
    assert_true(candidate["score"] == 96, "stale-data policy must preserve the raw technical score")
    assert_true(candidate["adjusted_score"] <= 49, "stale-data policy must cap only the adjusted rank")


def audit_learning_upgrade_respects_personality_gate():
    blocked = learning_confirmed_setup_row(personality_setup_allowed="NO")
    tier, priority, _ = dwo.buy_tier_for(blocked, 0)
    assert_true(tier == "SETUP ONLY", "personality-blocked setup must not receive a learning BUY upgrade")
    assert_true(priority == 3, "personality-blocked setup must retain ordinary setup priority")
    dwo.apply_buy_tiers([blocked])
    assert_true("learning_confirmed_setup" not in blocked["reason_codes"], "blocked setup must not record a learning promotion")


def executable_prior(**overrides):
    prior = row(
        "2026-06-01",
        "BUY CANDIDATE",
        100,
        setup="MOMENTUM BUY",
        ticker="MU",
        entry_zone_low=99,
        entry_zone_high=101,
        stop_est=97,
    )
    prior.update(overrides)
    return prior


def executable_current(**overrides):
    current = row("2026-06-02", "WATCH TREND", 103, ticker="MU", open=100, high=104, low=99)
    current.update(overrides)
    return current


def synthetic_price_frame(start_price, daily_change, periods=240):
    closes = [start_price + daily_change * index for index in range(periods)]
    return pd.DataFrame({
        "date": pd.bdate_range("2025-07-01", periods=periods),
        "open": [close - 0.2 for close in closes],
        "high": [close + 0.6 for close in closes],
        "low": [close - 0.7 for close in closes],
        "close": closes,
        "adjclose": closes,
        "volume": [1_000_000 + index * 1000 for index in range(periods)],
    })


def audit_stop_breach_cannot_be_working():
    outcome = dwo.self_score_prior_signal(
        executable_prior(),
        executable_current(close=104, low=96),
        "2026-06-02",
    )
    assert_true(outcome["outcome_label"] == "FAILED", "next-bar stop breach must never be recorded as WORKING")
    assert_true(outcome["stop_hit"] is True, "stop-aware outcome must record the next-bar stop breach")


def audit_stale_stop_breach_is_not_learnable():
    outcome = dwo.self_score_prior_signal(
        executable_prior(),
        executable_current(close=104, low=96, freshness_block="YES"),
        "2026-06-02",
    )
    assert_true(outcome["outcome_label"] == "PENDING", "stale comparison must short-circuit before a stop-breach label")
    assert_true(outcome["stop_hit"] is False, "stale OHLC must not record a stop hit")
    assert_true(outcome["outcome_learnable"] is False, "stale stop scenario must be excluded from learning")


def audit_gap_through_entry_stop_is_non_learnable():
    outcome = dwo.self_score_prior_signal(
        executable_prior(),
        executable_current(open=98, high=103, low=96, close=102),
        "2026-06-02",
    )
    assert_true(outcome["outcome_label"] == "NON_LEARNABLE", "gap below entry zone must not infer a valid fill from OHLC")
    assert_true(outcome["outcome_learnable"] is False, "gap-through scenario must be excluded from learning")


def audit_outcome_does_not_depend_on_current_action():
    prior = executable_prior()
    working_ohlc = executable_current(close=104)
    changed_action = {**working_ohlc, "action": "EXIT PRESSURE", "operator_state": "DISTRIBUTION"}
    first = dwo.self_score_prior_signal(prior, working_ohlc, "2026-06-02")
    second = dwo.self_score_prior_signal(prior, changed_action, "2026-06-02")
    assert_true(first["outcome_label"] == second["outcome_label"] == "WORKING", "unchanged OHLC must keep the same outcome regardless of current action")
    assert_true(first["outcome_score"] == second["outcome_score"], "current action must not alter the OHLC outcome score")


def audit_hard_gate_blocked_signal_cannot_work_or_learn():
    gate_blocks = {
        "personality_setup_allowed": "NO",
        "market_permission": "BLOCK",
        "ticker_permission": "CAUTION",
        "risk_permission": "BLOCK",
        "walk_forward_permission": "INSUFFICIENT",
    }
    for gate, value in gate_blocks.items():
        outcome = dwo.self_score_prior_signal(
            executable_prior(**{gate: value}),
            executable_current(close=104),
            "2026-06-02",
        )
        assert_true(outcome["entry_eligible"] is False, f"{gate} block must make the prior signal entry-ineligible")
        assert_true(outcome["outcome_label"] != "WORKING", f"{gate} block must not produce WORKING")
        assert_true(outcome["outcome_learnable"] is False, f"{gate} block must exclude the outcome from learning")
        assert_true(
            not dwo.build_learning_stats(pd.DataFrame([outcome])),
            f"{gate} block must not contribute to learning stats",
        )


def outcome_rows(count, learning_key, *, model_version=dwo.LEARNING_MODEL_VERSION, ticker_prefix="T"):
    return [
        {
            "learning_key": learning_key,
            "prior_action": "SETUP FORMING",
            "prior_setup": "PULLBACK BUY",
            "ticker": f"{ticker_prefix}{index}",
            "evaluation_run_date": f"2026-06-{index + 1:02d}",
            "signal_run_date": f"2026-05-{index + 20:02d}",
            "entry_model_version": model_version,
            "outcome_learnable": True,
            "forecast_learnable": True,
            "outcome_label": "WORKING",
            "outcome_score": 1.0,
            "close_return_pct": 2.5,
            "label_horizon_sessions": dwo.LEARNING_HORIZON_SESSIONS,
            "path_status": "SETTLED",
            "prior_prediction_upside_probability": 0.70,
            "prior_prediction_downside_probability": 0.15,
            "prior_prediction_no_edge_probability": 0.15,
            "prior_prediction_confidence": 0.50,
            "prior_prediction_state": "WALK_FORWARD",
            "prior_prediction_key": learning_key,
            "prior_prediction_scope": "exact signal personality",
        }
        for index in range(count)
    ]


def audit_learning_excludes_unversioned_outcomes():
    legacy = pd.DataFrame(outcome_rows(6, "SETUP FORMING|PULLBACK BUY|BALANCED|ACCUMULATION|NONE"))
    legacy = legacy.drop(columns=["entry_model_version"])
    assert_true(not dwo.build_learning_stats(legacy), "outcomes without the current entry-model version must be excluded")


def audit_learning_requires_explicit_learnable_outcome():
    rows = pd.DataFrame(outcome_rows(6, "SETUP FORMING|PULLBACK BUY|BALANCED|ACCUMULATION|NONE"))
    rows = rows.drop(columns=["outcome_learnable", "forecast_learnable"])
    assert_true(not dwo.build_learning_stats(rows), "outcome aggregation must require an explicit learnable flag")


def audit_missing_boolean_is_never_affirmative():
    assert_true(not dwo.is_affirmative(float("nan")), "NaN must never serialize as an affirmative execution or learning flag")
    assert_true(not dwo.is_affirmative(None), "missing boolean must remain false")


def audit_gated_setup_calibrates_forecast_without_becoming_executable():
    prior = executable_prior(
        action="SETUP FORMING",
        setup="PULLBACK BUY",
        market_permission="BLOCK",
    )
    bars = [
        executable_current(date=f"2026-06-0{day}", open=100, high=104, low=99, close=103)
        for day in range(2, 2 + dwo.LEARNING_HORIZON_SESSIONS)
    ]
    outcome = dwo.score_signal_horizon(prior, bars)
    assert_true(outcome["outcome_label"] == "WORKING", "settled OHLC path must retain its technical forecast result")
    assert_true(outcome["entry_eligible"] is False, "market-blocked setup must never become executable")
    assert_true(outcome["outcome_learnable"] is False, "blocked setup must stay excluded from execution learning")
    assert_true(outcome["forecast_learnable"] is True, "settled path should calibrate forecast quality")
    assert_true(bool(dwo.build_learning_stats(pd.DataFrame([outcome]))), "settled forecast evidence must reach calibration stats")


def audit_counterfactual_forecasts_cannot_promote_execution():
    current = learning_confirmed_setup_row()
    key = dwo.learning_key_for(current)
    outcomes = pd.DataFrame(outcome_rows(8, key))
    outcomes["outcome_learnable"] = False
    stats = dwo.build_learning_stats(outcomes)
    dwo.apply_learning_adjustments([current], stats)
    assert_true(current["learning_execution_sample_count"] == 0, "counterfactual paths must not become execution evidence")
    assert_true(current["learning_adjustment"] == 0.0, "counterfactual paths must not adjust the live score")
    assert_true(not current["learning_promotion_eligible"], "counterfactual paths must not authorize promotion")


def audit_invalid_probabilities_are_excluded_from_calibration():
    key = "SETUP FORMING|PULLBACK BUY|BALANCED|ACCUMULATION|NONE"
    rows = pd.DataFrame(outcome_rows(8, key))
    rows["prior_prediction_upside_probability"] = 1.1
    rows["prior_prediction_downside_probability"] = 0.0
    rows["prior_prediction_no_edge_probability"] = 0.0
    stats = dwo.build_learning_stats(rows)
    assert_true(stats[key]["calibration_sample_count"] == 0, "out-of-range probabilities must not enter Brier calibration")
    assert_true(stats[key]["brier_score"] is None, "invalid probabilities must not create a passing Brier score")


def audit_same_bar_entry_target_order_is_ambiguous():
    prior = executable_prior(target_est=103)
    bars = [executable_current(open=105, high=106, low=100, close=104)] * dwo.LEARNING_HORIZON_SESSIONS
    outcome = dwo.score_signal_horizon(prior, bars)
    assert_true(outcome["path_status"] == "AMBIGUOUS", "daily OHLC cannot order a target touch before versus after a pullback entry")
    assert_true(not outcome["forecast_learnable"], "intrabar-order ambiguity must not calibrate the forecast")


def audit_learning_uses_displayed_target_when_available():
    prior = executable_prior(target_est=110)
    bars = [executable_current(open=100, high=104, low=99, close=103)] * dwo.LEARNING_HORIZON_SESSIONS
    outcome = dwo.score_signal_horizon(prior, bars)
    assert_true(outcome["outcome_label"] == "STALE", "a 1R move below the displayed target must not be learned as target success")


def audit_exit_pressure_has_risk_first_action_precedence():
    action, rank = dwo.select_signal_action(
        filters_ok=True,
        continuation_ok=True,
        setup_forming=True,
        exit_pressure=True,
        seller_control=True,
        trend_damage=True,
        mode="POWER TREND",
    )
    assert_true(action == "EXIT PRESSURE" and rank == 20, "hard exit evidence must override simultaneous BUY/BUILDING conditions")


def audit_signal_outcome_history_is_paginated():
    calls = []
    original_select = dwo.supabase_select
    original_local = dwo.load_local_signal_outcomes

    def fake_select(path):
        calls.append(path)
        if path.startswith("watchlist_refresh_runs?"):
            return [{"payload": {"publication_id": "pub-validated", "sync_state": "complete"}}]
        offset = 1000 if "offset=1000" in path else 0
        count = 500 if offset else 1000
        return [
            {
                "ticker": f"T{offset + index}",
                "signal_run_date": "2026-07-07",
                "evaluation_run_date": "2026-07-14",
                "outcome_label": "WORKING",
                "learning_key": "SETUP FORMING|PULLBACK BUY|BALANCED|ACCUMULATION|NONE",
                "entry_model_version": dwo.LEARNING_MODEL_VERSION,
                "forecast_learnable": True,
                "payload": {"publication_id": "pub-validated"},
            }
            for index in range(count)
        ]

    dwo.supabase_select = fake_select
    dwo.load_local_signal_outcomes = lambda run_date: pd.DataFrame()
    try:
        history = dwo.fetch_signal_outcome_history("2026-07-15")
    finally:
        dwo.supabase_select = original_select
        dwo.load_local_signal_outcomes = original_local
    assert_true(len(history) == 1500, "learning history must not stop at the first PostgREST page")
    assert_true(any("offset=1000" in path for path in calls), "learning history must request subsequent pages")


def audit_missing_optional_outcome_metrics_do_not_crash_learning():
    rows = pd.DataFrame(outcome_rows(3, "SETUP FORMING|PULLBACK BUY|BALANCED|ACCUMULATION|NONE"))
    rows = rows.drop(columns=["outcome_score", "close_return_pct"])
    stats = dwo.build_learning_stats(rows)
    assert_true(bool(stats), "missing optional score/return fields must not crash probability aggregation")


def directional_sample_rows(count):
    feature_count = len(dwo.DIRECTIONAL_NUMERIC_FEATURES) + len(dwo.DIRECTIONAL_PERSONALITIES)
    rows = []
    start = pd.Timestamp("2025-01-02")
    for index in range(count):
        signal_date = start + pd.offsets.BDay(index)
        rows.append({
            "ticker": f"T{index % 20}",
            "signal_run_date": signal_date.date().isoformat(),
            "evaluation_run_date": (signal_date + pd.offsets.BDay(dwo.LEARNING_HORIZON_SESSIONS)).date().isoformat(),
            "features": pd.Series([(index % 11) / 10 + column * 0.01 for column in range(feature_count)]).to_numpy(),
            "label": dwo.DIRECTIONAL_LABELS[index % len(dwo.DIRECTIONAL_LABELS)],
            "personality_type": dwo.DIRECTIONAL_PERSONALITIES[index % len(dwo.DIRECTIONAL_PERSONALITIES)],
            "forward_return_pct": 0.0,
            "move_threshold_pct": 1.0,
        })
    return pd.DataFrame(rows)


def audit_directional_walk_forward_is_future_invariant():
    base = dwo.directional_walk_forward_predictions(directional_sample_rows(240))
    extended = dwo.directional_walk_forward_predictions(directional_sample_rows(260)).iloc[:240]
    compared = 0
    for index in base.index:
        first = base.at[index, "prediction"]
        second = extended.at[index, "prediction"]
        if isinstance(first, np.ndarray):
            assert_true(isinstance(second, np.ndarray), "existing walk-forward prediction must remain available after future rows append")
            assert_true(np.allclose(first, second), "future outcomes must not change a frozen directional prediction")
            assert_true(abs(float(first.sum()) - 1.0) < 1e-9, "directional probabilities must sum to one")
            compared += 1
    assert_true(compared > 0, "fixture must produce post-warmup walk-forward predictions")


def audit_directional_model_requires_sample_out_evidence():
    metrics = dwo.directional_validation_metrics(dwo.directional_walk_forward_predictions(directional_sample_rows(50)))
    assert_true(not metrics["passed"], "small in-sample feature history must never validate the directional model")


def audit_directional_veto_cannot_be_reupgraded_by_buy_tier():
    current = learning_confirmed_setup_row(
        learning_promotion_eligible=False,
        learning_adjustment=0.0,
        reason_codes=["directional_model_not_confirmed"],
    )
    assert_true(not dwo.learning_confirms_setup_upgrade(current), "directional rejection must block the legacy learning upgrade path")
    tier, _, _ = dwo.buy_tier_for(current, 0)
    assert_true(tier == "SETUP ONLY", "buy-tier calculation must preserve the directional veto")


def audit_categorical_promotion_requires_thirty_executable_samples():
    current = learning_confirmed_setup_row()
    key = dwo.learning_key_for(current)
    stats = dwo.build_learning_stats(pd.DataFrame(outcome_rows(29, key)))
    dwo.apply_learning_adjustments([current], stats)
    assert_true(current["learning_adjustment"] == 0.0, "29 correlated execution samples must remain below the promotion threshold")
    assert_true(not current["learning_promotion_eligible"], "undersized execution evidence must remain reporting-only")


def audit_learning_window_uses_recent_evaluation_sessions_only():
    key = "SETUP FORMING|PULLBACK BUY|BALANCED|ACCUMULATION|NONE"
    rows = outcome_rows(1, key, ticker_prefix="OLD") + outcome_rows(3, key, ticker_prefix="NEW")
    rows[0]["evaluation_run_date"] = "2026-01-02"
    rows[0]["outcome_label"] = "WORKING"
    rows[1]["evaluation_run_date"] = "2026-07-10"
    rows[1]["outcome_label"] = "FAILED"
    rows[2]["evaluation_run_date"] = "2026-07-11"
    rows[2]["outcome_label"] = "FAILED"
    rows[3]["evaluation_run_date"] = "2026-07-14"
    rows[3]["outcome_label"] = "FAILED"
    history = pd.DataFrame(rows)
    filtered = dwo.restrict_learning_outcomes_to_window(history, "2026-07-15", lookback_days=3)
    stats = dwo.build_learning_stats(history, "2026-07-15", lookback_days=3)
    assert_true(len(filtered) == 3, "learning loader window must retain exactly the latest evaluation sessions")
    assert_true(filtered.attrs["learning_window"]["evaluation_date_min"] == "2026-07-10", "window must expose its oldest evaluation date")
    assert_true(stats[key]["sample_count"] == 3, "old current-model outcomes must not affect learning stats")
    assert_true(stats[key]["working_rate"] == 0.0, "in-window outcomes must determine learning rates")


def audit_replay_market_gate_matches_live_context():
    ticker = synthetic_price_frame(100, 0.35)
    benchmarks = {symbol: synthetic_price_frame(100, 0.2) for symbol in ("SPY", "QQQ", "SMH")}
    replay = dwo.build_behavior_history("TEST", ticker, days=1, benchmark_frames=benchmarks)
    live_gate = dwo.market_permission_from_frames(benchmarks)
    assert_true(len(replay) == 1, "replay fixture should produce one date-aligned snapshot")
    assert_true(replay[0]["market_permission"] == live_gate["market_permission"] == "ALLOW", "replay market gate must match the live benchmark gate on the same date")


def audit_replay_gate_cache_is_bounded_and_historical():
    ticker = synthetic_price_frame(100, 0.35, periods=248)
    benchmarks = {symbol: synthetic_price_frame(100, 0.2, periods=248) for symbol in ("SPY", "QQQ", "SMH")}
    calls = {"ticker": 0, "walk_forward": 0}
    original_ticker_profile = dwo.ticker_learning_profile
    original_walk_forward = dwo.walk_forward_setup_stats

    def counted_ticker_profile(*args, **kwargs):
        calls["ticker"] += 1
        return original_ticker_profile(*args, **kwargs)

    def counted_walk_forward(*args, **kwargs):
        calls["walk_forward"] += 1
        return original_walk_forward(*args, **kwargs)

    dwo.ticker_learning_profile = counted_ticker_profile
    dwo.walk_forward_setup_stats = counted_walk_forward
    try:
        replay = dwo.build_behavior_history("TEST", ticker, days=8, benchmark_frames=benchmarks)
    finally:
        dwo.ticker_learning_profile = original_ticker_profile
        dwo.walk_forward_setup_stats = original_walk_forward

    assert_true(len(replay) == 8, "replay cache fixture must retain every requested historical session")
    assert_true(calls["ticker"] < len(replay), "replay must not recalculate ticker gates on every historical bar")
    assert_true(calls["walk_forward"] < len(replay), "replay must not recalculate walk-forward gates on every historical bar")
    assert_true(calls["ticker"] >= 2, "replay must refresh cached gates during a multi-session replay")
    assert_true(calls["walk_forward"] >= 2, "replay must refresh cached gates during a multi-session replay")


def audit_ohlcv_cache_reuses_persistent_history():
    stored = synthetic_price_frame(100, 0.2, periods=dwo.OHLCV_RETENTION_BARS)
    live = synthetic_price_frame(140, 0.25, periods=252)
    live["date"] = pd.bdate_range(stored["date"].iloc[-252], periods=252)
    calls = {"years": None, "persisted": 0}
    original_load = dwo.load_ohlcv_from_supabase
    original_fetch = dwo.fetch_chart
    original_persist = dwo.persist_ohlcv_to_supabase
    dwo.load_ohlcv_from_supabase = lambda ticker: stored.copy()

    def fetch_recent(ticker, years, refresh):
        calls["years"] = years
        return live.copy()

    def persist(ticker, frame):
        calls["persisted"] = len(frame)

    dwo.fetch_chart = fetch_recent
    dwo.persist_ohlcv_to_supabase = persist
    try:
        combined = dwo.load_or_refresh_ohlcv("TEST", years=2, refresh=True)
    finally:
        dwo.load_ohlcv_from_supabase = original_load
        dwo.fetch_chart = original_fetch
        dwo.persist_ohlcv_to_supabase = original_persist

    assert_true(calls["years"] == dwo.OHLCV_INCREMENTAL_YEARS, "seeded OHLCV cache must request only the short live refresh window")
    assert_true(len(combined) == dwo.OHLCV_RETENTION_BARS, "OHLCV cache must enforce the fixed retention cap")
    assert_true(0 < calls["persisted"] < dwo.OHLCV_RETENTION_BARS, "seeded OHLCV cache must write only recent revisions")


def audit_risk_off_or_missing_replay_cannot_seed_bullish_learning():
    ticker = synthetic_price_frame(100, 0.35)
    risk_off_benchmarks = {symbol: synthetic_price_frame(180, -0.25) for symbol in ("SPY", "QQQ", "SMH")}
    replay = dwo.build_behavior_history("TEST", ticker, days=3, benchmark_frames=risk_off_benchmarks)
    missing_replay = dwo.build_behavior_history("TEST", ticker, days=1, benchmark_frames={})
    assert_true(replay and all(item["market_permission"] == "BLOCK" for item in replay), "risk-off replay must retain date-aligned market blocks")
    assert_true(missing_replay and missing_replay[0]["market_permission"] == "BLOCK", "missing benchmark history must block replay execution")
    risk_off_outcome = dwo.self_score_prior_signal(executable_prior(market_permission=replay[-1]["market_permission"]), executable_current(close=104), "2026-06-02")
    missing_market_outcome = dwo.self_score_prior_signal(executable_prior(market_permission="UNKNOWN"), executable_current(close=104), "2026-06-02")
    assert_true(risk_off_outcome["outcome_label"] == "NON_LEARNABLE", "risk-off replay must not seed a learnable bullish outcome")
    assert_true(missing_market_outcome["outcome_learnable"] is False, "missing benchmark history must be non-promotable")


def audit_broad_learning_cannot_promote_score():
    current = learning_confirmed_setup_row()
    current["adjusted_score"] = 78
    stats = dwo.build_learning_stats(pd.DataFrame(outcome_rows(6, "OTHER|KEY")))
    dwo.apply_learning_adjustments([current], stats)
    assert_true(current["learning_scope"] == "action/setup family", "broad family evidence should remain visible")
    assert_true(current["learning_adjustment"] == 0.0, "broad positive evidence must not promote score")
    assert_true(current["adjusted_score"] == 78.0, "broad positive evidence must not change adjusted score")


def audit_exact_learning_requires_diverse_evidence_for_promotion():
    current = learning_confirmed_setup_row()
    current["adjusted_score"] = 78
    key = dwo.learning_key_for(current)
    narrow = pd.DataFrame(outcome_rows(30, key, ticker_prefix="ONE"))
    narrow["ticker"] = "ONE"
    stats = dwo.build_learning_stats(narrow)
    dwo.apply_learning_adjustments([current], stats)
    assert_true(current["learning_adjustment"] == 0.0, "single-ticker exact evidence must not promote score")

    diverse_current = learning_confirmed_setup_row()
    diverse_current["adjusted_score"] = 78
    diverse_stats = dwo.build_learning_stats(pd.DataFrame(outcome_rows(30, key)))
    dwo.apply_learning_adjustments([diverse_current], diverse_stats)
    assert_true(diverse_current["learning_adjustment"] > 0, "diverse exact evidence may promote score")
    assert_true(diverse_current["learning_distinct_ticker_count"] >= 8, "promotion must expose distinct-ticker evidence")


def audit_prediction_probabilities_are_smoothed_and_complete():
    current = learning_confirmed_setup_row()
    key = dwo.learning_key_for(current)
    outcomes = pd.DataFrame(outcome_rows(6, key))
    outcomes.loc[0, "outcome_label"] = "FAILED"
    outcomes.loc[0, "outcome_score"] = -1.0
    stats = dwo.build_learning_stats(outcomes)
    dwo.apply_learning_adjustments([current], stats)
    probability_sum = (
        float(current["prediction_upside_probability"])
        + float(current["prediction_downside_probability"])
        + float(current["prediction_no_edge_probability"])
    )
    assert_true(abs(probability_sum - 1.0) < 0.002, "smoothed prediction probabilities must sum to one")
    assert_true(current["prediction_horizon_sessions"] == dwo.LEARNING_HORIZON_SESSIONS, "prediction must disclose its horizon")


def audit_walk_forward_prediction_has_no_future_leakage():
    key = "SETUP FORMING|PULLBACK BUY|BALANCED|ACCUMULATION|NONE"
    rows = pd.DataFrame(outcome_rows(8, key))
    rows["signal_run_date"] = [f"2026-06-{index + 2:02d}" for index in range(8)]
    rows["evaluation_run_date"] = [f"2026-06-{index + 1:02d}" for index in range(8)]
    for column in (
        "prior_prediction_upside_probability",
        "prior_prediction_downside_probability",
        "prior_prediction_no_edge_probability",
    ):
        rows[column] = float("nan")
    predicted = dwo.attach_walk_forward_predictions(rows)
    assert_true(predicted.iloc[0]["prior_prediction_state"] == "INSUFFICIENT_EVIDENCE", "first signal cannot learn from future outcomes")
    assert_true(pd.isna(predicted.iloc[0]["prior_prediction_upside_probability"]), "insufficient evidence must clear stale probabilities")
    assert_true(predicted.iloc[-1]["prior_prediction_state"] == "WALK_FORWARD", "later signals should learn from already-settled outcomes")


def audit_bad_walk_forward_calibration_blocks_promotion():
    current = learning_confirmed_setup_row()
    current["adjusted_score"] = 78
    key = dwo.learning_key_for(current)
    outcomes = pd.DataFrame(outcome_rows(8, key))
    outcomes["prior_prediction_upside_probability"] = 0.05
    outcomes["prior_prediction_downside_probability"] = 0.90
    outcomes["prior_prediction_no_edge_probability"] = 0.05
    stats = dwo.build_learning_stats(outcomes)
    dwo.apply_learning_adjustments([current], stats)
    assert_true(current["learning_brier_score"] > dwo.LEARNING_CALIBRATION_MAX_BRIER, "fixture must fail calibration")
    assert_true(current["learning_adjustment"] == 0.0, "poor sample-out calibration must block positive promotion")
    assert_true(current["learning_reporting_only"], "poor calibration must remain reporting-only")


def audit_outcome_freezes_original_prediction():
    prior = executable_prior(
        prediction_upside_probability=0.62,
        prediction_downside_probability=0.18,
        prediction_no_edge_probability=0.20,
        prediction_confidence=0.55,
        prediction_state="CALIBRATED",
    )
    outcome = dwo.score_signal_horizon(
        prior,
        [executable_current(open=100, high=104, low=99, close=103)] * dwo.LEARNING_HORIZON_SESSIONS,
    )
    assert_true(outcome["prior_prediction_upside_probability"] == 0.62, "outcomes must retain the forecast made before evaluation")
    assert_true(outcome["prior_prediction_state"] == "CALIBRATED", "outcomes must retain the original prediction state")


def audit_learning_promotion_requires_all_execution_gates():
    key = dwo.learning_key_for(learning_confirmed_setup_row())
    stats = dwo.build_learning_stats(pd.DataFrame(outcome_rows(30, key)))
    blocked_gates = {
        "market_permission": "BLOCK",
        "ticker_permission": "BLOCK",
        "walk_forward_permission": "BLOCK",
        "risk_permission": "BLOCK",
        "personality_setup_allowed": "NO",
    }
    for gate, blocked_value in blocked_gates.items():
        current = learning_confirmed_setup_row(**{gate: blocked_value})
        current["adjusted_score"] = 78
        dwo.apply_learning_adjustments([current], stats)
        assert_true(current["learning_adjustment"] == 0.0, f"{gate} must suppress positive learning adjustment")
        assert_true(current["adjusted_score"] == 78.0, f"{gate} must preserve the pre-learning score")
        assert_true(not current["learning_promotion_eligible"], f"{gate} must block learning promotion eligibility")
        assert_true(current["learning_reporting_only"], f"{gate} must keep learning reporting-only")


def audit_personality_setup_governor_blocks_range_chase():
    allowed = dwo.personality_setup_execution_allowed(
        "RANGE_BOUND", "MOMENTUM BUY", "MEAN REVERSION", True, 92, False, False, False, True, True
    )
    assert_true(not allowed, "range-bound momentum must remain BUILDING even with strong buyer tape")
    reversal = dwo.personality_setup_execution_allowed(
        "RANGE_BOUND", "REVERSAL BUY", "MEAN REVERSION", True, 75, True, True, False, False, False
    )
    assert_true(reversal, "confirmed range-bound reversal should remain executable")


def audit_personality_exit_separates_profit_protect():
    soft_range_exit = dwo.personality_exit_pressure("RANGE_BOUND", False, True, True)
    assert_true(not soft_range_exit, "range-bound distribution without hard damage must stay profit protect")
    hard_range_exit = dwo.personality_exit_pressure("RANGE_BOUND", True, False, True)
    assert_true(hard_range_exit, "range-bound structural damage must remain a hard EXIT")


def main():
    audit_profit_active_does_not_force_defense()
    audit_profit_protect_requires_giveback_or_supply()
    audit_post_exit_cooldown_sees_short_pressure()
    audit_post_exit_risk_persistence_keeps_exit_pressure()
    audit_post_exit_risk_persistence_allows_strong_reclaim()
    audit_range_bound_reclaim_cannot_skip_post_exit_cooldown()
    audit_volatile_hold_has_consistent_score()
    audit_behavior_history_seeds_learning()
    audit_unfilled_buy_is_excluded_from_learning()
    audit_ambiguous_daily_path_is_excluded_from_learning()
    audit_non_executable_signal_is_excluded_from_risk_path_learning()
    audit_defensive_learning_shows_samples_without_promotion()
    audit_learning_lookback_supports_60_day_window()
    audit_learning_key_uses_behavior_not_ticker_identity()
    audit_action_display_labels_match_product_ui()
    audit_learning_can_upgrade_building_execution_tier()
    audit_learning_upgrade_respects_anti_signals()
    audit_safety_gates_preserve_raw_technical_score()
    audit_freshness_gate_preserves_raw_technical_score()
    audit_learning_upgrade_respects_personality_gate()
    audit_stop_breach_cannot_be_working()
    audit_stale_stop_breach_is_not_learnable()
    audit_gap_through_entry_stop_is_non_learnable()
    audit_outcome_does_not_depend_on_current_action()
    audit_hard_gate_blocked_signal_cannot_work_or_learn()
    audit_learning_excludes_unversioned_outcomes()
    audit_learning_requires_explicit_learnable_outcome()
    audit_missing_boolean_is_never_affirmative()
    audit_gated_setup_calibrates_forecast_without_becoming_executable()
    audit_counterfactual_forecasts_cannot_promote_execution()
    audit_invalid_probabilities_are_excluded_from_calibration()
    audit_same_bar_entry_target_order_is_ambiguous()
    audit_learning_uses_displayed_target_when_available()
    audit_exit_pressure_has_risk_first_action_precedence()
    audit_signal_outcome_history_is_paginated()
    audit_missing_optional_outcome_metrics_do_not_crash_learning()
    audit_directional_walk_forward_is_future_invariant()
    audit_directional_model_requires_sample_out_evidence()
    audit_directional_veto_cannot_be_reupgraded_by_buy_tier()
    audit_categorical_promotion_requires_thirty_executable_samples()
    audit_learning_window_uses_recent_evaluation_sessions_only()
    audit_broad_learning_cannot_promote_score()
    audit_exact_learning_requires_diverse_evidence_for_promotion()
    audit_prediction_probabilities_are_smoothed_and_complete()
    audit_walk_forward_prediction_has_no_future_leakage()
    audit_bad_walk_forward_calibration_blocks_promotion()
    audit_outcome_freezes_original_prediction()
    audit_learning_promotion_requires_all_execution_gates()
    audit_replay_market_gate_matches_live_context()
    audit_replay_gate_cache_is_bounded_and_historical()
    audit_ohlcv_cache_reuses_persistent_history()
    audit_risk_off_or_missing_replay_cannot_seed_bullish_learning()
    audit_personality_setup_governor_blocks_range_chase()
    audit_personality_exit_separates_profit_protect()
    print({
        "contextOverlayAudit": "ok",
        "cases": 54,
    })


if __name__ == "__main__":
    main()
