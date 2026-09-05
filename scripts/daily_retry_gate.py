#!/usr/bin/env python3
"""Run one daily recovery only when the preceding scheduled daily refresh failed.

The workflow run name contains the triggering cron expression. That marker is
authoritative even when GitHub starts Friday's daily refresh on Saturday UTC.
Weekly runs and untagged scheduled runs are deliberately ignored.
"""

from __future__ import annotations

import argparse
from datetime import datetime, time, timedelta, timezone
import json
import sys
from typing import Any

from weekly_retry_gate import ACTIVE_STATUSES, RETRY_CONCLUSIONS, parse_github_time


PRIMARY_SCHEDULE_MARKER = "17 23 * * 1-5"
RETRY_SCHEDULE_MARKER = "17 02 * * 2-6"
PRIMARY_SCHEDULE_UTC = time(23, 17)


def retry_decision(payload: dict[str, Any], current_run_id: str) -> tuple[str, str]:
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list):
        raise ValueError("workflow_runs must be a list")

    current = next((run for run in runs if str(run.get("id")) == str(current_run_id)), None)
    if current is None:
        raise ValueError(f"current workflow run {current_run_id} is missing from API response")
    current_created = parse_github_time(current.get("created_at"))
    if current_created is None:
        raise ValueError("current workflow run has no valid created_at")
    if RETRY_SCHEDULE_MARKER not in str(current.get("display_title") or ""):
        raise ValueError("daily retry gate must run from the tagged daily retry schedule")
    if current_created.weekday() not in {1, 2, 3, 4, 5}:
        raise ValueError("daily retry gate must run Tuesday through Saturday UTC")

    primary_date = current_created.date() - timedelta(days=1)
    window_start = datetime.combine(primary_date, PRIMARY_SCHEDULE_UTC, tzinfo=timezone.utc)
    next_primary_start = datetime.combine(current_created.date(), PRIMARY_SCHEDULE_UTC, tzinfo=timezone.utc)
    window_end = min(current_created, next_primary_start)
    candidates = []
    for run in runs:
        if str(run.get("id")) == str(current_run_id) or run.get("event") != "schedule":
            continue
        if PRIMARY_SCHEDULE_MARKER not in str(run.get("display_title") or ""):
            continue
        created = parse_github_time(run.get("created_at"))
        if created is None or not window_start <= created < window_end:
            continue
        candidates.append((created, run))

    if not candidates:
        return "retry", "preceding tagged daily primary is missing; running recovery"

    _, primary = max(candidates, key=lambda item: item[0])
    status = str(primary.get("status") or "unknown")
    conclusion = str(primary.get("conclusion") or "unknown")
    primary_id = primary.get("id", "unknown")
    if status in ACTIVE_STATUSES:
        return "skip", f"daily primary {primary_id} is {status}"
    if conclusion == "success":
        return "skip", f"daily primary {primary_id} succeeded"
    if conclusion in RETRY_CONCLUSIONS:
        return "retry", f"daily primary {primary_id} concluded {conclusion}"
    return "skip", f"daily primary {primary_id} has unrecognized state {status}/{conclusion}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-run-id", required=True)
    args = parser.parse_args()
    try:
        payload = json.load(sys.stdin)
        decision, reason = retry_decision(payload, args.current_run_id)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Daily retry selector error: {exc}", file=sys.stderr)
        return 2
    print(reason, file=sys.stderr)
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
