import sys
from pathlib import Path

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
        {**row("2026-06-01", "BUY CANDIDATE", 100, setup="MOMENTUM BUY"), "ticker": "MU"},
        {**row("2026-06-02", "WATCH TREND", 104, setup="NONE"), "ticker": "MU"},
        {**row("2026-06-03", "SETUP FORMING", 103, setup="PULLBACK BUY"), "ticker": "MU"},
    ]
    outcomes = dwo.build_backfilled_signal_outcomes(history_rows)
    assert_true(len(outcomes) >= 1, "behavior replay should create backfilled learning samples")
    first = outcomes.iloc[0].to_dict()
    assert_true(first["signal_run_date"] == "2026-06-01", "backfilled sample must use prior history date")
    assert_true(first["evaluation_run_date"] == "2026-06-02", "backfilled sample must evaluate on next history date")
    assert_true(first["outcome_label"] == "WORKING", "BUY with follow-through should seed WORKING")
    stats = dwo.build_learning_stats(outcomes)
    assert_true(bool(stats), "backfilled outcomes should feed learning stats")


def audit_defensive_learning_shows_samples_without_promotion():
    history_rows = []
    for ticker in ["A", "B", "C"]:
        history_rows.append({**row("2026-06-01", "EXIT PRESSURE", 100, setup="NONE"), "ticker": ticker})
        history_rows.append({**row("2026-06-02", "EXIT PRESSURE", 98, setup="NONE"), "ticker": ticker})
    outcomes = dwo.build_backfilled_signal_outcomes(history_rows)
    stats = dwo.build_learning_stats(outcomes)
    current = row("2026-06-03", "EXIT PRESSURE", 100, setup="NONE", score=20)
    current["ticker"] = "NVDA"
    current["adjusted_score"] = 20
    dwo.apply_learning_adjustments([current], stats)
    assert_true(current["learning_sample_count"] == 3, "defensive family samples should be visible")
    assert_true(current["learning_adjustment"] == 0.0, "successful defensive learning must not promote EXIT score")
    assert_true(float(current["adjusted_score"]) == 20.0, "EXIT adjusted score must remain unchanged by positive defense learning")


def audit_learning_lookback_stays_on_30_day_window():
    history_rows = [
        {**row(f"2026-06-{day:02d}", "BUY CANDIDATE", 100 + day, setup="MOMENTUM BUY"), "ticker": "MU"}
        for day in range(1, 31)
    ]
    learning_outcomes = dwo.build_backfilled_signal_outcomes(history_rows)
    assert_true(dwo.DEFAULT_LEARNING_LOOKBACK_DAYS == 30, "default learning lookback should stay aligned to stored 30-day history")
    assert_true(len(learning_outcomes) == 29, "30 stored days should create 29 adjacent learning samples")


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
        "learning_sample_count": 8,
        "learning_working_rate": 0.75,
        "learning_failed_rate": 0.125,
        "learning_adjustment": 5.0,
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


def main():
    audit_profit_active_does_not_force_defense()
    audit_profit_protect_requires_giveback_or_supply()
    audit_post_exit_cooldown_sees_short_pressure()
    audit_post_exit_risk_persistence_keeps_exit_pressure()
    audit_post_exit_risk_persistence_allows_strong_reclaim()
    audit_volatile_hold_has_consistent_score()
    audit_behavior_history_seeds_learning()
    audit_defensive_learning_shows_samples_without_promotion()
    audit_learning_lookback_stays_on_30_day_window()
    audit_action_display_labels_match_product_ui()
    audit_learning_can_upgrade_building_execution_tier()
    audit_learning_upgrade_respects_anti_signals()
    print({
        "contextOverlayAudit": "ok",
        "cases": 12,
    })


if __name__ == "__main__":
    main()
