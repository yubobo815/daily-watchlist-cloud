"""Fetch an explicitly curated public summary; never summarize private text in CI."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from probe_market_brief_drive import DriveReader, FILE_ID, FOLDER_MIME, MAX_BYTES, ProbeError

REPORT_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:-(?:independent-us-market-ai-report|us-market-report|daily-report)(?:-v(\d+))?)?\.md$")
SUMMARY_NAME = re.compile(r"^market-brief-(\d{4}-\d{2}-\d{2})-v([1-9]\d*)\.json$")
BRIEF_KEYS = {"schema_version", "session_date", "issued_at", "headline", "summary", "metrics", "highlights", "forecast", "limitations", "sources"}
FORECAST_KEYS = {"id", "outlook", "horizon", "evaluates_at", "reference_close", "lower_bound", "upper_bound", "probabilities", "completed_sample", "method", "watch_next"}
METRIC_LABELS = ["S&P 500", "Nasdaq Composite", "US 10-year yield", "Brent futures"]
PRIVATE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|BEGIN [A-Z ]*PRIVATE KEY|\bBearer\s+[A-Za-z0-9._-]+|\b(?:my holdings|my portfolio|account number|account balance|api[_ -]?key)\b|账户余额|持仓数量|银行卡", re.I)


def require(ok, message):
    if not ok:
        raise ProbeError(message)


def exact_keys(obj, keys, label):
    require(isinstance(obj, dict) and set(obj) == set(keys), f"Unexpected fields in {label}; publish only the documented market-only schema.")


def parse_json(body):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON field; refusing ambiguous content.")
            result[key] = value
        return result
    try:
        return json.loads(body, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ProbeError("Non-finite JSON number.")))
    except (UnicodeError, json.JSONDecodeError):
        raise ProbeError("The curated summary is not valid UTF-8 JSON.") from None


def timestamp(value):
    require(isinstance(value, str), "A source timestamp is missing.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(parsed.tzinfo is not None, "Timestamps must include a timezone.")
        return parsed
    except ValueError:
        raise ProbeError("Invalid source timestamp.") from None


def text(value, max_length=650):
    require(isinstance(value, str) and 0 < len(value.strip()) <= max_length, "A public text field is empty or too long.")
    require(not PRIVATE.search(value), "Potential private/account/credential text found; review the curated summary before publishing.")


def number(value):
    return type(value) in (int, float) and value == value and abs(value) != float("inf")


def validate_brief(brief, now):
    exact_keys(brief, BRIEF_KEYS, "public brief")
    require(brief["schema_version"] == 1, "Unsupported public summary version.")
    try:
        session = date.fromisoformat(brief["session_date"])
    except (ValueError, TypeError):
        raise ProbeError("Invalid US session date.") from None
    require(str(session) == brief["session_date"], "Session date must be YYYY-MM-DD.")
    issued = timestamp(brief["issued_at"])
    require(datetime.combine(session, datetime.min.time(), timezone.utc) <= issued <= now, "The summary is future-dated or predates its US session.")
    for key in ("headline", "summary", "limitations"):
        text(brief[key], 180 if key == "headline" else 650)
    require(isinstance(brief["metrics"], list) and len(brief["metrics"]) == 4, "Exactly four reported market metrics are required.")
    for metric, label in zip(brief["metrics"], METRIC_LABELS):
        exact_keys(metric, {"label", "value", "detail"}, "market metric")
        require(metric["label"] == label, "Unexpected market metric or order.")
        text(metric["value"], 60)
        text(metric["detail"], 180)
    require(isinstance(brief["highlights"], list) and 1 <= len(brief["highlights"]) <= 5, "One to five concise public highlights are required.")
    for highlight in brief["highlights"]:
        exact_keys(highlight, {"title", "text"}, "market highlight")
        text(highlight["title"], 100)
        text(highlight["text"], 500)
    forecast = brief["forecast"]
    exact_keys(forecast, FORECAST_KEYS, "forecast")
    require(re.fullmatch(r"IND-" + re.escape(str(session)) + r"-[A-Za-z0-9-]+", forecast["id"] or ""), "The forecast ID must match the report session.")
    for key in ("outlook", "horizon", "method", "watch_next"):
        text(forecast[key], 800)
    require(timestamp(forecast["evaluates_at"]) > issued, "Forecast evaluation must follow original publication.")
    for key in ("reference_close", "lower_bound", "upper_bound"):
        require(number(forecast[key]) and forecast[key] > 0, "Invalid forecast reference or boundary.")
    require(forecast["lower_bound"] < forecast["upper_bound"], "Forecast boundaries are reversed.")
    exact_keys(forecast["probabilities"], {"bull", "base", "bear"}, "probabilities")
    probabilities = list(forecast["probabilities"].values())
    require(all(number(p) and 0 <= p <= 100 for p in probabilities) and abs(sum(probabilities) - 100) < .001, "Forecast probabilities must sum to 100.")
    require(type(forecast["completed_sample"]) is int and forecast["completed_sample"] >= 0, "Invalid completed calibration sample.")
    require(isinstance(brief["sources"], list) and 2 <= len(brief["sources"]) <= 12, "Missing or excessive public sources.")
    for source in brief["sources"]:
        require(isinstance(source, dict) and {"label", "url"} <= set(source) <= {"label", "url", "modified_at"}, "Unexpected source fields.")
        text(source["label"], 180)
        text(source["url"], 2000)
        url = urlparse(source["url"])
        require(url.scheme == "https" and url.hostname and not url.username and not url.password and url.port in (None, 443), "Unsafe public source URL.")
        require(not any(re.search(r"token|secret|password|signature|api.?key", k, re.I) for k in parse_qs(url.query)), "A source URL may contain credentials.")
        try:
            ipaddress.ip_address(url.hostname)
        except ValueError:
            pass
        else:
            raise ProbeError("IP-address source URLs are not permitted.")
        if "modified_at" in source:
            timestamp(source["modified_at"])


def latest_named(files, pattern, label, session=None):
    matches = []
    for metadata in files:
        match = pattern.fullmatch(metadata.get("name", ""))
        if not match or metadata.get("trashed") or (session and match[1] != session):
            continue
        try:
            date.fromisoformat(match[1])
        except ValueError:
            continue
        matches.append(((match[1], int(match[2] or 1)), metadata))
    require(bool(matches), f"Missing {label}; retain the last published snapshot and add the final dated source to Drive.")
    rank = max(rank for rank, _ in matches)
    selected = [metadata for value, metadata in matches if value == rank]
    require(len(selected) == 1, f"Ambiguous duplicate {label}; resolve duplicate names in the authorized folder.")
    return selected[0], rank[0]


def verified_source(reader, reference, metadata, folder_id):
    exact_keys(reference, {"id", "modified_at", "sha256"}, "source identity")
    require(FILE_ID.fullmatch(reference["id"] or "") and re.fullmatch(r"[0-9a-f]{64}", reference["sha256"] or ""), "Invalid source identity or checksum.")
    require(reference["id"] == metadata["id"] and folder_id in metadata.get("parents", []), "The summary does not reference the latest authorized source.")
    before = reader.get(reference["id"])
    require(before.get("modifiedTime") == reference["modified_at"] and folder_id in before.get("parents", []), "Source changed since curation; regenerate the summary without changing an old forecast.")
    require(before.get("capabilities", {}).get("canEdit") is False and before.get("mimeType") in {"text/markdown", "text/plain", "application/octet-stream"}, "Expected a read-only text source.")
    body = reader.get(reference["id"], media=True)
    require(hashlib.sha256(body).hexdigest() == reference["sha256"], "Source checksum does not match the approved summary.")
    after = reader.get(reference["id"])
    require(after.get("modifiedTime") == before.get("modifiedTime") and folder_id in after.get("parents", []) and after.get("capabilities", {}).get("canEdit") is False, "Source changed during reading; retry after the upload completes.")
    return body.decode("utf-8")


def collect(reader, folder_id, current, now=None):
    now = now or datetime.now(timezone.utc)
    folder = reader.get(folder_id)
    require(folder.get("mimeType") == FOLDER_MIME and folder.get("capabilities", {}).get("canEdit") is False and folder.get("capabilities", {}).get("canAddChildren") is False, "Expected read-only access to the authorized folder.")
    files = reader.list_children(folder_id)
    report, session = latest_named(files, REPORT_NAME, "final dated daily report")
    require(session >= current["session_date"], "Drive's latest report is older than the published snapshot; no rollback allowed.")
    summary_meta, _ = latest_named(files, SUMMARY_NAME, "curated market summary JSON", session)
    raw = reader.get(summary_meta["id"], media=True)
    require(len(raw) <= 32768, "Curated summary exceeds the public size limit.")
    envelope = parse_json(raw)
    exact_keys(envelope, {"schema_version", "status", "approved_for_publication", "source_report", "source_forecast", "brief"}, "curation envelope")
    require(envelope["schema_version"] == 1 and envelope["status"] == "FINAL" and envelope["approved_for_publication"] is True, "Only final, explicitly publication-approved market summaries may be published.")
    brief = envelope["brief"]
    validate_brief(brief, now)
    require(brief["session_date"] == session, "The summary is not for the newest daily report.")
    require(timestamp(brief["issued_at"]) >= timestamp(current["issued_at"]), "A publication timestamp cannot move backwards.")
    forecast_matches = [f for f in files if f.get("name") == brief["forecast"]["id"] + ".md"]
    require(len(forecast_matches) == 1, "Missing or duplicated separately issued matching forecast card.")
    verified_source(reader, envelope["source_report"], report, folder_id)
    card = verified_source(reader, envelope["source_forecast"], forecast_matches[0], folder_id)
    require(brief["forecast"]["id"] in card, "Forecast ID not found in its original card.")
    plain_card = card.replace("**", "").replace(",", "")
    for outcome in ("bull", "base", "bear"):
        p = brief["forecast"]["probabilities"][outcome]
        require(re.search(r"\|\s*" + outcome + r"\s*\|\s*" + re.escape(f"{p:g}") + r"%\s*\|", plain_card, re.I), "Forecast probability does not match the separately issued card.")
    reference = re.search(r"Reference S&P 500:\s*([\d.]+)", plain_card)
    require(reference and float(reference[1]) == brief["forecast"]["reference_close"], "Forecast reference does not match the original card.")
    for outcome, operator, key in (("Bull", "Greater than", "upper_bound"), ("Bear", "Less than", "lower_bound")):
        boundary = re.search(r"\|\s*" + outcome + r"\s*\|\s*[\d.]+%\s*\|\s*" + operator + r"\s+([\d.]+)\s*\|", plain_card, re.I)
        require(boundary and float(boundary[1]) == brief["forecast"][key], "Forecast outcome boundary does not match its original card.")
    final_close = re.search(r"Final official close (?:[A-Za-z]+\s+)?(\d{1,2})\s+([A-Za-z]+)(?:\s+(\d{4}))?\s+is", plain_card)
    require(final_close, "Forecast card must state its final official close date explicitly.")
    try:
        month = datetime.strptime(final_close[2], "%B").month
    except ValueError:
        month = datetime.strptime(final_close[2], "%b").month
    year = int(final_close[3]) if final_close[3] else int(session[:4]) + (month < int(session[5:7]))
    evaluation_day = timestamp(brief["forecast"]["evaluates_at"]).astimezone(ZoneInfo("America/New_York")).date()
    require(evaluation_day == date(year, month, int(final_close[1])), "Forecast horizon does not match its original final-close date.")
    require(re.search(r"\bn\s*=\s*" + str(brief["forecast"]["completed_sample"]) + r"\b", plain_card), "Completed calibration sample is not supported by the forecast card.")
    references = [envelope["source_report"], envelope["source_forecast"]]
    private_links = [s for s in brief["sources"] if urlparse(s["url"]).hostname == "drive.google.com"]
    require(len(private_links) == 2, "Only the report and matching card may be linked as private sources.")
    for reference in references:
        expected = f"https://drive.google.com/file/d/{reference['id']}/view"
        require(any(s["url"] == expected and s.get("modified_at") == reference["modified_at"] for s in private_links), "Public provenance must retain the original file ID and modification timestamp.")
    if current["forecast"]["id"] == brief["forecast"]["id"]:
        require(current["forecast"] == brief["forecast"], "An existing forecast cannot be retrospectively revised; issue a new forecast ID.")
        old_provenance = current.get("provenance", {}).get("forecast")
        require(not old_provenance or old_provenance == envelope["source_forecast"], "An immutable forecast source was modified.")
    # A versioned curation file may be re-uploaded without causing a new commit.
    candidate = {**brief, "provenance": {"report": references[0], "forecast": references[1]}}
    summary_after = reader.get(summary_meta["id"])
    require(summary_after.get("modifiedTime") == summary_meta.get("modifiedTime") and folder_id in summary_after.get("parents", []), "Curated summary changed during reading.")
    return candidate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--current", default="data/market-brief.json")
    parser.add_argument("--expect")
    args = parser.parse_args()
    try:
        current = parse_json(Path(args.current).read_bytes())
        candidate = collect(DriveReader(os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", "")), os.environ.get("MARKET_REPORTS_DRIVE_FOLDER_ID", ""), current)
        if args.expect:
            require(candidate == parse_json(Path(args.expect).read_bytes()), "Drive changed while checks ran; do not merge the stale candidate. Rerun sync.")
        Path(args.output).write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": "unchanged" if candidate == current else "candidate_ready", "session_date": candidate["session_date"], "forecast_id": candidate["forecast"]["id"], "private_content_logged": False}))
        return 0
    except (ProbeError, OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        # Error messages deliberately omit source text and access tokens.
        print("Market brief sync failed: " + (str(exc) if isinstance(exc, ProbeError) else "Invalid or unavailable input; inspect the curated summary contract."), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
