#!/usr/bin/env python3
"""Evaluate no-lookahead momentum-climax gates against saved watchlist history."""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import daily_watchlist_overview as scanner


ACTIONABLE = {"BUY CANDIDATE", "STRONG CONTINUATION"}


@dataclass(frozen=True)
class Gate:
    name: str
    move_multiple: float
    return_atr: float
    corroborators: int


GATES = (
    Gate("balanced", 1.75, 0.90, 2),
    Gate("conservative", 2.00, 1.00, 2),
    Gate("production", 2.00, 1.15, 3),
)


def ticker_from_path(path: Path) -> str:
    return re.sub(r"^watchlist_|_1y$", "", path.stem)


def load_price_features(root: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(root.glob("watchlist_*_1y.csv")):
        ticker = ticker_from_path(path)
        raw = pd.read_csv(path)
        raw.columns = [str(column).strip().lower() for column in raw.columns]
        required = {"date", "open", "high", "low", "close", "volume"}
        if not required.issubset(raw.columns):
            continue
        prepared = scanner.prepare(raw)
        prepared["date"] = pd.to_datetime(prepared["date"]).dt.strftime("%Y-%m-%d")
        prepared["ticker"] = scanner.display_ticker(ticker)
        prepared["day_change_pct_raw"] = prepared["close"].pct_change() * 100.0
        prepared["ema_extension_atr"] = np.where(
            prepared["atr"] > 0,
            (prepared["close"] - prepared["ema_fast"]) / prepared["atr"],
            np.nan,
        )
        prepared["gap_atr"] = np.where(
            prepared["atr"] > 0,
            (prepared["open"] - prepared["close"].shift(1)) / prepared["atr"],
            np.nan,
        )
        prepared["next_return_pct"] = prepared["close"].shift(-1) / prepared["close"] * 100.0 - 100.0
        prepared["return_5d_forward_pct"] = prepared["close"].shift(-5) / prepared["close"] * 100.0 - 100.0
        future_highs = pd.concat([prepared["high"].shift(-step) for step in range(1, 6)], axis=1)
        future_lows = pd.concat([prepared["low"].shift(-step) for step in range(1, 6)], axis=1)
        prepared["mfe_5d_pct"] = future_highs.max(axis=1) / prepared["close"] * 100.0 - 100.0
        prepared["mae_5d_pct"] = future_lows.min(axis=1) / prepared["close"] * 100.0 - 100.0
        prepared["momentum_climax_state"] = [
            scanner.momentum_climax_state(prepared, index, ticker in scanner.ETF_HINTS)["state"]
            for index in range(len(prepared))
        ]
        reclaim_actions = pd.Series("", index=prepared.index, dtype="object")
        for index in prepared.index[prepared["momentum_climax_state"] == "RECLAIM CONFIRMED"]:
            if index < 219:
                continue
            signal = scanner.classify_and_score(
                ticker,
                prepared.iloc[: index + 1],
                prepared=True,
                include_setup_stats=False,
                include_audit_gates=False,
            )
            reclaim_actions.loc[index] = signal["action"]
        prepared["reclaim_action"] = reclaim_actions
        prepared["next_momentum_climax_state"] = prepared["momentum_climax_state"].shift(-1)
        prepared["next_reclaim_action"] = prepared["reclaim_action"].shift(-1)
        prepared["reentry_return_5d_pct"] = prepared["close"].shift(-6) / prepared["close"].shift(-1) * 100.0 - 100.0
        reentry_lows = pd.concat([prepared["low"].shift(-step) for step in range(2, 7)], axis=1)
        prepared["reentry_mae_5d_pct"] = reentry_lows.min(axis=1) / prepared["close"].shift(-1) * 100.0 - 100.0
        frames.append(
            prepared[
                [
                    "ticker", "date", "relative_volume", "range_atr", "close_loc",
                    "ema_extension_atr", "gap_atr", "next_return_pct",
                    "return_5d_forward_pct", "mfe_5d_pct", "mae_5d_pct",
                    "momentum_climax_state", "next_momentum_climax_state",
                    "reclaim_action", "next_reclaim_action", "reentry_return_5d_pct", "reentry_mae_5d_pct",
                ]
            ]
        )
    if not frames:
        raise RuntimeError("No watchlist_*_1y.csv files with OHLCV data were found")
    return pd.concat(frames, ignore_index=True)


def replay_core_signals(root: Path) -> pd.DataFrame:
    records = []
    for path in sorted(root.glob("watchlist_*_1y.csv")):
        ticker = ticker_from_path(path)
        raw = pd.read_csv(path)
        raw.columns = [str(column).strip().lower() for column in raw.columns]
        if not {"date", "open", "high", "low", "close", "volume"}.issubset(raw.columns):
            continue
        prepared = scanner.prepare(raw)
        for index in range(219, len(prepared) - 5):
            baseline = scanner.classify_and_score(
                ticker,
                prepared.iloc[: index + 1],
                prepared=True,
                include_setup_stats=False,
                include_audit_gates=False,
                include_climax_gate=False,
            )
            if baseline["action"] not in ACTIONABLE:
                continue
            candidate = scanner.classify_and_score(
                ticker,
                prepared.iloc[: index + 1],
                prepared=True,
                include_setup_stats=False,
                include_audit_gates=False,
                include_climax_gate=True,
            )
            current = prepared.iloc[index]
            future = prepared.iloc[index + 1 : index + 6]
            next_state = scanner.momentum_climax_state(prepared, index + 1, ticker in scanner.ETF_HINTS)["state"]
            next_reclaim_action = ""
            if next_state == "RECLAIM CONFIRMED":
                next_reclaim_action = scanner.classify_and_score(
                    ticker,
                    prepared.iloc[: index + 2],
                    prepared=True,
                    include_setup_stats=False,
                    include_audit_gates=False,
                    include_climax_gate=True,
                )["action"]
            reentry_return = (
                (float(prepared.iloc[index + 6].close) / float(prepared.iloc[index + 1].close) - 1.0) * 100.0
                if index + 6 < len(prepared)
                else np.nan
            )
            reentry_lows = prepared.iloc[index + 2 : index + 7].low
            reentry_mae = (
                (float(reentry_lows.min()) / float(prepared.iloc[index + 1].close) - 1.0) * 100.0
                if len(reentry_lows) == 5
                else np.nan
            )
            records.append({
                **baseline,
                "ticker": scanner.display_ticker(ticker),
                "date": pd.to_datetime(current.date).strftime("%Y-%m-%d"),
                "baseline_action": baseline["action"],
                "candidate_action": candidate["action"],
                "candidate_position_size_factor": candidate["position_size_factor"],
                "ema_extension_atr": (
                    (float(current.close) - float(current.ema_fast)) / float(current.atr)
                    if float(current.atr) > 0
                    else np.nan
                ),
                "gap_atr": (
                    (float(current.open) - float(prepared.iloc[index - 1].close)) / float(current.atr)
                    if float(current.atr) > 0
                    else np.nan
                ),
                "next_momentum_climax_state": next_state,
                "next_reclaim_action": next_reclaim_action,
                "reentry_return_5d_pct": reentry_return,
                "reentry_mae_5d_pct": reentry_mae,
                "next_return_pct": (float(prepared.iloc[index + 1].close) / float(current.close) - 1.0) * 100.0,
                "return_5d_forward_pct": (float(prepared.iloc[index + 5].close) / float(current.close) - 1.0) * 100.0,
                "mfe_5d_pct": (float(future.high.max()) / float(current.close) - 1.0) * 100.0,
                "mae_5d_pct": (float(future.low.min()) / float(current.close) - 1.0) * 100.0,
            })
    if not records:
        raise RuntimeError("Replay produced no actionable core signals")
    return pd.DataFrame(records)


def mark_gate(rows: pd.DataFrame, gate: Gate) -> pd.Series:
    if gate.name == "production":
        if {"baseline_action", "candidate_action"}.issubset(rows.columns):
            return rows["baseline_action"] != rows["candidate_action"]
        return rows["momentum_climax_state"].isin({"CLIMAX LOCKOUT", "RECLAIM FAILED", "RECLAIM PENDING"})
    normal_move = pd.to_numeric(rows["personality_abs_move_pct"], errors="coerce").fillna(1.5).clip(lower=0.5)
    atr_pct = pd.to_numeric(rows["atr_pct"], errors="coerce").replace(0, np.nan)
    day_change = pd.to_numeric(rows["day_change_pct"], errors="coerce")
    shock = (day_change >= np.maximum(3.0, normal_move * gate.move_multiple)) & (
        day_change / atr_pct >= gate.return_atr
    )
    corroboration = (
        (rows["relative_volume"] >= 1.20).astype(int)
        + (rows["range_atr"] >= 1.25).astype(int)
        + (rows["ema_extension_atr"] >= 2.00).astype(int)
        + (pd.to_numeric(rows["rsi"], errors="coerce") >= 72.0).astype(int)
        + (rows["gap_atr"] >= 0.50).astype(int)
    )
    return shock & (corroboration >= gate.corroborators)


def metrics(rows: pd.DataFrame) -> dict:
    valid = rows.dropna(subset=["next_return_pct"])
    five_day = rows.dropna(subset=["return_5d_forward_pct"])
    return {
        "signals": int(len(rows)),
        "next_day_samples": int(len(valid)),
        "next_day_mean_pct": round(float(valid["next_return_pct"].mean()), 3) if len(valid) else None,
        "next_day_positive_rate": round(float((valid["next_return_pct"] > 0).mean()), 3) if len(valid) else None,
        "five_day_samples": int(len(five_day)),
        "five_day_mean_pct": round(float(five_day["return_5d_forward_pct"].mean()), 3) if len(five_day) else None,
        "five_day_median_pct": round(float(five_day["return_5d_forward_pct"].median()), 3) if len(five_day) else None,
        "five_day_tenth_percentile_pct": round(float(five_day["return_5d_forward_pct"].quantile(0.10)), 3) if len(five_day) else None,
        "five_day_failure_rate": round(float((five_day["return_5d_forward_pct"] <= -5.0).mean()), 3) if len(five_day) else None,
        "five_day_mean_mae_pct": round(float(five_day["mae_5d_pct"].mean()), 3) if len(five_day) else None,
        "five_day_mean_mfe_pct": round(float(five_day["mfe_5d_pct"].mean()), 3) if len(five_day) else None,
    }


def evaluate_gate(rows: pd.DataFrame, gate: Gate, split_date: str) -> dict:
    marked = rows.copy()
    marked["climax"] = mark_gate(marked, gate)
    periods = {
        "train": marked[marked["date"] <= split_date],
        "holdout": marked[marked["date"] > split_date],
        "all": marked,
    }
    parameters = gate.__dict__
    if gate.name == "production":
        parameters = {
            "personality": "HIGH_BETA",
            "strict_climax": {
                "move_multiple": scanner.CLIMAX_MOVE_MULTIPLE,
                "return_atr": scanner.CLIMAX_RETURN_ATR,
                "corroborators": scanner.CLIMAX_MIN_EVIDENCE,
            },
            "mature_chase": {
                "move_multiple": scanner.MATURE_CHASE_MOVE_MULTIPLE,
                "return_atr": scanner.MATURE_CHASE_RETURN_ATR,
                "return_20d_pct": scanner.MATURE_CHASE_RETURN_20D_PCT,
                "ema_extension_atr": scanner.MATURE_CHASE_EMA_EXTENSION_ATR,
            },
        }
    result = {"gate": gate.name, "parameters": parameters, "periods": {}}
    for name, period in periods.items():
        blocked = period[period["climax"]]
        retained = period[~period["climax"]]
        confirmed = blocked[
            (blocked["next_momentum_climax_state"] == "RECLAIM CONFIRMED")
            & blocked["next_reclaim_action"].isin(ACTIONABLE)
        ]
        failed = blocked[blocked["next_momentum_climax_state"] == "RECLAIM FAILED"]
        delayed_valid = confirmed.dropna(subset=["reentry_return_5d_pct"])
        result["periods"][name] = {
            "baseline": metrics(period),
            "retained": metrics(retained),
            "blocked": metrics(blocked),
            "blocked_tickers": sorted(blocked["ticker"].unique().tolist()),
            "blocked_by_personality": {
                str(personality): metrics(group)
                for personality, group in blocked.groupby("personality_type")
            },
            "next_session_states": {
                str(state): int(count)
                for state, count in blocked["next_momentum_climax_state"].value_counts(dropna=False).items()
            },
            "confirmed_reentry": {
                "signals": int(len(confirmed)),
                "five_day_samples": int(len(delayed_valid)),
                "five_day_mean_pct": round(float(delayed_valid["reentry_return_5d_pct"].mean()), 3) if len(delayed_valid) else None,
                "five_day_positive_rate": round(float((delayed_valid["reentry_return_5d_pct"] > 0).mean()), 3) if len(delayed_valid) else None,
                "five_day_mean_mae_pct": round(float(delayed_valid["reentry_mae_5d_pct"].mean()), 3) if len(delayed_valid) else None,
            },
            "failed_reclaim": metrics(failed),
            "blocked_examples": blocked[
                [
                    "ticker", "date", "personality_type", "action", "setup",
                    "day_change_pct", "relative_volume", "range_atr", "rsi",
                    "ema_extension_atr", "next_return_pct", "return_5d_forward_pct",
                    "mae_5d_pct", "mfe_5d_pct", "next_momentum_climax_state",
                    "next_reclaim_action", "reentry_return_5d_pct", "reentry_mae_5d_pct",
                ]
            ].head(50).replace({np.nan: None}).to_dict("records"),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--history", type=Path, default=Path("watchlist_behavior_history_latest.csv"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--rows-output", type=Path, help="Optional CSV of replay rows for independent diagnostics")
    parser.add_argument("--replay", action="store_true", help="Recompute core signals across every eligible historical bar")
    args = parser.parse_args()

    if args.replay:
        rows = replay_core_signals(args.root)
        rows["action"] = rows["baseline_action"]
    else:
        history_path = args.history if args.history.is_absolute() else args.root / args.history
        history = pd.read_csv(history_path)
        history["date"] = pd.to_datetime(history["date"]).dt.strftime("%Y-%m-%d")
        price_features = load_price_features(args.root)
        rows = history.merge(price_features, on=["ticker", "date"], how="left", validate="many_to_one")
        rows = rows[rows["action"].isin(ACTIONABLE)].copy()
    if rows.empty:
        raise RuntimeError("Behavior history contains no actionable signals")

    dates = sorted(rows["date"].unique())
    split_date = dates[max(0, math.ceil(len(dates) * 0.65) - 1)]
    report = {
        "method": (
            "core signals recomputed on each historical bar with the climax gate disabled for baseline"
            if args.replay
            else "signals frozen from historical replay; OHLCV features and outcomes joined by ticker/date"
        ),
        "date_range": [dates[0], dates[-1]],
        "split_date": split_date,
        "actionable_signals": int(len(rows)),
        "missing_feature_rows": int(rows["relative_volume"].isna().sum()),
        "gates": [evaluate_gate(rows, gate, split_date) for gate in GATES],
    }
    if args.replay:
        changed = rows[rows["baseline_action"] != rows["candidate_action"]]
        report["candidate_action_changes"] = {
            "count": int(len(changed)),
            "from_to": {
                f"{source} -> {target}": int(count)
                for (source, target), count in changed.groupby(["baseline_action", "candidate_action"]).size().items()
            },
        }
    output = json.dumps(report, indent=2, sort_keys=True)
    print(output)
    if args.rows_output:
        rows.to_csv(args.rows_output, index=False)
    if args.json_output:
        args.json_output.write_text(output + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
