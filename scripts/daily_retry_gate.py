#!/usr/bin/env python3
"""Run guarded daily recoveries only when earlier scheduled attempts failed.

The workflow run name contains the triggering cron expression. That marker is
authoritative even when GitHub starts a schedule hours late or after midnight.
Weekly runs and untagged scheduled runs are deliberately ignored.
"""

from __future__ import annotations

import argparse
from datetime import datetime, time, timedelta, timezone
import json
import sys
from typing import Any
from zoneinfo import ZoneInfo

from weekly_retry_gate import ACTIVE_STATUSES, RETRY_CONCLUSIONS, parse_github_time


MELBOURNE_TZ = ZoneInfo("Australia/Melbourne")
PRIMARY_SCHEDULES = {
    # 11:17 Melbourne during daylight-saving time (UTC+11).
    "17 00 * * 2-6": time(0, 17),
    # 11:17 Melbourne during standard time (UTC+10).
    "17 01 * * 2-6": time(1, 17),
}
RETRY_TO_PRIMARY = {
    # 14:17 Melbourne during daylight-saving time.
    "17 03 * * 2-6": ("17 00 * * 2-6", time(0, 17), ("17 00 * * 2-6",)),
    # 14:17 Melbourne during standard time.
    "17 04 * * 2-6": ("17 01 * * 2-6", time(1, 17), ("17 01 * * 2-6",)),
    # 17:17 final recovery checks both earlier attempts.
    "17 06 * * 2-6": (
        "17 00 * * 2-6", time(0, 17), ("17 00 * * 2-6", "17 03 * * 2-6")
    ),
    "17 07 * * 2-6": (
        "17 01 * * 2-6", time(1, 17), ("17 01 * * 2-6", "17 04 * * 2-6")
    ),
}


def melbourne_schedule_kind(schedule: str, reference_time: datetime | None = None) -> str:
    """Select the UTC cron that represents Melbourne's active daily slots."""
    reference = reference_time or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    offset = reference.astimezone(MELBOURNE_TZ).utcoffset()
    offset_hours = int(offset.total_seconds() // 3600) if offset is not None else 0
    active_primary = "17 00 * * 2-6" if offset_hours == 11 else "17 01 * * 2-6"
    active_retries = (
        ("17 03 * * 2-6", "17 06 * * 2-6")
        if offset_hours == 11
        else ("17 04 * * 2-6", "17 07 * * 2-6")
    )
    if schedule == active_primary:
        return "primary"
    if schedule in active_retries:
        return "retry"
    if schedule in PRIMARY_SCHEDULES or schedule in RETRY_TO_PRIMARY:
        return "skip"
    raise ValueError(f"unrecognized daily schedule: {schedule}")


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
    current_title = str(current.get("display_title") or "")
    retry_marker = next((marker for marker in RETRY_TO_PRIMARY if marker in current_title), None)
    if retry_marker is None:
        raise ValueError("daily retry gate must run from the tagged daily retry schedule")
    if current_created.weekday() not in {1, 2, 3, 4, 5, 6}:
        raise ValueError("daily retry gate must run Tuesday through Sunday UTC")

    primary_marker, primary_schedule_utc, preceding_markers = RETRY_TO_PRIMARY[retry_marker]
    primary_date = current_created.date()
    if current_created.time() < primary_schedule_utc:
        primary_date -= timedelta(days=1)
    window_start = datetime.combine(primary_date, primary_schedule_utc, tzinfo=timezone.utc)
    next_primary_start = window_start + timedelta(days=1)
    window_end = min(current_created, next_primary_start)
    candidates = []
    for run in runs:
        if str(run.get("id")) == str(current_run_id) or run.get("event") != "schedule":
            continue
        if not any(marker in str(run.get("display_title") or "") for marker in preceding_markers):
            continue
        created = parse_github_time(run.get("created_at"))
        if created is None or not window_start <= created < window_end:
            continue
        candidates.append((created, run))

    if not candidates:
        return "retry", "preceding tagged daily attempts are missing; running recovery"

    active = [item for item in candidates if str(item[1].get("status") or "") in ACTIVE_STATUSES]
    if active:
        _, attempt = max(active, key=lambda item: item[0])
        return "skip", f"daily attempt {attempt.get('id', 'unknown')} is {attempt.get('status', 'unknown')}"
    successful = [item for item in candidates if str(item[1].get("conclusion") or "") == "success"]
    if successful:
        _, attempt = max(successful, key=lambda item: item[0])
        return "skip", f"daily attempt {attempt.get('id', 'unknown')} succeeded"
    _, attempt = max(candidates, key=lambda item: item[0])
    status = str(attempt.get("status") or "unknown")
    conclusion = str(attempt.get("conclusion") or "unknown")
    attempt_id = attempt.get("id", "unknown")
    if conclusion in RETRY_CONCLUSIONS:
        return "retry", f"daily attempt {attempt_id} concluded {conclusion}"
    return "skip", f"daily attempt {attempt_id} has unrecognized state {status}/{conclusion}"


def main() -> int:
    parser = argparse.ArgumentParser()
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--current-run-id")
    selector.add_argument("--schedule-kind")
    parser.add_argument("--reference-time")
    args = parser.parse_args()
    if args.schedule_kind:
        try:
            reference_time = parse_github_time(args.reference_time) if args.reference_time else None
            if args.reference_time and reference_time is None:
                raise ValueError("reference time must be an ISO-8601 timestamp")
            print(melbourne_schedule_kind(args.schedule_kind, reference_time))
        except ValueError as exc:
            print(f"Daily schedule selector error: {exc}", file=sys.stderr)
            return 2
        return 0
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
