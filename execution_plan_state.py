"""Deterministic daily-OHLC lifecycle for frozen BUY execution plans."""

from __future__ import annotations

import hashlib
import json
from typing import Any


MODEL_VERSION = "daily-ohlcv-plan-v1"
ACTIVE_STATUSES = {"ARMED", "MODEL_FILLED", "TP1_HIT"}
SETUP_STYLES = {
    "BREAKOUT BUY": "BREAKOUT TRIGGER",
    "MOMENTUM BUY": "BREAKOUT TRIGGER",
    "PULLBACK BUY": "PULLBACK LIMIT",
    "EARLY PULLBACK BUY": "PULLBACK LIMIT",
    "REVERSAL BUY": "PULLBACK LIMIT",
}
PLAN_FIELDS = (
    "execution_plan_id",
    "execution_plan_model_version",
    "execution_plan_status",
    "execution_plan_signal_date",
    "execution_plan_last_evaluation_date",
    "execution_plan_age_sessions",
    "execution_plan_valid_sessions",
    "execution_plan_setup",
    "execution_plan_style",
    "execution_plan_personality",
    "execution_plan_volatility_regime",
    "execution_plan_zone_low",
    "execution_plan_zone_high",
    "execution_plan_stop",
    "execution_plan_target",
    "execution_plan_final_target",
    "execution_plan_post_tp1_stop",
    "execution_plan_management_sessions",
    "execution_plan_source_close",
    "execution_plan_fill_est",
    "execution_plan_entry_date",
    "execution_plan_risk_pct",
    "execution_plan_reason_code",
    "execution_plan_summary",
    "execution_plan_events",
    "execution_plan_previous_id",
    "execution_plan_previous_status",
    "execution_plan_previous_date",
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def _date(row: dict[str, Any]) -> str:
    return _text(row.get("date") or row.get("history_date") or row.get("data_date"))[:10]


def _plan_values_valid(row: dict[str, Any]) -> bool:
    low = _number(row.get("entry_zone_low"))
    high = _number(row.get("entry_zone_high"))
    stop = _number(row.get("stop_est"))
    target = _number(row.get("take_profit_1") or row.get("target_est"))
    return bool(
        low is not None
        and high is not None
        and stop is not None
        and target is not None
        and 0 < stop < low <= high < target
    )


def _valid_sessions(style: str, personality: str) -> int:
    if style == "BREAKOUT TRIGGER":
        return 1
    if personality in {"HIGH_BETA", "RANGE_BOUND"}:
        return 1
    return 2


def _plan_id(row: dict[str, Any]) -> str:
    identity = "|".join(
        [
            _text(row.get("ticker")).upper(),
            _date(row),
            _text(row.get("setup")).upper(),
            MODEL_VERSION,
        ]
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _event(date: str, status: str, reason: str) -> dict[str, str]:
    return {"date": date, "status": status, "reason": reason}


def _events(plan: dict[str, Any]) -> list[dict[str, str]]:
    value = plan.get("execution_plan_events")
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)][-3:]
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
            return [item for item in parsed if isinstance(item, dict)][-3:]
        except (TypeError, ValueError):
            return []
    return []


def _set_status(plan: dict[str, Any], date: str, status: str, reason: str, summary: str) -> dict[str, Any]:
    updated = dict(plan)
    updated["execution_plan_status"] = status
    updated["execution_plan_reason_code"] = reason
    updated["execution_plan_summary"] = summary
    events = _events(updated)
    event = _event(date, status, reason)
    if not events or events[-1] != event:
        events.append(event)
    updated["execution_plan_events"] = json.dumps(events[-4:], separators=(",", ":"))
    return updated


def create_execution_plan(row: dict[str, Any]) -> dict[str, Any] | None:
    """Create a frozen plan only from a final BUY candidate."""
    source_close = _number(row.get("close"))
    if (
        _text(row.get("action")).upper() != "BUY CANDIDATE"
        or _text(row.get("freshness_block")).upper() == "YES"
        or source_close is None
        or source_close <= 0
        or not _plan_values_valid(row)
    ):
        return None
    date = _date(row)
    setup = _text(row.get("setup")).upper()
    style = _text(row.get("execution_style")).upper()
    if style not in {"PULLBACK LIMIT", "BREAKOUT TRIGGER"} or SETUP_STYLES.get(setup) != style:
        return None
    personality = _text(row.get("personality_type")).upper() or "BALANCED"
    zone_high = float(row["entry_zone_high"])
    stop = float(row["stop_est"])
    first_target = float(row.get("take_profit_1") or row.get("target_est"))
    plan = {
        "execution_plan_id": _plan_id(row),
        "execution_plan_model_version": MODEL_VERSION,
        "execution_plan_status": "ARMED",
        "execution_plan_signal_date": date,
        "execution_plan_last_evaluation_date": date,
        "execution_plan_age_sessions": 0,
        "execution_plan_valid_sessions": _valid_sessions(style, personality),
        "execution_plan_setup": _text(row.get("setup")),
        "execution_plan_style": style,
        "execution_plan_personality": personality,
        "execution_plan_volatility_regime": _text(row.get("volatility_regime")),
        "execution_plan_zone_low": round(float(row["entry_zone_low"]), 2),
        "execution_plan_zone_high": round(zone_high, 2),
        "execution_plan_stop": round(stop, 2),
        "execution_plan_target": round(first_target, 2),
        "execution_plan_final_target": round(float(row.get("target_est") or first_target), 2),
        "execution_plan_post_tp1_stop": round(float(row.get("post_tp1_stop") or stop), 2),
        "execution_plan_management_sessions": 5,
        "execution_plan_source_close": round(source_close, 2),
        "execution_plan_fill_est": "",
        "execution_plan_entry_date": "",
        "execution_plan_risk_pct": round((zone_high - stop) / zone_high * 100, 2),
        "execution_plan_reason_code": "BUY_SETUP_FROZEN",
        "execution_plan_summary": "BUY SETUP recorded. The entry zone and protection level are fixed for the next session plan.",
        "execution_plan_events": json.dumps([_event(date, "ARMED", "BUY_SETUP_FROZEN")], separators=(",", ":")),
    }
    return plan


def _copy_plan(row: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    updated = dict(row)
    for field in PLAN_FIELDS:
        if field in plan:
            updated[field] = plan[field]
    return updated


def _complete_filled_bar(plan: dict[str, Any], date: str, open_: float, high: float, low: float) -> dict[str, Any]:
    after_tp1 = _text(plan.get("execution_plan_status")).upper() == "TP1_HIT"
    stop = float(plan.get("execution_plan_post_tp1_stop") or plan["execution_plan_stop"]) if after_tp1 else float(plan["execution_plan_stop"])
    target = float(plan.get("execution_plan_final_target") or plan["execution_plan_target"]) if after_tp1 else float(plan["execution_plan_target"])
    stop_hit = low <= stop
    target_hit = high >= target
    if open_ <= stop:
        return _set_status(plan, date, "STOPPED", "OPENED_THROUGH_STOP", "The modeled entry was open, then price opened through the protection level.")
    if open_ >= target:
        if after_tp1:
            return _set_status(plan, date, "TARGET_HIT", "OPENED_AT_FINAL_TARGET", "Price opened at or above the frozen further target.")
        if float(plan.get("execution_plan_final_target") or target) <= target:
            return _set_status(plan, date, "TARGET_HIT", "OPENED_AT_FINAL_TARGET", "Price opened at or above the frozen target.")
        return _set_status(plan, date, "TP1_HIT", "OPENED_AT_FIRST_TARGET", "Price opened at or above the first profit review; the model raised protection.")
    if stop_hit and target_hit:
        return _set_status(plan, date, "AMBIGUOUS", "STOP_AND_TARGET_SAME_BAR", "The daily bar reached both protection and target; their order cannot be verified from daily data.")
    if stop_hit:
        return _set_status(plan, date, "STOPPED", "PROTECTION_REACHED", "After the modeled entry, price reached the frozen protection level.")
    if target_hit:
        if after_tp1:
            return _set_status(plan, date, "TARGET_HIT", "FINAL_TARGET_REACHED", "After the first profit review, price reached the frozen further target.")
        if float(plan.get("execution_plan_final_target") or target) <= target:
            return _set_status(plan, date, "TARGET_HIT", "FINAL_TARGET_REACHED", "Price reached the frozen target.")
        return _set_status(plan, date, "TP1_HIT", "FIRST_TARGET_REACHED", "Price reached the first profit review; the model raised protection and continues toward the further target.")
    return _set_status(plan, date, "MODEL_FILLED", "MODEL_ENTRY_OPEN", "Price reached the frozen entry condition; the model is now tracking protection and target.")


def evaluate_execution_plan(plan: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    """Advance one plan by one new daily bar without revising frozen levels."""
    status = _text(plan.get("execution_plan_status")).upper()
    date = _date(row)
    if status not in ACTIVE_STATUSES or not date or date <= _text(plan.get("execution_plan_last_evaluation_date")):
        return dict(plan)

    updated = dict(plan)
    updated["execution_plan_last_evaluation_date"] = date
    updated["execution_plan_age_sessions"] = int(_number(plan.get("execution_plan_age_sessions")) or 0) + 1
    values = [_number(row.get(field)) for field in ("open", "high", "low", "close")]
    invalid_ohlc = (
        any(value is None for value in values)
        or (all(value is not None for value in values) and (
            float(values[1]) < max(float(values[0]), float(values[3]))
            or float(values[2]) > min(float(values[0]), float(values[3]))
            or float(values[2]) <= 0
        ))
    )
    if invalid_ohlc or _text(row.get("freshness_block")).upper() == "YES":
        return _set_status(updated, date, "INVALIDATED", "DATA_UNAVAILABLE", "The next daily bar was incomplete or stale, so the plan was closed without inferring a trade.")
    open_, high, low, _ = (float(value) for value in values)
    zone_low = float(updated["execution_plan_zone_low"])
    zone_high = float(updated["execution_plan_zone_high"])
    stop = float(updated["execution_plan_stop"])
    target = float(updated["execution_plan_target"])

    hard_state = _text(row.get("operator_state")).upper()
    structural_exit = _text(row.get("action")).upper() == "EXIT PRESSURE"
    if status in {"MODEL_FILLED", "TP1_HIT"}:
        result = _complete_filled_bar(updated, date, open_, high, low)
        if _text(result.get("execution_plan_status")).upper() in {"MODEL_FILLED", "TP1_HIT"} and (
            hard_state in {"BULL_TRAP", "DISTRIBUTION"} or structural_exit
        ):
            return _set_status(result, date, "INVALIDATED", "HARD_RISK_CONFIRMED", "A confirmed trap, distribution pattern, or structural exit closed the frozen plan.")
        if (
            _text(result.get("execution_plan_status")).upper() in {"MODEL_FILLED", "TP1_HIT"}
            and int(updated["execution_plan_age_sessions"]) >= int(updated.get("execution_plan_management_sessions") or 5)
        ):
            return _set_status(result, date, "CLOSED", "MANAGEMENT_WINDOW_COMPLETE", "The five-session management window ended; review the stock as a new decision.")
        return result

    if hard_state in {"BULL_TRAP", "DISTRIBUTION"} or structural_exit:
        return _set_status(updated, date, "INVALIDATED", "HARD_RISK_CONFIRMED", "A confirmed trap, distribution pattern, or structural exit closed the frozen plan before entry.")

    style = _text(updated.get("execution_plan_style")).upper()
    fill = None
    if style == "BREAKOUT TRIGGER":
        if open_ > zone_high:
            return _set_status(updated, date, "INVALIDATED", "OPENED_ABOVE_MAX_ENTRY", "Price opened above the maximum entry price, so the plan was not chased.")
        if open_ <= stop:
            return _set_status(updated, date, "INVALIDATED", "OPENED_THROUGH_STOP", "Price opened below the protection level before the breakout could trigger.")
        if zone_low <= open_ <= zone_high:
            fill = open_
        elif open_ < zone_low <= high:
            if low <= stop:
                return _set_status(updated, date, "AMBIGUOUS", "ENTRY_AND_STOP_SAME_BAR", "The daily bar reached both the breakout trigger and protection; their order cannot be verified.")
            fill = zone_low
    else:
        if open_ <= stop:
            return _set_status(updated, date, "INVALIDATED", "OPENED_THROUGH_STOP", "Price opened below the protection level before a valid pullback entry.")
        if open_ < zone_low:
            return _set_status(updated, date, "INVALIDATED", "OPENED_BELOW_ZONE", "Price opened below the entry zone, so an intraday recovery was not treated as a valid entry.")
        if zone_low <= open_ <= zone_high:
            fill = open_
        elif open_ > zone_high and low <= zone_high and high >= zone_low:
            if low <= stop or high >= target:
                return _set_status(updated, date, "AMBIGUOUS", "ENTRY_AND_EXIT_SAME_BAR", "The daily bar reached the entry zone and an exit level; their order cannot be verified.")
            fill = zone_high

    if fill is not None:
        updated["execution_plan_fill_est"] = round(fill, 2)
        updated["execution_plan_entry_date"] = date
        updated = _set_status(updated, date, "TOUCHED", "ENTRY_ZONE_REACHED", "Price reached the frozen entry condition.")
        return _complete_filled_bar(updated, date, open_, high, low)
    if int(updated["execution_plan_age_sessions"]) >= int(updated["execution_plan_valid_sessions"]):
        return _set_status(updated, date, "EXPIRED", "ENTRY_NOT_REACHED", "Price did not reach the frozen entry condition before the plan expired.")
    return _set_status(updated, date, "ARMED", "AWAITING_ENTRY", "The frozen entry condition was not reached; the plan remains valid for the next session.")


def apply_execution_plan_lifecycle(
    rows: list[dict[str, Any]],
    previous_rows: list[dict[str, Any]],
    bars_by_ticker: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    """Attach the latest frozen plan state to each current scanner row."""
    previous_by_ticker: dict[str, list[dict[str, Any]]] = {}
    for item in previous_rows:
        ticker = _text(item.get("ticker")).upper()
        if ticker and item.get("execution_plan_id"):
            previous_by_ticker.setdefault(ticker, []).append(item)

    output: list[dict[str, Any]] = []
    for source in rows:
        row = dict(source)
        ticker = _text(row.get("ticker")).upper()
        candidates = sorted(previous_by_ticker.get(ticker, []), key=_date)
        prior = candidates[-1] if candidates else None
        plan = {field: prior.get(field) for field in PLAN_FIELDS if field in prior} if prior else None
        if plan and _text(plan.get("execution_plan_status")).upper() in ACTIVE_STATUSES:
            current_date = _date(row)
            pending_bars = [
                dict(bar)
                for bar in (bars_by_ticker or {}).get(ticker, [])
                if _text(plan.get("execution_plan_last_evaluation_date")) < _date(bar) <= current_date
            ]
            pending_by_date = {_date(bar): bar for bar in pending_bars if _date(bar)}
            pending_by_date[current_date] = row
            for bar_date in sorted(pending_by_date):
                plan = evaluate_execution_plan(plan, pending_by_date[bar_date])
                if _text(plan.get("execution_plan_status")).upper() not in ACTIVE_STATUSES:
                    break
            if (
                _text(plan.get("execution_plan_status")).upper() not in ACTIVE_STATUSES
                and _text(plan.get("execution_plan_last_evaluation_date")) <= current_date
                and _text(row.get("action")).upper() == "BUY CANDIDATE"
            ):
                predecessor = plan
                plan = create_execution_plan(row)
                if plan:
                    plan["execution_plan_previous_id"] = predecessor.get("execution_plan_id")
                    plan["execution_plan_previous_status"] = predecessor.get("execution_plan_status")
                    plan["execution_plan_previous_date"] = predecessor.get("execution_plan_last_evaluation_date")
        elif not plan or _date(row) > _text(plan.get("execution_plan_last_evaluation_date")):
            plan = create_execution_plan(row)
        if plan:
            row = _copy_plan(row, plan)
        output.append(row)
    return output
