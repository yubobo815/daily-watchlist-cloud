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
    assert_true(result["action"] == "SETUP FORMING", "cooldown must downgrade rebound BUY to SETUP")
    assert_true(result["next_day_bias"] == "EXECUTION BLOCKED", "cooldown must block next-day execution")


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


def main():
    audit_profit_active_does_not_force_defense()
    audit_profit_protect_requires_giveback_or_supply()
    audit_post_exit_cooldown_sees_short_pressure()
    audit_volatile_hold_has_consistent_score()
    print({
        "contextOverlayAudit": "ok",
        "cases": 4,
    })


if __name__ == "__main__":
    main()
