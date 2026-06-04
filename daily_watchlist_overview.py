import argparse
import base64
import http.cookiejar
import html
import json
import math
import os
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


ETF_HINTS = {
    "SPY", "QQQ", "DIA", "IWM", "SMH", "VGT", "XLK", "XLE", "XLF", "XLV",
    "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "ARKK", "SOXX", "IBB",
    "TLT", "GLD", "SLV", "USO", "DRAM",
}

RUN_TIMEZONE = ZoneInfo("Australia/Melbourne")
SCANNER_VERSION = "2026.06.04-entry-quality"
PERSONALITY_LOOKBACK_BARS = 100
EMA_SLOPE_LOOKBACK_BARS = 5
SHORT_RS_LOOKBACK_BARS = 10
LOCAL_CANDLE_LOOKBACK_BARS = 3
PIVOT_LEFT_BARS = 3
PIVOT_RIGHT_BARS = 3
BENCHMARK_LOOKBACK_BARS = 20
EVENT_RISK_DAYS = 10
MARKET_LEADER_THRESHOLD_PCT = 3.0
MARKET_LAGGARD_THRESHOLD_PCT = -3.0
BUY_QUALITY_MINIMUM = 60.0

STOCK_NAMES = {
    "AAPL": "Apple",
    "ABBV": "AbbVie",
    "ABNB": "Airbnb",
    "ABT": "Abbott Laboratories",
    "ACN": "Accenture",
    "ADBE": "Adobe",
    "ADI": "Analog Devices",
    "ADP": "Automatic Data Processing",
    "ADSK": "Autodesk",
    "AEP": "American Electric Power",
    "ALNY": "Alnylam Pharmaceuticals",
    "AMAT": "Applied Materials",
    "AMGN": "Amgen",
    "AMT": "American Tower",
    "AMD": "Advanced Micro Devices",
    "AMZN": "Amazon",
    "ANET": "Arista Networks",
    "APP": "AppLovin",
    "ARM": "Arm Holdings",
    "ASML": "ASML",
    "ASTS": "AST SpaceMobile",
    "AXON": "Axon Enterprise",
    "AXP": "American Express",
    "AVGO": "Broadcom",
    "BA": "Boeing",
    "BAC": "Bank of America",
    "BKR": "Baker Hughes",
    "BKNG": "Booking Holdings",
    "BLK": "BlackRock",
    "BMY": "Bristol Myers Squibb",
    "BNY": "BNY Mellon",
    "BRK.B": "Berkshire Hathaway",
    "C": "Citigroup",
    "CAT": "Caterpillar",
    "CCEP": "Coca-Cola Europacific Partners",
    "CDNS": "Cadence Design Systems",
    "CEG": "Constellation Energy",
    "CHTR": "Charter Communications",
    "CL": "Colgate-Palmolive",
    "CMCSA": "Comcast",
    "COHR": "Coherent",
    "COF": "Capital One",
    "COP": "ConocoPhillips",
    "COST": "Costco",
    "CPRT": "Copart",
    "CRM": "Salesforce",
    "CRWD": "CrowdStrike",
    "CSCO": "Cisco Systems",
    "CSX": "CSX",
    "CTAS": "Cintas",
    "CTSH": "Cognizant",
    "CVS": "CVS Health",
    "CVX": "Chevron",
    "CRWV": "CoreWeave",
    "DASH": "DoorDash",
    "DDOG": "Datadog",
    "DE": "Deere",
    "DELL": "Dell Technologies",
    "DHR": "Danaher",
    "DIS": "Disney",
    "DRAM": "Global X DRAM ETF",
    "DUK": "Duke Energy",
    "DXCM": "Dexcom",
    "EA": "Electronic Arts",
    "EMR": "Emerson Electric",
    "EOS.AX": "Electro Optic Systems",
    "EXC": "Exelon",
    "FANG": "Diamondback Energy",
    "FAST": "Fastenal",
    "FDX": "FedEx",
    "FER": "Ferrovial",
    "FTNT": "Fortinet",
    "GD": "General Dynamics",
    "GE": "GE Aerospace",
    "GEHC": "GE HealthCare",
    "GEV": "GE Vernova",
    "GILD": "Gilead Sciences",
    "GLW": "Corning",
    "GM": "General Motors",
    "GOOG": "Alphabet",
    "GOOGL": "Alphabet",
    "GS": "Goldman Sachs",
    "HD": "Home Depot",
    "HON": "Honeywell",
    "IBM": "IBM",
    "IDXX": "IDEXX Laboratories",
    "INSM": "Insmed",
    "INTC": "Intel",
    "INTU": "Intuit",
    "ISRG": "Intuitive Surgical",
    "JNJ": "Johnson & Johnson",
    "JPM": "JPMorgan Chase",
    "KDP": "Keurig Dr Pepper",
    "KHC": "Kraft Heinz",
    "KLAC": "KLA",
    "KO": "Coca-Cola",
    "LIN": "Linde",
    "LITE": "Lumentum",
    "LLY": "Eli Lilly",
    "LMT": "Lockheed Martin",
    "LOW": "Lowe's",
    "LRCX": "Lam Research",
    "MA": "Mastercard",
    "MAR": "Marriott International",
    "MCD": "McDonald's",
    "MCHP": "Microchip Technology",
    "MDLZ": "Mondelez International",
    "MDT": "Medtronic",
    "MELI": "MercadoLibre",
    "META": "Meta Platforms",
    "MMM": "3M",
    "MNST": "Monster Beverage",
    "MO": "Altria",
    "MPWR": "Monolithic Power Systems",
    "MRK": "Merck",
    "MRVL": "Marvell Technology",
    "MS": "Morgan Stanley",
    "MSFT": "Microsoft",
    "MSTR": "MicroStrategy",
    "MU": "Micron",
    "NASA": "Nasa",
    "NEE": "NextEra Energy",
    "NFLX": "Netflix",
    "NKE": "Nike",
    "NOW": "ServiceNow",
    "NXPI": "NXP Semiconductors",
    "NVDA": "Nvidia",
    "ODFL": "Old Dominion Freight Line",
    "OKTA": "Okta",
    "ORCL": "Oracle",
    "ORLY": "O'Reilly Automotive",
    "PANW": "Palo Alto Networks",
    "PAYX": "Paychex",
    "PCAR": "PACCAR",
    "PDD": "PDD Holdings",
    "PEP": "PepsiCo",
    "PFE": "Pfizer",
    "PG": "Procter & Gamble",
    "PLTR": "Palantir",
    "PM": "Philip Morris International",
    "PYPL": "PayPal",
    "QCOM": "Qualcomm",
    "REGN": "Regeneron Pharmaceuticals",
    "ROP": "Roper Technologies",
    "ROK": "Rockwell Automation",
    "RKLB": "Rocket Lab",
    "ROST": "Ross Stores",
    "RTX": "RTX",
    "SBUX": "Starbucks",
    "SCHW": "Charles Schwab",
    "SHOP": "Shopify",
    "SMCI": "Super Micro Computer",
    "SMH": "VanEck Semiconductor ETF",
    "SNAP": "Snap",
    "SNOW": "Snowflake",
    "SNDK": "SanDisk",
    "SNPS": "Synopsys",
    "SO": "Southern Company",
    "SOHR": "Soho House",
    "SPG": "Simon Property Group",
    "SRM": "SRM Entertainment",
    "STX": "Seagate",
    "T": "AT&T",
    "TEAM": "Atlassian",
    "TMO": "Thermo Fisher Scientific",
    "TMUS": "T-Mobile US",
    "TRI": "Thomson Reuters",
    "TTWO": "Take-Two Interactive",
    "TSLA": "Tesla",
    "TSM": "Taiwan Semiconductor",
    "TXN": "Texas Instruments",
    "UBER": "Uber",
    "UNP": "Union Pacific",
    "UNH": "UnitedHealth",
    "UPS": "UPS",
    "USB": "U.S. Bancorp",
    "V": "Visa",
    "VGT": "Vanguard Information Technology ETF",
    "VRSK": "Verisk Analytics",
    "VRTX": "Vertex Pharmaceuticals",
    "VZ": "Verizon",
    "VOLT": "Volt Information Sciences",
    "VRT": "Vertiv",
    "WBD": "Warner Bros. Discovery",
    "WDAY": "Workday",
    "WDC": "Western Digital",
    "WFC": "Wells Fargo",
    "WMT": "Walmart",
    "XEL": "Xcel Energy",
    "XOM": "Exxon Mobil",
    "ZM": "Zoom",
    "ZS": "Zscaler",
}


def normalize_ticker(ticker: str) -> str:
    ticker = ticker.strip().upper()
    aliases = {"SPX": "^GSPC", "BRK.B": "BRK-B"}
    return aliases.get(ticker, ticker)


def display_ticker(ticker: str) -> str:
    return ticker.replace("^GSPC", "SPX").replace("BRK-B", "BRK.B")


def stock_name(ticker: str) -> str:
    return STOCK_NAMES.get(display_ticker(ticker), display_ticker(ticker))


def read_watchlist(path: Path) -> list[str]:
    tickers: list[str] = []
    seen: set[str] = set()
    for raw in path.read_text().replace(",", "\n").splitlines():
        ticker = normalize_ticker(raw)
        if ticker and ticker not in seen:
            tickers.append(ticker)
            seen.add(ticker)
    return tickers


def local_run_date() -> str:
    return datetime.now(RUN_TIMEZONE).strftime("%Y-%m-%d")


def fetch_chart(ticker: str, years: int = 3, refresh: bool = False) -> pd.DataFrame:
    cache_path = Path(f"watchlist_{ticker.replace('^', '_')}_{years}y.csv")
    if cache_path.exists() and not refresh:
        return pd.read_csv(cache_path, parse_dates=["date"])

    period2 = int(time.time())
    period1 = period2 - int(years * 365.25 * 24 * 60 * 60)
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?period1={period1}&period2={period2}&interval=1d&events=history"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    result = payload["chart"]["result"][0]
    q = result["indicators"]["quote"][0]
    adj = result["indicators"].get("adjclose", [{}])[0].get("adjclose", q["close"])
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(result["timestamp"], unit="s", utc=True).tz_convert(None).date,
            "open": q["open"],
            "high": q["high"],
            "low": q["low"],
            "close": q["close"],
            "adjclose": adj,
            "volume": q["volume"],
        }
    )
    df = df.dropna(subset=["open", "high", "low", "close", "volume"]).reset_index(drop=True)
    df.to_csv(cache_path, index=False)
    return df


def cached_chart(ticker: str, years: int = 3) -> pd.DataFrame:
    cache_path = Path(f"watchlist_{ticker.replace('^', '_')}_{years}y.csv")
    if not cache_path.exists():
        raise FileNotFoundError(f"cache not found: {cache_path}")
    return pd.read_csv(cache_path, parse_dates=["date"])


def check_live_data_access() -> tuple[bool, str]:
    req = urllib.request.Request(
        "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=5d&interval=1d",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return False, f"Yahoo preflight returned HTTP {resp.status}"
        return True, "Live Yahoo access available."
    except Exception as exc:
        return False, f"Live Yahoo access unavailable: {exc}"


def yahoo_value(value, key: str = "fmt"):
    if isinstance(value, dict):
        return value.get(key) or value.get("raw")
    return value


def compact_yahoo_text(value) -> str:
    value = yahoo_value(value)
    return "" if value is None else str(value)


def yahoo_raw_value(value):
    return yahoo_value(value, "raw")


def yahoo_headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://finance.yahoo.com/",
    }


def yahoo_quote_summary(ticker: str, modules: str) -> dict:
    base = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{urllib.parse.quote(ticker)}"
    query = f"modules={urllib.parse.quote(modules)}"
    req = urllib.request.Request(f"{base}?{query}", headers=yahoo_headers())
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        cookie_jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        crumb_req = urllib.request.Request(
            "https://query2.finance.yahoo.com/v1/test/getcrumb",
            headers=yahoo_headers(),
        )
        with opener.open(crumb_req, timeout=8) as resp:
            crumb = resp.read().decode("utf-8").strip()
        crumb_query = (
            f"{query}&formatted=true&lang=en-US&region=US"
            f"&corsDomain=finance.yahoo.com&crumb={urllib.parse.quote(crumb)}"
        )
        quote_req = urllib.request.Request(f"{base}?{crumb_query}", headers=yahoo_headers())
        with opener.open(quote_req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))


def fetch_company_profile(ticker: str, refresh: bool = False) -> dict:
    display = display_ticker(ticker)
    cache_path = Path(f"watchlist_profile_{display.replace('.', '_').replace('^', '_')}.json")
    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text())

    modules = ",".join(
        [
            "assetProfile",
            "calendarEvents",
            "financialData",
            "incomeStatementHistoryQuarterly",
        ]
    )
    try:
        payload = yahoo_quote_summary(ticker, modules)
        result = (payload.get("quoteSummary", {}).get("result") or [{}])[0]
    except Exception:
        if cache_path.exists():
            return json.loads(cache_path.read_text())
        return {}

    asset = result.get("assetProfile") or {}
    calendar = result.get("calendarEvents") or {}
    financial = result.get("financialData") or {}
    quarterly = (
        result.get("incomeStatementHistoryQuarterly", {})
        .get("incomeStatementHistory", [])
    )
    latest_quarter = quarterly[0] if quarterly else {}
    earnings_dates = (
        calendar.get("earnings", {})
        .get("earningsDate", [])
    )
    next_report = compact_yahoo_text(earnings_dates[0]) if earnings_dates else ""
    next_report_ts = yahoo_raw_value(earnings_dates[0]) if earnings_dates else None

    revenue = compact_yahoo_text(latest_quarter.get("totalRevenue"))
    net_income = compact_yahoo_text(latest_quarter.get("netIncome"))
    revenue_growth = compact_yahoo_text(financial.get("revenueGrowth"))
    earnings_growth = compact_yahoo_text(financial.get("earningsGrowth"))
    highlights = []
    if revenue:
        highlights.append(f"latest quarterly revenue {revenue}")
    if net_income:
        highlights.append(f"net income {net_income}")
    if revenue_growth:
        highlights.append(f"revenue growth {revenue_growth}")
    if earnings_growth:
        highlights.append(f"earnings growth {earnings_growth}")

    profile = {
        "ticker": display,
        "business_summary": asset.get("longBusinessSummary", ""),
        "website": asset.get("website", ""),
        "sector": asset.get("sector", ""),
        "industry": asset.get("industry", ""),
        "latest_report_highlights": "; ".join(highlights),
        "next_report_date": next_report,
        "next_report_timestamp": next_report_ts,
        "profile_source": "Yahoo Finance",
    }
    cache_path.write_text(json.dumps(profile, indent=2, sort_keys=True))
    return profile


def clean_json_value(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, dict):
        return {key: clean_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json_value(item) for item in value]
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def clean_record(record: dict) -> dict:
    return {key: clean_json_value(value) for key, value in record.items()}


def numeric_or_none(value):
    value = clean_json_value(value)
    if value == "":
        return None
    return value


def supabase_credentials() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    return url, key


def is_supabase_jwt_key(key: str) -> bool:
    return len(key.split(".")) == 3 and not key.startswith("sb_")


def describe_supabase_key(key: str) -> str:
    if key.startswith("sb_secret_"):
        return "secret key prefix=sb_secret"
    if key.startswith("sb_publishable_"):
        return "publishable key prefix=sb_publishable"

    parts = key.split(".")
    if len(parts) != 3:
        prefix = key.split("_", 1)[0] if "_" in key else "unknown"
        return f"non-jwt key prefix={prefix}"

    try:
        payload_part = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_part).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return "jwt key payload unreadable"

    role = payload.get("role", "unknown")
    ref = payload.get("ref") or payload.get("iss", "unknown")
    return f"jwt role={role} ref={ref}"


def supabase_headers(key: str) -> dict[str, str]:
    headers = {
        "apikey": key,
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    if is_supabase_jwt_key(key):
        headers["Authorization"] = f"Bearer {key}"
    return headers


def supabase_upsert(table: str, records: list[dict], conflict_columns: list[str]) -> None:
    if not records:
        return

    url, key = supabase_credentials()
    if not url or not key:
        return

    endpoint = f"{url}/rest/v1/{table}?on_conflict={urllib.parse.quote(','.join(conflict_columns))}"
    payload = json.dumps(records).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers=supabase_headers(key),
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            if resp.status not in {200, 201, 204}:
                raise RuntimeError(f"Supabase upsert to {table} returned HTTP {resp.status}")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"Supabase upsert to {table} failed with HTTP {exc.code}: {body}") from exc


OPTIONAL_SIGNAL_COLUMNS = {
    "signal_stage",
    "transition_label",
    "transition_score",
    "signal_age_days",
    "price_progress_since_signal_pct",
    "freshness_penalty",
    "adjusted_score",
    "distance_from_ref_zone_pct",
    "extension_state",
    "reason_codes",
}

SUPABASE_RETENTION_DAYS = int(os.getenv("SUPABASE_RETENTION_DAYS", "180"))


def supabase_upsert_with_optional_signal_columns(table: str, records: list[dict], conflict_columns: list[str]) -> None:
    try:
        supabase_upsert(table, records, conflict_columns)
        return
    except RuntimeError as exc:
        message = str(exc).lower()
        schema_cache_error = "could not find" in message or "schema cache" in message or "column" in message
        has_optional_columns = any(OPTIONAL_SIGNAL_COLUMNS.intersection(record) for record in records)
        if not schema_cache_error or not has_optional_columns:
            raise

        stripped_records = [
            {key: value for key, value in record.items() if key not in OPTIONAL_SIGNAL_COLUMNS}
            for record in records
        ]
        print(f"Supabase {table} optional signal columns unavailable; storing transition fields in payload only.")
        supabase_upsert(table, stripped_records, conflict_columns)


def supabase_delete_older_than(table: str, date_column: str, cutoff_date: str) -> None:
    url, key = supabase_credentials()
    if not url or not key:
        return

    endpoint = f"{url}/rest/v1/{table}?{urllib.parse.quote(date_column)}=lt.{urllib.parse.quote(cutoff_date)}"
    req = urllib.request.Request(
        endpoint,
        method="DELETE",
        headers=supabase_headers(key),
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            if resp.status not in {200, 202, 204}:
                raise RuntimeError(f"Supabase retention cleanup for {table} returned HTTP {resp.status}")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"Supabase retention cleanup for {table} failed with HTTP {exc.code}: {body}") from exc


def cleanup_supabase_retention(run_date: str) -> None:
    if SUPABASE_RETENTION_DAYS <= 0:
        return

    cutoff = (datetime.fromisoformat(run_date).date() - timedelta(days=SUPABASE_RETENTION_DAYS)).isoformat()
    cleanup_targets = [
        ("watchlist_snapshots", "run_date"),
        ("watchlist_behavior_history", "run_date"),
        ("watchlist_refresh_runs", "run_date"),
    ]
    for table, date_column in cleanup_targets:
        supabase_delete_older_than(table, date_column, cutoff)
    print(f"Supabase retention cleanup complete: kept rows from {cutoff} onward ({SUPABASE_RETENTION_DAYS} days).")


def sync_supabase(report: pd.DataFrame, history: pd.DataFrame, run_date: str, run_metadata: Optional[dict] = None) -> None:
    url, key = supabase_credentials()
    if not url or not key:
        print("Supabase sync skipped: SUPABASE_URL and SUPABASE_SECRET_KEY are not set.")
        print("Legacy fallback: SUPABASE_SERVICE_ROLE_KEY is also supported.")
        return

    print(f"Supabase sync target: {urllib.parse.urlparse(url).netloc} ({describe_supabase_key(key)})")

    report_records = []
    for record in report.to_dict(orient="records"):
        row = clean_record(record)
        report_records.append(
            {
                "run_date": run_date,
                "ticker": row.get("ticker"),
                "name": row.get("name"),
                "data_date": row.get("date"),
                "action": row.get("action"),
                "setup": row.get("setup"),
                "adaptive_mode": row.get("adaptive_mode"),
                "psychology": row.get("psychology"),
                "score": numeric_or_none(row.get("score")),
                "close": numeric_or_none(row.get("close")),
                "day_change_pct": numeric_or_none(row.get("day_change_pct")),
                "entry_est": numeric_or_none(row.get("entry_est")),
                "stop_est": numeric_or_none(row.get("stop_est")),
                "target_est": numeric_or_none(row.get("target_est")),
                "notes": row.get("notes"),
                "signal_stage": row.get("signal_stage"),
                "transition_label": row.get("transition_label"),
                "transition_score": numeric_or_none(row.get("transition_score")),
                "signal_age_days": numeric_or_none(row.get("signal_age_days")),
                "price_progress_since_signal_pct": numeric_or_none(row.get("price_progress_since_signal_pct")),
                "freshness_penalty": numeric_or_none(row.get("freshness_penalty")),
                "adjusted_score": numeric_or_none(row.get("adjusted_score")),
                "distance_from_ref_zone_pct": numeric_or_none(row.get("distance_from_ref_zone_pct")),
                "extension_state": row.get("extension_state"),
                "reason_codes": row.get("reason_codes") or [],
                "payload": row,
            }
        )

    history_records = []
    if not history.empty:
        for record in history.to_dict(orient="records"):
            row = clean_record(record)
            history_records.append(
                {
                    "run_date": run_date,
                    "ticker": row.get("ticker"),
                    "history_date": row.get("date"),
                    "action": row.get("action"),
                    "setup": row.get("setup"),
                    "adaptive_mode": row.get("adaptive_mode"),
                    "psychology": row.get("psychology"),
                    "score": numeric_or_none(row.get("score")),
                    "close": numeric_or_none(row.get("close")),
                    "day_change_pct": numeric_or_none(row.get("day_change_pct")),
                    "entry_est": numeric_or_none(row.get("entry_est")),
                    "stop_est": numeric_or_none(row.get("stop_est")),
                    "target_est": numeric_or_none(row.get("target_est")),
                    "notes": row.get("notes"),
                    "signal_stage": row.get("signal_stage"),
                    "transition_label": row.get("transition_label"),
                    "transition_score": numeric_or_none(row.get("transition_score")),
                    "signal_age_days": numeric_or_none(row.get("signal_age_days")),
                    "price_progress_since_signal_pct": numeric_or_none(row.get("price_progress_since_signal_pct")),
                    "freshness_penalty": numeric_or_none(row.get("freshness_penalty")),
                    "adjusted_score": numeric_or_none(row.get("adjusted_score")),
                    "distance_from_ref_zone_pct": numeric_or_none(row.get("distance_from_ref_zone_pct")),
                    "extension_state": row.get("extension_state"),
                    "reason_codes": row.get("reason_codes") or [],
                    "payload": row,
                }
            )

    if run_metadata:
        try:
            supabase_upsert("watchlist_refresh_runs", [clean_record(run_metadata)], ["run_date"])
        except RuntimeError as exc:
            print(f"Supabase run-health sync skipped: {exc}")

    supabase_upsert_with_optional_signal_columns("watchlist_snapshots", report_records, ["run_date", "ticker"])
    supabase_upsert_with_optional_signal_columns("watchlist_behavior_history", history_records, ["run_date", "ticker", "history_date"])
    print(f"Synced {len(report_records)} snapshot rows and {len(history_records)} history rows to Supabase.")
    try:
        cleanup_supabase_retention(run_date)
    except RuntimeError as exc:
        print(f"Supabase retention cleanup skipped: {exc}")


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False, min_periods=length).mean()


def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()


def macd_hist(close: pd.Series) -> pd.Series:
    macd = ema(close, 12) - ema(close, 26)
    signal = ema(macd, 9)
    return macd - signal


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values("date").reset_index(drop=True)
    out["rsi"] = rsi(out["close"])
    out["bb_basis"] = out["close"].rolling(20, min_periods=20).mean()
    out["bb_std"] = out["close"].rolling(20, min_periods=20).std(ddof=0)
    out["upper_bb"] = out["bb_basis"] + 2.0 * out["bb_std"]
    out["lower_bb"] = out["bb_basis"] - 2.0 * out["bb_std"]
    out["ema_fast"] = ema(out["close"], 20)
    out["ema_slow"] = ema(out["close"], 50)
    out["ema_long"] = ema(out["close"], 200)
    out["vol_ma"] = out["volume"].rolling(20, min_periods=20).mean()
    out["atr"] = atr(out)
    out["atr_pct"] = out["atr"] / out["close"] * 100
    out["macd_hist"] = macd_hist(out["close"])
    out["range"] = out["high"] - out["low"]
    out["close_loc"] = np.where(out["range"] > 0, (out["close"] - out["low"]) / out["range"], 0.5)
    out["body"] = (out["close"] - out["open"]).abs()
    out["body_pct"] = np.where(out["range"] > 0, out["body"] / out["range"], 0)
    out["upper_wick_pct"] = np.where(out["range"] > 0, (out["high"] - out[["open", "close"]].max(axis=1)) / out["range"], 0)
    out["lower_wick_pct"] = np.where(out["range"] > 0, (out[["open", "close"]].min(axis=1) - out["low"]) / out["range"], 0)
    return out


def bool_text(value: bool) -> str:
    return "YES" if value else "NO"


SIGNAL_STAGE_ORDER = {
    "WAIT": 0,
    "WAIT / AVOID": 0,
    "WATCH TREND": 1,
    "SETUP FORMING": 2,
    "BUY CANDIDATE": 3,
    "STRONG CONTINUATION": 4,
    "EXIT PRESSURE": 5,
}

SIGNAL_STAGE_LABELS = {
    "WAIT": "WAIT",
    "WAIT / AVOID": "WAIT",
    "WATCH TREND": "WATCH",
    "SETUP FORMING": "SETUP",
    "BUY CANDIDATE": "BUY",
    "STRONG CONTINUATION": "TRENDING",
    "EXIT PRESSURE": "EXIT",
}


def signal_stage(action: str) -> str:
    return SIGNAL_STAGE_LABELS.get(action, "WAIT")


def signal_stage_rank(action: str) -> int:
    return SIGNAL_STAGE_ORDER.get(action, 0)


def clamp_entry_to_current_zone(entry: float, close: float, atr_now: float, max_pullback_pct: float) -> tuple[float, str]:
    if math.isnan(entry) or entry <= 0 or close <= 0:
        return entry, ""

    max_pullback = close * (1 - max_pullback_pct / 100)
    if atr_now > 0:
        max_pullback = max(max_pullback, close - atr_now * 1.5)

    if entry < max_pullback:
        return max_pullback, f"Reference zone capped near current price; original retest {entry:.2f} was stale"
    return entry, ""


def latest_pivot(values: pd.Series, left: int = 3, right: int = 3, kind: str = "high") -> float:
    if len(values) < left + right + 1:
        return np.nan
    confirmed = []
    for idx in range(left, len(values) - right):
        window = values.iloc[idx - left : idx + right + 1]
        value = values.iloc[idx]
        if kind == "high" and value == window.max():
            confirmed.append(float(value))
        elif kind == "low" and value == window.min():
            confirmed.append(float(value))
    return confirmed[-1] if confirmed else np.nan


def clamp_float(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def stock_personality_profile(d: pd.DataFrame, i: int, is_etf: bool, trend_efficiency: float) -> dict:
    lookback = d.iloc[max(0, i - PERSONALITY_LOOKBACK_BARS + 1) : i + 1]
    median_atr_pct = float(lookback["atr_pct"].dropna().median()) if not lookback["atr_pct"].dropna().empty else 5.0
    median_abs_move_pct = (
        float(lookback["close"].pct_change().abs().dropna().median() * 100)
        if len(lookback) > 2
        else 1.5
    )
    volatility_ratio = clamp_float(median_atr_pct / 5.0, 0.55, 1.9)

    if is_etf:
        personality = "ETF"
    elif median_atr_pct >= 7.0 or median_abs_move_pct >= 2.6:
        personality = "HIGH_BETA"
    elif trend_efficiency >= 0.28 and median_atr_pct <= 4.5:
        personality = "COMPOUNDER"
    elif trend_efficiency < 0.14 and median_atr_pct <= 5.5:
        personality = "RANGE_BOUND"
    else:
        personality = "BALANCED"

    profile = {
        "personality_type": personality,
        "personality_atr_pct": round(median_atr_pct, 2),
        "personality_abs_move_pct": round(median_abs_move_pct, 2),
        "min_buy_quality": BUY_QUALITY_MINIMUM,
        "min_close_loc": 0.56,
        "min_buyer_score": 56.0,
        "max_zone_distance_pct": clamp_float(6.0 * volatility_ratio, 3.5, 9.0),
        "max_zone_distance_atr": clamp_float(2.0 * volatility_ratio, 1.35, 2.8),
        "min_reward_risk": 1.05,
    }

    if personality == "ETF":
        profile.update(
            {
                "min_close_loc": 0.58,
                "min_buyer_score": 54.0,
                "max_zone_distance_pct": clamp_float(4.5 * volatility_ratio, 3.0, 6.0),
                "max_zone_distance_atr": clamp_float(1.7 * volatility_ratio, 1.2, 2.2),
                "min_reward_risk": 1.0,
            }
        )
    elif personality == "COMPOUNDER":
        profile.update(
            {
                "min_close_loc": 0.62,
                "min_buyer_score": 62.0,
                "max_zone_distance_pct": clamp_float(4.6 * volatility_ratio, 3.5, 6.2),
                "max_zone_distance_atr": clamp_float(1.65 * volatility_ratio, 1.25, 2.1),
                "min_reward_risk": 1.15,
            }
        )
    elif personality == "HIGH_BETA":
        profile.update(
            {
                "min_close_loc": 0.55,
                "min_buyer_score": 58.0,
                "max_zone_distance_pct": clamp_float(7.5 * volatility_ratio, 6.0, 10.5),
                "max_zone_distance_atr": clamp_float(2.25 * volatility_ratio, 1.8, 3.0),
                "min_reward_risk": 1.2,
            }
        )
    elif personality == "RANGE_BOUND":
        profile.update(
            {
                "min_close_loc": 0.60,
                "min_buyer_score": 60.0,
                "max_zone_distance_pct": clamp_float(4.8 * volatility_ratio, 3.2, 6.0),
                "max_zone_distance_atr": clamp_float(1.55 * volatility_ratio, 1.2, 2.0),
                "min_reward_risk": 1.1,
            }
        )

    return profile


def detect_setup_at(d: pd.DataFrame, i: int) -> str:
    if i < 210:
        return "NONE"

    row = d.iloc[i]
    prev = d.iloc[i - 1]
    if pd.isna(row.atr) or pd.isna(row.ema_long) or pd.isna(prev.macd_hist):
        return "NONE"

    lookback_bars = 3
    ema_slope_bars = 5
    close = float(row.close)
    open_ = float(row.open)
    high = float(row.high)
    low = float(row.low)
    atr_now = float(row.atr)

    price_follow = close > prev.high
    constructive_close = row.close_loc >= 0.55 and close >= (open_ + prev.close) / 2
    demand_tail = row.lower_wick_pct >= 0.30 and row.close_loc >= 0.55
    wide_bullish = close > open_ and row.body_pct >= 0.45 and row.close_loc >= 0.65

    recent_oversold_bb = (
        (d["low"].iloc[i - lookback_bars : i + 1] <= d["lower_bb"].iloc[i - lookback_bars : i + 1])
        & (d["rsi"].iloc[i - lookback_bars : i + 1] < 45)
    ).any()
    back_inside_bb = close > row.lower_bb
    right_side = recent_oversold_bb and back_inside_bb and row.rsi > prev.rsi and (price_follow or constructive_close or demand_tail)

    uptrend = close > row.ema_slow and row.ema_fast > row.ema_slow and row.ema_slow >= d.iloc[i - ema_slope_bars].ema_slow
    strong_momentum = close > row.ema_fast and row.ema_fast > row.ema_slow and row.ema_fast >= d.iloc[i - ema_slope_bars].ema_fast and row.ema_slow >= d.iloc[i - ema_slope_bars].ema_slow
    pullback_support = low <= row.ema_fast or low <= row.bb_basis or close <= row.ema_fast * 1.02
    shallow_pullback = low <= row.ema_fast * 1.015 or low <= row.bb_basis or close <= row.ema_fast * 1.025
    support_held = close > row.ema_slow and close > row.lower_bb
    pullback_reversal = 40 <= row.rsi <= 60 and row.rsi > prev.rsi and (price_follow or constructive_close)
    pullback = uptrend and (pullback_support or (strong_momentum and shallow_pullback)) and support_held and pullback_reversal

    early_pullback = (
        uptrend
        and (low <= row.ema_fast * 1.03 or low <= row.bb_basis * 1.02 or close <= row.ema_fast * 1.04)
        and support_held
        and 38 <= row.rsi <= 68
        and row.rsi >= prev.rsi - 2
        and (demand_tail or constructive_close)
    )

    recent_momentum_high = d["high"].iloc[i - 10 : i].max()
    momentum_dip = d["low"].iloc[i - 2 : i + 1].min() <= recent_momentum_high * 0.97
    momentum = strong_momentum and momentum_dip and close > open_ and close > prev.close and close > row.ema_fast and 55 <= row.rsi <= 85 and close <= row.ema_fast * 1.35

    breakout_level = d["close"].iloc[i - 20 : i].max()
    breakout_ext = (close - row.ema_fast) / atr_now if atr_now > 0 else 0
    breakout = strong_momentum and close >= breakout_level and close > prev.high and wide_bullish and 55 <= row.rsi <= 82 and breakout_ext <= 3.5 and row.macd_hist >= prev.macd_hist

    body_for_ratio = max(float(row.body), 0.01)
    lower_wick = min(open_, close) - low
    vol_ready = not math.isnan(row.vol_ma) and row.vol_ma > 0
    breakdown_vol = vol_ready and row.volume > row.vol_ma * 1.2 and close < open_ and close < row.ema_fast and close < prev.low and row.close_loc <= 0.45
    fear_rejected = lower_wick > body_for_ratio * 1.5 and row.close_loc >= 0.60 and (low <= row.lower_bb or low <= row.ema_fast or low < prev.low) and not breakdown_vol
    reversal = right_side or (fear_rejected and recent_oversold_bb and back_inside_bb)

    if breakout:
        return "BREAKOUT BUY"
    if momentum:
        return "MOMENTUM BUY"
    if pullback:
        return "PULLBACK BUY"
    if early_pullback:
        return "EARLY PULLBACK BUY"
    if reversal:
        return "REVERSAL BUY"
    return "NONE"


def historical_setup_stats(d: pd.DataFrame, setup: str, holding_days: int = 10, lookback_days: int = 500) -> dict:
    if setup == "NONE":
        return {"hist_trades": "", "hist_win_rate": "", "hist_avg_return": ""}

    returns: list[float] = []
    end = len(d) - holding_days - 1
    start = max(210, end - lookback_days)
    for i in range(start, end):
        if detect_setup_at(d, i) != setup:
            continue
        entry = float(d.iloc[i].close)
        exit_ = float(d.iloc[i + holding_days].close)
        if entry > 0:
            returns.append((exit_ / entry - 1) * 100)

    if not returns:
        return {"hist_trades": 0, "hist_win_rate": "", "hist_avg_return": ""}

    wins = sum(1 for value in returns if value > 0)
    return {
        "hist_trades": len(returns),
        "hist_win_rate": round(wins / len(returns) * 100, 1),
        "hist_avg_return": round(float(np.mean(returns)), 2),
    }


def classify_and_score(ticker: str, raw: pd.DataFrame, prepared: bool = False, include_setup_stats: bool = True) -> dict:
    d = raw.copy() if prepared else prepare(raw)
    if len(d) < 220:
        raise ValueError("not enough history")

    i = len(d) - 1
    row = d.iloc[i]
    prev = d.iloc[i - 1]
    lookback_bars = LOCAL_CANDLE_LOOKBACK_BARS
    ema_slope_bars = EMA_SLOPE_LOOKBACK_BARS
    personality_lookback = PERSONALITY_LOOKBACK_BARS
    pivot_left_bars = PIVOT_LEFT_BARS
    pivot_right_bars = PIVOT_RIGHT_BARS
    is_etf = ticker in ETF_HINTS

    close = float(row.close)
    open_ = float(row.open)
    high = float(row.high)
    low = float(row.low)
    atr_now = float(row.atr)
    vol_ready = not math.isnan(row.vol_ma) and row.vol_ma > 0
    body_for_ratio = max(float(row.body), 0.01)
    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low
    range_atr = float(row.range / atr_now) if atr_now > 0 else 0.0
    last_pivot_high = latest_pivot(d["high"].iloc[: i + 1], pivot_left_bars, pivot_right_bars, "high")
    last_pivot_low = latest_pivot(d["low"].iloc[: i + 1], pivot_left_bars, pivot_right_bars, "low")

    travel = d["close"].diff().abs().iloc[i - personality_lookback + 1 : i + 1].sum()
    trend_efficiency = abs(close - float(d.iloc[i - personality_lookback].close)) / travel if travel > 0 else 0.0
    personality_profile = stock_personality_profile(d, i, is_etf, float(trend_efficiency))

    effective_monster_eff = 0.30 * (1.15 if is_etf else 1.0)
    effective_compounder_eff = 0.18 * (0.75 if is_etf else 1.0)
    effective_high_vol_atr = 10.0 * (1.35 if is_etf else 1.0)
    effective_avoid_eff = 0.08 * (0.60 if is_etf else 1.0)

    ema_alignment_clean = close > row.ema_fast > row.ema_slow > row.ema_long
    ema_alignment_bearish = close < row.ema_slow and row.ema_fast < row.ema_slow
    long_slope_up = row.ema_long >= d.iloc[i - ema_slope_bars].ema_long
    slow_slope_up = row.ema_slow >= d.iloc[i - ema_slope_bars].ema_slow
    rs_up = close > float(d.iloc[i - SHORT_RS_LOOKBACK_BARS].close)

    accum_vol = vol_ready and row.volume > row.vol_ma * 0.9 and close > open_ and close >= prev.close and row.close_loc >= 0.55
    dist_vol = vol_ready and row.volume > row.vol_ma * 1.2 and close < open_ and close <= prev.close and row.close_loc <= 0.45
    dry_up_vol = vol_ready and row.volume < row.vol_ma and (low <= row.ema_fast * 1.025 or low <= row.bb_basis) and close >= row.ema_slow
    breakout_vol = vol_ready and row.volume > row.vol_ma * 1.1 and (close > prev.high or close > row.ema_fast) and row.close_loc >= 0.60
    breakdown_vol = vol_ready and row.volume > row.vol_ma * 1.2 and close < open_ and close < row.ema_fast and close < prev.low and row.close_loc <= 0.45
    exhaust_vol = vol_ready and row.volume > row.vol_ma * 1.5 and atr_now > 0 and (close - row.ema_fast) / atr_now >= 3.375 and row.close_loc <= 0.55

    buyer_score = min(
        100.0,
        row.close_loc * 45
        + (20 if close > open_ else 0)
        + (15 if row.body > atr_now * 0.75 and close > open_ else 0)
        + (15 if accum_vol or breakout_vol else 0)
        + (5 if lower_wick > body_for_ratio * 1.5 else 0),
    )
    seller_score = min(
        100.0,
        (1 - row.close_loc) * 45
        + (20 if close < open_ else 0)
        + (15 if row.body > atr_now * 0.75 and close < open_ else 0)
        + (15 if dist_vol or breakdown_vol else 0)
        + (5 if upper_wick > body_for_ratio * 1.5 else 0),
    )

    buyer_control = buyer_score >= 70
    seller_control = seller_score >= 70
    fear_rejected = lower_wick > body_for_ratio * 1.5 and row.close_loc >= 0.60 and (low <= row.lower_bb or low <= row.ema_fast or low < prev.low) and not breakdown_vol
    greed_rejected = upper_wick > body_for_ratio * 1.5 and row.close_loc <= 0.40 and (high >= row.upper_bb or high >= d["high"].iloc[i - lookback_bars : i].max())
    fomo = range_atr >= 2.5 and vol_ready and row.volume > row.vol_ma * 1.8 and close > row.ema_fast * 1.08 and row.rsi >= 75
    quiet_absorption = vol_ready and row.volume < row.vol_ma and row.close_loc >= 0.45 and close >= row.ema_slow and (low <= row.ema_fast * 1.02 or low <= row.bb_basis) and not seller_control
    psych = (
        "FR" if fear_rejected else
        "QA" if quiet_absorption else
        "FOMO" if fomo else
        "GR" if greed_rejected else
        "BUYERS" if buyer_control else
        "SELLERS" if seller_control else
        "MIXED"
    )

    range_bound = trend_efficiency < effective_compounder_eff and row.atr_pct <= effective_high_vol_atr and not ema_alignment_bearish
    power_trend = ema_alignment_clean and long_slope_up and slow_slope_up and trend_efficiency >= effective_monster_eff and (rs_up or is_etf)
    steady_trend = ema_alignment_clean and slow_slope_up and trend_efficiency >= effective_compounder_eff and row.atr_pct <= effective_high_vol_atr
    mean_reversion = range_bound and (fear_rejected or quiet_absorption or close > row.ema_slow)
    high_vol = row.atr_pct > effective_high_vol_atr and trend_efficiency < effective_compounder_eff
    avoid = ema_alignment_bearish and trend_efficiency < effective_avoid_eff and (not is_etf or close < row.ema_long) and not fear_rejected
    mode = (
        "WAIT / AVOID" if avoid else
        "POWER TREND" if power_trend else
        "STEADY TREND" if steady_trend else
        "MEAN REVERSION" if mean_reversion else
        "HIGH VOLATILITY" if high_vol else
        "MIXED / NEUTRAL"
    )

    rsi_oversold = row.rsi < 30
    rsi_near_oversold = row.rsi < 45
    rsi_recovering = row.rsi > 30 and prev.rsi <= 30
    rsi_turning_up = row.rsi > prev.rsi and prev.rsi <= d.iloc[i - 2].rsi
    bb_touch_or_pierce = (d["low"].iloc[i - lookback_bars : i + 1] <= d["lower_bb"].iloc[i - lookback_bars : i + 1]).any()
    recent_oversold_bb = ((d["low"].iloc[i - lookback_bars : i + 1] <= d["lower_bb"].iloc[i - lookback_bars : i + 1]) & (d["rsi"].iloc[i - lookback_bars : i + 1] < 45)).any()
    back_inside_bb = close > row.lower_bb
    price_follow = close > prev.high
    bullish_reversal_close = close > open_ and row.close_loc >= 0.50
    constructive_close = row.close_loc >= 0.55 and close >= (open_ + prev.close) / 2
    demand_tail = row.lower_wick_pct >= 0.30 and row.close_loc >= 0.55
    wide_bullish = close > open_ and row.body_pct >= 0.45 and row.close_loc >= 0.65
    bb_reclaim = (close > row.lower_bb and prev.close <= prev.lower_bb) or (back_inside_bb and close > prev.high)
    right_side = recent_oversold_bb and bb_reclaim and row.rsi > prev.rsi and (price_follow or bullish_reversal_close or demand_tail)

    trend_condition = close > row.ema_slow and row.ema_fast >= row.ema_slow
    uptrend = close > row.ema_slow and row.ema_fast > row.ema_slow and row.ema_slow >= d.iloc[i - ema_slope_bars].ema_slow
    strong_momentum = close > row.ema_fast and row.ema_fast > row.ema_slow and row.ema_fast >= d.iloc[i - ema_slope_bars].ema_fast and row.ema_slow >= d.iloc[i - ema_slope_bars].ema_slow
    pullback_support = low <= row.ema_fast or low <= row.bb_basis or close <= row.ema_fast * 1.02
    shallow_pullback = low <= row.ema_fast * 1.015 or low <= row.bb_basis or close <= row.ema_fast * 1.025
    support_held = close > row.ema_slow and close > row.lower_bb
    early_support_zone = low <= row.ema_fast * 1.03 or low <= row.bb_basis * 1.02 or close <= row.ema_fast * 1.04
    early_support_held = close > row.ema_slow and close >= row.lower_bb and row.close_loc >= 0.50
    early_pullback_candle = demand_tail or constructive_close or (close >= prev.close and row.close_loc >= 0.50)
    standard_pullback_reversal = 40 <= row.rsi <= 60 and row.rsi > prev.rsi and (price_follow or constructive_close)
    momentum_pullback_reversal = 45 <= row.rsi <= 70 and row.rsi >= prev.rsi and (close > row.ema_fast or price_follow or constructive_close)
    pullback_reversal = standard_pullback_reversal or (strong_momentum and momentum_pullback_reversal)
    pullback = uptrend and (pullback_support or (strong_momentum and shallow_pullback)) and support_held and pullback_reversal
    early_pullback = uptrend and early_support_zone and early_support_held and 38 <= row.rsi <= 68 and row.rsi >= prev.rsi - 2 and early_pullback_candle
    recent_momentum_high = d["high"].iloc[i - 10 : i].max()
    momentum_dip = d["low"].iloc[i - 2 : i + 1].min() <= recent_momentum_high * 0.97
    momentum_reclaim = close > open_ and close > prev.close and close > row.ema_fast and row.close_loc >= 0.55
    momentum = strong_momentum and momentum_dip and momentum_reclaim and 55 <= row.rsi <= 85 and close <= row.ema_fast * 1.35
    breakout_level = d["close"].iloc[i - 20 : i].max()
    breakout_ext = (close - row.ema_fast) / atr_now if atr_now > 0 else 0
    breakout = strong_momentum and close >= breakout_level and close > prev.high and wide_bullish and 55 <= row.rsi <= 82 and breakout_ext <= 3.5 and row.macd_hist >= prev.macd_hist
    frequent_buy_setup = bb_touch_or_pierce and back_inside_bb and (rsi_near_oversold or rsi_turning_up)
    profile_buy = (frequent_buy_setup or (fear_rejected and recent_oversold_bb and back_inside_bb)) and trend_condition
    reversal = right_side or profile_buy

    selected = (
        ("BREAKOUT BUY", breakout),
        ("MOMENTUM BUY", momentum and not breakout),
        ("PULLBACK BUY", pullback and not breakout and not momentum),
        ("EARLY PULLBACK BUY", early_pullback and not breakout and not momentum and not pullback),
        ("REVERSAL BUY", reversal and not breakout and not momentum and not pullback and not early_pullback),
    )
    setup = next((name for name, flag in selected if flag), "NONE")
    setup_forming = setup != "NONE"
    setup_stats = (
        historical_setup_stats(d, setup)
        if include_setup_stats
        else {"hist_trades": "", "hist_win_rate": "", "hist_avg_return": ""}
    )

    setup_max_atr = 12.0 if setup == "BREAKOUT BUY" else 10.0 if setup == "MOMENTUM BUY" else 8.0
    setup_atr_ok = row.atr_pct <= setup_max_atr
    behavior_volume_ok = (
        breakout_vol if setup == "BREAKOUT BUY" else
        (accum_vol or breakout_vol) if setup == "MOMENTUM BUY" else
        (dry_up_vol or accum_vol or breakout_vol) if "PULLBACK" in setup else
        (accum_vol or breakout_vol or ((fear_rejected or quiet_absorption or buyer_control) and recent_oversold_bb))
    )
    volume_ok = vol_ready and not dist_vol and behavior_volume_ok
    close_ok = row.close_loc >= float(personality_profile["min_close_loc"])
    buyer_quality_ok = buyer_score >= float(personality_profile["min_buyer_score"])
    setup_low = min(low, float(d["low"].iloc[i - lookback_bars : i + 1].min()))
    close_above_setup_low_atr = (close - setup_low) / atr_now if atr_now > 0 else 0.0
    close_above_pivot_pct = (close - last_pivot_high) / last_pivot_high * 100 if not math.isnan(last_pivot_high) and last_pivot_high > 0 else 0.0
    no_chase = range_atr <= 2.5 and close_above_setup_low_atr <= 2.5 and close_above_pivot_pct <= 8.0
    high_beta_no_chase = not high_vol or (range_atr <= 2.5 * (0.90 if is_etf else 0.75) and close_above_setup_low_atr <= 2.5 * (0.90 if is_etf else 0.75))
    personality_entry_ok = mode != "MEAN REVERSION" or fear_rejected or quiet_absorption or buyer_control
    filters_ok = setup_forming and volume_ok and setup_atr_ok and close_ok and buyer_quality_ok and no_chase and high_beta_no_chase and personality_entry_ok and not avoid and not seller_control and not fomo and not greed_rejected
    continuation_ok = (
        setup_forming
        and not filters_ok
        and mode in {"POWER TREND", "STEADY TREND"}
        and volume_ok
        and setup_atr_ok
        and close_ok
        and high_beta_no_chase
        and personality_entry_ok
        and close > row.ema_fast
        and row.ema_fast >= row.ema_slow
        and row.rsi <= 85
        and row.close_loc >= 0.58
        and buyer_score >= 55
        and not avoid
        and not seller_control
        and not fomo
        and not greed_rejected
    )

    sell_rsi = row.rsi > 75
    close_off_high = row.close_loc < 0.55
    confirmed_exhaustion = sell_rsi and (high > row.upper_bb or greed_rejected) and close_off_high and (close < open_ or row.macd_hist < prev.macd_hist)
    atr_extension = (close - row.ema_fast) / atr_now if atr_now > 0 else 0.0
    atr_extension_exhaustion = atr_extension >= 4.5 and (close_off_high or row.macd_hist < prev.macd_hist or row.rsi < prev.rsi)
    trend_damage = close < row.ema_fast or (row.macd_hist < 0 <= prev.macd_hist) or (row.rsi < prev.rsi and close < prev.low)
    confirmed_break = close < row.ema_fast and close < prev.low and ((close < open_ and row.close_loc <= 0.40 and row.body_pct >= 0.35) or breakdown_vol or row.macd_hist < prev.macd_hist)
    exit_pressure = ((confirmed_exhaustion and confirmed_break) or atr_extension_exhaustion or (seller_control and (close_off_high or trend_damage)))

    candle_entry_midpoint = (high + low) / 2
    prior_high = float(prev.high)
    breakout_retest_level = max(prior_high, float(breakout_level))
    reclaim_retest_level = prior_high if close > prior_high else candle_entry_midpoint
    if setup == "BREAKOUT BUY":
        entry_est = min(close, breakout_retest_level)
        entry_est, entry_note = clamp_entry_to_current_zone(float(entry_est), close, atr_now, 5.0)
    elif setup == "MOMENTUM BUY":
        entry_est = min(close, max(reclaim_retest_level, float(row.ema_fast))) if close > prior_high else min(close, candle_entry_midpoint)
        entry_est, entry_note = clamp_entry_to_current_zone(float(entry_est), close, atr_now, 4.0)
    elif setup in {"PULLBACK BUY", "EARLY PULLBACK BUY"}:
        entry_est = min(close, max(min(float(row.ema_fast), close), candle_entry_midpoint))
        entry_est, entry_note = clamp_entry_to_current_zone(float(entry_est), close, atr_now, 6.0)
    elif setup == "REVERSAL BUY":
        entry_est = min(close, candle_entry_midpoint)
        entry_est, entry_note = clamp_entry_to_current_zone(float(entry_est), close, atr_now, 5.0)
    else:
        entry_est = np.nan
        entry_note = ""

    trade_entry = close
    stop_pct = 6.0 if setup == "BREAKOUT BUY" else 4.0 if setup == "MOMENTUM BUY" else 7.0 if setup == "PULLBACK BUY" else 6.0 if setup == "EARLY PULLBACK BUY" else 5.0
    atr_stop_mult = 4.0 if setup in {"BREAKOUT BUY", "MOMENTUM BUY"} else 3.5 if setup == "PULLBACK BUY" else 3.25 if setup == "EARLY PULLBACK BUY" else 3.0
    percent_stop = max(close * (1 - stop_pct / 100), close * 0.93)
    atr_stop = close - atr_now * atr_stop_mult if atr_now > 0 else percent_stop
    stop = max(percent_stop, atr_stop)
    target = close + atr_now * 3.0 if atr_now > 0 else close * (1 + (12.0 if setup == "MOMENTUM BUY" else 10.0 if "PULLBACK" in setup else 8.0) / 100)
    reward_risk = (target - trade_entry) / (trade_entry - stop) if trade_entry > stop else np.nan
    distance_from_ref_zone_pct = (
        (close - float(entry_est)) / float(entry_est) * 100
        if setup_forming and not math.isnan(entry_est) and float(entry_est) > 0
        else np.nan
    )
    distance_from_ref_zone_atr = (
        (close - float(entry_est)) / atr_now
        if setup_forming and not math.isnan(entry_est) and atr_now > 0
        else np.nan
    )
    extended_from_zone = (
        setup_forming
        and not math.isnan(distance_from_ref_zone_pct)
        and (distance_from_ref_zone_pct >= 7.0 or (not math.isnan(distance_from_ref_zone_atr) and distance_from_ref_zone_atr >= 2.25))
    )
    profile_extended_from_zone = (
        setup_forming
        and not math.isnan(distance_from_ref_zone_pct)
        and (
            distance_from_ref_zone_pct >= float(personality_profile["max_zone_distance_pct"])
            or (
                not math.isnan(distance_from_ref_zone_atr)
                and distance_from_ref_zone_atr >= float(personality_profile["max_zone_distance_atr"])
            )
        )
    )
    reward_risk_ok = (
        not setup_forming
        or math.isnan(reward_risk)
        or reward_risk >= float(personality_profile["min_reward_risk"])
    )
    buy_quality_penalty = 0.0
    buy_quality_penalty += max(0.0, (float(personality_profile["min_close_loc"]) - float(row.close_loc)) * 60)
    buy_quality_penalty += max(0.0, (float(personality_profile["min_buyer_score"]) - float(buyer_score)) * 0.6)
    buy_quality_penalty += 18.0 if profile_extended_from_zone else 0.0
    buy_quality_penalty += 8.0 if not reward_risk_ok else 0.0
    buy_quality_score = max(0.0, min(100.0, 100.0 - buy_quality_penalty))
    profile_buy_ok = (
        not setup_forming
        or (
            buy_quality_score >= float(personality_profile["min_buy_quality"])
            and not profile_extended_from_zone
            and reward_risk_ok
        )
    )
    high_quality_entry_override = (
        setup_forming
        and not no_chase
        and setup in {"BREAKOUT BUY", "MOMENTUM BUY"}
        and personality_profile["personality_type"] == "HIGH_BETA"
        and volume_ok
        and setup_atr_ok
        and close_ok
        and buyer_quality_ok
        and high_beta_no_chase
        and personality_entry_ok
        and profile_buy_ok
        and not avoid
        and not seller_control
        and not fomo
        and not greed_rejected
        and not extended_from_zone
        and buyer_score >= 65
        and not math.isnan(distance_from_ref_zone_pct)
        and distance_from_ref_zone_pct <= float(personality_profile["max_zone_distance_pct"])
    )
    fast_breakout_entry = (
        setup_forming
        and setup in {"BREAKOUT BUY", "MOMENTUM BUY"}
        and buyer_score >= 75
        and (breakout_vol or accum_vol)
        and not math.isnan(distance_from_ref_zone_pct)
        and distance_from_ref_zone_pct <= float(personality_profile["max_zone_distance_pct"])
        and not extended_from_zone
        and not profile_extended_from_zone
    )
    pullback_reclaim_entry = (
        setup_forming
        and setup in {"PULLBACK BUY", "EARLY PULLBACK BUY", "REVERSAL BUY"}
        and not math.isnan(distance_from_ref_zone_pct)
        and distance_from_ref_zone_pct <= 3.0
        and (dry_up_vol or accum_vol or breakout_vol or quiet_absorption or fear_rejected)
        and not extended_from_zone
        and not profile_extended_from_zone
    )

    if extended_from_zone or profile_extended_from_zone:
        entry_quality_label = "Extended"
        entry_quality_score = max(0.0, min(70.0, buy_quality_score - 25.0))
    elif fast_breakout_entry:
        entry_quality_label = "Fast Breakout"
        entry_quality_score = min(100.0, buy_quality_score + 5.0)
    elif pullback_reclaim_entry:
        entry_quality_label = "Pullback/Reclaim"
        entry_quality_score = min(100.0, buy_quality_score + 3.0)
    elif setup_forming and buy_quality_score >= 85 and (
        math.isnan(distance_from_ref_zone_pct) or distance_from_ref_zone_pct <= 5.0
    ):
        entry_quality_label = "Developing"
        entry_quality_score = buy_quality_score
    elif setup_forming:
        entry_quality_label = "Low Quality"
        entry_quality_score = min(60.0, buy_quality_score)
    else:
        entry_quality_label = ""
        entry_quality_score = 0.0

    if setup_forming:
        filters_ok = (filters_ok and profile_buy_ok) or high_quality_entry_override
        continuation_ok = continuation_ok and not profile_extended_from_zone
    extension_state = "EXTENDED" if extended_from_zone or profile_extended_from_zone else "NEAR_ZONE" if setup_forming else ""

    if filters_ok:
        action = "BUY CANDIDATE"
        rank = 100
    elif continuation_ok:
        action = "STRONG CONTINUATION"
        rank = 85
    elif setup_forming:
        action = "SETUP FORMING"
        rank = 70
    elif exit_pressure:
        action = "EXIT PRESSURE"
        rank = 20
    elif mode in {"POWER TREND", "STEADY TREND"}:
        action = "WATCH TREND"
        rank = 50
    elif mode == "WAIT / AVOID":
        action = "WAIT / AVOID"
        rank = 0
    else:
        action = "WAIT"
        rank = 30

    score = rank
    score += 10 if mode == "POWER TREND" else 7 if mode == "STEADY TREND" else 4 if mode == "MEAN REVERSION" else 0
    score += 8 if psych in {"FR", "QA", "BUYERS"} else -8 if psych in {"FOMO", "GR", "SELLERS"} else 0
    score += min(max(trend_efficiency * 20, 0), 10)
    score -= min(max(row.atr_pct - setup_max_atr, 0), 15)
    score -= max(0.0, (float(personality_profile["min_buy_quality"]) - buy_quality_score) * 0.25) if setup_forming else 0.0

    notes = []
    if fear_rejected:
        notes.append("Fear rejected")
    if quiet_absorption:
        notes.append("Quiet absorption")
    if breakout:
        notes.append("Breakout attempt")
    if continuation_ok:
        notes.append("Strong continuation")
    if entry_note:
        notes.append(entry_note)
    if profile_extended_from_zone:
        notes.append("Personality-adjusted zone is extended")
    if high_quality_entry_override:
        notes.append("High-beta breakout entry quality accepted")
    if setup_forming and not reward_risk_ok:
        notes.append("Reward/risk is below personality threshold")
    if exit_pressure:
        notes.append("Exit pressure")
    if avoid:
        notes.append("Weak mode")

    reason_codes = []
    if volume_ok and (breakout_vol or accum_vol):
        reason_codes.append("volume_expansion")
    if breakout:
        reason_codes.append("trend_reclaim")
    if momentum:
        reason_codes.append("momentum_reclaim")
    if pullback or early_pullback:
        reason_codes.append("support_retest")
    if reversal or fear_rejected:
        reason_codes.append("fear_rejection")
    if quiet_absorption:
        reason_codes.append("quiet_absorption")
    if buyer_control:
        reason_codes.append("buyer_tape")
    if seller_control:
        reason_codes.append("seller_pressure")
    if exit_pressure:
        reason_codes.append("exit_pressure")
    if extended_from_zone:
        reason_codes.append("extended_from_zone")
    if profile_extended_from_zone:
        reason_codes.append("personality_extended")
    if high_quality_entry_override:
        reason_codes.append("high_beta_entry_quality")
    if fast_breakout_entry:
        reason_codes.append("fast_breakout_entry")
    if pullback_reclaim_entry:
        reason_codes.append("pullback_reclaim_entry")
    if setup_forming and not reward_risk_ok:
        reason_codes.append("weak_reward_risk")
    if setup_forming and not buyer_quality_ok:
        reason_codes.append("buyer_quality_low")
    if entry_note:
        reason_codes.append("reference_zone_adjusted")
    reason_codes = list(dict.fromkeys(reason_codes))

    return {
        "ticker": display_ticker(ticker),
        "name": stock_name(ticker),
        "date": str(pd.to_datetime(row.date).date()),
        "instrument": "ETF" if is_etf else "Stock",
        "action": action,
        "setup": setup,
        "adaptive_mode": mode,
        "psychology": psych,
        "score": round(float(score), 1),
        "close": round(close, 2),
        "day_change_pct": round((close / prev.close - 1) * 100, 2),
        "rsi": round(float(row.rsi), 1),
        "atr_pct": round(float(row.atr_pct), 2),
        "setup_atr_limit": setup_max_atr,
        "trend_efficiency": round(float(trend_efficiency), 2),
        "personality_type": personality_profile["personality_type"],
        "personality_atr_pct": personality_profile["personality_atr_pct"],
        "personality_abs_move_pct": personality_profile["personality_abs_move_pct"],
        "buy_quality_score": round(float(buy_quality_score), 1),
        "buy_quality_minimum": round(float(personality_profile["min_buy_quality"]), 1),
        "entry_quality_label": entry_quality_label,
        "entry_quality_score": round(float(entry_quality_score), 1),
        "profile_zone_limit_pct": round(float(personality_profile["max_zone_distance_pct"]), 2),
        "buyer_score": round(float(buyer_score), 0),
        "seller_score": round(float(seller_score), 0),
        "volume_state": "BREAKDOWN" if breakdown_vol else "DISTRIBUTION" if dist_vol else "BREAKOUT" if breakout_vol else "DEMAND" if accum_vol else "DRY-UP" if dry_up_vol else "NEUTRAL",
        "entry_est": round(float(entry_est), 2) if setup_forming and not math.isnan(entry_est) else "",
        "stop_est": round(float(stop), 2) if setup_forming else "",
        "target_est": round(float(target), 2) if setup_forming else "",
        "reward_risk": round(float(reward_risk), 2) if setup_forming and not math.isnan(reward_risk) else "",
        "distance_from_ref_zone_pct": round(float(distance_from_ref_zone_pct), 2) if setup_forming and not math.isnan(distance_from_ref_zone_pct) else "",
        "extension_state": extension_state,
        "reason_codes": reason_codes,
        "signal_stage": signal_stage(action),
        "hist_trades": setup_stats["hist_trades"],
        "hist_win_rate": setup_stats["hist_win_rate"],
        "hist_avg_return": setup_stats["hist_avg_return"],
        "exit_pressure": bool_text(exit_pressure),
        "confirmed_break": bool_text(confirmed_break),
        "notes": "; ".join(notes),
    }


def action_class(action: str) -> str:
    return {
        "BUY CANDIDATE": "buy",
        "STRONG CONTINUATION": "continue",
        "SETUP FORMING": "setup",
        "EXIT PRESSURE": "exit",
        "WATCH TREND": "watch",
        "WAIT": "avoid",
        "WAIT / AVOID": "avoid",
    }.get(action, "wait")


def enrich_signal_transitions(history_rows: list[dict]) -> list[dict]:
    if not history_rows:
        return history_rows

    enriched: list[dict] = []
    for index, row in enumerate(history_rows):
        previous = enriched[index - 1] if index else None
        action = row.get("action", "")
        previous_action = previous.get("action", "") if previous else ""
        current_rank = signal_stage_rank(action)
        previous_rank = signal_stage_rank(previous_action)
        transition_label = "New Today"
        transition_score = 0.0

        if previous:
            if action == previous_action and row.get("setup") == previous.get("setup"):
                transition_label = "Repeated Signal"
                transition_score = 0.0
            elif action == "EXIT PRESSURE":
                transition_label = "Downgraded"
                transition_score = -35.0
            elif action == "BUY CANDIDATE" and previous_action == "SETUP FORMING":
                transition_label = "Fresh Setup To Buy"
                transition_score = 35.0
            elif current_rank > previous_rank and action != "EXIT PRESSURE":
                transition_label = "Upgraded"
                transition_score = 20.0
            elif current_rank < previous_rank or action == "WAIT / AVOID":
                transition_label = "Downgraded"
                transition_score = -20.0
            else:
                transition_label = "Changed"
                transition_score = 5.0

        streak_start = index
        while streak_start > 0 and history_rows[streak_start - 1].get("action") == action:
            streak_start -= 1
        signal_age_days = index - streak_start + 1
        start_close = numeric_or_none(history_rows[streak_start].get("close"))
        close = numeric_or_none(row.get("close"))
        price_progress = (
            (float(close) / float(start_close) - 1) * 100
            if start_close and close and float(start_close) > 0
            else None
        )

        stale_penalty = 0.0
        reason_codes = list(row.get("reason_codes") or [])
        if action == "BUY CANDIDATE" and signal_age_days >= 3 and (price_progress is None or price_progress < 1.0):
            stale_penalty = min(22.0, (signal_age_days - 2) * 5.0)
            transition_label = "Stale Buy"
            reason_codes.append("stale_buy_no_progress")
        elif action == "BUY CANDIDATE" and signal_age_days == 1:
            reason_codes.append("fresh_buy_signal")

        if row.get("extension_state") == "EXTENDED":
            stale_penalty += 12.0
            transition_label = "Extended"
            reason_codes.append("extended_from_zone")

        adjusted_score = max(0.0, min(128.0, float(numeric_or_none(row.get("score")) or 0) + transition_score - stale_penalty))
        row.update(
            {
                "signal_stage": signal_stage(action),
                "transition_label": transition_label,
                "transition_score": round(float(transition_score - stale_penalty), 1),
                "signal_age_days": signal_age_days,
                "price_progress_since_signal_pct": round(float(price_progress), 2) if price_progress is not None else "",
                "freshness_penalty": round(float(stale_penalty), 1),
                "adjusted_score": round(float(adjusted_score), 1),
                "reason_codes": list(dict.fromkeys(reason_codes)),
            }
        )
        enriched.append(row)
    return enriched


def build_behavior_history(ticker: str, raw: pd.DataFrame, days: int = 30) -> list[dict]:
    d = prepare(raw)
    if len(d) < 220:
        return []

    history_rows: list[dict] = []
    start = max(220, len(d) - days + 1)
    for end in range(start, len(d) + 1):
        try:
            snapshot = classify_and_score(ticker, d.iloc[:end].copy(), prepared=True, include_setup_stats=False)
        except Exception:
            continue
        snapshot["history_day"] = len(d) - end
        history_rows.append(snapshot)
    return enrich_signal_transitions(history_rows)


LATEST_SIGNAL_FIELDS = [
    "signal_stage",
    "transition_label",
    "transition_score",
    "signal_age_days",
    "price_progress_since_signal_pct",
    "freshness_penalty",
    "adjusted_score",
    "distance_from_ref_zone_pct",
    "extension_state",
    "reason_codes",
]


def apply_latest_signal_context(row: dict, ticker_history: list[dict]) -> dict:
    if not ticker_history:
        row.setdefault("signal_stage", signal_stage(row.get("action", "")))
        row.setdefault("transition_label", "New Today")
        row.setdefault("transition_score", 0.0)
        row.setdefault("signal_age_days", 1)
        row.setdefault("freshness_penalty", 0.0)
        row.setdefault("adjusted_score", row.get("score", 0.0))
        return row

    latest = ticker_history[-1]
    for field in LATEST_SIGNAL_FIELDS:
        if field in latest:
            row[field] = latest[field]
    return row


def trailing_return_pct(frame: pd.DataFrame, bars: int = BENCHMARK_LOOKBACK_BARS) -> Optional[float]:
    if frame is None or len(frame) <= bars:
        return None
    latest = float(frame.iloc[-1].close)
    prior = float(frame.iloc[-bars - 1].close)
    if prior <= 0:
        return None
    return (latest / prior - 1) * 100


def market_context_for(raw: pd.DataFrame, benchmarks: dict[str, pd.DataFrame]) -> dict:
    ticker_return = trailing_return_pct(raw)
    spy_return = trailing_return_pct(benchmarks.get("SPY"))
    qqq_return = trailing_return_pct(benchmarks.get("QQQ"))
    benchmark_values = [value for value in (spy_return, qqq_return) if value is not None]
    benchmark_return = float(np.mean(benchmark_values)) if benchmark_values else None
    relative_return = ticker_return - benchmark_return if ticker_return is not None and benchmark_return is not None else None

    if relative_return is None:
        state = "UNKNOWN"
    elif relative_return >= MARKET_LEADER_THRESHOLD_PCT:
        state = "LEADING"
    elif relative_return <= MARKET_LAGGARD_THRESHOLD_PCT:
        state = "LAGGING"
    else:
        state = "INLINE"

    return {
        "market_context": state,
        "relative_return_20d_pct": round(float(relative_return), 2) if relative_return is not None else "",
        "ticker_return_20d_pct": round(float(ticker_return), 2) if ticker_return is not None else "",
        "benchmark_return_20d_pct": round(float(benchmark_return), 2) if benchmark_return is not None else "",
        "spy_return_20d_pct": round(float(spy_return), 2) if spy_return is not None else "",
        "qqq_return_20d_pct": round(float(qqq_return), 2) if qqq_return is not None else "",
    }


def days_until_timestamp(timestamp_value) -> Optional[int]:
    if timestamp_value in {"", None}:
        return None
    try:
        timestamp = float(timestamp_value)
    except (TypeError, ValueError):
        return None
    report_date = datetime.fromtimestamp(timestamp, tz=RUN_TIMEZONE).date()
    return (report_date - datetime.now(RUN_TIMEZONE).date()).days


def apply_quality_overlays(row: dict, market_context: dict) -> dict:
    row.update(market_context)
    action = row.get("action", "")
    actionable = action in {"BUY CANDIDATE", "SETUP FORMING", "STRONG CONTINUATION"}
    reason_codes = list(row.get("reason_codes") or [])
    adjusted_score = float(numeric_or_none(row.get("adjusted_score")) or numeric_or_none(row.get("score")) or 0)
    transition_label = row.get("transition_label", "")

    market_state = market_context.get("market_context", "UNKNOWN")
    if actionable and market_state == "LEADING":
        adjusted_score = min(128.0, adjusted_score + 4.0)
        reason_codes.append("market_leader")
    elif actionable and market_state == "LAGGING":
        adjusted_score = max(0.0, adjusted_score - 8.0)
        reason_codes.append("market_lagging")

    days_to_report = days_until_timestamp(row.get("next_report_timestamp"))
    event_risk = days_to_report is not None and 0 <= days_to_report <= EVENT_RISK_DAYS
    row["days_to_report"] = days_to_report if days_to_report is not None else ""
    row["event_risk"] = bool_text(event_risk)
    if actionable and event_risk:
        adjusted_score = max(0.0, adjusted_score - 10.0)
        reason_codes.append("event_risk")
        if transition_label in {"New Today", "Upgraded", "Fresh Setup To Buy"}:
            row["transition_label"] = "Event Risk"

    if row.get("extension_state") == "EXTENDED":
        signal_quality = "EXTENDED"
    elif event_risk and actionable:
        signal_quality = "EVENT RISK"
    elif row.get("transition_label") in {"New Today", "Upgraded", "Fresh Setup To Buy"}:
        signal_quality = "FRESH"
    elif row.get("transition_label") == "Stale Buy":
        signal_quality = "STALE"
    elif market_state == "LAGGING" and actionable:
        signal_quality = "LAGGING"
    elif actionable:
        signal_quality = "VALID"
    elif action == "EXIT PRESSURE":
        signal_quality = "EXIT RISK"
    else:
        signal_quality = "NEUTRAL"

    row["adjusted_score"] = round(float(adjusted_score), 1)
    row["signal_quality"] = signal_quality
    row["reason_codes"] = list(dict.fromkeys(reason_codes))
    return row


def write_history_html(path: Path) -> None:
    html_page = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Watchlist Behavior History</title>
  <style>
    :root {
      --bg: #f1efe5;
      --ink: #12140f;
      --muted: #69705f;
      --line: #dad7c8;
      --panel: rgba(255,255,248,.92);
      --buy: #ccefd9;
      --setup: #ffe5a3;
      --watch: #d7e4ff;
      --exit: #ffd0cc;
      --avoid: #e5e5df;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Avenir Next, Charter, Georgia, ui-serif, serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 5%, rgba(126, 169, 255, .28), transparent 34%),
        radial-gradient(circle at 90% 10%, rgba(255, 197, 77, .32), transparent 30%),
        linear-gradient(135deg, #fbf4df 0%, var(--bg) 55%, #e2eadf 100%);
      min-height: 100vh;
    }
    .page { padding: 24px; max-width: 1220px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
    .eyebrow { margin: 0 0 6px; color: #647052; font-size: 12px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
    h1 { margin: 0; font-size: clamp(32px, 5vw, 64px); letter-spacing: -.06em; line-height: .9; }
    .meta { margin-top: 10px; color: var(--muted); max-width: 760px; line-height: 1.4; }
    .link-button, button {
      border: 1px solid rgba(17,20,15,.15);
      background: #fffdf2;
      color: var(--ink);
      border-radius: 999px;
      padding: 10px 13px;
      text-decoration: none;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 8px 24px rgba(50, 56, 42, .08);
    }
    .controls {
      margin: 22px 0;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      background: var(--panel);
      border: 1px solid rgba(17,20,15,.10);
      border-radius: 22px;
      padding: 14px;
      box-shadow: 0 18px 60px rgba(50, 56, 42, .10);
    }
    input {
      min-width: 220px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 11px 14px;
      font: inherit;
      font-weight: 800;
      text-transform: uppercase;
      background: white;
    }
    .cards { display: grid; grid-template-columns: repeat(5, minmax(125px, 1fr)); gap: 12px; margin-bottom: 16px; }
    .card { background: var(--panel); border: 1px solid rgba(17,20,15,.10); border-radius: 22px; padding: 16px; box-shadow: 0 16px 50px rgba(50,56,42,.10); }
    .card span { display: block; color: var(--muted); font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: .08em; }
    .card strong { display: block; margin-top: 6px; font-size: 24px; letter-spacing: -.04em; }
    .timeline { display: grid; grid-template-columns: repeat(auto-fit, minmax(86px, 1fr)); gap: 8px; margin-bottom: 18px; }
    .day { border: 1px solid rgba(17,20,15,.10); border-radius: 16px; padding: 10px; min-height: 90px; background: white; }
    .day.buy { background: var(--buy); }
    .day.continue { background: #d7f4ff; }
    .day.setup { background: var(--setup); }
    .day.watch { background: var(--watch); }
    .day.exit { background: var(--exit); }
    .day.avoid { background: var(--avoid); }
    .date { font-size: 11px; color: var(--muted); font-weight: 800; }
    .signal { margin-top: 5px; font-size: 12px; font-weight: 900; }
    .price { margin-top: 5px; font-size: 16px; font-weight: 900; }
    .table-wrap { background: var(--panel); border: 1px solid rgba(17,20,15,.10); border-radius: 22px; overflow: auto; box-shadow: 0 18px 60px rgba(50,56,42,.10); }
    table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; }
    th, td { padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: left; white-space: nowrap; }
    th { position: sticky; top: 0; background: #20221f; color: #f7f1db; z-index: 1; font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }
    .empty { padding: 24px; background: var(--panel); border-radius: 22px; color: var(--muted); }
    @media (max-width: 820px) {
      .page { padding: 12px; }
      .topbar { display: block; }
      .cards { grid-template-columns: repeat(2, minmax(135px, 1fr)); }
      input { width: 100%; }
    }
  </style>
</head>
<body>
  <main class="page">
    <div class="topbar">
      <div>
        <p class="eyebrow">Behavior rewind</p>
        <h1>30-Day History</h1>
        <div class="meta">Type a symbol like ORCL to see how the scanner classified each recent trading day. This is the scanner's historical read, not a TradingView confirmation.</div>
      </div>
      <a class="link-button" href="index.html">Back to Watchlist</a>
    </div>
    <section class="controls">
      <input id="ticker" value="ORCL" aria-label="Ticker">
      <button id="load" type="button">Show History</button>
      <a class="link-button" href="watchlist_behavior_history_latest.csv">Download History CSV</a>
    </section>
    <section class="cards" id="cards"></section>
    <section class="timeline" id="timeline"></section>
    <section class="table-wrap">
      <table>
        <thead>
          <tr><th>Date</th><th>Signal</th><th>Setup</th><th>Mode</th><th>Tape</th><th>Score</th><th>Close</th><th>Chg%</th><th>Ref Zone</th><th>Stop</th><th>Target</th><th>Notes</th></tr>
        </thead>
        <tbody id="rows"></tbody>
      </table>
    </section>
  </main>
  <script src="supabase-config.js"></script>
  <script>
    const input = document.querySelector("#ticker");
    const loadButton = document.querySelector("#load");
    const cards = document.querySelector("#cards");
    const timeline = document.querySelector("#timeline");
    const rowsBody = document.querySelector("#rows");
    let historyRows = [];

    function parseCSV(text) {
      const lines = text.trim().split(/\\r?\\n/);
      const headers = lines.shift().split(",");
      return lines.map((line) => {
        const cells = [];
        let current = "";
        let quoted = false;
        for (let i = 0; i < line.length; i += 1) {
          const char = line[i];
          const next = line[i + 1];
          if (char === '"' && quoted && next === '"') {
            current += '"';
            i += 1;
          } else if (char === '"') {
            quoted = !quoted;
          } else if (char === "," && !quoted) {
            cells.push(current);
            current = "";
          } else {
            current += char;
          }
        }
        cells.push(current);
        return Object.fromEntries(headers.map((header, index) => [header, cells[index] || ""]));
      });
    }

    function actionKind(action) {
      if (action === "BUY CANDIDATE") return "buy";
      if (action === "STRONG CONTINUATION") return "continue";
      if (action === "SETUP FORMING") return "setup";
      if (action === "WATCH TREND") return "watch";
      if (action === "EXIT PRESSURE") return "exit";
      return "avoid";
    }

    function shortAction(action) {
      return {
        "BUY CANDIDATE": "BUY",
        "STRONG CONTINUATION": "TRENDING",
        "SETUP FORMING": "SETUP",
        "WATCH TREND": "WATCH",
        "EXIT PRESSURE": "EXIT",
        "WAIT / AVOID": "AVOID",
      }[action] || action || "WAIT";
    }

    function supabaseHeaders(config) {
      return {
        apikey: config.anonKey,
        Authorization: `Bearer ${config.anonKey}`,
      };
    }

    async function loadSupabaseHistory(ticker) {
      const config = window.WATCHLIST_SUPABASE;
      if (!config || !config.url || !config.anonKey) return null;

      const baseUrl = config.url.replace(/\\/$/, "");
      const latestUrl = `${baseUrl}/rest/v1/watchlist_snapshots?select=run_date&order=run_date.desc&limit=1`;
      const latestResponse = await fetch(latestUrl, { headers: supabaseHeaders(config) });
      if (!latestResponse.ok) throw new Error("Could not read latest Supabase run.");
      const latestRuns = await latestResponse.json();
      if (!latestRuns.length) return [];

      const runDate = latestRuns[0].run_date;
      const selectedTicker = ticker.trim().toUpperCase();
      const historyUrl = `${baseUrl}/rest/v1/watchlist_behavior_history?select=payload&run_date=eq.${encodeURIComponent(runDate)}&ticker=eq.${encodeURIComponent(selectedTicker)}&order=history_date.asc`;
      const historyResponse = await fetch(historyUrl, { headers: supabaseHeaders(config) });
      if (!historyResponse.ok) throw new Error("Could not read Supabase history.");
      const rows = await historyResponse.json();
      return rows.map((row) => row.payload || row);
    }

    async function loadCsvHistory() {
      const response = await fetch("watchlist_behavior_history_latest.csv");
      if (!response.ok) throw new Error("History CSV is not available.");
      return parseCSV(await response.text());
    }

    function renderTicker() {
      const ticker = input.value.trim().toUpperCase();
      const rows = historyRows.filter((row) => row.ticker === ticker).sort((a, b) => a.date.localeCompare(b.date));
      const params = new URLSearchParams(window.location.search);
      params.set("ticker", ticker);
      window.history.replaceState(null, "", `${window.location.pathname}?${params.toString()}`);

      if (!rows.length) {
        cards.innerHTML = "";
        timeline.innerHTML = `<div class="empty">No 30-day history found for ${ticker}. It may have failed data fetch or have too little price history.</div>`;
        rowsBody.innerHTML = "";
        return;
      }

      const latest = rows[rows.length - 1];
      const first = rows[0];
      const signalChanges = rows.reduce((count, row, index) => count + (index > 0 && row.action !== rows[index - 1].action ? 1 : 0), 0);
      const closeChange = Number(first.close) ? ((Number(latest.close) / Number(first.close) - 1) * 100).toFixed(1) : "";
      cards.innerHTML = `
        <div class="card"><span>Latest Signal</span><strong>${shortAction(latest.action)}</strong></div>
        <div class="card"><span>Latest Score</span><strong>${latest.score || "-"}</strong></div>
        <div class="card"><span>30-Day Change</span><strong>${closeChange}%</strong></div>
        <div class="card"><span>Signal Changes</span><strong>${signalChanges}</strong></div>
      `;
      timeline.innerHTML = rows.map((row) => `
        <div class="day ${actionKind(row.action)}" title="${row.date} ${row.action} ${row.setup}">
          <div class="date">${row.date.slice(5)}</div>
          <div class="signal">${shortAction(row.action)}</div>
          <div class="price">${Number(row.close).toFixed(2)}</div>
          <div class="date">${row.setup === "NONE" ? "" : row.setup.replace(" BUY", "")}</div>
        </div>
      `).join("");
      rowsBody.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${row.date}</td><td>${shortAction(row.action)}</td><td>${row.setup}</td><td>${row.adaptive_mode}</td>
          <td>${row.psychology}</td><td>${row.score}</td><td>${row.close}</td><td>${row.day_change_pct}</td>
          <td>${row.entry_est}</td><td>${row.stop_est}</td><td>${row.target_est}</td><td>${row.notes}</td>
        </tr>
      `).join("");
    }

    function hasSupabaseConfig() {
      const config = window.WATCHLIST_SUPABASE;
      return !!(config && config.url && config.anonKey);
    }

    async function showTicker() {
      const ticker = input.value.trim().toUpperCase();
      if (!ticker) return;

      if (hasSupabaseConfig()) {
        try {
          historyRows = await loadSupabaseHistory(ticker);
        } catch {
          historyRows = await loadCsvHistory();
        }
      }
      renderTicker();
    }

    Promise.resolve()
      .then(() => {
        const ticker = (new URLSearchParams(window.location.search).get("ticker") || input.value || "ORCL").toUpperCase();
        input.value = ticker;
        return hasSupabaseConfig() ? loadSupabaseHistory(ticker) : loadCsvHistory();
      })
      .then((rows) => rows || loadCsvHistory())
      .catch(() => loadCsvHistory())
      .then((rows) => {
        historyRows = rows;
        const ticker = new URLSearchParams(window.location.search).get("ticker");
        if (ticker) input.value = ticker.toUpperCase();
        renderTicker();
      })
      .catch(() => {
        timeline.innerHTML = '<div class="empty">History CSV is not available yet. It will appear after the next successful refresh.</div>';
      });
    loadButton.addEventListener("click", showTicker);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") showTicker();
    });
  </script>
</body>
</html>
"""
    path.write_text(html_page)


def write_html(df: pd.DataFrame, path: Path, status_text: Optional[str] = None, preflight_text: Optional[str] = None) -> None:
    display_columns = [
        "ticker", "name", "action", "score", "close", "day_change_pct",
        "setup", "adaptive_mode", "psychology", "hist_win_rate", "reward_risk",
        "volume_state", "entry_est", "stop_est", "target_est", "notes",
    ]
    display_columns = [col for col in display_columns if col in df.columns]
    visible_df = df[display_columns].copy()

    summary_items = [
        ("BUY", int((df["action"] == "BUY CANDIDATE").sum()), "buy"),
        ("TRENDING", int((df["action"] == "STRONG CONTINUATION").sum()), "continue"),
        ("SETUP", int((df["action"] == "SETUP FORMING").sum()), "setup"),
        ("WATCH", int((df["action"] == "WATCH TREND").sum()), "watch"),
        ("EXIT", int((df["action"] == "EXIT PRESSURE").sum()), "exit"),
        ("AVOID", int(df["action"].isin(["WAIT", "WAIT / AVOID"]).sum()), "avoid"),
    ]
    cards = "".join(
        f"<button class='card {kind}' type='button' data-filter='{kind}'><span>{label}</span><strong>{value}</strong></button>"
        for label, value, kind in summary_items
    )

    header_labels = {
        "ticker": "Sym",
        "name": "Name",
        "action": "Signal",
        "score": "Score",
        "close": "Last",
        "day_change_pct": "Chg%",
        "setup": "Setup",
        "adaptive_mode": "Mode",
        "psychology": "Tape",
        "hist_win_rate": "Win%",
        "reward_risk": "R/R",
        "volume_state": "Vol",
        "entry_est": "Ref Zone",
        "stop_est": "Stop",
        "target_est": "Target",
        "notes": "Read",
    }
    action_labels = {
        "BUY CANDIDATE": "BUY",
        "STRONG CONTINUATION": "TRENDING",
        "SETUP FORMING": "SETUP",
        "EXIT PRESSURE": "EXIT",
        "WATCH TREND": "WATCH",
        "WAIT": "WAIT",
        "WAIT / AVOID": "AVOID",
    }
    setup_labels = {
        "BREAKOUT BUY": "BO",
        "MOMENTUM BUY": "MOM",
        "PULLBACK BUY": "PB",
        "EARLY PULLBACK BUY": "EPB",
        "REVERSAL BUY": "REV",
        "NONE": "-",
    }
    mode_labels = {
        "POWER TREND": "Power",
        "STEADY TREND": "Steady",
        "MEAN REVERSION": "Revert",
        "HIGH VOLATILITY": "Volatile",
        "WAIT / AVOID": "Avoid",
        "MIXED / NEUTRAL": "Mixed",
    }
    psych_labels = {
        "FR": "FR",
        "QA": "QA",
        "FOMO": "FOMO",
        "GR": "GR",
        "BUYERS": "BUYERS",
        "SELLERS": "SELLERS",
        "MIXED": "-",
    }

    def fmt_cell(col: str, value) -> str:
        text = "" if pd.isna(value) else str(value)
        escaped = html.escape(text)
        if col == "ticker":
            return f"<a class='ticker-link' href='history.html?ticker={escaped}'>{escaped}</a>"
        if col == "action":
            short = html.escape(action_labels.get(text, text))
            return f"<span class='badge action {action_class(text)}'>{short}</span>"
        if col == "setup":
            short = html.escape(setup_labels.get(text, text.replace("_BUY", "").replace("_", " ")))
            return f"<span class='badge setup'>{short}</span>" if short != "-" else "<span class='dash'>-</span>"
        if col == "psychology" and text not in {"", "MIXED"}:
            short = html.escape(psych_labels.get(text, text))
            return f"<span class='badge psych'>{short}</span>"
        if col == "psychology":
            return "<span class='dash'>-</span>"
        if col == "adaptive_mode":
            short = html.escape(mode_labels.get(text, text.title()))
            return f"<span class='mode'>{short}</span>"
        if col in {"score", "hist_win_rate", "reward_risk", "day_change_pct"}:
            try:
                return f"{float(value):.1f}"
            except (TypeError, ValueError):
                return escaped
        if col in {"close", "entry_est", "stop_est", "target_est"}:
            try:
                return f"{float(value):.2f}"
            except (TypeError, ValueError):
                return escaped
        return escaped

    numeric_columns = {"score", "hist_win_rate", "reward_risk", "day_change_pct", "close", "entry_est", "stop_est", "target_est"}

    rows = []
    for _, row in visible_df.iterrows():
        search_text = " ".join(str(row.get(col, "")) for col in visible_df.columns).lower()
        action_kind = action_class(row["action"])
        score_value = row.get("score", "")
        change_value = row.get("day_change_pct", "")
        data_attrs = (
            f"data-action='{action_kind}' "
            f"data-score='{html.escape(str(score_value))}' "
            f"data-change='{html.escape(str(change_value))}' "
            f"data-ticker='{html.escape(str(row.get('ticker', '')))}' "
            f"data-search='{html.escape(search_text)}'"
        )
        cells = "".join(f"<td data-col='{col}'>{fmt_cell(col, row[col])}</td>" for col in visible_df.columns)
        rows.append(f"<tr class='{action_kind}' {data_attrs}>{cells}</tr>")
    header = "".join(
        f"<th data-col='{c}' data-sort='{'number' if c in numeric_columns else 'text'}'>{header_labels.get(c, c.replace('_', ' ').title())}</th>"
        for c in visible_df.columns
    )
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    meta_line = f"{generated_at} · Confirm BUY CANDIDATE entries on TradingView before acting."
    status_block = ""
    if status_text:
        status_block = f"<div class='status'>{html.escape(status_text)}</div>"
    preflight_block = ""
    if preflight_text:
        preflight_block = f"<div class='status preflight'>{html.escape(preflight_text)}</div>"

    html_page = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Daily Watchlist Overview</title>
  <style>
    :root {{
      --bg: #eef1e8;
      --ink: #11140f;
      --muted: #68705f;
      --line: #d9dece;
      --panel: rgba(255,255,250,.92);
      --panel-strong: #fffdf3;
      --buy: #d8f7e4;
      --setup: #fff0b8;
      --watch: #dfeaff;
      --exit: #ffddd8;
      --avoid: #eaebe5;
      --shadow: 0 20px 70px rgba(54, 67, 40, .14);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Avenir Next, Charter, Georgia, ui-serif, serif;
      background:
        radial-gradient(circle at 10% 0%, rgba(255, 211, 87, .35), transparent 30%),
        radial-gradient(circle at 88% 12%, rgba(94, 154, 255, .23), transparent 36%),
        linear-gradient(135deg, #f5f1df 0%, var(--bg) 52%, #dde8e0 100%);
      color: var(--ink);
      min-height: 100vh;
    }}
    .page {{ padding: 24px; }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: flex-start;
      margin-bottom: 16px;
    }}
    .eyebrow {{ margin: 0 0 5px; color: #647052; font-size: 12px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }}
    h1 {{ margin: 0; font-size: clamp(32px, 5vw, 68px); letter-spacing: -.06em; line-height: .88; }}
    .meta {{ color: var(--muted); font-size: 13px; line-height: 1.35; margin-top: 10px; max-width: 760px; }}
    .status {{
      margin-top: 8px;
      display: inline-block;
      padding: 8px 10px;
      border-radius: 999px;
      background: #fff4cf;
      border: 1px solid #ebd98a;
      color: #5b4b12;
      font-size: 12px;
      font-weight: 600;
    }}
    .status.preflight {{
      margin-left: 8px;
      background: #ffe7e2;
      border-color: #efb0a2;
      color: #7b2f1d;
    }}
    .actions {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
      min-width: 260px;
    }}
    .link-button {{
      border: 1px solid rgba(17,20,15,.12);
      color: var(--ink);
      background: var(--panel);
      border-radius: 999px;
      padding: 10px 13px;
      text-decoration: none;
      font-size: 13px;
      font-weight: 800;
      box-shadow: 0 8px 28px rgba(0,0,0,.06);
    }}
    .ticker-link {{ color: #0f4029; font-weight: 900; text-decoration-thickness: 2px; text-underline-offset: 3px; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(5, minmax(140px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-top: 4px solid #a7aba1;
      border-radius: 16px;
      padding: 12px 14px;
      min-height: 70px;
      text-align: left;
      cursor: pointer;
      box-shadow: 0 10px 40px rgba(0,0,0,.06);
      transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }}
    .card:hover, .card.active {{ transform: translateY(-2px); box-shadow: var(--shadow); }}
    .card.active {{ outline: 2px solid rgba(17,20,15,.72); }}
    .card span {{ display: block; color: var(--muted); font-size: 11px; font-weight: 900; letter-spacing: .12em; margin-bottom: 6px; }}
    .card strong {{ font-size: 32px; line-height: 1; }}
    .card.buy {{ border-top-color: #1d9a55; }}
    .card.continue {{ border-top-color: #0891b2; }}
    .card.setup {{ border-top-color: #d69b00; }}
    .card.watch {{ border-top-color: #3f6fd5; }}
    .card.exit {{ border-top-color: #c93b32; }}
    .card.avoid {{ border-top-color: #777; }}
    .control-panel {{
      display: grid;
      grid-template-columns: minmax(220px, 1fr) repeat(3, auto);
      gap: 10px;
      align-items: center;
      background: rgba(255,255,250,.78);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 10px;
      margin-bottom: 12px;
      box-shadow: 0 12px 45px rgba(0,0,0,.07);
      backdrop-filter: blur(12px);
    }}
    input, select, .pill {{
      border: 1px solid rgba(17,20,15,.12);
      border-radius: 999px;
      background: #fffef7;
      color: var(--ink);
      font: inherit;
      font-size: 13px;
      font-weight: 700;
      padding: 10px 12px;
    }}
    input[type="search"] {{ width: 100%; }}
    .pill {{ cursor: pointer; }}
    .pill.active {{ background: #1e211b; color: #fff; }}
    .visible-count {{ color: var(--muted); font-size: 13px; font-weight: 800; text-align: right; white-space: nowrap; }}
    .table-wrap {{
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: var(--panel);
      max-height: calc(100vh - 230px);
      box-shadow: var(--shadow);
    }}
    table {{ border-collapse: separate; border-spacing: 0; width: 100%; font-size: 12px; font-family: Avenir Next, ui-sans-serif, system-ui, sans-serif; }}
    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      white-space: nowrap;
      background: inherit;
    }}
    th {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: #20221f;
      color: #fff;
      font-size: 11px;
      font-weight: 650;
      cursor: pointer;
      user-select: none;
    }}
    th.sorted::after {{ content: " ↓"; opacity: .7; }}
    th[data-col="ticker"], td[data-col="ticker"] {{
      position: sticky;
      left: 0;
      z-index: 3;
      font-weight: 700;
      background: inherit;
      min-width: 68px;
    }}
    th[data-col="name"], td[data-col="name"] {{
      position: sticky;
      left: 68px;
      z-index: 3;
      background: inherit;
      min-width: 170px;
      max-width: 170px;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    th[data-col="ticker"], th[data-col="name"] {{ z-index: 4; background: #20221f; }}
    td[data-col="score"], td[data-col="hist_win_rate"], td[data-col="hist_avg_return"],
    td[data-col="hist_trades"], td[data-col="close"], td[data-col="day_change_pct"],
    td[data-col="entry_est"], td[data-col="stop_est"], td[data-col="target_est"],
    td[data-col="rsi"], td[data-col="atr_pct"], td[data-col="reward_risk"] {{
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}
    td[data-col="score"] {{ font-weight: 800; color: #111; }}
    td[data-col="setup"], td[data-col="adaptive_mode"], td[data-col="psychology"] {{ text-align: center; }}
    tr.buy {{ background: var(--buy); }}
    tr.continue {{ background: #d7f4ff; }}
    tr.setup {{ background: var(--setup); }}
    tr.exit {{ background: var(--exit); }}
    tr.watch {{ background: var(--watch); }}
    tr.avoid {{ background: var(--avoid); color: #62665f; }}
    tr.hidden {{ display: none; }}
    tr:hover td {{ filter: brightness(0.97); }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      min-width: 42px;
      justify-content: center;
      padding: 2px 7px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      border: 1px solid rgba(0,0,0,.08);
      background: #f4f4f1;
    }}
    .badge.buy {{ color: #0b6b39; background: #ccefd9; }}
    .badge.continue {{ color: #075985; background: #cff3ff; }}
    .badge.setup {{ color: #866000; background: #ffe5a3; }}
    .badge.watch {{ color: #214eaa; background: #d7e4ff; }}
    .badge.exit {{ color: #9b2018; background: #ffd0cc; }}
    .badge.avoid {{ color: #555; background: #dfdfdc; }}
    .badge.psych {{ color: #235458; background: #d6f1ef; }}
    .mode {{ font-weight: 700; color: #30342e; }}
    .dash {{ color: #999; }}
    @media (max-width: 900px) {{
      .page {{ padding: 10px; }}
      .cards {{ grid-template-columns: repeat(2, minmax(140px, 1fr)); }}
      .topbar, .control-panel {{ display: block; }}
      .actions {{ justify-content: flex-start; margin-top: 14px; }}
      .control-panel > * {{ margin-bottom: 8px; width: 100%; }}
      h1 {{ font-size: 20px; }}
      .table-wrap {{ max-height: none; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <div class="topbar">
      <div>
        <p class="eyebrow">Daily trading cockpit</p>
        <h1>Watchlist</h1>
        <div class="meta">{meta_line}</div>
        {status_block}
        {preflight_block}
      </div>
      <div class="actions">
        <a class="link-button" href="daily_watchlist_overview_latest.csv">Download CSV</a>
        <a class="link-button" href="history.html?ticker=ORCL">30-Day History</a>
        <a class="link-button" href="https://github.com/yubobo815/daily-watchlist-cloud/actions/workflows/daily-watchlist-pages.yml">Refresh history</a>
      </div>
    </div>
    <section class="cards">{cards}</section>
    <section class="control-panel" aria-label="Watchlist controls">
      <input id="search" type="search" placeholder="Search ticker, setup, note, mode..." autocomplete="off">
      <button class="pill active" type="button" data-filter="all">All</button>
      <select id="sort">
        <option value="score-desc">Score high to low</option>
        <option value="change-desc">Best day change</option>
        <option value="change-asc">Worst day change</option>
        <option value="ticker-asc">Ticker A to Z</option>
      </select>
      <div class="visible-count"><span id="visibleCount">{len(rows)}</span> / {len(rows)} shown</div>
    </section>
    <section class="table-wrap">
      <table id="watchTable">
        <thead><tr>{header}</tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>
  </main>
  <script>
    const rows = Array.from(document.querySelectorAll("#watchTable tbody tr"));
    const search = document.querySelector("#search");
    const sort = document.querySelector("#sort");
    const visibleCount = document.querySelector("#visibleCount");
    const filterButtons = Array.from(document.querySelectorAll("[data-filter]"));
    let activeFilter = "all";

    function rowMatches(row) {{
      const term = search.value.trim().toLowerCase();
      const actionOk = activeFilter === "all" || row.dataset.action === activeFilter;
      const searchOk = !term || row.dataset.search.includes(term);
      return actionOk && searchOk;
    }}

    function sortRows() {{
      const [field, direction] = sort.value.split("-");
      const multiplier = direction === "asc" ? 1 : -1;
      const tbody = document.querySelector("#watchTable tbody");
      rows.sort((a, b) => {{
        if (field === "ticker") {{
          return a.dataset.ticker.localeCompare(b.dataset.ticker) * multiplier;
        }}
        const key = field === "change" ? "change" : "score";
        const av = Number.parseFloat(a.dataset[key]) || 0;
        const bv = Number.parseFloat(b.dataset[key]) || 0;
        return (av - bv) * multiplier;
      }});
      rows.forEach((row) => tbody.appendChild(row));
    }}

    function applyFilters() {{
      sortRows();
      let visible = 0;
      rows.forEach((row) => {{
        const show = rowMatches(row);
        row.classList.toggle("hidden", !show);
        if (show) visible += 1;
      }});
      visibleCount.textContent = visible;
      filterButtons.forEach((button) => button.classList.toggle("active", button.dataset.filter === activeFilter));
    }}

    filterButtons.forEach((button) => {{
      button.addEventListener("click", () => {{
        activeFilter = button.dataset.filter;
        applyFilters();
      }});
    }});
    search.addEventListener("input", applyFilters);
    sort.addEventListener("change", applyFilters);
    document.querySelectorAll("th").forEach((th) => {{
      th.addEventListener("click", () => {{
        const col = th.dataset.col;
        if (col === "ticker") sort.value = "ticker-asc";
        if (col === "score") sort.value = "score-desc";
        if (col === "day_change_pct") sort.value = "change-desc";
        document.querySelectorAll("th").forEach((node) => node.classList.remove("sorted"));
        th.classList.add("sorted");
        applyFilters();
      }});
    }});
    applyFilters();
  </script>
</body>
</html>
"""
    path.write_text(html_page)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a daily stock/ETF watchlist overview.")
    parser.add_argument("--watchlist", default="daily_watchlist.txt")
    parser.add_argument("--refresh", action="store_true", help="Fetch fresh Yahoo data instead of using cached CSV files.")
    parser.add_argument("--years", type=int, default=3)
    parser.add_argument("--history-days", type=int, default=30, help="Number of recent trading days to include in behavior history.")
    parser.add_argument("--no-supabase", action="store_true", help="Skip Supabase sync even if credentials are configured.")
    args = parser.parse_args()

    tickers = read_watchlist(Path(args.watchlist))
    live_access_ok = True
    live_access_message = "Live Yahoo access available."
    if args.refresh:
        live_access_ok, live_access_message = check_live_data_access()

    rows = []
    history_rows = []
    failures = []
    stale_cache_fallbacks = []
    benchmark_frames: dict[str, pd.DataFrame] = {}
    for benchmark in ("SPY", "QQQ"):
        try:
            if args.refresh and not live_access_ok:
                benchmark_frames[benchmark] = cached_chart(benchmark, years=args.years)
            else:
                benchmark_frames[benchmark] = fetch_chart(benchmark, years=args.years, refresh=args.refresh)
        except Exception as exc:
            print(f"Benchmark context unavailable for {benchmark}: {exc}")

    for ticker in tickers:
        try:
            if args.refresh and not live_access_ok:
                df = cached_chart(ticker, years=args.years)
                stale_cache_fallbacks.append(
                    {"ticker": display_ticker(ticker), "error": live_access_message}
                )
            else:
                df = fetch_chart(ticker, years=args.years, refresh=args.refresh)
            row = classify_and_score(ticker, df)
            ticker_history = build_behavior_history(ticker, df, days=args.history_days)
            row = apply_latest_signal_context(row, ticker_history)
            row.update(fetch_company_profile(ticker, refresh=args.refresh and live_access_ok))
            row = apply_quality_overlays(row, market_context_for(df, benchmark_frames))
            rows.append(row)
            history_rows.extend(ticker_history)
        except URLError as exc:
            if not args.refresh:
                failures.append({"ticker": display_ticker(ticker), "error": str(exc)})
                continue
            try:
                df = cached_chart(ticker, years=args.years)
                row = classify_and_score(ticker, df)
                ticker_history = build_behavior_history(ticker, df, days=args.history_days)
                row = apply_latest_signal_context(row, ticker_history)
                row.update(fetch_company_profile(ticker, refresh=False))
                row = apply_quality_overlays(row, market_context_for(df, benchmark_frames))
                rows.append(row)
                history_rows.extend(ticker_history)
                stale_cache_fallbacks.append(
                    {"ticker": display_ticker(ticker), "error": f"live refresh failed; used cache ({exc})"}
                )
            except Exception as cache_exc:
                failures.append({"ticker": display_ticker(ticker), "error": f"{exc}; fallback failed: {cache_exc}"})
        except Exception as exc:
            failures.append({"ticker": display_ticker(ticker), "error": str(exc)})

    if not rows:
        raise SystemExit("No symbols could be analyzed.")

    report = pd.DataFrame(rows)
    sort_score_col = "adjusted_score" if "adjusted_score" in report.columns else "score"
    report = report.sort_values([sort_score_col, "score", "action", "ticker"], ascending=[False, False, True, True]).reset_index(drop=True)

    today = local_run_date()
    csv_path = Path(f"daily_watchlist_overview_{today}.csv")
    html_path = Path(f"daily_watchlist_overview_{today}.html")
    report.to_csv(csv_path, index=False)
    data_dates = sorted(str(value) for value in pd.to_datetime(report["date"]).dt.date.unique())
    latest_data_date = data_dates[-1]
    earliest_data_date = data_dates[0]
    status_parts = [f"Report data as of {latest_data_date}"]
    if earliest_data_date != latest_data_date:
        status_parts.append(f"mixed source dates {earliest_data_date} to {latest_data_date}")
    if stale_cache_fallbacks:
        status_parts.append(f"{len(stale_cache_fallbacks)} symbols used cached data")
    if failures:
        status_parts.append(f"{len(failures)} symbols failed")
    status_text = " | ".join(status_parts)
    preflight_text = None if live_access_ok else f"{live_access_message} Running cache-backed refresh."
    run_status = "ok"
    if not live_access_ok or stale_cache_fallbacks:
        run_status = "degraded"
    if failures and not rows:
        run_status = "failed"
    run_metadata = {
        "run_date": today,
        "status": run_status,
        "live_access_ok": live_access_ok,
        "live_access_message": live_access_message,
        "earliest_data_date": earliest_data_date,
        "latest_data_date": latest_data_date,
        "symbols_total": len(tickers),
        "symbols_analyzed": len(rows),
        "symbols_failed": len(failures),
        "symbols_stale_cache": len(stale_cache_fallbacks),
        "snapshot_rows": len(report),
        "history_rows": len(history_rows),
        "scanner_version": SCANNER_VERSION,
        "notes": status_text,
        "payload": {
            "failures": failures[:25],
            "stale_cache_fallbacks": stale_cache_fallbacks[:25],
        },
    }

    write_html(report, html_path, status_text=status_text, preflight_text=preflight_text)
    report.to_csv("daily_watchlist_overview_latest.csv", index=False)
    write_html(report, Path("daily_watchlist_overview_latest.html"), status_text=status_text, preflight_text=preflight_text)

    history = pd.DataFrame(history_rows)
    if not history.empty:
        history = history.sort_values(["ticker", "date"]).reset_index(drop=True)
        history_path = Path(f"watchlist_behavior_history_{today}.csv")
        history.to_csv(history_path, index=False)
        history.to_csv("watchlist_behavior_history_latest.csv", index=False)
        write_history_html(Path("history.html"))
    elif Path("watchlist_behavior_history_latest.csv").exists():
        Path("watchlist_behavior_history_latest.csv").unlink()

    if failures:
        pd.DataFrame(failures).to_csv("daily_watchlist_overview_failures.csv", index=False)
    elif Path("daily_watchlist_overview_failures.csv").exists():
        Path("daily_watchlist_overview_failures.csv").unlink()

    if stale_cache_fallbacks:
        pd.DataFrame(stale_cache_fallbacks).to_csv("daily_watchlist_overview_stale_cache.csv", index=False)
    elif Path("daily_watchlist_overview_stale_cache.csv").exists():
        Path("daily_watchlist_overview_stale_cache.csv").unlink()

    if not args.no_supabase:
        sync_supabase(report, history, today, run_metadata)

    columns = ["ticker", "action", "setup", "adaptive_mode", "psychology", "score", "close", "day_change_pct", "notes"]
    print(report[columns].to_string(index=False))
    print(live_access_message)
    print(f"\nWrote {csv_path}, {html_path}, daily_watchlist_overview_latest.csv, daily_watchlist_overview_latest.html, watchlist_behavior_history_latest.csv, and history.html")
    if failures:
        print(f"Skipped {len(failures)} symbol(s); see daily_watchlist_overview_failures.csv")
    if stale_cache_fallbacks:
        print(f"Used cached data for {len(stale_cache_fallbacks)} symbol(s); see daily_watchlist_overview_stale_cache.csv")


if __name__ == "__main__":
    main()
