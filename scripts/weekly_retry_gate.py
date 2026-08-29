#!/usr/bin/env python3
"""Decide whether Saturday's weekly rebuild retry should run.

The workflow's dynamic run name includes the triggering cron expression, so a
delayed Friday daily run cannot be mistaken for Saturday's weekly primary. For
older untagged runs, use the latest scheduled run in the primary window; GitHub
Actions can delay a nominally earlier cron for many hours.
"""

from __future__ import annotations

import argparse
from datetime import datetime, time, timezone
import json
import sys
from typing import Any


RETRY_CONCLUSIONS = {
    "failure",
    "cancelled",
    "timed_out",
    "startup_failure",
    "stale",
    "action_required",
}
ACTIVE_STATUSES = {"queued", "in_progress"}
PRIMARY_SCHEDULE_UTC = time(3, 47)
PRIMARY_SCHEDULE_MARKER = "47 03 * * 6"
RETRY_SCHEDULE_MARKER = "47 07 * * 6"


def parse_github_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


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
    if current_created.weekday() != 5:
        raise ValueError("weekly retry gate must run on Saturday UTC")
    primary_window_start = datetime.combine(
        current_created.date(), PRIMARY_SCHEDULE_UTC, tzinfo=timezone.utc
    )

    candidates = []
    for run in runs:
        if str(run.get("id")) == str(current_run_id) or run.get("event") != "schedule":
            continue
        created = parse_github_time(run.get("created_at"))
        if created is None:
            continue
        if primary_window_start <= created < current_created:
            candidates.append((created, run))

    if not candidates:
        return "retry", "same-day weekly primary is missing; running recovery"

    tagged_candidates = [
        item
        for item in candidates
        if PRIMARY_SCHEDULE_MARKER in str(item[1].get("display_title") or "")
    ]
    current_is_tagged = RETRY_SCHEDULE_MARKER in str(current.get("display_title") or "")
    if current_is_tagged and not tagged_candidates:
        return "retry", "same-day tagged weekly primary is missing; running recovery"
    # Tagged run names are authoritative. The latest-run fallback is only for
    # deployments created before run-name included the cron expression.
    _, primary = max(tagged_candidates or candidates, key=lambda item: item[0])
    status = str(primary.get("status") or "unknown")
    conclusion = str(primary.get("conclusion") or "unknown")
    primary_id = primary.get("id", "unknown")
    if status in ACTIVE_STATUSES:
        return "skip", f"weekly primary {primary_id} is {status}"
    if conclusion == "success":
        return "skip", f"weekly primary {primary_id} succeeded"
    if conclusion in RETRY_CONCLUSIONS:
        return "retry", f"weekly primary {primary_id} concluded {conclusion}"
    return "skip", f"weekly primary {primary_id} has unrecognized state {status}/{conclusion}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-run-id", required=True)
    args = parser.parse_args()
    try:
        payload = json.load(sys.stdin)
        decision, reason = retry_decision(payload, args.current_run_id)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Weekly retry selector error: {exc}", file=sys.stderr)
        return 2
    print(reason, file=sys.stderr)
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
