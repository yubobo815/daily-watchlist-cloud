"""Verify a curated ready-PR against the read-only monthly archive. No curation in CI."""
from __future__ import annotations

import argparse
import copy
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

from probe_market_brief_drive import DriveReader, FOLDER_MIME, ProbeError
from sync_market_brief_drive import exact_keys, parse_json, require, timestamp, validate_brief

MONTH = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")
REPORT = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:-v([1-9]\d*))?\.md$")


def readonly_folder(reader, folder_id, parent=None):
    meta = reader.get(folder_id)
    require(meta.get("id") == folder_id and meta.get("mimeType") == FOLDER_MIME, "Expected the authorized archive folder.")
    require(meta.get("capabilities", {}).get("canEdit") is False and meta.get("capabilities", {}).get("canAddChildren") is False, "The archive identity must have read-only access.")
    require(parent is None or parent in meta.get("parents", []), "The month folder is outside the authorized archive.")
    return meta


def newest_report(reader, root, now):
    readonly_folder(reader, root)
    today = now.astimezone(ZoneInfo("Australia/Melbourne")).date()
    first = today.replace(day=1)
    from datetime import timedelta
    previous = (first - timedelta(days=1)).strftime("%Y-%m")
    months = {today.strftime("%Y-%m"), previous}
    folders = [f for f in reader.list_children(root) if MONTH.fullmatch(f.get("name", "")) and f["name"] in months and not f.get("trashed")]
    require(len({f["name"] for f in folders}) == len(folders), "Ambiguous duplicate month folders.")
    reports = []
    for folder in folders:
        readonly_folder(reader, folder["id"], root)
        for meta in reader.list_children(folder["id"]):
            match = REPORT.fullmatch(meta.get("name", ""))
            if not match or meta.get("trashed"):
                continue
            try:
                day = date.fromisoformat(match[1])
            except ValueError:
                continue
            if day <= today:
                reports.append(((day, int(match[2] or 1)), folder["id"], meta))
    require(bool(reports), "No completed dated monthly US report is available.")
    rank = max(r[0] for r in reports)
    latest = [r for r in reports if r[0] == rank]
    require(len(latest) == 1, "Ambiguous duplicate latest report.")
    return latest[0][1:]


def verify(reader, root, candidate, now=None):
    now = now or datetime.now(timezone.utc)
    brief = copy.deepcopy(candidate)
    provenance = brief.pop("provenance", None)
    exact_keys(provenance, {"report", "forecast"}, "source provenance")
    validate_brief(brief, now, embedded=True)
    month, report = newest_report(reader, root, now)
    reference = provenance["report"]
    exact_keys(reference, {"id", "modified_at", "sha256"}, "report provenance")
    require(reference == provenance["forecast"], "The original US outlook must come from the same report.")
    require(reference["id"] == report["id"] and re.fullmatch(r"[0-9a-f]{64}", reference["sha256"] or ""), "The ready PR does not reference the latest monthly source.")
    before = reader.get(reference["id"])
    require(before.get("modifiedTime") == reference["modified_at"] and month in before.get("parents", []) and before.get("capabilities", {}).get("canEdit") is False, "The source changed or is not read-only in the authorized month.")
    require(before.get("mimeType") in {"text/markdown", "text/plain", "application/octet-stream"}, "Expected a text report.")
    raw = reader.get(reference["id"], media=True)
    require(hashlib.sha256(raw).hexdigest() == reference["sha256"], "The original report checksum changed; re-curate before publishing.")
    source = raw.decode("utf-8").replace("**", "").replace(",", "")
    header = re.search(r"^#\s*美股盘后日报[^\n]*美国[^\n]*?(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})\s*交易时段", source, re.M)
    require(header is not None, "Expected the original US post-close daily report, not a preview.")
    session = datetime.strptime(f"{header[1]} {header[2][:3]} {header[3]}", "%d %b %Y").date()
    require(str(session) == brief["session_date"], "The filename date is not the US session stated in the report.")
    outlook = re.search(r"^##\s*9\.[\s\S]*?(?=^##\s*10\.)", source, re.M)
    require(outlook is not None, "The original US outlook section is missing.")
    text = outlook[0]
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] in {"Bull", "Base", "Bear"}:
            require(cells[0] not in rows, "Ambiguous duplicate original outlook rows.")
            rows[cells[0]] = cells
    require(set(rows) == {"Bull", "Base", "Bear"}, "The original three-way US outlook is incomplete.")
    f = brief["forecast"]
    require(f["id"] == f"drive:{reference['id']}#us-original-outlook", "The outlook locator must identify this original report.")
    for name, row in rows.items():
        require(re.fullmatch(r"\d+(?:\.\d+)?%", row[1]) and float(row[1][:-1]) == f["probabilities"][name.lower()], "The probability differs from the original US outlook.")
    for name, operator, key in (("Bull", ">", "upper_bound"), ("Bear", "<", "lower_bound")):
        bound = re.search(re.escape(operator) + r"\s*(\d+(?:\.\d+)?)", rows[name][2])
        require(bound is not None and float(bound[1]) == f[key], "The final-close boundary differs from the original US outlook.")
    base = re.search(r"(\d+(?:\.\d+)?)\s*[–—-]\s*(\d+(?:\.\d+)?)", rows["Base"][2])
    require(base is not None and [float(base[1]), float(base[2])] == [f["lower_bound"], f["upper_bound"]], "The original base-case range is inconsistent.")
    close = re.search(r"参考收盘\s*(?:SPX|S&P\s*500)\s*(\d+(?:\.\d+)?)", text)
    require(close is not None and float(close[1]) == f["reference_close"], "The reference close differs from the original US outlook.")
    horizon = re.search(r"[A-Za-z]{3,9}\s+(\d{1,2})(?:\s+([A-Za-z]{3,9}))?\s*[–—-]\s*[A-Za-z]{3,9}\s+(\d{1,2})\s+([A-Za-z]{3,9})", text.splitlines()[0])
    require(horizon is not None, "The original US outlook horizon is missing.")
    start_month = datetime.strptime((horizon[2] or horizon[4])[:3], "%b").month
    end_month = datetime.strptime(horizon[4][:3], "%b").month
    start_year = session.year + (start_month < session.month)
    end_day = date(start_year + (end_month < start_month), end_month, int(horizon[3]))
    require(timestamp(f["evaluates_at"]).astimezone(ZoneInfo("America/New_York")).date() == end_day, "The forecast settlement differs from the original horizon.")
    us_text = source.split("## 今日澳股", 1)[0]
    sample = re.search(r"(\d+)\s*个已结算窗口", us_text)
    require(sample is not None and int(sample[1]) == f["completed_sample"], "The completed US calibration sample differs from the report.")
    require(timestamp(brief["issued_at"]) == timestamp(reference["modified_at"]), "The disclosed archive publication time must match completed Drive metadata.")
    links = [s for s in brief["sources"] if s["url"].startswith("https://drive.google.com/")]
    require(len(links) == 1 and links[0]["url"] == f"https://drive.google.com/file/d/{reference['id']}/view" and links[0].get("modified_at") == reference["modified_at"], "Only the original report may be linked as a private source.")
    after = reader.get(reference["id"])
    require(after.get("modifiedTime") == before.get("modifiedTime") and month in after.get("parents", []) and after.get("capabilities", {}).get("canEdit") is False, "The source changed during verification.")
    return {"source_verified": True, "session_date": brief["session_date"], "private_content_logged": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", nargs="?")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    try:
        reader = DriveReader(os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", ""))
        root = os.environ.get("MARKET_REPORTS_DRIVE_FOLDER_ID", "")
        if args.probe:
            month, report = newest_report(reader, root, datetime.now(timezone.utc))
            meta = reader.get(report["id"])
            require(month in meta.get("parents", []) and meta.get("capabilities", {}).get("canEdit") is False, "The report identity must be read-only.")
            reader.get(report["id"], media=True)
            result = {"archive_readable": True, "read_only": True, "private_content_logged": False}
        else:
            require(bool(args.candidate), "A curated candidate is required.")
            candidate = parse_json(Path(args.candidate).read_bytes())
            result = verify(reader, root, candidate)
        print(json.dumps(result))
        return 0
    except (ProbeError, OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print(str(exc) if isinstance(exc, ProbeError) else "Source verification failed; no private content was published.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
