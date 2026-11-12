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
US_ARCHIVE = "1vFVQbX-xmbVrOSO4OXDGb1ACwZF3-oXw"
US_REPORT = re.compile(r"^US_AI_Daily_(\d{4}-\d{2}-\d{2})_US-(\d{4}-\d{2}-\d{2})_v1\.md$")


def latest_modified(reports):
    if len(reports) == 1:
        return reports[0]
    times = [timestamp(report["modifiedTime"]) for _, report in reports]
    newest = max(times)
    require(times.count(newest) == 1, "Ambiguous latest report modification time.")
    return reports[times.index(newest)]


def structured_outlook(source, brief):
    sections = list(re.finditer(r"^## 3\. 三日 S&P 500 预测（NEW）与澳洲条件展望[ \t]*\n([\s\S]*?)(?=^## |\Z)", source, re.M))
    require(len(sections) == 1, "Expected a unique original section 3 US outlook.")
    blocks = list(re.finditer(
        r"^### 3\.1 预测块（固定解析字段）[ \t]*\n([\s\S]*?)(?=^### |\Z)", sections[0][1], re.M))
    require(len(blocks) == 1, "Expected a unique original section 3 US forecast block.")
    block = blocks[0][1]

    def field(label, pattern, body=block):
        found = re.findall(r"^" + re.escape(label) + r"\s*" + pattern + r"\s*$", body, re.M)
        require(len(found) == 1, "A structured US outlook field is missing or ambiguous.")
        return found[0]

    session = field("Source US session:", r"(\d{4}-\d{2}-\d{2})")
    close = re.findall(r"^\| 最近完成的美国常规现金时段 \|\s*(\d{4}-\d{2}-\d{2})（", source[:sections[0].start()], re.M)
    require(close == [session] and session == brief["session_date"], "The structured outlook is not from the stated completed US session.")
    require(field("Status:", r"(NEW)") == "NEW", "A revised outlook cannot be published.")
    f = brief["forecast"]
    require(field("Forecast ID:", r"(IND-\d{4}-\d{2}-\d{2}-3D-v1)") == f["id"], "The author-issued forecast ID differs.")
    day, clock, offset = field("Issued:", r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}) (?:AEDT|AEST) \(UTC([+-]\d{2}:\d{2})\) / [^\n]+")
    require(timestamp(f"{day}T{clock}{offset}") == timestamp(brief["issued_at"]), "The author-issued timestamp differs.")
    number = r"(\d+(?:\.\d+)?)"
    for label, key in (("Reference S&P 500:", "reference_close"), ("Lower bound:", "lower_bound"), ("Upper bound:", "upper_bound")):
        require(float(field(label, number)) == f[key], "A structured US reference or boundary differs.")
    day, local_time, utc = field("Target session:", r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) America/New_York \(([^)]+)\)")
    target = timestamp(utc)
    require(target == timestamp(f["evaluates_at"]) and target.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M") == f"{day} {local_time}", "The structured US settlement differs.")
    for name, pattern, expected in (
        ("Bull", r">\s*" + number, (f["upper_bound"],)),
        ("Base", number + r"\s*[–—-]\s*" + number + r"\s*\(inclusive\)", (f["lower_bound"], f["upper_bound"])),
        ("Bear", r"<\s*" + number, (f["lower_bound"],)),
    ):
        cells = field("| " + name + " |", pattern + r"\s*\|\s*" + number + r"%\s*\|")
        require(tuple(map(float, cells[:-1])) == expected and float(cells[-1]) == f["probabilities"][name.lower()], "A structured US scenario differs.")
    sample = re.findall(r"^\[计算\] IND 序列已评分\s+(\d+)\s*个窗口\b", source, re.M)
    require(len(sample) == 1 and int(sample[0]) == f["completed_sample"], "The completed IND calibration sample differs.")


def readonly_folder(reader, folder_id, parent=None):
    meta = reader.get(folder_id)
    require(meta.get("id") == folder_id and meta.get("mimeType") == FOLDER_MIME, "Expected the authorized archive folder.")
    require(meta.get("capabilities", {}).get("canEdit") is False and meta.get("capabilities", {}).get("canAddChildren") is False, "The archive identity must have read-only access.")
    require(parent is None or parent in meta.get("parents", []), "The month folder is outside the authorized archive.")
    return meta


def newest_report(reader, root, now, extra=None, session=None):
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
    if extra and session:
        readonly_folder(reader, extra)
        alternatives = []
        for meta in reader.list_children(extra):
            match = US_REPORT.fullmatch(meta.get("name", ""))
            if match and not meta.get("trashed") and match[2] == session:
                day = date.fromisoformat(match[1])
                if day <= today:
                    alternatives.append((extra, meta))
        if alternatives:
            parent, newest = latest_modified(alternatives)
            day = date.fromisoformat(US_REPORT.fullmatch(newest["name"])[1])
            reports.append(((day, 1), parent, newest))
    require(bool(reports), "No completed dated US report is available.")
    rank = max(r[0] for r in reports)
    latest = [r for r in reports if r[0] == rank]
    return latest_modified([r[1:] for r in latest])


def verify(reader, root, candidate, now=None, extra=None):
    now = now or datetime.now(timezone.utc)
    brief = copy.deepcopy(candidate)
    provenance = brief.pop("provenance", None)
    exact_keys(provenance, {"report", "forecast"}, "source provenance")
    validate_brief(brief, now, embedded=True)
    month, report = newest_report(reader, root, now, extra, brief["session_date"])
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
    if extra and month == extra:
        structured_outlook(source, brief)
        return finish_verification(reader, month, reference, before, brief, structured=True)
    header = re.search(r"^#\s*美股盘后日报[^\n]*美国[^\n]*?(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})\s*交易时段", source, re.M)
    require(header is not None, "Expected the original US post-close daily report, not a preview.")
    session = datetime.strptime(f"{header[1]} {header[2][:3]} {header[3]}", "%d %b %Y").date()
    require(str(session) == brief["session_date"], "The filename date is not the US session stated in the report.")
    # Accept only explicitly supported original-US layouts. Never search
    # historical records or the appended ASX revision for matching numbers.
    sections = list(re.finditer(r"^##\s*(?:9\.\s*展望|4\.\s*新美股展望)[^\n]*\n[\s\S]*?(?=^##\s|\Z)", source, re.M))
    require(len(sections) == 1, "A unique original US outlook section is required.")
    outlook = sections[0]
    text = outlook[0]
    paragraph = text.startswith("## 4.")
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] in {"Bull", "Base", "Bear"}:
            require(cells[0] not in rows, "Ambiguous duplicate original outlook rows.")
            rows[cells[0]] = cells
    bullets = not paragraph and not rows
    if paragraph or bullets:
        require(not rows, "Mixed original outlook layouts are ambiguous.")
        # The new layout is a single three-way bullet: Bull P% (收盘 >U)
        # / Base P% (L-U) / Bear P% (收盘 <L). Require exactly one of each.
        for name in ("Bull", "Base", "Bear"):
            prefix = r"^\s*-\s*" if bullets else r"\b"
            matches = list(re.finditer(prefix + name + r"\s+(\d+(?:\.\d+)?)%\s*[（(]([^）)]+)[）)]", text, re.M))
            require(len(matches) == 1, "The original three-way US outlook is incomplete or ambiguous.")
            outcome = matches[0]
            if name != "Base":
                require(outcome[2].strip().startswith("收盘"), "Expected an explicit final-close outcome.")
            rows[name] = [name, outcome[1] + "%", outcome[2]]
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
    close = re.search(r"参考" + (r"(?:收盘)?" if paragraph or bullets else r"收盘") + r"\s*(?:SPX|S&P\s*500)\s*(\d+(?:\.\d+)?)", text.splitlines()[0])
    require(close is not None and float(close[1]) == f["reference_close"], "The reference close differs from the original US outlook.")
    horizon = re.search(r"[A-Za-z]{3,9}\s+(\d{1,2})(?:\s+([A-Za-z]{3,9}))?\s*[–—-]\s*[A-Za-z]{3,9}\s+(\d{1,2})\s+([A-Za-z]{3,9})", text.splitlines()[0])
    require(horizon is not None, "The original US outlook horizon is missing.")
    start_month = datetime.strptime((horizon[2] or horizon[4])[:3], "%b").month
    end_month = datetime.strptime(horizon[4][:3], "%b").month
    start_year = session.year + (start_month < session.month)
    end_day = date(start_year + (end_month < start_month), end_month, int(horizon[3]))
    require(timestamp(f["evaluates_at"]).astimezone(ZoneInfo("America/New_York")).date() == end_day, "The forecast settlement differs from the original horizon.")
    # Calibration must precede the original outlook, outside appended AU text.
    us_text = source[:outlook.start()]
    sample = re.search(r"(\d+)\s*个已结算(?:原始)?窗口", us_text)
    if sample is None and bullets:
        sample = re.search(r"^累计美股 Brier 现为\s+\d+\.\d+[（(](\d+)\s*个窗口[，\s]+\d+(?:\.\d+)?/\1[）)]", us_text, re.M)
    require(sample is not None and int(sample[1]) == f["completed_sample"], "The completed US calibration sample differs from the report.")
    return finish_verification(reader, month, reference, before, brief)


def finish_verification(reader, month, reference, before, brief, structured=False):
    if not structured:
        require(timestamp(brief["issued_at"]) == timestamp(reference["modified_at"]), "The disclosed archive publication time must match completed Drive metadata.")
    links = [s for s in brief["sources"] if s["url"].startswith("https://drive.google.com/")]
    require(len(links) == 1 and links[0]["url"] == f"https://drive.google.com/file/d/{reference['id']}/view" and links[0].get("modified_at") == reference["modified_at"], "Only the original report may be linked as a private source.")
    after = reader.get(reference["id"])
    require(after.get("modifiedTime") == before.get("modifiedTime") and month in after.get("parents", []) and after.get("capabilities", {}).get("canEdit") is False, "The source changed during verification.")
    require(hashlib.sha256(reader.get(reference["id"], media=True)).hexdigest() == reference["sha256"], "The original report bytes changed during verification.")
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
            result = verify(reader, root, candidate, extra=US_ARCHIVE)
        print(json.dumps(result))
        return 0
    except (ProbeError, OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print(str(exc) if isinstance(exc, ProbeError) else "Source verification failed; no private content was published.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
