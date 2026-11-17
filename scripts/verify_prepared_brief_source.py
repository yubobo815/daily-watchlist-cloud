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
AM_REPORT = re.compile(r"US_AI_Daily_(\d{4}-\d{2}-\d{2})_US-(\d{4}-\d{2}-\d{2})_v1\.md")
NUMBER = r"\d+(?:\.\d+)?"


def unique(pattern, value):
    matches = list(re.finditer(pattern, value, re.M))
    require(len(matches) == 1, "Missing or ambiguous original AM forecast field.")
    return matches[0]


def verify_am(source, brief, filename, modified_at):
    f = brief["forecast"]
    header = unique(r"^# US & AI 每日研究报告（AM）— 美股 (\d{4}-\d{2}-\d{2})（周[一二三四五]）收盘 → 墨尔本 (\d{4}-\d{2}-\d{2})（周[一二三四五六日]）$", source)
    require(header[1] == filename[2] == brief["session_date"] and header[2] == filename[1], "AM report dates do not match.")
    section = unique(r"^## 3\. 三日标普 500 预测（NEW）与澳洲条件展望\n([\s\S]*?)(?=^## |\Z)", source)[1]
    block = unique(r"^### 3\.1 预测块[^\n]*\n([\s\S]*?)(?=^### |\Z)", section)[1]
    require(unique(r"^Status: (.+)$", block)[1] == "NEW", "Forecast was not issued.")
    require(unique(r"^Source US session: (\d{4}-\d{2}-\d{2})$", block)[1] == header[1], "Forecast source session differs.")
    require(unique(r"^Forecast ID: (.+)$", block)[1] == f["id"] == f"IND-{header[2]}-3D-v1", "Forecast ID differs.")
    issue = unique(r"^Issued: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) AE[DS]T / (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) E[DS]T$", block)
    issued = datetime.fromisoformat(issue[1]).replace(tzinfo=ZoneInfo("Australia/Melbourne"))
    require(issued == datetime.fromisoformat(issue[2]).replace(tzinfo=ZoneInfo("America/New_York")) and issued.date().isoformat() == header[2] and issued == timestamp(brief["issued_at"]) and issued <= timestamp(modified_at), "Forecast issue time differs.")
    target = unique(r"^Target session: (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) America/New_York \(([^)]+)\)$", block)
    settled = timestamp(f["evaluates_at"])
    require(timestamp(target[3]) == settled and settled.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M") == f"{target[1]} {target[2]}", "Forecast settlement differs.")
    for label, key in (("Reference S&P 500", "reference_close"), ("Lower bound", "lower_bound"), ("Upper bound", "upper_bound")):
        require(float(unique(rf"^{re.escape(label)}: ({NUMBER})$", block)[1]) == f[key], "Forecast reference or boundary differs.")
    for name, interval, keys in (("Bull", rf">\s*({NUMBER})", ["upper_bound"]), ("Base", rf"({NUMBER})\s*[–—-]\s*({NUMBER})\s*\(inclusive\)", ["lower_bound", "upper_bound"]), ("Bear", rf"<\s*({NUMBER})", ["lower_bound"])):
        row_line = unique(rf"^\|[ \t]*{name}[ \t]*\|[^\n]*$", block)[0]
        row = re.fullmatch(rf"\|\s*{name}\s*\|\s*([^|]+?)\s*\|\s*({NUMBER})%\s*\|\s*", row_line)
        require(row is not None, "Invalid original forecast row.")
        bounds = re.fullmatch(interval, row[1])
        require(bounds is not None and list(map(float, bounds.groups())) == [f[k] for k in keys] and float(row[2]) == f["probabilities"][name.lower()], "Forecast range or probability differs.")
    ledger = unique(r"^## 9\. 历史预测账本[^\n]*\n([\s\S]*?)(?=^## |\Z)", source)[1]
    sample = unique(r"^### 9-C 累计序列[^\n]*\n([^\n]+)", ledger)[1]
    require(int(unique(r"(\d+) 个窗口\s*[，,]?\s*合计", sample)[1]) == f["completed_sample"], "Completed US sample differs.")


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
            am = AM_REPORT.fullmatch(meta.get("name", ""))
            match = am or REPORT.fullmatch(meta.get("name", ""))
            if not match or meta.get("trashed"):
                continue
            try:
                day = date.fromisoformat(match[1])
            except ValueError:
                continue
            if day <= today and (not am or day.strftime("%Y-%m") == folder["name"]):
                reports.append(((day, 1 if am else int(match[2] or 1)), folder["id"], meta))
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
    month, report = newest_report(reader, root, now)
    am = AM_REPORT.fullmatch(report["name"])
    validate_brief(brief, now, embedded=True, am=bool(am))
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
    if am:
        verify_am(source, brief, am, reference["modified_at"])
    else:
        verify_legacy(source, brief, reference)
    links = [s for s in brief["sources"] if s["url"].startswith("https://drive.google.com/")]
    require(len(links) == 1 and links[0]["url"] == f"https://drive.google.com/file/d/{reference['id']}/view" and links[0].get("modified_at") == reference["modified_at"], "Only the original report may be linked as a private source.")
    after = reader.get(reference["id"])
    require(after.get("modifiedTime") == before.get("modifiedTime") and after.get("name") == before.get("name") == report["name"] and month in after.get("parents", []) and after.get("capabilities", {}).get("canEdit") is False, "The source changed during verification.")
    return {"source_verified": True, "session_date": brief["session_date"], "private_content_logged": False}


def verify_legacy(source, brief, reference):
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
    require(timestamp(brief["issued_at"]) == timestamp(reference["modified_at"]), "The disclosed archive publication time must match completed Drive metadata.")


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
