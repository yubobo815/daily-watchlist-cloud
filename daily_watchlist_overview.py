import argparse
import base64
import http.cookiejar
import html
import hashlib
import itertools
import json
import math
import os
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError
from typing import Optional
from datetime import date as date_cls, datetime, time as time_cls, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from pandas.tseries.holiday import (
    AbstractHolidayCalendar,
    GoodFriday,
    Holiday,
    USLaborDay,
    USMartinLutherKingJr,
    USMemorialDay,
    USPresidentsDay,
    USThanksgivingDay,
    nearest_workday,
)


ETF_HINTS = {
    "SPY", "QQQ", "DIA", "IWM", "SMH", "VGT", "XLK", "XLE", "XLF", "XLV",
    "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "ARKK", "SOXX", "IBB",
    "TLT", "GLD", "SLV", "USO", "DRAM",
}

RUN_TIMEZONE = ZoneInfo("Australia/Melbourne")
MARKET_TIMEZONE = ZoneInfo("America/New_York")
US_MARKET_CLOSE_TIME = time_cls(16, 0)
SCANNER_VERSION = "2026.07.22-execution-fillability"
LEARNING_MODEL_VERSION = "five-session-execution-v6"
INCREMENTAL_STATE_VERSION = "incremental-state-v1"
INDICATOR_STATE_VERSION = "indicator-state-v1"
CALIBRATION_ARTIFACT_VERSION = "calibration-artifact-v1"
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
CLIMAX_MOVE_MULTIPLE = 2.0
CLIMAX_RETURN_ATR = 1.15
CLIMAX_MIN_EVIDENCE = 3
MATURE_CHASE_MOVE_MULTIPLE = 1.25
MATURE_CHASE_RETURN_ATR = 0.55
MATURE_CHASE_RETURN_20D_PCT = 15.0
MATURE_CHASE_EMA_EXTENSION_ATR = 1.25
SCANNER_RISK_DOLLARS = 1000.0
MAX_SCANNER_POSITION_VALUE = 25000.0
MAX_SIGNAL_RISK_PCT = 7.0
NUMERIC_TOLERANCE = 1e-6
TICKER_EDGE_MIN_TRADES = 6
WALK_FORWARD_MIN_TEST_TRADES = 3
MAX_EXECUTION_DATA_AGE_DAYS = int(os.getenv("MAX_EXECUTION_DATA_AGE_DAYS", "0"))
TOP_BUY_TIER_LIMIT = int(os.getenv("TOP_BUY_TIER_LIMIT", "8"))
BUY_WATCH_TIER_LIMIT = int(os.getenv("BUY_WATCH_TIER_LIMIT", "24"))
LEARNING_LOOKBACK_DAYS = int(os.getenv("LEARNING_LOOKBACK_DAYS", "60"))
DEFAULT_LEARNING_LOOKBACK_DAYS = LEARNING_LOOKBACK_DAYS
LEARNING_HORIZON_SESSIONS = int(os.getenv("LEARNING_HORIZON_SESSIONS", "5"))
# Historical replay recalculates expensive per-ticker and walk-forward gates on
# this cadence. Between refreshes, only earlier replay sessions are reusable.
REPLAY_AUDIT_GATE_REFRESH_BARS = int(os.getenv("REPLAY_AUDIT_GATE_REFRESH_BARS", "5"))
MARKET_DATA_TIMEOUT_SECONDS = int(os.getenv("MARKET_DATA_TIMEOUT_SECONDS", "12"))
SELF_SCORE_ACTIONS = {
    "BUY CANDIDATE",
    "STRONG CONTINUATION",
    "SETUP FORMING",
    "WATCH TREND",
    "EXIT PRESSURE",
    "WAIT",
    "WAIT / AVOID",
}
SELF_SCORE_WORKING_RETURN_PCT = 2.0
SELF_SCORE_FAILED_RETURN_PCT = -2.0
SELF_SCORE_EXIT_AVOIDED_RETURN_PCT = -1.0
LEARNING_MIN_SAMPLES = int(os.getenv("LEARNING_MIN_SAMPLES", "3"))
LEARNING_ADJUSTMENT_CAP = float(os.getenv("LEARNING_ADJUSTMENT_CAP", "10"))
FILLABILITY_MIN_SAMPLES = int(os.getenv("FILLABILITY_MIN_SAMPLES", "8"))
FILLABILITY_MIN_DISTINCT_TICKERS = int(os.getenv("FILLABILITY_MIN_DISTINCT_TICKERS", "4"))
FILLABILITY_MIN_EVALUATION_DATES = int(os.getenv("FILLABILITY_MIN_EVALUATION_DATES", "4"))
FILLABILITY_MIN_RATE = float(os.getenv("FILLABILITY_MIN_RATE", "0.45"))
LEARNING_CONFIRM_MIN_SAMPLES = int(os.getenv("LEARNING_CONFIRM_MIN_SAMPLES", "30"))
LEARNING_CONFIRM_MIN_WORKING_RATE = float(os.getenv("LEARNING_CONFIRM_MIN_WORKING_RATE", "0.60"))
LEARNING_CONFIRM_MAX_FAILED_RATE = float(os.getenv("LEARNING_CONFIRM_MAX_FAILED_RATE", "0.25"))
LEARNING_CONFIRM_MIN_ADJUSTMENT = float(os.getenv("LEARNING_CONFIRM_MIN_ADJUSTMENT", "2.0"))
LEARNING_CONFIRM_MIN_SCORE = float(os.getenv("LEARNING_CONFIRM_MIN_SCORE", "78.0"))
LEARNING_CONFIRM_MIN_DISTINCT_TICKERS = int(os.getenv("LEARNING_CONFIRM_MIN_DISTINCT_TICKERS", "8"))
LEARNING_CONFIRM_MIN_EVALUATION_DATES = int(os.getenv("LEARNING_CONFIRM_MIN_EVALUATION_DATES", "10"))
LEARNING_CALIBRATION_MIN_SAMPLES = int(os.getenv("LEARNING_CALIBRATION_MIN_SAMPLES", "30"))
LEARNING_CALIBRATION_MAX_BRIER = float(os.getenv("LEARNING_CALIBRATION_MAX_BRIER", "0.62"))
DIRECTIONAL_MODEL_VERSION = "ohlcv-ridge-v1"
DIRECTIONAL_MODEL_MIN_TRAIN_SAMPLES = int(os.getenv("DIRECTIONAL_MODEL_MIN_TRAIN_SAMPLES", "200"))
DIRECTIONAL_MODEL_MIN_OOS_SAMPLES = int(os.getenv("DIRECTIONAL_MODEL_MIN_OOS_SAMPLES", "1000"))
DIRECTIONAL_MODEL_MIN_OOS_DATES = int(os.getenv("DIRECTIONAL_MODEL_MIN_OOS_DATES", "40"))
DIRECTIONAL_MODEL_MIN_PERSONALITY_SAMPLES = int(os.getenv("DIRECTIONAL_MODEL_MIN_PERSONALITY_SAMPLES", "200"))
DIRECTIONAL_MODEL_MIN_PERSONALITY_DATES = int(os.getenv("DIRECTIONAL_MODEL_MIN_PERSONALITY_DATES", "30"))
DIRECTIONAL_MODEL_MIN_BRIER_SKILL = float(os.getenv("DIRECTIONAL_MODEL_MIN_BRIER_SKILL", "0.03"))
DIRECTIONAL_MODEL_RIDGE = float(os.getenv("DIRECTIONAL_MODEL_RIDGE", "12.0"))
DIRECTIONAL_RAW_LOOKBACK_DAYS = int(os.getenv("DIRECTIONAL_RAW_LOOKBACK_DAYS", "60"))
DIRECTIONAL_REFIT_INTERVAL_DAYS = int(os.getenv("DIRECTIONAL_REFIT_INTERVAL_DAYS", "5"))
POST_EXIT_COOLDOWN_BARS = int(os.getenv("POST_EXIT_COOLDOWN_BARS", "2"))
POST_EXIT_RECLAIM_MIN_PCT = float(os.getenv("POST_EXIT_RECLAIM_MIN_PCT", "6"))
POST_EXIT_RISK_PERSISTENCE_BARS = int(os.getenv("POST_EXIT_RISK_PERSISTENCE_BARS", "3"))
PROFIT_PROTECT_LOOKBACK_BARS = int(os.getenv("PROFIT_PROTECT_LOOKBACK_BARS", "5"))
PROFIT_PROTECT_TRIGGER_GAIN_PCT = float(os.getenv("PROFIT_PROTECT_TRIGGER_GAIN_PCT", "7"))
PROFIT_PROTECT_GIVEBACK_PCT = float(os.getenv("PROFIT_PROTECT_GIVEBACK_PCT", "4"))
PROFIT_PROTECT_SUPPLY_SCORE = float(os.getenv("PROFIT_PROTECT_SUPPLY_SCORE", "45"))
VOLATILE_TREND_MAX_SUPPLY_SCORE = float(os.getenv("VOLATILE_TREND_MAX_SUPPLY_SCORE", "45"))
DATA_PROVIDER_PRIORITY = [
    provider.strip().lower()
    for provider in os.getenv("DATA_PROVIDER_PRIORITY", "polygon,twelvedata,stooq,yahoo").split(",")
    if provider.strip()
]
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY") or os.getenv("MASSIVE_API_KEY") or ""
POLYGON_BASE_URL = (
    os.getenv("POLYGON_BASE_URL")
    or ("https://api.massive.com" if os.getenv("MASSIVE_API_KEY") and not os.getenv("POLYGON_API_KEY") else "https://api.polygon.io")
).rstrip("/")
POLYGON_PROVIDER_LABEL = "massive" if os.getenv("MASSIVE_API_KEY") and not os.getenv("POLYGON_API_KEY") else "polygon"
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")

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


def canonical_date(value: object) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    return "" if pd.isna(parsed) else str(parsed.date())


def resolve_refresh_mode(requested: str, now: Optional[datetime] = None) -> str:
    requested_mode = str(requested or "auto").strip().lower()
    if requested_mode in {"daily", "weekly_rebuild"}:
        return requested_mode
    if requested_mode != "auto":
        raise ValueError(f"Unsupported refresh mode: {requested}")
    local_now = now.astimezone(RUN_TIMEZONE) if now else datetime.now(RUN_TIMEZONE)
    # Saturday Melbourne follows the Friday US session and is the natural
    # weekly calibration boundary.
    return "weekly_rebuild" if local_now.weekday() == 5 else "daily"


def cache_path_for(ticker: str, years: int) -> Path:
    safe_ticker = ticker.replace("^", "_").replace("/", "_").replace(".", "_")
    return Path(f"watchlist_{safe_ticker}_{years}y.csv")


def attach_data_provider(
    df: pd.DataFrame,
    provider: str,
    status: str,
    error: str = "",
    latency_ms: Optional[float] = None,
) -> pd.DataFrame:
    df.attrs["data_provider"] = provider
    df.attrs["data_provider_status"] = status
    df.attrs["data_provider_error"] = error
    df.attrs["data_provider_latency_ms"] = latency_ms
    return df


def data_provider_context(df: pd.DataFrame) -> dict:
    return {
        "data_provider": df.attrs.get("data_provider", ""),
        "data_provider_status": df.attrs.get("data_provider_status", ""),
        "data_provider_error": df.attrs.get("data_provider_error", ""),
        "data_provider_latency_ms": numeric_or_none(df.attrs.get("data_provider_latency_ms")),
    }


def ohlcv_window_hash(df: pd.DataFrame) -> str:
    columns = [column for column in ("date", "open", "high", "low", "close", "volume") if column in df.columns]
    canonical = df[columns].tail(OHLCV_RETENTION_BARS).copy()
    if "date" in canonical:
        canonical["date"] = pd.to_datetime(canonical["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    records = clean_json_value(canonical.to_dict(orient="records"))
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def apply_data_provider_context(row: dict, df: pd.DataFrame) -> dict:
    row.update(data_provider_context(df))
    return row


def apply_data_provider_context_to_rows(rows: list[dict], df: pd.DataFrame) -> list[dict]:
    context = data_provider_context(df)
    for row in rows:
        row.update(context)
    return rows


def record_stale_cache_fallback(fallbacks: list[dict], ticker: str, df: pd.DataFrame, fallback_reason: str = "") -> None:
    if df.attrs.get("data_provider") != "cache":
        return
    display = display_ticker(ticker)
    if any(str(item.get("ticker", "")).upper() == display.upper() for item in fallbacks):
        return
    reason = fallback_reason or df.attrs.get("data_provider_error") or df.attrs.get("data_provider_status") or "used cached data"
    fallbacks.append({"ticker": display, "error": reason})


def normalize_provider_ticker(ticker: str, provider: str) -> str:
    symbol = display_ticker(ticker)
    if provider == "polygon":
        return symbol
    if provider == "twelvedata":
        return symbol
    return ticker


def request_json(url: str, provider: str, timeout: int = 30) -> tuple[dict, float]:
    started = time.perf_counter()
    req = urllib.request.Request(url, headers={"User-Agent": "DailyTradeCopilot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"{provider} HTTP {exc.code}: {body}") from exc
    return payload, round((time.perf_counter() - started) * 1000, 1)


def market_dates_from_timestamps(values, unit: str) -> list:
    timestamps = pd.to_datetime(values, unit=unit, utc=True, errors="coerce")
    return list(timestamps.tz_convert(MARKET_TIMEZONE).date)


def fetch_polygon_chart(ticker: str, years: int = 3) -> pd.DataFrame:
    if not POLYGON_API_KEY:
        raise RuntimeError("Polygon/Massive API key is not configured.")
    symbol = urllib.parse.quote(normalize_provider_ticker(ticker, "polygon"), safe="")
    to_date = datetime.utcnow().date()
    from_date = (datetime.utcnow() - timedelta(days=int(years * 365.25) + 10)).date()
    params = urllib.parse.urlencode(
        {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
            "apiKey": POLYGON_API_KEY,
        }
    )
    url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{symbol}/range/1/day/{from_date}/{to_date}?{params}"
    payload, latency_ms = request_json(url, "polygon", timeout=MARKET_DATA_TIMEOUT_SECONDS)
    results = payload.get("results") or []
    if not results:
        message = payload.get("error") or payload.get("message") or "no aggregate bars returned"
        raise RuntimeError(f"Polygon/Massive returned no bars for {display_ticker(ticker)}: {message}")
    df = pd.DataFrame(
        {
            "date": market_dates_from_timestamps([item.get("t") for item in results], "ms"),
            "open": [item.get("o") for item in results],
            "high": [item.get("h") for item in results],
            "low": [item.get("l") for item in results],
            "close": [item.get("c") for item in results],
            "adjclose": [item.get("c") for item in results],
            "volume": [item.get("v") for item in results],
        }
    )
    df = df.dropna(subset=["open", "high", "low", "close", "volume"]).reset_index(drop=True)
    if df.empty:
        raise RuntimeError(f"Polygon/Massive returned only incomplete bars for {display_ticker(ticker)}.")
    return attach_data_provider(df, POLYGON_PROVIDER_LABEL, "LIVE_OK", latency_ms=latency_ms)


def fetch_twelvedata_chart(ticker: str, years: int = 3) -> pd.DataFrame:
    if not TWELVE_DATA_API_KEY:
        raise RuntimeError("Twelve Data API key is not configured.")
    outputsize = min(max(int(years * 260) + 20, 30), 5000)
    params = urllib.parse.urlencode(
        {
            "symbol": normalize_provider_ticker(ticker, "twelvedata"),
            "interval": "1day",
            "outputsize": outputsize,
            "format": "JSON",
            "apikey": TWELVE_DATA_API_KEY,
        }
    )
    payload, latency_ms = request_json(f"https://api.twelvedata.com/time_series?{params}", "twelvedata", timeout=MARKET_DATA_TIMEOUT_SECONDS)
    if str(payload.get("status", "")).lower() == "error":
        raise RuntimeError(payload.get("message") or "Twelve Data returned error status.")
    values = payload.get("values") or []
    if not values:
        raise RuntimeError(f"Twelve Data returned no bars for {display_ticker(ticker)}.")
    values = list(reversed(values))
    df = pd.DataFrame(
        {
            "date": pd.to_datetime([item.get("datetime") for item in values]).date,
            "open": [item.get("open") for item in values],
            "high": [item.get("high") for item in values],
            "low": [item.get("low") for item in values],
            "close": [item.get("close") for item in values],
            "adjclose": [item.get("close") for item in values],
            "volume": [item.get("volume") or 0 for item in values],
        }
    )
    for col in ["open", "high", "low", "close", "adjclose", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close", "volume"]).reset_index(drop=True)
    if df.empty:
        raise RuntimeError(f"Twelve Data returned only incomplete bars for {display_ticker(ticker)}.")
    return attach_data_provider(df, "twelvedata", "LIVE_OK", latency_ms=latency_ms)


def stooq_symbol(ticker: str) -> str:
    symbol = display_ticker(ticker).lower()
    if "." not in symbol:
        return f"{symbol}.us"
    if symbol.endswith(".ax"):
        return symbol
    return f"{symbol.replace('.', '-')}.us"


def fetch_stooq_chart(ticker: str, years: int = 3) -> pd.DataFrame:
    to_date = datetime.utcnow().date()
    from_date = (datetime.utcnow() - timedelta(days=int(years * 365.25) + 10)).date()
    params = urllib.parse.urlencode(
        {
            "s": stooq_symbol(ticker),
            "d1": from_date.strftime("%Y%m%d"),
            "d2": to_date.strftime("%Y%m%d"),
            "i": "d",
        }
    )
    started = time.perf_counter()
    req = urllib.request.Request(f"https://stooq.com/q/d/l/?{params}", headers={"User-Agent": "DailyTradeCopilot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=MARKET_DATA_TIMEOUT_SECONDS) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"stooq HTTP {exc.code}: {body}") from exc
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    if "No data" in body or not body.strip():
        raise RuntimeError(f"Stooq returned no bars for {display_ticker(ticker)}.")
    rows = [line.split(",") for line in body.strip().splitlines()]
    if len(rows) < 2 or rows[0][:6] != ["Date", "Open", "High", "Low", "Close", "Volume"]:
        raise RuntimeError(f"Stooq returned an unexpected response for {display_ticker(ticker)}.")
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df = df.rename(columns={"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["adjclose"] = df["close"]
    df = df[["date", "open", "high", "low", "close", "adjclose", "volume"]].dropna(subset=["date", "open", "high", "low", "close", "volume"]).reset_index(drop=True)
    if df.empty:
        raise RuntimeError(f"Stooq returned only incomplete bars for {display_ticker(ticker)}.")
    return attach_data_provider(df, "stooq", "LIVE_OK", latency_ms=latency_ms)


def fetch_yahoo_chart(ticker: str, years: int = 3) -> pd.DataFrame:
    period2 = int(time.time())
    period1 = period2 - int(years * 365.25 * 24 * 60 * 60)
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?period1={period1}&period2={period2}&interval=1d&events=history"
    )
    payload, latency_ms = request_json(url, "yahoo", timeout=MARKET_DATA_TIMEOUT_SECONDS)
    result = payload["chart"]["result"][0]
    q = result["indicators"]["quote"][0]
    adj = result["indicators"].get("adjclose", [{}])[0].get("adjclose", q["close"])
    df = pd.DataFrame(
        {
            "date": market_dates_from_timestamps(result["timestamp"], "s"),
            "open": q["open"],
            "high": q["high"],
            "low": q["low"],
            "close": q["close"],
            "adjclose": adj,
            "volume": q["volume"],
        }
    )
    df = df.dropna(subset=["open", "high", "low", "close", "volume"]).reset_index(drop=True)
    return attach_data_provider(df, "yahoo", "LIVE_OK", latency_ms=latency_ms)


def configured_data_providers() -> list[str]:
    providers: list[str] = []
    for provider in DATA_PROVIDER_PRIORITY:
        if provider in {"polygon", "massive"} and "polygon" not in providers:
            providers.append("polygon")
        elif provider in {"twelvedata", "twelve_data", "twelve-data"} and "twelvedata" not in providers:
            providers.append("twelvedata")
        elif provider == "stooq" and "stooq" not in providers:
            providers.append("stooq")
        elif provider == "yahoo" and "yahoo" not in providers:
            providers.append("yahoo")
    return providers or ["polygon", "twelvedata", "stooq", "yahoo"]


def fetch_live_chart_from_provider(provider: str, ticker: str, years: int = 3) -> pd.DataFrame:
    if provider == "polygon":
        return fetch_polygon_chart(ticker, years)
    if provider == "twelvedata":
        return fetch_twelvedata_chart(ticker, years)
    if provider == "stooq":
        return fetch_stooq_chart(ticker, years)
    if provider == "yahoo":
        return fetch_yahoo_chart(ticker, years)
    raise RuntimeError(f"Unsupported data provider: {provider}")


def fetch_chart(ticker: str, years: int = 3, refresh: bool = False) -> pd.DataFrame:
    cache_path = cache_path_for(ticker, years)
    if cache_path.exists() and not refresh:
        return attach_data_provider(pd.read_csv(cache_path, parse_dates=["date"]), "cache", "CACHE_READ")

    errors: list[str] = []
    for provider in configured_data_providers():
        try:
            df = fetch_live_chart_from_provider(provider, ticker, years)
            reject_stale_live_frame(df, ticker, provider)
            df.to_csv(cache_path, index=False)
            return df
        except Exception as exc:
            errors.append(f"{provider}: {exc}")

    if cache_path.exists():
        return attach_data_provider(
            pd.read_csv(cache_path, parse_dates=["date"]),
            "cache",
            "CACHE_FALLBACK",
            "; ".join(errors),
        )

    raise RuntimeError("; ".join(errors) or f"No data providers available for {display_ticker(ticker)}.")


def cached_chart(ticker: str, years: int = 3) -> pd.DataFrame:
    cache_path = cache_path_for(ticker, years)
    if not cache_path.exists():
        raise FileNotFoundError(f"cache not found: {cache_path}")
    return attach_data_provider(pd.read_csv(cache_path, parse_dates=["date"]), "cache", "CACHE_READ")


def check_live_data_access() -> tuple[bool, str]:
    errors: list[str] = []
    for provider in configured_data_providers():
        try:
            df = fetch_live_chart_from_provider(provider, "AAPL", years=1)
            latest = str(pd.to_datetime(df["date"]).dt.date.max())
            return True, f"Live {provider} access available; AAPL latest bar {latest}."
        except Exception as exc:
            errors.append(f"{provider}: {exc}")
    return False, "Live market data unavailable from configured providers: " + " | ".join(errors)


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


def is_affirmative(value: object) -> bool:
    return value is True or str(value or "").strip().upper() in {"YES", "TRUE", "1"}


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


def supabase_select(path: str) -> list[dict]:
    url, key = supabase_credentials()
    if not url or not key:
        return []

    endpoint = f"{url}/rest/v1/{path}"
    req = urllib.request.Request(endpoint, method="GET", headers=supabase_headers(key))
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Supabase select returned HTTP {resp.status}")
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"Supabase select failed with HTTP {exc.code}: {body}") from exc


OPTIONAL_REFRESH_RUN_COLUMNS = {
    "learning_history_rows",
}

OPTIONAL_OUTCOME_COLUMNS = {
    "forecast_learnable",
    "prior_prediction_key",
    "prior_prediction_scope",
}

# Each table has a different job. A single blanket retention window made the
# replay table grow by every ticker x every replay day x every scanner run.
SUPABASE_SNAPSHOT_RETENTION_DAYS = int(os.getenv("SUPABASE_SNAPSHOT_RETENTION_DAYS", "14"))
SUPABASE_OUTCOME_RETENTION_DAYS = int(os.getenv("SUPABASE_OUTCOME_RETENTION_DAYS", "120"))
SUPABASE_REFRESH_RUN_RETENTION_DAYS = int(os.getenv("SUPABASE_REFRESH_RUN_RETENTION_DAYS", "60"))
SUPABASE_UPSERT_BATCH_SIZE = int(os.getenv("SUPABASE_UPSERT_BATCH_SIZE", "100"))
ALLOW_STALE_SUPABASE_SYNC = os.getenv("ALLOW_STALE_SUPABASE_SYNC", "").strip().lower() in {"1", "true", "yes"}
# 400 sessions covers indicator warm-up plus the 60-session learning replay,
# while keeping the persistent raw-data layer well below the database budget.
OHLCV_RETENTION_BARS = int(os.getenv("OHLCV_RETENTION_BARS", "400"))
OHLCV_MIN_READY_BARS = int(os.getenv("OHLCV_MIN_READY_BARS", str(OHLCV_RETENTION_BARS)))
OHLCV_INCREMENTAL_YEARS = float(os.getenv("OHLCV_INCREMENTAL_YEARS", "0.1"))
SUPABASE_SNAPSHOT_PAYLOAD_MAX_BYTES = int(os.getenv("SUPABASE_SNAPSHOT_PAYLOAD_MAX_BYTES", "8192"))
SUPABASE_HISTORY_PAYLOAD_MAX_BYTES = int(os.getenv("SUPABASE_HISTORY_PAYLOAD_MAX_BYTES", "6144"))
SUPABASE_OUTCOME_PAYLOAD_MAX_BYTES = int(os.getenv("SUPABASE_OUTCOME_PAYLOAD_MAX_BYTES", "2048"))


def should_sync_supabase_snapshot(report: pd.DataFrame, run_date: str) -> tuple[bool, str]:
    if ALLOW_STALE_SUPABASE_SYNC:
        return True, "ALLOW_STALE_SUPABASE_SYNC override enabled."
    if report.empty:
        return False, "No snapshot rows were produced."

    date_values = report["date"] if "date" in report.columns else pd.Series(dtype=str)
    latest_dates = pd.to_datetime(date_values, errors="coerce").dropna()
    if latest_dates.empty:
        return False, "No valid data_date values were produced."

    latest_data_date = str(latest_dates.dt.date.max())
    data_age_days = nyse_session_age(latest_data_date)
    if data_age_days is None or data_age_days > MAX_EXECUTION_DATA_AGE_DAYS:
        return False, (
            f"Latest market data is {data_age_days if data_age_days is not None else 'unknown'} NYSE session(s) old "
            f"({latest_data_date}); not overwriting Supabase snapshots."
        )

    stale_count = int((report.get("freshness_block", pd.Series(dtype=str)) == "YES").sum())
    if stale_count >= len(report):
        return False, "Every row is execution-blocked for stale data; not overwriting Supabase snapshots."

    return True, f"Latest market data is fresh enough for Supabase sync ({latest_data_date}, age {data_age_days} NYSE session(s))."


def batched_records(records: list[dict], batch_size: int = SUPABASE_UPSERT_BATCH_SIZE) -> list[list[dict]]:
    size = max(1, int(batch_size or 100))
    return [records[index : index + size] for index in range(0, len(records), size)]


def load_ohlcv_from_supabase(ticker: str) -> pd.DataFrame:
    """Load the compact persistent price cache; failure falls back to live data."""
    try:
        rows = supabase_select(
            "watchlist_ohlcv?select=data_date,open,high,low,close,adjclose,volume,data_provider"
            f"&ticker=eq.{urllib.parse.quote(display_ticker(ticker))}"
            "&order=data_date.desc"
            f"&limit={OHLCV_RETENTION_BARS}"
        )
    except RuntimeError as exc:
        print(f"OHLCV cache unavailable for {display_ticker(ticker)}: {exc}")
        return pd.DataFrame()
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows).rename(columns={"data_date": "date"})
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for column in ("open", "high", "low", "close", "adjclose", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return (
        frame.dropna(subset=["date", "open", "high", "low", "close", "volume"])
        .sort_values("date")
        .reset_index(drop=True)
    )


def persist_ohlcv_to_supabase(ticker: str, frame: pd.DataFrame) -> None:
    if frame.empty:
        return
    records = []
    for item in frame.tail(OHLCV_RETENTION_BARS).to_dict(orient="records"):
        records.append(
            {
                "ticker": display_ticker(ticker),
                "data_date": str(pd.Timestamp(item["date"]).date()),
                "open": numeric_or_none(item.get("open")),
                "high": numeric_or_none(item.get("high")),
                "low": numeric_or_none(item.get("low")),
                "close": numeric_or_none(item.get("close")),
                "adjclose": numeric_or_none(item.get("adjclose")),
                "volume": numeric_or_none(item.get("volume")),
                "data_provider": item.get("data_provider"),
            }
        )
    supabase_upsert_batches("watchlist_ohlcv", records, ["ticker", "data_date"])


def load_or_refresh_ohlcv(ticker: str, years: int, refresh: bool, force_full: bool = False) -> pd.DataFrame:
    """Use durable OHLCV locally, fetching a full seed only when it is absent."""
    stored = load_ohlcv_from_supabase(ticker) if refresh else pd.DataFrame()
    needs_seed = len(stored) < OHLCV_MIN_READY_BARS or force_full
    if not refresh and not stored.empty:
        return stored.tail(OHLCV_RETENTION_BARS).reset_index(drop=True)

    # Once seeded, request a short window and only write dates that are new or
    # recent enough to correct provider revisions. This keeps daily syncs small.
    try:
        live = fetch_chart(ticker, years=years if needs_seed else OHLCV_INCREMENTAL_YEARS, refresh=refresh)
    except Exception as exc:
        if stored.empty or force_full:
            raise
        return attach_data_provider(
            stored.tail(OHLCV_RETENTION_BARS).reset_index(drop=True),
            "cache",
            "STALE_FALLBACK",
            str(exc),
        )
    provider_context = data_provider_context(live)
    live = live.copy()
    live["data_provider"] = provider_context["data_provider"]
    combined = pd.concat([stored, live], ignore_index=True, sort=False)
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
    combined = combined.dropna(subset=["date", "open", "high", "low", "close", "volume"])
    combined = combined.sort_values("date").drop_duplicates("date", keep="last").tail(OHLCV_RETENTION_BARS).reset_index(drop=True)
    if needs_seed:
        persist_ohlcv_to_supabase(ticker, combined)
    else:
        latest_stored = pd.Timestamp(stored["date"].max())
        revision_start = latest_stored - pd.Timedelta(days=10)
        persist_ohlcv_to_supabase(ticker, live.loc[pd.to_datetime(live["date"]) >= revision_start])
    return attach_data_provider(
        combined,
        provider_context["data_provider"],
        provider_context["data_provider_status"],
        provider_context["data_provider_error"],
        provider_context["data_provider_latency_ms"],
    )


def supabase_upsert_batches(table: str, records: list[dict], conflict_columns: list[str]) -> None:
    for batch in batched_records(records):
        supabase_upsert(table, batch, conflict_columns)


def supabase_upsert_with_optional_outcome_columns(records: list[dict], conflict_columns: list[str]) -> None:
    try:
        supabase_upsert_batches("watchlist_signal_outcomes", records, conflict_columns)
        return
    except RuntimeError as exc:
        message = str(exc).lower()
        schema_cache_error = "could not find" in message or "schema cache" in message or "column" in message
        if not schema_cache_error:
            raise
        stripped_records = [
            {key: value for key, value in record.items() if key not in OPTIONAL_OUTCOME_COLUMNS}
            for record in records
        ]
        print("Supabase outcome calibration columns unavailable; storing them in payload only.")
        supabase_upsert_batches("watchlist_signal_outcomes", stripped_records, conflict_columns)


def supabase_upsert_refresh_run(records: list[dict]) -> None:
    try:
        supabase_upsert("watchlist_refresh_runs", records, ["publication_id"])
        return
    except RuntimeError as exc:
        message = str(exc).lower()
        schema_cache_error = "could not find" in message or "schema cache" in message or "column" in message
        has_optional_columns = any(OPTIONAL_REFRESH_RUN_COLUMNS.intersection(record) for record in records)
        if not schema_cache_error or not has_optional_columns:
            raise

        stripped_records = []
        for record in records:
            payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
            optional_payload = {
                key: record[key]
                for key in OPTIONAL_REFRESH_RUN_COLUMNS
                if key in record and record[key] is not None
            }
            stripped = {key: value for key, value in record.items() if key not in OPTIONAL_REFRESH_RUN_COLUMNS}
            stripped["payload"] = {**payload, **optional_payload}
            stripped_records.append(stripped)
        print("Supabase watchlist_refresh_runs optional health columns unavailable; storing full health in payload only.")
        supabase_upsert("watchlist_refresh_runs", stripped_records, ["publication_id"])


def compact_payload(row: dict, typed_record: dict, *, aliases: tuple[str, ...] = (), max_bytes: int) -> dict:
    """Keep only non-empty fields not already represented by typed columns."""
    excluded = set(typed_record).union(aliases, {"payload"})
    payload = {
        key: value
        for key, value in row.items()
        if key not in excluded and value not in (None, "", [], {})
    }
    payload_bytes = len(json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8"))
    if payload_bytes > max_bytes:
        raise ValueError(f"Compact Supabase payload is {payload_bytes} bytes; limit is {max_bytes} bytes.")
    return payload


def sync_supabase(
    report: pd.DataFrame,
    history: pd.DataFrame,
    outcomes: pd.DataFrame,
    run_date: str,
    run_metadata: Optional[dict] = None,
    calibration_artifact: Optional[dict] = None,
    learning_stats: Optional[dict[str, dict]] = None,
) -> None:
    url, key = supabase_credentials()
    if not url or not key:
        print("Supabase sync skipped: SUPABASE_URL and SUPABASE_SECRET_KEY are not set.")
        print("Legacy fallback: SUPABASE_SERVICE_ROLE_KEY is also supported.")
        return

    print(f"Supabase sync target: {urllib.parse.urlparse(url).netloc} ({describe_supabase_key(key)})")

    report_records = []
    indicator_records = []
    for record in report.to_dict(orient="records"):
        row = clean_record(record)
        report_record = {
            "publication_id": row.get("publication_id"),
            "run_date": run_date,
            "ticker": row.get("ticker"),
            "name": row.get("name"),
            "data_date": row.get("date"),
            "action": row.get("action"),
            "setup": row.get("setup"),
            "adaptive_mode": row.get("adaptive_mode"),
            "psychology": row.get("psychology"),
            "score": numeric_or_none(row.get("score")),
            "open": numeric_or_none(row.get("open")),
            "high": numeric_or_none(row.get("high")),
            "low": numeric_or_none(row.get("low")),
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
        }
        report_record["payload"] = compact_payload(
            row,
            report_record,
            aliases=("date",),
            max_bytes=SUPABASE_SNAPSHOT_PAYLOAD_MAX_BYTES,
        )
        report_records.append(report_record)
        indicator_fields = (
            "rsi", "atr_pct", "trend_efficiency", "buyer_score", "seller_score",
            "volume_state", "personality_type", "personality_atr_pct", "ema_alignment_clean",
            "slow_slope_up", "signed_volume_pressure_5", "demand_days_5", "supply_days_5",
            "accum_vol", "breakout_vol", "dist_vol", "breakdown_vol",
        )
        indicator_records.append({
            "publication_id": row.get("publication_id"),
            "ticker": row.get("ticker"),
            "data_date": row.get("date"),
            "state_version": row.get("indicator_state_version") or INDICATOR_STATE_VERSION,
            "scanner_version": SCANNER_VERSION,
            "raw_window_hash": row.get("raw_window_hash"),
            "payload": clean_record({key: row.get(key) for key in indicator_fields if row.get(key) not in (None, "")}),
        })

    history_records = []
    if not history.empty:
        for record in history.to_dict(orient="records"):
            row = clean_record(record)
            history_record = {
                "publication_id": row.get("publication_id"),
                "run_date": run_date,
                "ticker": row.get("ticker"),
                "history_date": row.get("date"),
                "action": row.get("action"),
                "setup": row.get("setup"),
                "adaptive_mode": row.get("adaptive_mode"),
                "psychology": row.get("psychology"),
                "score": numeric_or_none(row.get("score")),
                "open": numeric_or_none(row.get("open")),
                "high": numeric_or_none(row.get("high")),
                "low": numeric_or_none(row.get("low")),
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
            }
            history_record["payload"] = compact_payload(
                row,
                history_record,
                aliases=("date",),
                max_bytes=SUPABASE_HISTORY_PAYLOAD_MAX_BYTES,
            )
            history_records.append(history_record)

    outcome_records = []
    if not outcomes.empty:
        for record in outcomes.to_dict(orient="records"):
            row = clean_record(record)
            outcome_record = {
                    "signal_run_date": row.get("signal_run_date"),
                    "evaluation_run_date": row.get("evaluation_run_date"),
                    "ticker": row.get("ticker"),
                    "publication_id": row.get("publication_id"),
                    "prior_action": row.get("prior_action"),
                    "prior_setup": row.get("prior_setup"),
                    "prior_buy_tier": row.get("prior_buy_tier"),
                    "prior_operator_state": row.get("prior_operator_state"),
                    "prior_anti_signal_level": row.get("prior_anti_signal_level"),
                    "prior_prediction_upside_probability": numeric_or_none(row.get("prior_prediction_upside_probability")),
                    "prior_prediction_downside_probability": numeric_or_none(row.get("prior_prediction_downside_probability")),
                    "prior_prediction_no_edge_probability": numeric_or_none(row.get("prior_prediction_no_edge_probability")),
                    "prior_prediction_confidence": numeric_or_none(row.get("prior_prediction_confidence")),
                    "prior_prediction_state": row.get("prior_prediction_state"),
                    "prior_prediction_key": row.get("prior_prediction_key"),
                    "prior_prediction_scope": row.get("prior_prediction_scope"),
                    "prior_close": numeric_or_none(row.get("prior_close")),
                    "entry_model_version": row.get("entry_model_version"),
                    "entry_eligible": is_affirmative(row.get("entry_eligible")),
                    "entry_filled": is_affirmative(row.get("entry_filled")),
                    "forecast_learnable": is_affirmative(row.get("forecast_learnable")),
                    "entry_fill_est": numeric_or_none(row.get("entry_fill_est")),
                    "current_action": row.get("current_action"),
                    "current_operator_state": row.get("current_operator_state"),
                    "current_close": numeric_or_none(row.get("current_close")),
                    "close_return_pct": numeric_or_none(row.get("close_return_pct")),
                    "outcome_label": row.get("outcome_label"),
                    "outcome_score": numeric_or_none(row.get("outcome_score")),
                    "outcome_reason": row.get("outcome_reason"),
                    "learning_key": row.get("learning_key"),
                }
            outcome_record["payload"] = compact_payload(
                row,
                outcome_record,
                max_bytes=SUPABASE_OUTCOME_PAYLOAD_MAX_BYTES,
            )
            outcome_records.append(outcome_record)

    if run_metadata:
        try:
            publishing_metadata = clean_record(run_metadata)
            publishing_metadata["status"] = "publishing"
            publishing_payload = publishing_metadata.get("payload") if isinstance(publishing_metadata.get("payload"), dict) else {}
            publishing_metadata["payload"] = {**publishing_payload, "sync_state": "publishing"}
            supabase_upsert_refresh_run([publishing_metadata])
        except Exception as exc:
            print(f"Supabase run-health sync skipped: {exc}")

    snapshot_synced = 0
    indicator_state_synced = 0
    history_synced = 0
    outcome_synced = 0
    artifact_synced = calibration_artifact is None
    learning_state_synced = learning_stats is None
    try:
        supabase_upsert_batches("watchlist_snapshots", report_records, ["publication_id", "ticker"])
        snapshot_synced = len(report_records)
    except Exception as exc:
        print(f"Supabase snapshot sync skipped: {exc}")
    try:
        supabase_upsert_batches(
            "watchlist_indicator_state",
            indicator_records,
            ["publication_id", "ticker"],
        )
        indicator_state_synced = len(indicator_records)
    except Exception as exc:
        print(f"Supabase indicator-state sync skipped: {exc}")
    try:
        supabase_upsert_batches("watchlist_behavior_history", history_records, ["publication_id", "ticker", "history_date"])
        history_synced = len(history_records)
    except Exception as exc:
        print(f"Supabase behavior-history sync skipped: {exc}")
    try:
        # Outcomes can grow well beyond normal snapshot batches. Keep this
        # non-critical archive write bounded so it cannot block publishing.
        supabase_upsert_with_optional_outcome_columns(
            outcome_records,
            ["publication_id", "signal_run_date", "evaluation_run_date", "ticker"],
        )
        outcome_synced = len(outcome_records)
    except Exception as exc:
        print(f"Supabase signal-outcome sync skipped: {exc}")
    if calibration_artifact:
        try:
            artifact_payload = clean_record(calibration_artifact)
            artifact_record = {
                "artifact_id": artifact_payload.get("artifact_id"),
                "source_publication_id": artifact_payload.get("source_publication_id"),
                "cutoff_date": artifact_payload.get("cutoff_date"),
                "artifact_version": artifact_payload.get("artifact_version"),
                "scanner_version": artifact_payload.get("scanner_version"),
                "learning_model_version": artifact_payload.get("learning_model_version"),
                "directional_model_version": artifact_payload.get("directional_model_version"),
                "content_hash": artifact_payload.get("content_hash"),
                "state": "validated",
                "payload_bytes": calibration_payload_bytes(artifact_payload),
                "payload": artifact_payload,
            }
            supabase_upsert("watchlist_calibration_artifacts", [artifact_record], ["artifact_id"])
            artifact_synced = True
        except Exception as exc:
            print(f"Supabase calibration-artifact sync skipped: {exc}")
    if learning_stats is not None:
        try:
            learning_records = []
            for learning_key, stats in learning_stats.items():
                stats_payload = clean_record(stats)
                learning_records.append({
                    "publication_id": (run_metadata or {}).get("publication_id"),
                    "run_date": run_date,
                    "learning_key": str(learning_key),
                    "scope": str(stats_payload.get("scope") or "unknown"),
                    "model_version": str(stats_payload.get("model_version") or LEARNING_MODEL_VERSION),
                    "horizon_sessions": LEARNING_HORIZON_SESSIONS,
                    "sample_count": int(stats_payload.get("sample_count") or 0),
                    "working_rate": numeric_or_none(stats_payload.get("working_rate")),
                    "failed_rate": numeric_or_none(stats_payload.get("failed_rate")),
                    "trap_avoided_rate": numeric_or_none(stats_payload.get("trap_avoided_rate")),
                    "distinct_ticker_count": int(stats_payload.get("distinct_ticker_count") or 0),
                    "evaluation_date_count": int(stats_payload.get("evaluation_date_count") or 0),
                    "payload": stats_payload,
                })
            supabase_upsert_batches(
                "watchlist_learning_state",
                learning_records,
                ["publication_id", "learning_key", "scope"],
            )
            learning_state_synced = True
        except Exception as exc:
            print(f"Supabase learning-state sync skipped: {exc}")
    sync_complete = (
        snapshot_synced == len(report_records)
        and indicator_state_synced == len(indicator_records)
        and history_synced == len(history_records)
        and outcome_synced == len(outcome_records)
        and artifact_synced
        and learning_state_synced
    )
    if run_metadata:
        try:
            final_metadata = clean_record(run_metadata)
            final_payload = final_metadata.get("payload") if isinstance(final_metadata.get("payload"), dict) else {}
            scanner_status = str(run_metadata.get("status") or "ok")
            final_metadata["status"] = "pending_audit" if sync_complete else "sync_failed"
            final_metadata["payload"] = {
                **final_payload,
                "scanner_status": scanner_status,
                "sync_state": "complete" if sync_complete else "failed",
                "synced_snapshot_rows": snapshot_synced,
                "synced_indicator_state_rows": indicator_state_synced,
                "synced_history_rows": history_synced,
                "synced_outcome_rows": outcome_synced,
                "calibration_artifact_id": (calibration_artifact or {}).get("artifact_id") or final_payload.get("calibration_artifact_id", ""),
                "synced_learning_state_rows": len(learning_stats or {}),
            }
            supabase_upsert_refresh_run([final_metadata])
        except Exception as exc:
            print(f"Supabase final run-health sync skipped: {exc}")
    print(
        f"Synced {snapshot_synced}/{len(report_records)} snapshot rows, "
        f"{history_synced}/{len(history_records)} history rows, and "
        f"{outcome_synced}/{len(outcome_records)} signal-outcome rows to Supabase."
    )
    if not sync_complete:
        print("Supabase cleanup skipped because the publication is incomplete.")


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
    # Multi-session supply/demand proxies. These are observable OHLCV
    # properties, not claims about the identity of the market participant.
    out["relative_volume"] = np.where(out["vol_ma"] > 0, out["volume"] / out["vol_ma"], np.nan)
    out["range_atr"] = np.where(out["atr"] > 0, out["range"] / out["atr"], np.nan)
    up_day = (out["close"] > out["open"]) & (out["close"] >= out["close"].shift(1)) & (out["close_loc"] >= 0.55)
    down_day = (out["close"] < out["open"]) & (out["close"] <= out["close"].shift(1)) & (out["close_loc"] <= 0.45)
    out["demand_day"] = (up_day & (out["relative_volume"] >= 0.90)).astype(int)
    out["supply_day"] = (down_day & (out["relative_volume"] >= 1.05)).astype(int)
    out["demand_days_5"] = out["demand_day"].rolling(5, min_periods=3).sum()
    out["supply_days_5"] = out["supply_day"].rolling(5, min_periods=3).sum()
    out["signed_volume_pressure_5"] = (
        np.sign(out["close"].diff()).fillna(0) * out["relative_volume"].fillna(0)
    ).rolling(5, min_periods=3).mean()
    out["volatility_contraction_5"] = out["range_atr"].rolling(5, min_periods=3).mean() <= out["range_atr"].rolling(20, min_periods=10).mean() * 0.78
    out["volume_contraction_5"] = out["relative_volume"].rolling(5, min_periods=3).mean() <= 0.85
    failed_breakout = (out["high"] > out["high"].shift(1)) & (out["close"] <= out["high"].shift(1)) & (out["close_loc"] <= 0.50)
    failed_breakdown = (out["low"] < out["low"].shift(1)) & (out["close"] >= out["low"].shift(1)) & (out["close_loc"] >= 0.50)
    # Confirmation occurs on a later bar, preventing a single wick from being
    # treated as a fully formed trap.
    out["bull_trap_confirmed"] = failed_breakout.shift(1, fill_value=False).astype(bool) & (out["close"] < out["low"].shift(1))
    out["bear_trap_confirmed"] = failed_breakdown.shift(1, fill_value=False).astype(bool) & (out["close"] > out["high"].shift(1))
    return out


def momentum_climax_state(d: pd.DataFrame, i: int, is_etf: bool = False) -> dict:
    """Classify a large upside shock and its next-session reclaim without lookahead."""
    empty = {
        "state": "NONE",
        "event_type": "NONE",
        "event": False,
        "execution_block": False,
        "evidence_count": 0,
        "event_midpoint": np.nan,
        "day_change_atr": 0.0,
    }
    if i < PERSONALITY_LOOKBACK_BARS or i >= len(d):
        return empty

    def event_at(index: int) -> dict:
        if index < PERSONALITY_LOOKBACK_BARS:
            return {**empty}
        row = d.iloc[index]
        previous = d.iloc[index - 1]
        window = d.iloc[index - PERSONALITY_LOOKBACK_BARS + 1 : index + 1]
        normal_move = float(window["close"].pct_change().abs().dropna().median() * 100.0)
        normal_move = max(normal_move, 0.50)
        atr_pct = float(row.atr_pct) if not pd.isna(row.atr_pct) else 0.0
        day_change = (float(row.close) / float(previous.close) - 1.0) * 100.0
        day_change_atr = day_change / atr_pct if atr_pct > 0 else 0.0
        travel = d["close"].diff().abs().iloc[index - PERSONALITY_LOOKBACK_BARS + 1 : index + 1].sum()
        trend_efficiency = (
            abs(float(row.close) - float(d.iloc[index - PERSONALITY_LOOKBACK_BARS].close)) / travel
            if travel > 0
            else 0.0
        )
        personality = stock_personality_profile(d, index, is_etf, float(trend_efficiency))["personality_type"]
        high_beta = personality == "HIGH_BETA"
        return_20d = (float(row.close) / float(d.iloc[index - 20].close) - 1.0) * 100.0
        ema_extension_atr = float(row.close - row.ema_fast) / float(row.atr) if float(row.atr) > 0 else 0.0
        evidence = (
            int(float(row.relative_volume) >= 1.20)
            + int(float(row.range_atr) >= 1.25)
            + int(float(row.close - row.ema_fast) / float(row.atr) >= 2.00 if float(row.atr) > 0 else False)
            + int(float(row.rsi) >= 72.0)
            + int(float(row.open - previous.close) / float(row.atr) >= 0.50 if float(row.atr) > 0 else False)
        )
        strict_climax = high_beta and (
            day_change >= max(3.0, normal_move * CLIMAX_MOVE_MULTIPLE)
            and day_change_atr >= CLIMAX_RETURN_ATR
            and evidence >= CLIMAX_MIN_EVIDENCE
        )
        mature_chase = high_beta and (
            day_change >= normal_move * MATURE_CHASE_MOVE_MULTIPLE
            and day_change_atr >= MATURE_CHASE_RETURN_ATR
            and return_20d >= MATURE_CHASE_RETURN_20D_PCT
            and ema_extension_atr >= MATURE_CHASE_EMA_EXTENSION_ATR
        )
        event = strict_climax or mature_chase
        return {
            "event": event,
            "event_type": "MOMENTUM CLIMAX" if strict_climax else "MATURE HIGH-BETA CHASE" if mature_chase else "NONE",
            "evidence_count": evidence,
            "event_midpoint": (float(row.high) + float(row.low)) / 2.0,
            "day_change_atr": day_change_atr,
        }

    current = event_at(i)
    if current["event"]:
        return {
            **current,
            "state": "CLIMAX LOCKOUT",
            "execution_block": True,
        }

    prior = event_at(i - 1)
    if not prior["event"]:
        return empty

    row = d.iloc[i]
    midpoint = float(prior["event_midpoint"])
    relative_volume = float(row.relative_volume) if not pd.isna(row.relative_volume) else 0.0
    failed = float(row.close) < midpoint and (
        float(row.close) < float(row.open)
        or float(row.close_loc) < 0.45
        or relative_volume >= 1.10
    )
    reclaimed = (
        float(row.close) >= max(midpoint, float(d.iloc[i - 1].close))
        and float(row.close_loc) >= 0.55
        and not failed
    )
    return {
        **prior,
        "state": "RECLAIM CONFIRMED" if reclaimed else "RECLAIM FAILED" if failed else "RECLAIM PENDING",
        "execution_block": not reclaimed,
    }


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
    "WAIT": "AVOID",
    "WAIT / AVOID": "AVOID",
    "WATCH TREND": "WATCH",
    "SETUP FORMING": "BUILDING",
    "BUY CANDIDATE": "BUY",
    "STRONG CONTINUATION": "TRENDING",
    "EXIT PRESSURE": "EXIT",
}

ACTION_DISPLAY_LABELS = {
    **SIGNAL_STAGE_LABELS,
    "WAIT / AVOID": "AVOID",
}


def signal_stage(action: str) -> str:
    return SIGNAL_STAGE_LABELS.get(action, "WAIT")


def signal_stage_rank(action: str) -> int:
    return SIGNAL_STAGE_ORDER.get(action, 0)


def days_between_dates(later: str, earlier: str) -> Optional[int]:
    try:
        later_date = datetime.fromisoformat(str(later)).date()
        earlier_date = datetime.fromisoformat(str(earlier)).date()
    except (TypeError, ValueError):
        return None
    return (later_date - earlier_date).days


class NyseHolidayCalendar(AbstractHolidayCalendar):
    rules = [
        Holiday("NewYearsDay", month=1, day=1, observance=nearest_workday),
        USMartinLutherKingJr,
        USPresidentsDay,
        GoodFriday,
        USMemorialDay,
        Holiday("JuneteenthNationalIndependenceDay", month=6, day=19, observance=nearest_workday, start_date="2022-01-01"),
        Holiday("IndependenceDay", month=7, day=4, observance=nearest_workday),
        USLaborDay,
        USThanksgivingDay,
        Holiday("ChristmasDay", month=12, day=25, observance=nearest_workday),
    ]


def nyse_holidays(start: date_cls, end: date_cls) -> set[date_cls]:
    return set(NyseHolidayCalendar().holidays(start=start, end=end).date)


def is_nyse_trading_day(day: date_cls) -> bool:
    if day.weekday() >= 5:
        return False
    return day not in nyse_holidays(day, day)


def previous_nyse_trading_day(day: date_cls) -> date_cls:
    candidate = day - timedelta(days=1)
    while not is_nyse_trading_day(candidate):
        candidate -= timedelta(days=1)
    return candidate


def latest_completed_nyse_session(now: Optional[datetime] = None) -> date_cls:
    current = (now or datetime.now(MARKET_TIMEZONE)).astimezone(MARKET_TIMEZONE)
    candidate = current.date()
    if not is_nyse_trading_day(candidate):
        return previous_nyse_trading_day(candidate)
    if current.time() < US_MARKET_CLOSE_TIME:
        return previous_nyse_trading_day(candidate)
    return candidate


def nyse_session_age(data_date_text: Optional[str], now: Optional[datetime] = None) -> Optional[int]:
    if not data_date_text:
        return None
    try:
        data_day = datetime.fromisoformat(str(data_date_text)).date()
    except (TypeError, ValueError):
        return None
    reference_day = latest_completed_nyse_session(now)
    if data_day >= reference_day:
        return 0
    age = 0
    cursor = data_day
    while cursor < reference_day:
        cursor += timedelta(days=1)
        if is_nyse_trading_day(cursor):
            age += 1
    return age


def latest_frame_date(df: pd.DataFrame) -> Optional[str]:
    if df.empty or "date" not in df.columns:
        return None
    dates = pd.to_datetime(df["date"], errors="coerce").dropna()
    if dates.empty:
        return None
    return str(dates.dt.date.max())


def reject_stale_live_frame(df: pd.DataFrame, ticker: str, provider: str) -> None:
    latest_date = latest_frame_date(df)
    age = nyse_session_age(latest_date)
    if age is not None and age <= MAX_EXECUTION_DATA_AGE_DAYS:
        return
    raise RuntimeError(
        f"{provider} returned stale data for {display_ticker(ticker)}: "
        f"latest bar {latest_date or 'unknown'} is {age if age is not None else 'unknown'} NYSE session(s) old"
    )


def append_unique_reason(row: dict, code: str) -> None:
    codes = list(row.get("reason_codes") or [])
    if code not in codes:
        codes.append(code)
    row["reason_codes"] = codes


def apply_data_freshness_gate(row: dict, run_date: str, cached_tickers: set[str]) -> dict:
    ticker = str(row.get("ticker", "")).upper()
    data_date = row.get("date") or row.get("data_date") or row.get("history_date")
    data_age_days = nyse_session_age(str(data_date)) if data_date else None
    cached_source = ticker in cached_tickers
    freshness_block = data_age_days is None or data_age_days > MAX_EXECUTION_DATA_AGE_DAYS

    if freshness_block:
        freshness_status = "STALE_BLOCK"
        freshness_plan = (
            f"Execution blocked: market data is {data_age_days if data_age_days is not None else 'unknown'} NYSE session(s) old; refresh live data before acting."
        )
        append_unique_reason(row, "data_stale_block")
        actionable_stale = row.get("action") in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}
        if row.get("action") in {"BUY CANDIDATE", "STRONG CONTINUATION"}:
            row["action"] = "SETUP FORMING"
            row["signal_stage"] = "SETUP"
        if actionable_stale:
            row["adjusted_score"] = min(float(numeric_or_none(row.get("adjusted_score")) or numeric_or_none(row.get("score")) or 0), 49.0)
            row["signal_quality"] = "STALE DATA"
            row["transition_label"] = "Data Stale"
            row["transition_score"] = min(float(numeric_or_none(row.get("transition_score")) or 0), -30.0)
            row["next_day_bias"] = "EXECUTION BLOCKED"
            row["next_day_plan"] = freshness_plan
            row["notes"] = "; ".join([item for item in [row.get("notes"), freshness_plan] if item])
    elif cached_source:
        freshness_status = "CACHED_OK"
        freshness_plan = "Cached data is recent enough for reference, but confirm live price and Pine chart before execution."
        append_unique_reason(row, "cached_data_ok")
    else:
        freshness_status = "LIVE_OR_CURRENT"
        freshness_plan = "Data freshness is acceptable for scanner use."

    row["data_age_days"] = data_age_days if data_age_days is not None else ""
    row["freshness_status"] = freshness_status
    row["freshness_block"] = bool_text(freshness_block)
    row["freshness_plan"] = freshness_plan
    return row


def compute_anti_signal(row: dict) -> tuple[float, str, str, list[str]]:
    operator_state = str(row.get("operator_state") or "").upper()
    operator_pressure = str(row.get("operator_pressure") or "").upper()
    next_day = str(row.get("next_day_bias") or "").upper()
    extension_state = str(row.get("extension_state") or "").upper()
    quality = str(row.get("signal_quality") or "").upper()
    freshness_block = str(row.get("freshness_block") or "").upper() == "YES"
    bull_trap_score = float(numeric_or_none(row.get("bull_trap_score")) or 0)
    distribution_score = float(numeric_or_none(row.get("distribution_score")) or 0)

    score = 0.0
    triggers: list[str] = []
    if freshness_block or quality == "STALE DATA":
        score += 45.0
        triggers.append("stale data")
    if operator_state == "BULL_TRAP" or bull_trap_score >= 58.0:
        score += 38.0
        triggers.append("bull trap")
    if operator_state == "DISTRIBUTION" or "DISTRIBUTION" in operator_pressure or distribution_score >= 55.0:
        score += 34.0
        triggers.append("distribution")
    if extension_state == "EXTENDED" or next_day == "AVOID CHASE" or quality == "EXTENDED":
        score += 28.0
        triggers.append("extended chase")
    if next_day == "EXECUTION BLOCKED":
        score += 35.0
        triggers.append("execution blocked")
    elif next_day == "DEFENSIVE / EXIT RISK":
        score += 24.0
        triggers.append("defensive tape")

    score = min(100.0, score)
    if score >= 45.0:
        level = "BLOCK"
        plan = f"Anti-signal block: {', '.join(dict.fromkeys(triggers))}; downgrade execution even if trend score is high."
    elif score >= 25.0:
        level = "CAUTION"
        plan = f"Anti-signal caution: {', '.join(dict.fromkeys(triggers))}; keep on watch, but do not upgrade without a clean reset."
    else:
        level = "NONE"
        plan = "No major anti-signal penalty."
    return score, level, plan, list(dict.fromkeys(triggers))


def apply_anti_signal_penalty(row: dict) -> dict:
    score, level, plan, triggers = compute_anti_signal(row)
    row["anti_signal_score"] = round(float(score), 1)
    row["anti_signal_level"] = level
    row["anti_signal_plan"] = plan

    if level == "NONE":
        return row

    append_unique_reason(row, "anti_signal_block" if level == "BLOCK" else "anti_signal_caution")
    reason_by_trigger = {
        "stale data": "anti_stale_data",
        "bull trap": "anti_bull_trap",
        "distribution": "anti_distribution",
        "extended chase": "anti_extended_chase",
        "execution blocked": "anti_execution_blocked",
        "defensive tape": "anti_defensive_tape",
    }
    for trigger in triggers:
        code = reason_by_trigger.get(trigger)
        if code:
            append_unique_reason(row, code)

    actionable = row.get("action") in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}
    adjusted_score = float(numeric_or_none(row.get("adjusted_score")) or numeric_or_none(row.get("score")) or 0)
    if level == "BLOCK":
        if row.get("action") in {"BUY CANDIDATE", "STRONG CONTINUATION"}:
            row["action"] = "SETUP FORMING"
            row["signal_stage"] = "SETUP"
        if actionable:
            row["adjusted_score"] = min(adjusted_score, 49.0)
        if row.get("next_day_bias") not in {"AVOID CHASE", "DEFENSIVE / EXIT RISK", "EXECUTION BLOCKED"}:
            row["next_day_bias"] = "EXECUTION BLOCKED"
            row["next_day_plan"] = plan
    elif level == "CAUTION" and actionable:
        row["adjusted_score"] = min(adjusted_score, 76.0)

    row["notes"] = "; ".join([item for item in [row.get("notes"), plan] if item])
    return row


def buy_tier_for(row: dict, rank_index: int) -> tuple[str, int, str]:
    action = row.get("action", "")
    quality = str(row.get("signal_quality") or "").upper()
    anti_level = str(row.get("anti_signal_level") or "NONE").upper()
    anti_plan = str(row.get("anti_signal_plan") or "").strip()
    next_day = str(row.get("next_day_bias") or "").upper()
    operator_pressure = str(row.get("operator_pressure") or "").upper()
    operator_state = str(row.get("operator_state") or "").upper()
    adjusted_score = float(numeric_or_none(row.get("adjusted_score")) or numeric_or_none(row.get("score")) or 0)
    score = float(numeric_or_none(row.get("score")) or 0)
    fresh = row.get("freshness_block") != "YES"
    risk_ok = row.get("risk_permission") == "ALLOW"
    market_ok = row.get("market_permission") == "ALLOW"
    ticker_ok = row.get("ticker_permission") == "ALLOW"
    walk_forward_ok = row.get("walk_forward_permission") == "ALLOW"
    personality_ok = is_affirmative(row.get("personality_setup_allowed"))
    absorption_or_neutral = (
        operator_state in {"", "NEUTRAL", "ACCUMULATION", "MARKUP / DEMAND CONTROL", "BEAR_TRAP / SQUEEZE WATCH"}
        or operator_pressure in {"NEUTRAL", "ACCUMULATION / ABSORPTION", "SQUEEZE WATCH"}
    )

    if anti_level == "BLOCK" and action in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}:
        return "SETUP ONLY", 4, anti_plan or "Anti-signal block; do not execute directly."
    if anti_level == "CAUTION" and action in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}:
        return "SETUP ONLY", 3, anti_plan or "Anti-signal caution; wait for a cleaner reset."
    if action == "BUY CANDIDATE" and fresh and risk_ok and market_ok and ticker_ok and walk_forward_ok and personality_ok and next_day == "BULLISH CONFIRM" and absorption_or_neutral and adjusted_score >= 92 and rank_index < TOP_BUY_TIER_LIMIT:
        return "A+ BUY", 1, "Highest execution tier; still confirm on Pine before acting."
    if action == "BUY CANDIDATE" and fresh and risk_ok and market_ok and ticker_ok and walk_forward_ok and personality_ok and next_day == "BULLISH CONFIRM" and adjusted_score >= 78 and rank_index < BUY_WATCH_TIER_LIMIT:
        return "BUY WATCH", 2, "Qualified buy watch; prefer reference-zone entry and Pine confirmation."
    if action == "SETUP FORMING" and learning_confirms_setup_upgrade(row) and rank_index < BUY_WATCH_TIER_LIMIT:
        return "BUY WATCH", 2, "Learning-confirmed BUILDING setup; use reference-zone entry and Pine confirmation, not a chase."
    if action in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}:
        if quality in {"STALE DATA", "EVENT RISK", "EXTENDED"} or row.get("freshness_block") == "YES":
            return "SETUP ONLY", 4, "Do not execute directly; treat as a setup until the blocker clears."
        return "SETUP ONLY", 3, "Setup is useful, but not in the top execution tier."
    if action == "WATCH TREND":
        return "WATCH", 5, "Trend is worth monitoring, not an entry signal."
    if action == "EXIT PRESSURE":
        return "EXIT RISK", 8, "Risk pressure is elevated."
    return "NO TRADE", 9 if score >= 25 else 10, "No actionable edge."


def learning_confirms_setup_upgrade(row: dict) -> bool:
    action = str(row.get("action") or "")
    if action != "SETUP FORMING":
        return False

    personality_allowed = is_affirmative(row.get("personality_setup_allowed"))
    anti_level = str(row.get("anti_signal_level") or "NONE").upper()
    operator_state = str(row.get("operator_state") or "").upper()
    operator_pressure = str(row.get("operator_pressure") or "").upper()
    next_day = str(row.get("next_day_bias") or "").upper()
    quality = str(row.get("signal_quality") or "").upper()
    extension_state = str(row.get("extension_state") or "").upper()
    stale = str(row.get("freshness_block") or "").upper() == "YES"
    risk_ok = row.get("risk_permission") == "ALLOW"
    market_ok = row.get("market_permission") == "ALLOW"
    ticker_ok = row.get("ticker_permission") == "ALLOW"
    walk_forward_ok = row.get("walk_forward_permission") == "ALLOW"
    adjusted_score = float(numeric_or_none(row.get("adjusted_score")) or numeric_or_none(row.get("score")) or 0)
    samples = int(numeric_or_none(row.get("learning_sample_count")) or 0)
    working_rate = float(numeric_or_none(row.get("learning_working_rate")) or 0)
    failed_rate = float(numeric_or_none(row.get("learning_failed_rate")) or 0)
    adjustment = float(numeric_or_none(row.get("learning_adjustment")) or 0)
    learning_scope = str(row.get("learning_scope") or "").lower()
    distinct_tickers = int(numeric_or_none(row.get("learning_distinct_ticker_count")) or 0)
    evaluation_dates = int(numeric_or_none(row.get("learning_evaluation_date_count")) or 0)
    promotion_eligible = row.get("learning_promotion_eligible") is True
    directional_rejected = "directional_model_not_confirmed" in (row.get("reason_codes") or [])

    if not promotion_eligible or directional_rejected:
        return False
    if not personality_allowed or stale or anti_level != "NONE" or not risk_ok or not market_ok or not ticker_ok or not walk_forward_ok:
        return False
    if extension_state == "EXTENDED" or quality in {"STALE DATA", "EVENT RISK", "EXTENDED", "FEEDBACK FAILED", "FEEDBACK STALE"}:
        return False
    if operator_state in {"BULL_TRAP", "DISTRIBUTION"} or "DISTRIBUTION" in operator_pressure:
        return False
    if next_day not in {"BULLISH CONFIRM", "CONSTRUCTIVE PULLBACK", "WATCH TREND"}:
        return False
    return (
        samples >= LEARNING_CONFIRM_MIN_SAMPLES
        and working_rate >= LEARNING_CONFIRM_MIN_WORKING_RATE
        and failed_rate <= LEARNING_CONFIRM_MAX_FAILED_RATE
        and adjustment >= LEARNING_CONFIRM_MIN_ADJUSTMENT
        and adjusted_score >= LEARNING_CONFIRM_MIN_SCORE
        and learning_scope == "exact signal personality"
        and distinct_tickers >= LEARNING_CONFIRM_MIN_DISTINCT_TICKERS
        and evaluation_dates >= LEARNING_CONFIRM_MIN_EVALUATION_DATES
    )


def row_float(row: dict, field: str, default: float = 0.0) -> float:
    value = numeric_or_none(row.get(field))
    return float(value) if value is not None else default


def append_context_note(row: dict, note: str) -> None:
    row["notes"] = "; ".join([item for item in [row.get("notes"), note] if item])


def set_context_overlay(row: dict, label: str, adjustment: float, plan: str) -> None:
    row["contextual_overlay"] = label
    row["contextual_score_adjustment"] = round(float(adjustment), 1)
    row["contextual_plan"] = plan
    append_context_note(row, plan)


def supply_risk_score(row: dict) -> float:
    return max(
        row_float(row, "distribution_score"),
        row_float(row, "bull_trap_score"),
        row_float(row, "short_pressure_proxy"),
    )


def post_exit_reclaim_is_strong(row: dict, prior_exit: dict) -> bool:
    close = row_float(row, "close")
    prior_close = row_float(prior_exit, "close")
    reclaim_pct = (close / prior_close - 1) * 100 if close > 0 and prior_close > 0 else 0.0
    operator_state = str(row.get("operator_state") or "").upper()
    next_day = str(row.get("next_day_bias") or "").upper()
    mode = str(row.get("adaptive_mode") or "").upper()
    personality = str(row.get("personality_type") or "").upper()
    supply_score = supply_risk_score(row)
    buyer_score = row_float(row, "buyer_score")
    demand_control = row_float(row, "demand_control_score")
    absorption_score = row_float(row, "absorption_score")

    # Range-bound/mean-reversion personalities often print convincing one-day
    # rebounds after EXIT. Make them prove a second day instead of bypassing
    # post-exit cooldown immediately.
    if personality == "RANGE_BOUND" or mode == "MEAN REVERSION":
        return False

    standard_reclaim = (
        reclaim_pct >= POST_EXIT_RECLAIM_MIN_PCT
        and next_day == "BULLISH CONFIRM"
        and operator_state in {"MARKUP / DEMAND CONTROL", "ACCUMULATION", "BEAR_TRAP / SQUEEZE WATCH"}
        and buyer_score >= 80.0
        and max(demand_control, absorption_score) >= 55.0
        and supply_score < 30.0
    )
    trend_reclaim = (
        reclaim_pct >= 2.5
        and next_day == "BULLISH CONFIRM"
        and mode in {"POWER TREND", "STEADY TREND"}
        and personality != "RANGE_BOUND"
        and operator_state == "MARKUP / DEMAND CONTROL"
        and demand_control >= 80.0
        and buyer_score >= 70.0
        and supply_score < 30.0
    )
    return standard_reclaim or trend_reclaim


def post_exit_cooldown_candidate(row: dict, prior_rows: list[dict]) -> Optional[dict]:
    if row.get("action") not in {"BUY CANDIDATE", "STRONG CONTINUATION"}:
        return None
    recent = prior_rows[-POST_EXIT_COOLDOWN_BARS:] if POST_EXIT_COOLDOWN_BARS > 0 else []
    prior_exit = next((item for item in reversed(recent) if item.get("action") == "EXIT PRESSURE"), None)
    if not prior_exit or post_exit_reclaim_is_strong(row, prior_exit):
        return None

    return {
        "priority": 100,
        "label": "POST-EXIT COOLDOWN",
        "adjustment": -35.0,
        "transition_label": "Post-Exit Cooldown",
        "next_day_bias": "EXECUTION BLOCKED",
        "next_day_plan": "Post-exit cooldown: require a stronger reclaim before upgrading back to BUY.",
        "force_action": "SETUP FORMING",
        "execution_block": "YES",
        "reason_code": "post_exit_cooldown",
        "plan": "EXIT pressure was too recent; downgrade any ordinary rebound to BUILDING until buyers prove control.",
    }


def post_exit_risk_persistence_candidate(row: dict, prior_rows: list[dict]) -> Optional[dict]:
    if row.get("action") == "EXIT PRESSURE":
        return None
    recent = prior_rows[-POST_EXIT_RISK_PERSISTENCE_BARS:] if POST_EXIT_RISK_PERSISTENCE_BARS > 0 else []
    prior_exit = next((item for item in reversed(recent) if item.get("action") == "EXIT PRESSURE"), None)
    if not prior_exit or post_exit_reclaim_is_strong(row, prior_exit):
        return None

    close = row_float(row, "close")
    prior_close = row_float(prior_exit, "close")
    day_change = row_float(row, "day_change_pct")
    seller_score = row_float(row, "seller_score")
    buyer_score = row_float(row, "buyer_score")
    distribution_score = row_float(row, "distribution_score")
    short_pressure = row_float(row, "short_pressure_proxy")
    next_day = str(row.get("next_day_bias") or "").upper()
    still_below_exit_zone = close > 0 and prior_close > 0 and close <= prior_close * 1.01
    pressure_persists = (
        day_change <= -0.75
        or seller_score >= 40.0
        or distribution_score >= 24.0
        or short_pressure >= 24.0
        or (next_day == "NEUTRAL" and buyer_score < 45.0)
    )
    if not (still_below_exit_zone and pressure_persists):
        return None

    return {
        "priority": 70,
        "label": "POST-EXIT RISK PERSISTENCE",
        "adjustment": -22.0,
        "transition_label": "Exit Risk Persists",
        "next_day_bias": "DEFENSIVE / EXIT RISK",
        "next_day_plan": "Post-exit risk persists: wait for a stronger reclaim before treating the weakness as neutral.",
        "force_action": "EXIT PRESSURE",
        "reason_code": "post_exit_risk_persistence",
        "plan": "Recent EXIT pressure has not been reclaimed; seller pressure or continued downside keeps this in risk-control mode.",
    }


def recent_buy_profit_context(history_rows: list[dict], index: int) -> Optional[dict]:
    start = max(0, index - PROFIT_PROTECT_LOOKBACK_BARS)
    current_close = row_float(history_rows[index], "close")
    if current_close <= 0:
        return None

    best_context: Optional[dict] = None
    for buy_index in range(index - 1, start - 1, -1):
        buy_row = history_rows[buy_index]
        if buy_row.get("action") not in {"BUY CANDIDATE", "STRONG CONTINUATION"}:
            continue
        trade_entry = (
            row_float(buy_row, "entry_zone_high")
            or row_float(buy_row, "entry_est")
            or row_float(buy_row, "close")
        )
        if trade_entry <= 0:
            continue
        # The BUY bar cannot establish whether entry or target happened first.
        # Profit management starts from the next complete daily bar.
        post_entry_rows = history_rows[buy_index + 1 : index + 1]
        highs = [row_float(item, "high") or row_float(item, "close") for item in post_entry_rows]
        peak_price = max([value for value in highs if value > 0], default=0.0)
        if peak_price <= 0:
            continue
        stop = row_float(buy_row, "stop_est")
        risk = trade_entry - stop if 0 < stop < trade_entry else 0.0
        take_profit_1 = row_float(buy_row, "take_profit_1")
        peak_gain_pct = (peak_price / trade_entry - 1) * 100
        giveback_pct = (current_close / peak_price - 1) * 100
        context = {
            "buy_index": buy_index,
            "buy_date": buy_row.get("date"),
            "trade_entry": trade_entry,
            "risk": risk,
            "peak_price": peak_price,
            "peak_gain_pct": peak_gain_pct,
            "giveback_pct": giveback_pct,
            "peak_gain_r": (peak_price - trade_entry) / risk if risk > 0 else 0.0,
            "giveback_r": (current_close - peak_price) / risk if risk > 0 else 0.0,
            "take_profit_1": take_profit_1,
            "take_profit_1_hit": take_profit_1 > trade_entry and peak_price >= take_profit_1,
            "take_profit_1_reduce_pct": row_float(buy_row, "take_profit_1_reduce_pct"),
            "post_tp1_stop": row_float(buy_row, "post_tp1_stop"),
            "volatility_regime": str(buy_row.get("volatility_regime") or "NORMAL").upper(),
        }
        if not best_context or peak_gain_pct > float(best_context["peak_gain_pct"]):
            best_context = context
    return best_context


def profit_context_candidate(row: dict, history_rows: list[dict], index: int) -> Optional[dict]:
    context = recent_buy_profit_context(history_rows, index)
    if not context or (
        not context["take_profit_1_hit"]
        and float(context["peak_gain_pct"]) < PROFIT_PROTECT_TRIGGER_GAIN_PCT
    ):
        return None

    action = row.get("action")
    giveback_pct = float(context["giveback_pct"])
    giveback_r = float(context["giveback_r"])
    volatility_regime = str(context["volatility_regime"])
    giveback_r_limit = -0.50 if volatility_regime == "REVERSAL VOLATILITY" else -0.75 if volatility_regime == "TREND VOLATILITY" else -0.65
    giveback_pct_limit = -3.0 if volatility_regime == "REVERSAL VOLATILITY" else -5.0 if volatility_regime == "TREND VOLATILITY" else -PROFIT_PROTECT_GIVEBACK_PCT
    supply_score = supply_risk_score(row)
    post_tp1_stop = float(context["post_tp1_stop"])
    protective_stop_breached = context["take_profit_1_hit"] and post_tp1_stop > 0 and row_float(row, "close") <= post_tp1_stop
    hard_protect = (
        giveback_pct <= giveback_pct_limit
        or (float(context["risk"]) > 0 and giveback_r <= giveback_r_limit)
        or protective_stop_breached
        or supply_score >= PROFIT_PROTECT_SUPPLY_SCORE
        or (action == "EXIT PRESSURE" and supply_score >= 35.0)
        or (row.get("extension_state") == "EXTENDED" and supply_score >= 25.0)
    )

    if hard_protect:
        return {
            "priority": 80,
            "label": "PROFIT PROTECT",
            "adjustment": -24.0,
            "transition_label": "Profit Protect",
            "next_day_bias": "DEFENSIVE / EXIT RISK",
            "next_day_plan": "Profit-protection mode: recent profit is now facing giveback or supply pressure.",
            "force_action": "SETUP FORMING" if action in {"BUY CANDIDATE", "STRONG CONTINUATION"} else None,
            "execution_block": "YES" if action in {"BUY CANDIDATE", "STRONG CONTINUATION"} else None,
            "reason_code": "profit_protect",
            "profit_stage": "PROTECT REMAINDER",
            "take_profit_1_hit": bool_text(bool(context["take_profit_1_hit"])),
            "profit_peak_r": round(float(context["peak_gain_r"]), 2),
            "profit_giveback_r": round(giveback_r, 2),
            "active_protective_stop": round(post_tp1_stop, 2) if post_tp1_stop > 0 else "",
            "plan": (
                f"Recent BUY from {context['buy_date']} reached {float(context['peak_gain_r']):.2f}R "
                f"and is now showing {giveback_r:.2f}R giveback or supply risk; protect the remaining position."
            ),
        }

    if context["take_profit_1_hit"]:
        reduce_pct = float(context["take_profit_1_reduce_pct"] or 33.0)
        return {
            "priority": 65,
            "label": "TAKE PROFIT 1",
            "adjustment": -6.0,
            "transition_label": "First Profit Taken",
            "next_day_bias": "PROFIT MANAGEMENT",
            "next_day_plan": (
                f"TP1 was reached; trim {reduce_pct:.0f}% and protect the balance at or above "
                f"{post_tp1_stop:.2f}."
            ),
            "force_action": "SETUP FORMING" if action in {"BUY CANDIDATE", "STRONG CONTINUATION"} else None,
            "execution_block": "YES" if action in {"BUY CANDIDATE", "STRONG CONTINUATION"} else None,
            "reason_code": "take_profit_1_hit",
            "profit_stage": "TP1 REACHED",
            "take_profit_1_hit": "YES",
            "profit_peak_r": round(float(context["peak_gain_r"]), 2),
            "profit_giveback_r": round(giveback_r, 2),
            "active_protective_stop": round(post_tp1_stop, 2),
            "plan": (
                f"Recent BUY from {context['buy_date']} reached TP1 at {float(context['take_profit_1']):.2f}; "
                f"trim {reduce_pct:.0f}% and manage the remainder with the raised stop."
            ),
        }

    if action not in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING", "WATCH TREND"}:
        return None

    return {
        "priority": 10,
        "label": "PROFIT ACTIVE",
        "adjustment": 0.0,
        "transition_label": None,
        "reason_code": "profit_active",
        "profit_stage": "PROFIT ACTIVE",
        "take_profit_1_hit": "NO",
        "profit_peak_r": round(float(context["peak_gain_r"]), 2) if float(context["risk"]) > 0 else "",
        "profit_giveback_r": round(giveback_r, 2) if float(context["risk"]) > 0 else "",
        "active_protective_stop": "",
        "plan": f"Recent BUY from {context['buy_date']} reached +{float(context['peak_gain_pct']):.1f}%; avoid fresh chase, but no hard exit pressure yet.",
    }


def volatile_trend_hold_candidate(row: dict) -> Optional[dict]:
    if row.get("action") != "EXIT PRESSURE":
        return None
    mode = str(row.get("adaptive_mode") or "").upper()
    personality = str(row.get("personality_type") or "").upper()
    strong_trend_personality = (
        personality == "HIGH_BETA"
        or (
            mode in {"POWER TREND", "STEADY TREND", "HIGH VOLATILITY"}
            and row_float(row, "demand_control_score") >= 45.0
        )
    )
    if not strong_trend_personality:
        return None
    if row.get("extension_state") == "EXTENDED":
        return None
    hard_supply = supply_risk_score(row)
    if hard_supply >= VOLATILE_TREND_MAX_SUPPLY_SCORE:
        return None
    if str(row.get("operator_state") or "").upper() in {"BULL_TRAP", "DISTRIBUTION"}:
        return None
    if mode not in {"POWER TREND", "STEADY TREND", "HIGH VOLATILITY"}:
        return None
    if row_float(row, "demand_control_score") < 45.0 and row_float(row, "absorption_score") < 45.0:
        return None

    return {
        "priority": 60,
        "label": "VOLATILE TREND HOLD",
        "adjustment": 14.0,
        "transition_label": "Volatile Trend Hold",
        "transition_score_override": 0.0,
        "next_day_bias": "WATCH TREND",
        "next_day_plan": "Trend hold: volatility is elevated, but supply evidence is not strong enough for EXIT.",
        "force_action": "WATCH TREND",
        "score_floor": 50.0,
        "reason_code": "volatile_trend_hold",
        "plan": "Strong trend behavior: treat ordinary volatility as WATCH unless distribution or bull-trap evidence is clear.",
    }


def resolve_context_overlay(row: dict, history_rows: list[dict], index: int, prior_rows: list[dict]) -> tuple[Optional[dict], float, Optional[str]]:
    candidates = [
        post_exit_cooldown_candidate(row, prior_rows),
        post_exit_risk_persistence_candidate(row, prior_rows),
        profit_context_candidate(row, history_rows, index),
        volatile_trend_hold_candidate(row),
    ]
    usable = [candidate for candidate in candidates if candidate]
    if not usable:
        return None, 0.0, None

    selected = max(usable, key=lambda item: int(item.get("priority", 0)))
    if selected.get("force_action"):
        row["action"] = str(selected["force_action"])
        row["signal_stage"] = signal_stage(row["action"])
    if selected.get("score_floor") is not None:
        row["score"] = max(row_float(row, "score"), float(selected["score_floor"]))
    if selected.get("next_day_bias"):
        row["next_day_bias"] = selected["next_day_bias"]
    if selected.get("next_day_plan"):
        row["next_day_plan"] = selected["next_day_plan"]
    if selected.get("execution_block"):
        row["execution_block"] = selected["execution_block"]
    for field in (
        "profit_stage",
        "take_profit_1_hit",
        "profit_peak_r",
        "profit_giveback_r",
        "active_protective_stop",
    ):
        if selected.get(field) not in (None, ""):
            row[field] = selected[field]
    reason_code = selected.get("reason_code")
    if reason_code:
        append_unique_reason(row, str(reason_code))
    set_context_overlay(row, str(selected["label"]), float(selected.get("adjustment", 0.0)), str(selected["plan"]))
    return selected, float(selected.get("adjustment", 0.0)), selected.get("transition_label")


def apply_buy_tiers(rows: list[dict]) -> list[dict]:
    buy_rank = 0
    for row in rows:
        if row.get("action") == "BUY CANDIDATE":
            tier, priority, plan = buy_tier_for(row, buy_rank)
            buy_rank += 1
        else:
            tier, priority, plan = buy_tier_for(row, buy_rank)
        row["buy_tier"] = tier
        row["execution_priority"] = priority
        row["execution_plan"] = plan
        if tier == "A+ BUY":
            append_unique_reason(row, "top_buy_tier")
        elif tier == "BUY WATCH":
            append_unique_reason(row, "buy_watch_tier")
            if row.get("action") == "SETUP FORMING" and learning_confirms_setup_upgrade(row):
                append_unique_reason(row, "learning_confirmed_setup")
        elif tier == "SETUP ONLY":
            append_unique_reason(row, "setup_only_tier")
    return rows


def signal_outcome_from_history(row: dict, ticker_history: list[dict]) -> dict:
    if not ticker_history:
        return {
            "feedback_window_days": "",
            "feedback_return_pct": "",
            "feedback_max_drawdown_pct": "",
            "feedback_stop_hit": "",
            "feedback_quality": "NO HISTORY",
            "feedback_plan": "Not enough behavior history to score this signal yet.",
        }

    latest_date = row.get("date")
    latest_close = numeric_or_none(row.get("close"))
    setup_rows = [
        item for item in ticker_history
        if item.get("action") in {"BUY CANDIDATE", "SETUP FORMING", "STRONG CONTINUATION"}
        and item.get("date") != latest_date
    ]
    anchor = setup_rows[-1] if setup_rows else ticker_history[0]
    anchor_close = numeric_or_none(anchor.get("close"))
    anchor_stop = numeric_or_none(anchor.get("stop_est"))
    if not latest_close or not anchor_close or float(anchor_close) <= 0:
        return {
            "feedback_window_days": "",
            "feedback_return_pct": "",
            "feedback_max_drawdown_pct": "",
            "feedback_stop_hit": "",
            "feedback_quality": "NO HISTORY",
            "feedback_plan": "Not enough close data to score this signal yet.",
        }

    try:
        anchor_index = next(index for index, item in enumerate(ticker_history) if item is anchor)
    except StopIteration:
        anchor_index = 0
    window_rows = ticker_history[anchor_index:]
    lows = [float(item.get("close")) for item in window_rows if numeric_or_none(item.get("close"))]
    min_close = min(lows) if lows else float(latest_close)
    feedback_return = (float(latest_close) / float(anchor_close) - 1) * 100
    max_drawdown = (min_close / float(anchor_close) - 1) * 100
    stop_hit = bool(anchor_stop and min_close <= float(anchor_stop))
    window_days = max(1, len(window_rows))

    if stop_hit or max_drawdown <= -7.0:
        quality = "FAILED"
        plan = "Prior signal has drawdown/stop stress; require fresh reclaim before upgrading."
    elif feedback_return >= 3.0:
        quality = "WORKING"
        plan = "Prior signal is working; avoid chasing and prefer controlled pullbacks."
    elif window_days >= 3 and feedback_return < 1.0:
        quality = "STALE"
        plan = "Prior signal has not progressed; downgrade urgency until price proves itself."
    else:
        quality = "PENDING"
        plan = "Signal feedback is still developing."

    return {
        "feedback_window_days": window_days,
        "feedback_return_pct": round(float(feedback_return), 2),
        "feedback_max_drawdown_pct": round(float(max_drawdown), 2),
        "feedback_stop_hit": bool_text(stop_hit),
        "feedback_quality": quality,
        "feedback_plan": plan,
    }


def merge_payload_row(row: dict) -> dict:
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    typed_values = {
        key: value
        for key, value in row.items()
        if key != "payload" and value not in (None, "")
    }
    merged = {**payload, **typed_values}
    if "date" not in merged:
        merged["date"] = merged.get("data_date") or merged.get("history_date") or merged.get("run_date")
    return merged


def fetch_previous_snapshot_rows(run_date: str) -> list[dict]:
    try:
        run_rows = supabase_select(
            "watchlist_refresh_runs?select=run_date,publication_id,payload&status=in.(ok,degraded)&"
            f"run_date=lte.{urllib.parse.quote(run_date)}&order=run_date.desc,created_at.desc&limit=1"
        )
        if not run_rows:
            return []
        previous_run_date = run_rows[0].get("run_date")
        previous_publication_id = run_rows[0].get("publication_id") or (run_rows[0].get("payload") or {}).get("publication_id")
        if not previous_publication_id:
            return []
        rows = supabase_select(
            "watchlist_snapshots?select=*&"
            f"run_date=eq.{urllib.parse.quote(str(previous_run_date))}&"
            f"publication_id=eq.{urllib.parse.quote(str(previous_publication_id))}&limit=1000"
        )
        return [merge_payload_row(row) for row in rows]
    except RuntimeError as exc:
        print(f"Previous snapshot fetch skipped: {exc}")
        return []


def fetch_previous_behavior_history(run_date: str) -> list[dict]:
    """Load the latest committed history as the canonical daily state."""
    try:
        run_rows = supabase_select(
            "watchlist_refresh_runs?select=run_date,publication_id,payload&status=in.(ok,degraded)&"
            f"run_date=lte.{urllib.parse.quote(run_date)}&order=run_date.desc,created_at.desc&limit=1"
        )
        if not run_rows:
            return []
        publication_id = run_rows[0].get("publication_id") or (run_rows[0].get("payload") or {}).get("publication_id")
        if not publication_id:
            return []
        rows = supabase_select(
            "watchlist_behavior_history?select=*&"
            f"publication_id=eq.{urllib.parse.quote(str(publication_id))}&"
            "order=ticker.asc,history_date.asc&limit=10000"
        )
        return [merge_payload_row(row) for row in rows]
    except RuntimeError as exc:
        print(f"Previous behavior-history fetch skipped: {exc}")
        return []


def fetch_previous_run_metadata(run_date: str) -> dict:
    try:
        rows = supabase_select(
            "watchlist_refresh_runs?select=publication_id,run_date,status,payload&status=in.(ok,degraded)&"
            f"run_date=lte.{urllib.parse.quote(run_date)}&order=run_date.desc,created_at.desc&limit=1"
        )
        if not rows:
            return {}
        payload = rows[0].get("payload") if isinstance(rows[0].get("payload"), dict) else {}
        return {**payload, "publication_id": rows[0].get("publication_id"), "run_date": rows[0].get("run_date")}
    except RuntimeError as exc:
        print(f"Previous run metadata fetch skipped: {exc}")
    return {}


def compatible_incremental_metadata(metadata: dict) -> dict:
    if (
        metadata.get("incremental_state_ready") is True
        and metadata.get("incremental_state_version") == INCREMENTAL_STATE_VERSION
        and metadata.get("learning_model_version") == LEARNING_MODEL_VERSION
    ):
        return metadata
    return {}


def behavior_history_by_ticker(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        ticker = str(row.get("ticker") or "").upper()
        date = str(row.get("date") or row.get("history_date") or "")
        if not ticker or not date:
            continue
        merged = dict(row)
        merged["date"] = date
        grouped.setdefault(ticker, []).append(merged)
    for ticker, ticker_rows in grouped.items():
        by_date = {str(row.get("date")): row for row in ticker_rows}
        grouped[ticker] = [by_date[date] for date in sorted(by_date)]
    return grouped


def load_local_behavior_history() -> list[dict]:
    path = Path("watchlist_behavior_history_latest.csv")
    if not path.exists():
        return []
    try:
        return pd.read_csv(path).to_dict(orient="records")
    except Exception as exc:
        print(f"Local behavior-history load skipped: {exc}")
        return []


def load_local_run_metadata() -> dict:
    path = Path("daily_watchlist_run_metadata_latest.json")
    if not path.exists():
        return {}
    try:
        metadata = json.loads(path.read_text())
        payload = metadata.get("payload") if isinstance(metadata.get("payload"), dict) else {}
        return {**payload, "publication_id": metadata.get("publication_id"), "run_date": metadata.get("run_date")}
    except Exception as exc:
        print(f"Local run-metadata load skipped: {exc}")
        return {}


def append_incremental_behavior_row(previous_rows: list[dict], current_row: dict, history_days: int) -> list[dict]:
    """Append one live session and recompute only transition-dependent overlays."""
    current_date = str(current_row.get("date") or "")
    retained = [dict(row) for row in previous_rows if str(row.get("date") or "") < current_date]
    combined = [*retained[-max(0, history_days - 1):], dict(current_row)]
    return [apply_anti_signal_penalty(row) for row in enrich_signal_transitions(combined)]


def freeze_final_signal_history(history_rows: list[dict], final_rows: list[dict], history_days: int) -> list[dict]:
    """Persist the exact post-learning/post-calibration signal shown to users."""
    grouped = behavior_history_by_ticker(history_rows)
    for final in final_rows:
        ticker = str(final.get("ticker") or "").upper()
        signal_date = str(final.get("date") or "")
        if not ticker or not signal_date:
            continue
        prior = [row for row in grouped.get(ticker, []) if str(row.get("date") or "") < signal_date]
        grouped[ticker] = [*prior[-max(0, history_days - 1):], dict(final)]
    return [row for ticker in sorted(grouped) for row in grouped[ticker][-history_days:]]


def preserve_failed_ticker_history(
    current_history: list[dict],
    previous_by_ticker: dict[str, list[dict]],
    expected_tickers: set[str],
    history_days: int,
) -> list[dict]:
    """Keep unsettled signal lifecycles when one ticker fails a daily scan."""
    present = {str(row.get("ticker") or "").upper() for row in current_history}
    preserved = list(current_history)
    for ticker in sorted(expected_tickers - present):
        preserved.extend(dict(row) for row in previous_by_ticker.get(ticker, [])[-history_days:])
    return preserved


def load_previous_local_report(run_date: str) -> list[dict]:
    candidates: list[tuple[str, Path]] = []
    for path in Path(".").glob("daily_watchlist_overview_*.csv"):
        stem_date = path.stem.replace("daily_watchlist_overview_", "")
        if stem_date == "latest" or stem_date >= run_date:
            continue
        if len(stem_date) == 10:
            candidates.append((stem_date, path))
    if not candidates:
        return []
    _, path = sorted(candidates)[-1]
    try:
        return pd.read_csv(path).to_dict(orient="records")
    except Exception as exc:
        print(f"Previous local report load skipped ({path}): {exc}")
        return []


def prior_signal_hard_gate_status(prior: dict, prior_action: str) -> tuple[bool, list[str]]:
    """Require the stored signal to satisfy the same execution boundary as live rows."""
    gates = {
        "market": prior.get("market_permission"),
        "ticker": prior.get("ticker_permission"),
        "risk": prior.get("risk_permission"),
        "walk-forward": prior.get("walk_forward_permission"),
    }
    blocked = [name for name, value in gates.items() if str(value or "UNKNOWN").upper() != "ALLOW"]
    if prior_action in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"} and not is_affirmative(
        prior.get("personality_setup_allowed")
    ):
        blocked.append("personality setup")
    return not blocked, blocked


def self_score_prior_signal(prior: dict, current: dict, evaluation_run_date: str) -> dict:
    prior_action = prior.get("action", "")
    prior_close = numeric_or_none(prior.get("close"))
    current_close = numeric_or_none(current.get("close"))
    comparison_stale = (
        str(prior.get("freshness_block") or "").upper() == "YES"
        or str(current.get("freshness_block") or "").upper() == "YES"
    )
    executable_action = prior_action in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}
    hard_gates_allow, hard_gate_blockers = prior_signal_hard_gate_status(prior, prior_action)
    entry_eligible = executable_action and hard_gates_allow
    zone_low = numeric_or_none(prior.get("entry_zone_low"))
    zone_high = numeric_or_none(prior.get("entry_zone_high"))
    entry_est = numeric_or_none(prior.get("entry_est"))
    if zone_low is None or zone_high is None or zone_high < zone_low:
        zone_low = entry_est
        zone_high = entry_est
    current_low = numeric_or_none(current.get("low"))
    current_high = numeric_or_none(current.get("high"))
    current_open = numeric_or_none(current.get("open"))
    entry_filled = False
    entry_fill_est = None
    stop_est = numeric_or_none(prior.get("stop_est"))
    stop_hit = False
    outcome_learnable = hard_gates_allow

    # Executable outcomes require a complete next-session OHLC bar. A close
    # alone cannot tell whether the planned zone filled before the stop.
    if not hard_gates_allow:
        return_pct = ""
        outcome = "NON_LEARNABLE"
        score = 0.0
        reason = f"Prior execution gate blocked ({', '.join(hard_gate_blockers)}); excluded from learning."
    elif executable_action:
        valid_ohlc = all(value is not None for value in (current_open, current_high, current_low, current_close))
        valid_plan = (
            zone_low is not None
            and zone_high is not None
            and stop_est is not None
            and float(zone_low) <= float(zone_high)
            and float(stop_est) < float(zone_low)
        )
        # Stale data is never allowed to turn an intraday low into a stop
        # outcome. It is excluded before any fill or stop inference.
        if comparison_stale:
            return_pct = ""
            outcome = "PENDING"
            score = 0.0
            reason = "Signal comparison contains stale market data; excluded before entry and stop evaluation."
            outcome_learnable = False
        elif not valid_ohlc or not valid_plan:
            return_pct = ""
            outcome = "NON_LEARNABLE"
            score = 0.0
            reason = "Missing complete OHLC or a valid entry-zone/stop plan; excluded from learning."
            outcome_learnable = False
        elif float(current_open) <= float(stop_est):
            return_pct = ""
            outcome = "NON_LEARNABLE"
            score = 0.0
            reason = "Next session gapped through the planned stop before a valid entry; excluded from learning."
            outcome_learnable = False
        elif float(current_open) < float(zone_low):
            return_pct = ""
            outcome = "NON_LEARNABLE"
            score = 0.0
            reason = "Next session opened below the entry zone; intraday reclaim sequence is not learnable from OHLC alone."
            outcome_learnable = False
        elif float(current_open) <= float(zone_high):
            entry_filled = True
            entry_fill_est = float(current_open)
        elif float(current_low) <= float(zone_high) and float(current_high) >= float(zone_low):
            entry_filled = True
            entry_fill_est = float(zone_high)
        else:
            return_pct = ""
            outcome = "NOT_FILLED"
            score = 0.0
            reason = "Next session did not touch the planned entry zone; excluded from learning."
            outcome_learnable = False

        if entry_filled:
            stop_hit = float(current_low) <= float(stop_est)
            return_pct = (float(current_close) / float(entry_fill_est) - 1) * 100
            if stop_hit:
                outcome = "FAILED"
                score = -1.0
                reason = "Next-session low breached the planned stop after entry."
            elif prior_action in {"BUY CANDIDATE", "STRONG CONTINUATION"}:
                if return_pct >= SELF_SCORE_WORKING_RETURN_PCT:
                    outcome = "WORKING"
                    score = 1.0
                    reason = "Filled BUY met the next-session return threshold without a stop breach."
                elif return_pct <= SELF_SCORE_FAILED_RETURN_PCT:
                    outcome = "FAILED"
                    score = -1.0
                    reason = "Filled BUY failed its next-session return threshold."
                else:
                    outcome = "STALE"
                    score = 0.0
                    reason = "Filled BUY did not progress enough without breaching its stop."
            else:
                if return_pct >= 1.0:
                    outcome = "WORKING"
                    score = 1.0
                    reason = "Filled BUILDING setup met the next-session return threshold without a stop breach."
                elif return_pct <= -2.5:
                    outcome = "FAILED"
                    score = -1.0
                    reason = "Filled BUILDING setup failed its next-session return threshold."
                else:
                    outcome = "STALE"
                    score = 0.0
                    reason = "Filled BUILDING setup remains unresolved without a stop breach."
    elif not prior_close or not current_close or float(prior_close) <= 0:
        return_pct = ""
        outcome = "PENDING"
        score = 0.0
        reason = "No valid close result yet."
        outcome_learnable = False
    else:
        return_pct = (float(current_close) / float(prior_close) - 1) * 100
        if comparison_stale:
            outcome = "PENDING"
            score = 0.0
            reason = "Signal comparison contains stale market data; excluded from learning."
            outcome_learnable = False
        elif prior_action == "WATCH TREND":
            if return_pct >= SELF_SCORE_WORKING_RETURN_PCT:
                outcome = "WORKING"
                score = 0.7
                reason = "WATCH trend met the next-session return threshold."
            elif return_pct <= -3.0:
                outcome = "FAILED"
                score = -0.7
                reason = "WATCH trend deteriorated beyond its next-session threshold."
            else:
                outcome = "STALE"
                score = 0.0
                reason = "WATCH trend stayed within its neutral next-session range."
        elif prior_action == "EXIT PRESSURE":
            if return_pct <= SELF_SCORE_EXIT_AVOIDED_RETURN_PCT:
                outcome = "TRAP_AVOIDED"
                score = 1.0
                reason = "EXIT pressure correctly warned of weak next-session follow-through."
            elif return_pct >= 2.5:
                outcome = "FAILED"
                score = -0.7
                reason = "EXIT pressure was too defensive before a strong next session."
            else:
                outcome = "STALE"
                score = 0.0
                reason = "EXIT pressure remains unresolved by next-session price action."
        elif prior_action in {"WAIT", "WAIT / AVOID"}:
            if return_pct <= (-1.0 if prior_action == "WAIT" else 0.5):
                outcome = "TRAP_AVOIDED"
                score = 0.7
                reason = "WAIT correctly avoided weak next-session follow-through."
            elif return_pct >= 2.5:
                outcome = "FAILED"
                score = -0.5
                reason = "WAIT was too defensive before a strong next session."
            else:
                outcome = "STALE"
                score = 0.0
                reason = "WAIT remains unresolved by next-session price action."
        else:
            outcome = "PENDING"
            score = 0.0
            reason = "Prior row was not a scored signal type."
            outcome_learnable = False

    learning_key = "|".join(
        [
            str(prior_action or "UNKNOWN"),
            str(prior.get("setup") or "NONE"),
            str(prior.get("personality_type") or "UNKNOWN"),
            str(prior.get("operator_state") or "NEUTRAL"),
            str(prior.get("anti_signal_level") or "NONE"),
        ]
    )
    return {
        "signal_run_date": prior.get("run_date") or prior.get("date") or prior.get("data_date"),
        "evaluation_run_date": evaluation_run_date,
        "ticker": prior.get("ticker"),
        "prior_action": prior_action,
        "prior_setup": prior.get("setup"),
        "prior_buy_tier": prior.get("buy_tier"),
        "prior_execution_style": prior.get("execution_style") or execution_style_for_setup(prior.get("setup")),
        "prior_operator_state": prior.get("operator_state"),
        "prior_anti_signal_level": prior.get("anti_signal_level"),
        # Freeze the forecast made at signal time. Later learning must never
        # overwrite the probability used for an outcome-calibration audit.
        "prior_prediction_upside_probability": numeric_or_none(prior.get("prediction_upside_probability")),
        "prior_prediction_downside_probability": numeric_or_none(prior.get("prediction_downside_probability")),
        "prior_prediction_no_edge_probability": numeric_or_none(prior.get("prediction_no_edge_probability")),
        "prior_prediction_confidence": numeric_or_none(prior.get("prediction_confidence")),
        "prior_prediction_state": prior.get("prediction_state"),
        "prior_prediction_key": prior.get("learning_key_used"),
        "prior_prediction_scope": prior.get("learning_scope"),
        "prior_close": round(float(prior_close), 2) if prior_close else "",
        "entry_model_version": LEARNING_MODEL_VERSION,
        "entry_eligible": entry_eligible,
        "entry_filled": entry_filled,
        "entry_fill_est": round(float(entry_fill_est), 2) if entry_fill_est else "",
        "stop_hit": stop_hit,
        "outcome_learnable": outcome_learnable,
        "current_action": current.get("action"),
        "current_operator_state": current.get("operator_state"),
        "current_close": round(float(current_close), 2) if current_close else "",
        "close_return_pct": round(float(return_pct), 2) if return_pct != "" else "",
        "outcome_label": outcome,
        "outcome_score": score,
        "outcome_reason": reason,
        "learning_key": learning_key,
    }


def build_daily_signal_outcomes(previous_rows: list[dict], current_rows: list[dict], evaluation_run_date: str) -> pd.DataFrame:
    current_by_ticker = {str(row.get("ticker", "")).upper(): row for row in current_rows}
    outcomes = []
    for prior in previous_rows:
        prior_action = prior.get("action", "")
        ticker = str(prior.get("ticker", "")).upper()
        if prior_action not in SELF_SCORE_ACTIONS or ticker not in current_by_ticker:
            continue
        outcomes.append(self_score_prior_signal(prior, current_by_ticker[ticker], evaluation_run_date))
    return pd.DataFrame(outcomes)


def score_signal_horizon(prior: dict, future_rows: list[dict], horizon_sessions: int = LEARNING_HORIZON_SESSIONS) -> dict:
    """Settle a planned entry using only daily bars available after the signal.

    Daily OHLC cannot establish intraday order when entry, stop, and target all
    trade in the same bar. Those cases are deliberately marked ambiguous rather
    than invented into wins or losses.
    """
    horizon = max(1, int(horizon_sessions))
    prior_action = str(prior.get("action") or "")
    final_row = future_rows[min(len(future_rows), horizon) - 1] if future_rows else {}
    evaluation_date = canonical_date(final_row.get("date") or final_row.get("history_date"))
    base = {
        "signal_run_date": canonical_date(prior.get("run_date") or prior.get("date") or prior.get("data_date")),
        "evaluation_run_date": evaluation_date,
        "ticker": prior.get("ticker"),
        "prior_action": prior_action,
        "prior_setup": prior.get("setup"),
        "prior_buy_tier": prior.get("buy_tier"),
        "prior_execution_style": prior.get("execution_style") or execution_style_for_setup(prior.get("setup")),
        "prior_operator_state": prior.get("operator_state"),
        "prior_anti_signal_level": prior.get("anti_signal_level"),
        "prior_personality_type": prior.get("personality_type"),
        "prior_market_permission": prior.get("market_permission"),
        "prior_ticker_permission": prior.get("ticker_permission"),
        "prior_risk_permission": prior.get("risk_permission"),
        "prior_walk_forward_permission": prior.get("walk_forward_permission"),
        "prior_personality_setup_allowed": prior.get("personality_setup_allowed"),
        "prior_entry_zone_low": numeric_or_none(prior.get("entry_zone_low")),
        "prior_entry_zone_high": numeric_or_none(prior.get("entry_zone_high")),
        "prior_entry_est": numeric_or_none(prior.get("entry_est")),
        "prior_stop_est": numeric_or_none(prior.get("stop_est")),
        "prior_target_est": numeric_or_none(prior.get("target_est")),
        "prior_prediction_upside_probability": numeric_or_none(prior.get("prediction_upside_probability")),
        "prior_prediction_downside_probability": numeric_or_none(prior.get("prediction_downside_probability")),
        "prior_prediction_no_edge_probability": numeric_or_none(prior.get("prediction_no_edge_probability")),
        "prior_prediction_confidence": numeric_or_none(prior.get("prediction_confidence")),
        "prior_prediction_state": prior.get("prediction_state"),
        "prior_prediction_key": prior.get("learning_key_used"),
        "prior_prediction_scope": prior.get("learning_scope"),
        "prior_close": numeric_or_none(prior.get("close")) or "",
        "entry_model_version": LEARNING_MODEL_VERSION,
        "label_horizon_sessions": horizon,
        "path_status": "PENDING",
        "entry_eligible": False,
        "entry_filled": False,
        "entry_fill_est": "",
        "stop_hit": False,
        "target_hit": False,
        "mfe_pct": "",
        "mae_pct": "",
        "relative_return_pct": "",
        "current_action": final_row.get("action"),
        "current_operator_state": final_row.get("operator_state"),
        "current_close": numeric_or_none(final_row.get("close")) or "",
        "close_return_pct": "",
        "outcome_label": "PENDING",
        "outcome_score": 0.0,
        "outcome_reason": "Awaiting a complete five-session evaluation window.",
        "outcome_learnable": False,
        "forecast_learnable": False,
    }
    base["learning_key"] = "|".join([
        prior_action or "UNKNOWN", str(prior.get("setup") or "NONE"),
        str(prior.get("personality_type") or "UNKNOWN"), str(prior.get("operator_state") or "NEUTRAL"),
        str(prior.get("anti_signal_level") or "NONE"),
    ])
    if len(future_rows) < horizon:
        return base

    gates_allow, gate_blockers = prior_signal_hard_gate_status(prior, prior_action)
    executable = prior_action in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}
    if not executable:
        base.update({
            "path_status": "NON_EXECUTABLE",
            "outcome_label": "NON_LEARNABLE",
            "outcome_reason": "The v4 first-hit model only learns planned entry, stop, and target paths.",
        })
        return base
    if not gates_allow:
        base["outcome_reason"] = (
            f"Execution was blocked ({', '.join(gate_blockers)}); "
            "the OHLCV path is retained only for forecast calibration."
        )

    zone_low = numeric_or_none(prior.get("entry_zone_low")) or numeric_or_none(prior.get("entry_est"))
    zone_high = numeric_or_none(prior.get("entry_zone_high")) or zone_low
    stop = numeric_or_none(prior.get("stop_est"))
    if zone_low is None or zone_high is None or stop is None or float(zone_high) < float(zone_low) or float(stop) >= float(zone_low):
        base.update({"path_status": "UNUSABLE", "outcome_label": "NON_LEARNABLE", "outcome_reason": "Missing a valid entry zone or stop; excluded from learning."})
        return base

    entry = None
    target = None
    entry_opened_above_zone = False
    highs: list[float] = []
    lows: list[float] = []
    for offset, bar in enumerate(future_rows[:horizon], start=1):
        open_, high, low, close = (numeric_or_none(bar.get(field)) for field in ("open", "high", "low", "close"))
        if any(value is None for value in (open_, high, low, close)):
            base.update({"path_status": "UNUSABLE", "outcome_label": "NON_LEARNABLE", "outcome_reason": "Incomplete OHLC inside the evaluation window; excluded from learning."})
            return base
        if entry is None:
            if float(open_) <= float(stop):
                base.update({"path_status": "GAP", "outcome_label": "NON_LEARNABLE", "outcome_reason": "Price gapped through the stop before a valid entry."})
                return base
            touches_zone = float(low) <= float(zone_high) and float(high) >= float(zone_low)
            if not touches_zone:
                continue
            if float(low) <= float(stop):
                base.update({"path_status": "AMBIGUOUS", "outcome_label": "NON_LEARNABLE", "outcome_reason": "Daily bar touched both the entry area and stop; intraday order is unknown."})
                return base
            entry_opened_above_zone = float(open_) > float(zone_high)
            entry = float(open_) if float(zone_low) <= float(open_) <= float(zone_high) else float(zone_high)
            target = numeric_or_none(prior.get("target_est")) or entry + (entry - float(stop))
            base.update({"entry_eligible": gates_allow, "entry_filled": True, "entry_fill_est": round(entry, 2)})
        highs.append(float(high))
        lows.append(float(low))
        hit_stop, hit_target = float(low) <= float(stop), float(high) >= float(target)
        if hit_stop and hit_target:
            base.update({"path_status": "AMBIGUOUS", "outcome_label": "NON_LEARNABLE", "outcome_reason": "Daily bar touched both stop and target; intraday order is unknown."})
            return base
        if hit_target and entry_opened_above_zone and len(highs) == 1:
            base.update({"path_status": "AMBIGUOUS", "outcome_label": "NON_LEARNABLE", "outcome_reason": "Entry zone and target were both touched after opening above the zone; intraday order is unknown."})
            return base
        if hit_target or hit_stop:
            mfe = (max(highs) / entry - 1) * 100
            mae = (min(lows) / entry - 1) * 100
            close_return = (float(close) / entry - 1) * 100
            base.update({
                "path_status": "SETTLED", "target_hit": hit_target, "stop_hit": hit_stop,
                "evaluation_run_date": canonical_date(bar.get("date") or bar.get("history_date")) or evaluation_date,
                "mfe_pct": round(mfe, 2), "mae_pct": round(mae, 2), "close_return_pct": round(close_return, 2),
                "current_close": round(float(close), 2), "outcome_learnable": gates_allow, "forecast_learnable": True,
                "outcome_label": "WORKING" if hit_target else "FAILED", "outcome_score": 1.0 if hit_target else -1.0,
                "outcome_reason": f"{'Target' if hit_target else 'Stop'} was reached first within {offset} session(s).",
            })
            return base

    if entry is None:
        base.update({"path_status": "NOT_FILLED", "outcome_label": "NOT_FILLED", "outcome_reason": f"Price did not enter the planned zone within {horizon} sessions."})
        return base
    final_close = numeric_or_none(future_rows[horizon - 1].get("close"))
    base.update({
        "path_status": "SETTLED", "outcome_learnable": gates_allow, "forecast_learnable": True, "outcome_label": "STALE", "outcome_score": 0.0,
        "mfe_pct": round((max(highs) / entry - 1) * 100, 2), "mae_pct": round((min(lows) / entry - 1) * 100, 2),
        "close_return_pct": round((float(final_close) / entry - 1) * 100, 2) if final_close else "",
        "current_close": round(float(final_close), 2) if final_close else "",
        "outcome_reason": f"Entry filled but neither target nor stop was reached within {horizon} sessions.",
    })
    return base


def build_backfilled_signal_outcomes(history_rows: list[dict]) -> pd.DataFrame:
    """Convert generated behavior replay rows into settled learning samples.

    Daily self-scoring starts once production snapshots exist. Behavior history
    already contains prior-day reads, so seed the same outcome table from that
    replay instead of making learning wait for new calendar days.
    """
    if not history_rows:
        return pd.DataFrame()

    by_ticker: dict[str, list[dict]] = {}
    for row in history_rows:
        ticker = str(row.get("ticker", "")).upper()
        history_date = row.get("date") or row.get("history_date") or row.get("data_date")
        if not ticker or not history_date:
            continue
        merged = dict(row)
        merged["date"] = str(history_date)
        merged["data_date"] = str(history_date)
        merged["run_date"] = str(history_date)
        by_ticker.setdefault(ticker, []).append(merged)

    outcomes: list[dict] = []
    for ticker_rows in by_ticker.values():
        by_date = {str(item.get("date") or ""): item for item in sorted(ticker_rows, key=lambda item: str(item.get("date") or ""))}
        ordered = [by_date[date] for date in sorted(date for date in by_date if date)]
        for index, prior in enumerate(ordered[:-1]):
            prior_action = prior.get("action", "")
            if prior_action not in SELF_SCORE_ACTIONS:
                continue
            outcomes.append(score_signal_horizon(prior, ordered[index + 1 : index + 1 + LEARNING_HORIZON_SESSIONS]))

    if not outcomes:
        return pd.DataFrame()

    frame = pd.DataFrame(outcomes)
    return frame.drop_duplicates(subset=["signal_run_date", "evaluation_run_date", "ticker"], keep="last")


def combine_signal_outcomes(*frames: pd.DataFrame) -> pd.DataFrame:
    usable = [frame for frame in frames if frame is not None and not frame.empty]
    if not usable:
        return pd.DataFrame()
    combined = pd.concat(usable, ignore_index=True)
    if {"signal_run_date", "ticker"}.issubset(combined.columns):
        combined["_canonical_signal_id"] = combined.apply(
            lambda row: "|".join(str(value) for value in signal_outcome_identity(row.to_dict())),
            axis=1,
        )
        combined = combined.drop_duplicates(subset=["_canonical_signal_id"], keep="last")
        combined = combined.drop(columns=["_canonical_signal_id"])
    return combined


def signal_outcome_identity(row: dict) -> tuple[str, str, str, int]:
    return (
        str(row.get("ticker") or "").upper(),
        canonical_date(row.get("signal_run_date")),
        str(row.get("entry_model_version") or LEARNING_MODEL_VERSION),
        int(numeric_or_none(row.get("label_horizon_sessions")) or LEARNING_HORIZON_SESSIONS),
    )


def build_incremental_signal_outcomes(
    behavior_rows: list[dict],
    raw_frames: dict[str, pd.DataFrame],
    existing_outcomes: pd.DataFrame,
) -> pd.DataFrame:
    """Settle only canonical signals whose five-session path is now available."""
    existing_ids = {
        signal_outcome_identity(row)
        for row in (existing_outcomes.to_dict(orient="records") if not existing_outcomes.empty else [])
    }
    candidates = behavior_history_by_ticker(behavior_rows)
    settled: list[dict] = []
    executable_actions = {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}
    for ticker, ticker_rows in candidates.items():
        raw = raw_frames.get(ticker)
        if raw is None or raw.empty:
            continue
        bars = raw.copy()
        bars["date"] = pd.to_datetime(bars["date"], errors="coerce")
        bars = bars.dropna(subset=["date"]).sort_values("date")
        for prior in ticker_rows:
            if str(prior.get("action") or "") not in executable_actions:
                continue
            identity = signal_outcome_identity({
                **prior,
                "signal_run_date": prior.get("date"),
                "entry_model_version": LEARNING_MODEL_VERSION,
                "label_horizon_sessions": LEARNING_HORIZON_SESSIONS,
            })
            if identity in existing_ids:
                continue
            signal_date = pd.to_datetime(prior.get("date"), errors="coerce")
            if pd.isna(signal_date):
                continue
            future = bars.loc[bars["date"] > signal_date].head(LEARNING_HORIZON_SESSIONS)
            if len(future) < LEARNING_HORIZON_SESSIONS:
                continue
            outcome = score_signal_horizon(prior, future.to_dict(orient="records"))
            settled.append(outcome)
            existing_ids.add(identity)
    return pd.DataFrame(settled)


def rebuild_canonical_signal_outcomes(
    canonical_outcomes: pd.DataFrame,
    raw_frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Re-score frozen production plans against the canonical OHLCV path."""
    rebuilt: list[dict] = []
    if canonical_outcomes is None or canonical_outcomes.empty:
        return pd.DataFrame()
    for raw_outcome in canonical_outcomes.to_dict(orient="records"):
        outcome = merge_payload_row(raw_outcome)
        if str(outcome.get("entry_model_version") or "") != LEARNING_MODEL_VERSION:
            continue
        ticker = str(outcome.get("ticker") or "").upper()
        bars = raw_frames.get(ticker)
        signal_date = pd.to_datetime(outcome.get("signal_run_date"), errors="coerce")
        if bars is None or bars.empty or pd.isna(signal_date):
            continue
        future = bars.copy()
        future["date"] = pd.to_datetime(future["date"], errors="coerce")
        future = future.loc[future["date"] > signal_date].dropna(subset=["date"]).sort_values("date").head(LEARNING_HORIZON_SESSIONS)
        if len(future) < LEARNING_HORIZON_SESSIONS:
            continue
        prior = {
            "ticker": ticker,
            "date": str(outcome.get("signal_run_date") or ""),
            "action": outcome.get("prior_action"),
            "setup": outcome.get("prior_setup"),
            "buy_tier": outcome.get("prior_buy_tier"),
            "execution_style": outcome.get("prior_execution_style") or execution_style_for_setup(outcome.get("prior_setup")),
            "operator_state": outcome.get("prior_operator_state"),
            "anti_signal_level": outcome.get("prior_anti_signal_level"),
            "personality_type": outcome.get("prior_personality_type"),
            "market_permission": outcome.get("prior_market_permission"),
            "ticker_permission": outcome.get("prior_ticker_permission"),
            "risk_permission": outcome.get("prior_risk_permission"),
            "walk_forward_permission": outcome.get("prior_walk_forward_permission"),
            "personality_setup_allowed": outcome.get("prior_personality_setup_allowed"),
            "entry_zone_low": outcome.get("prior_entry_zone_low"),
            "entry_zone_high": outcome.get("prior_entry_zone_high"),
            "entry_est": outcome.get("prior_entry_est"),
            "stop_est": outcome.get("prior_stop_est"),
            "target_est": outcome.get("prior_target_est"),
            "close": outcome.get("prior_close"),
            "prediction_upside_probability": outcome.get("prior_prediction_upside_probability"),
            "prediction_downside_probability": outcome.get("prior_prediction_downside_probability"),
            "prediction_no_edge_probability": outcome.get("prior_prediction_no_edge_probability"),
            "prediction_confidence": outcome.get("prior_prediction_confidence"),
            "prediction_state": outcome.get("prior_prediction_state"),
            "learning_key_used": outcome.get("prior_prediction_key"),
            "learning_scope": outcome.get("prior_prediction_scope"),
        }
        rebuilt.append(score_signal_horizon(prior, future.to_dict(orient="records")))
    return pd.DataFrame(rebuilt)


def replay_start_dates(raw_frames: dict[str, pd.DataFrame], sessions: int) -> dict[str, str]:
    starts: dict[str, str] = {}
    for ticker, frame in raw_frames.items():
        if frame is None or frame.empty or "date" not in frame:
            continue
        dates = pd.to_datetime(frame["date"], errors="coerce").dropna().drop_duplicates().sort_values()
        if dates.empty:
            continue
        starts[display_ticker(ticker)] = str(dates.tail(max(1, sessions)).iloc[0].date())
    return starts


def calibration_parity_report(
    incremental: pd.DataFrame,
    rebuilt: pd.DataFrame,
    replay_starts: dict[str, str],
) -> dict:
    """Compare settled canonical outcomes without tolerating identity drift."""
    def settled_map(frame: pd.DataFrame) -> dict[tuple[str, str, str, int], tuple[str, str]]:
        if frame is None or frame.empty:
            return {}
        result = {}
        for raw in frame.to_dict(orient="records"):
            row = merge_payload_row(raw)
            if str(row.get("path_status") or "").upper() != "SETTLED":
                continue
            result[signal_outcome_identity(row)] = (
                str(row.get("outcome_label") or "").upper(),
                canonical_date(row.get("evaluation_run_date")),
            )
        return result

    incremental_map = settled_map(incremental)
    rebuilt_map = settled_map(rebuilt)
    shared = set(incremental_map) & set(rebuilt_map)
    mismatched = sorted(key for key in shared if incremental_map[key] != rebuilt_map[key])
    incremental_cutoff = max((value[1] for value in incremental_map.values()), default="")
    missing_from_incremental = sorted(
        key
        for key in set(rebuilt_map) - set(incremental_map)
        if not incremental_cutoff or rebuilt_map[key][1] <= incremental_cutoff
    )
    newly_available = sorted(
        key
        for key in set(rebuilt_map) - set(incremental_map)
        if incremental_cutoff and rebuilt_map[key][1] > incremental_cutoff
    )
    rebuilt_cutoff = max((value[1] for value in rebuilt_map.values()), default="")
    missing_from_rebuild = sorted(
        key
        for key in set(incremental_map) - set(rebuilt_map)
        if (not replay_starts.get(key[0]) or key[1] >= replay_starts[key[0]])
        and (not rebuilt_cutoff or incremental_map[key][1] <= rebuilt_cutoff)
    )
    older_outside_rebuild = sorted(
        key
        for key in set(incremental_map) - set(rebuilt_map)
        if replay_starts.get(key[0]) and key[1] < replay_starts[key[0]]
    )
    # Incremental state may retain older identities outside the bounded replay,
    # but every identity inside the rebuilt signal/evaluation window must match.
    passed = bool(shared) and not mismatched and not missing_from_incremental and not missing_from_rebuild
    return {
        "passed": passed,
        "incremental_settled": len(incremental_map),
        "rebuilt_settled": len(rebuilt_map),
        "shared_settled": len(shared),
        "mismatched": len(mismatched),
        "missing_from_incremental": len(missing_from_incremental),
        "missing_from_rebuild": len(missing_from_rebuild),
        "older_outside_rebuild": len(older_outside_rebuild),
        "newly_available": len(newly_available),
        "sample_mismatches": [list(item) for item in mismatched[:10]],
    }


def attach_latest_outcomes(rows: list[dict], outcomes: pd.DataFrame) -> None:
    if outcomes.empty:
        return
    sortable = outcomes.copy()
    if "evaluation_run_date" in sortable.columns:
        sortable = sortable.sort_values("evaluation_run_date")
    outcome_by_ticker = {str(row["ticker"]).upper(): row for row in sortable.to_dict(orient="records")}
    for row in rows:
        outcome = outcome_by_ticker.get(str(row.get("ticker", "")).upper())
        if not outcome:
            continue
        row["last_outcome_label"] = outcome.get("outcome_label")
        row["last_outcome_score"] = outcome.get("outcome_score")
        row["last_outcome_reason"] = outcome.get("outcome_reason")
        row["last_outcome_return_pct"] = outcome.get("close_return_pct")


def summarize_signal_outcomes(outcomes: pd.DataFrame) -> dict:
    if outcomes.empty:
        return {"total": 0, "counts": {}, "avg_score": None}
    counts = outcomes["outcome_label"].value_counts().to_dict()
    return {
        "total": int(len(outcomes)),
        "counts": {key: int(value) for key, value in counts.items()},
        "avg_score": round(float(outcomes["outcome_score"].mean()), 3),
    }


def learning_key_for(row: dict) -> str:
    return "|".join(
        [
            str(row.get("action") or "UNKNOWN"),
            str(row.get("setup") or "NONE"),
            str(row.get("personality_type") or "UNKNOWN"),
            str(row.get("operator_state") or "NEUTRAL"),
            str(row.get("anti_signal_level") or "NONE"),
        ]
    )


def learning_action_setup_key(action: object, setup: object) -> str:
    return f"ACTION_SETUP|{action or 'UNKNOWN'}|{setup or 'NONE'}"


def learning_action_key(action: object) -> str:
    return f"ACTION|{action or 'UNKNOWN'}"


def learning_key_candidates_for(row: dict) -> list[tuple[str, str, float]]:
    action = row.get("action") or "UNKNOWN"
    setup = row.get("setup") or "NONE"
    return [
        (learning_key_for(row), "exact signal personality", 1.0),
        (learning_action_setup_key(action, setup), "action/setup family", 0.65),
        (learning_action_key(action), "action family", 0.45),
    ]


def restrict_learning_outcomes_to_window(
    outcomes: pd.DataFrame,
    run_date: Optional[str] = None,
    lookback_days: int = LEARNING_LOOKBACK_DAYS,
) -> pd.DataFrame:
    """Keep one trailing window of settled evaluation trading sessions."""
    if outcomes is None or outcomes.empty or "evaluation_run_date" not in outcomes.columns:
        return pd.DataFrame() if outcomes is None else outcomes.copy()

    parsed_dates = pd.to_datetime(outcomes["evaluation_run_date"], errors="coerce").dt.normalize()
    eligible = parsed_dates.notna()
    if run_date:
        cutoff_day = pd.to_datetime(run_date, errors="coerce")
        if pd.isna(cutoff_day):
            return outcomes.iloc[0:0].copy()
        eligible &= parsed_dates < cutoff_day.normalize()

    sessions = sorted(parsed_dates.loc[eligible].dropna().unique())
    if not sessions:
        return outcomes.iloc[0:0].copy()
    selected_sessions = sessions[-max(1, int(lookback_days)):]
    selected = outcomes.loc[eligible & parsed_dates.isin(selected_sessions)].copy()
    selected.attrs["learning_window"] = {
        "lookback_days": max(1, int(lookback_days)),
        "evaluation_date_min": pd.Timestamp(selected_sessions[0]).date().isoformat(),
        "evaluation_date_max": pd.Timestamp(selected_sessions[-1]).date().isoformat(),
        "evaluation_session_count": len(selected_sessions),
    }
    return selected


def load_local_signal_outcomes(run_date: str) -> pd.DataFrame:
    frames = []
    for path in sorted(Path(".").glob("daily_signal_outcomes_*.csv")):
        stem_date = path.stem.replace("daily_signal_outcomes_", "")
        if stem_date == "latest" or stem_date > run_date or len(stem_date) != 10:
            continue
        try:
            frames.append(pd.read_csv(path))
        except Exception as exc:
            print(f"Local signal-outcome history load skipped ({path}): {exc}")
    if not frames:
        return pd.DataFrame()
    return restrict_learning_outcomes_to_window(pd.concat(frames, ignore_index=True), run_date)


def fetch_signal_outcome_history(run_date: str) -> pd.DataFrame:
    try:
        run_timestamp = pd.Timestamp(run_date)
        cutoff = (run_timestamp - pd.Timedelta(days=max(90, LEARNING_LOOKBACK_DAYS * 3))).date().isoformat()
        validated_runs = supabase_select(
            "watchlist_refresh_runs?select=payload&status=in.(ok,degraded)&"
            f"run_date=lte.{urllib.parse.quote(run_date)}&run_date=gte.{urllib.parse.quote(cutoff)}&limit=200"
        )
        publication_ids = sorted({
            str((record.get("payload") or {}).get("publication_id") or "")
            for record in validated_runs
            if isinstance(record.get("payload"), dict)
            and (record.get("payload") or {}).get("sync_state") == "complete"
            and (record.get("payload") or {}).get("publication_id")
        })
        if not publication_ids:
            return load_local_signal_outcomes(run_date)
        publication_filter = ",".join(urllib.parse.quote(value, safe="") for value in publication_ids)
        rows: list[dict] = []
        page_size = 1000
        for offset in range(0, 25000, page_size):
            page = supabase_select(
                "watchlist_signal_outcomes?"
                "select=*&"
                f"evaluation_run_date=lt.{urllib.parse.quote(run_date)}&"
                f"evaluation_run_date=gte.{urllib.parse.quote(cutoff)}&"
                f"publication_id=in.({publication_filter})&"
                "outcome_label=neq.PENDING&"
                f"order=evaluation_run_date.desc,signal_run_date.desc,ticker.asc&limit={page_size}&offset={offset}"
            )
            rows.extend(page)
            if len(page) < page_size:
                break
        if rows:
            return restrict_learning_outcomes_to_window(pd.DataFrame([merge_payload_row(row) for row in rows]), run_date)
    except RuntimeError as exc:
        print(f"Signal-outcome history fetch skipped: {exc}")
    return load_local_signal_outcomes(run_date)


def build_learning_stats(
    outcome_history: pd.DataFrame,
    run_date: Optional[str] = None,
    lookback_days: int = LEARNING_LOOKBACK_DAYS,
) -> dict[str, dict]:
    outcome_history = restrict_learning_outcomes_to_window(outcome_history, run_date, lookback_days)
    if (
        outcome_history.empty
        or "learning_key" not in outcome_history.columns
        or "entry_model_version" not in outcome_history.columns
        or ("forecast_learnable" not in outcome_history.columns and "outcome_learnable" not in outcome_history.columns)
    ):
        return {}
    learnable_column = "forecast_learnable" if "forecast_learnable" in outcome_history.columns else "outcome_learnable"
    usable = outcome_history[
        outcome_history["outcome_label"].astype(str).str.upper().isin({"WORKING", "FAILED", "TRAP_AVOIDED", "STALE"})
        & outcome_history[learnable_column].map(is_affirmative)
    ].copy()
    # Every learning row must use the current executable entry model. Legacy
    # rows with no version are not comparable and must not influence weights.
    usable = usable[usable["entry_model_version"].astype(str) == LEARNING_MODEL_VERSION]
    if "label_horizon_sessions" in usable.columns:
        usable = usable[pd.to_numeric(usable["label_horizon_sessions"], errors="coerce") == LEARNING_HORIZON_SESSIONS]
    if "path_status" in usable.columns:
        usable = usable[usable["path_status"].astype(str).str.upper() == "SETTLED"]
    if usable.empty:
        return {}

    usable["learning_key_exact"] = usable["learning_key"].astype(str)
    usable["learning_key_action_setup"] = usable.apply(
        lambda row: learning_action_setup_key(row.get("prior_action"), row.get("prior_setup")),
        axis=1,
    )
    usable["learning_key_action"] = usable["prior_action"].apply(learning_action_key)

    stats: dict[str, dict] = {}
    grouped_sources = [
        ("learning_key_exact", "exact signal personality"),
        ("learning_key_action_setup", "action/setup family"),
        ("learning_key_action", "action family"),
    ]
    for column, scope in grouped_sources:
        for key, group in usable.groupby(column):
            labels = group["outcome_label"].astype(str).str.upper()
            scores = pd.to_numeric(group["outcome_score"], errors="coerce").dropna() if "outcome_score" in group.columns else pd.Series(dtype=float)
            returns = pd.to_numeric(group["close_return_pct"], errors="coerce").dropna() if "close_return_pct" in group.columns else pd.Series(dtype=float)
            total = int(len(group))
            working = int((labels == "WORKING").sum())
            failed = int((labels == "FAILED").sum())
            trap_avoided = int((labels == "TRAP_AVOIDED").sum())
            no_edge = int((labels == "STALE").sum())
            distinct_tickers = int(group["ticker"].dropna().astype(str).str.upper().nunique()) if "ticker" in group.columns else 0
            evaluation_series = pd.to_datetime(group["evaluation_run_date"], errors="coerce").dropna() if "evaluation_run_date" in group.columns else pd.Series(dtype="datetime64[ns]")
            evaluation_dates = int(evaluation_series.dt.normalize().nunique()) if not evaluation_series.empty else 0
            evaluation_date_min = evaluation_series.min().date().isoformat() if not evaluation_series.empty else ""
            evaluation_date_max = evaluation_series.max().date().isoformat() if not evaluation_series.empty else ""
            execution = group[group["outcome_learnable"].map(is_affirmative)].copy() if "outcome_learnable" in group.columns else pd.DataFrame()
            execution_labels = execution["outcome_label"].astype(str).str.upper() if not execution.empty else pd.Series(dtype=str)
            execution_scores = pd.to_numeric(execution["outcome_score"], errors="coerce").dropna() if "outcome_score" in execution.columns else pd.Series(dtype=float)
            execution_returns = pd.to_numeric(execution["close_return_pct"], errors="coerce").dropna() if "close_return_pct" in execution.columns else pd.Series(dtype=float)
            execution_total = int(len(execution))
            execution_tickers = int(execution["ticker"].dropna().astype(str).str.upper().nunique()) if "ticker" in execution.columns else 0
            execution_dates_series = pd.to_datetime(execution["evaluation_run_date"], errors="coerce").dropna() if "evaluation_run_date" in execution.columns else pd.Series(dtype="datetime64[ns]")
            execution_dates = int(execution_dates_series.dt.normalize().nunique()) if not execution_dates_series.empty else 0
            calibration = group.dropna(
                subset=[
                    "prior_prediction_upside_probability",
                    "prior_prediction_downside_probability",
                    "prior_prediction_no_edge_probability",
                ]
            ) if all(
                column in group.columns
                for column in (
                    "prior_prediction_upside_probability",
                    "prior_prediction_downside_probability",
                    "prior_prediction_no_edge_probability",
                )
            ) else pd.DataFrame()
            if not calibration.empty:
                valid_states = {"WALK_FORWARD", "REPORTING_ONLY", "CALIBRATED"}
                calibration = calibration[
                    calibration.get("prior_prediction_state", pd.Series(index=calibration.index, dtype=str)).astype(str).str.upper().isin(valid_states)
                    & (calibration.get("prior_prediction_key", pd.Series(index=calibration.index, dtype=str)).astype(str) == str(key))
                    & (calibration.get("prior_prediction_scope", pd.Series(index=calibration.index, dtype=str)).astype(str) == scope)
                ]
            brier_score = None
            if not calibration.empty:
                probability_columns = [
                    "prior_prediction_upside_probability",
                    "prior_prediction_downside_probability",
                    "prior_prediction_no_edge_probability",
                ]
                probabilities = calibration[probability_columns].apply(pd.to_numeric, errors="coerce")
                finite = pd.DataFrame(np.isfinite(probabilities), index=probabilities.index, columns=probabilities.columns).all(axis=1)
                valid = (
                    probabilities.notna().all(axis=1)
                    & finite
                    & probabilities.ge(0.0).all(axis=1)
                    & probabilities.le(1.0).all(axis=1)
                    & probabilities.sum(axis=1).sub(1.0).abs().le(1e-6)
                )
                calibration = calibration.loc[valid]
                probabilities = probabilities.loc[valid]
                if not calibration.empty:
                    calibration_labels = calibration["outcome_label"].astype(str).str.upper()
                    targets = np.column_stack(
                        [
                            (calibration_labels == "WORKING").astype(float),
                            (calibration_labels == "FAILED").astype(float),
                            calibration_labels.isin({"STALE", "TRAP_AVOIDED"}).astype(float),
                        ]
                    )
                    brier_score = float(np.mean(np.sum((probabilities.to_numpy(dtype=float) - targets) ** 2, axis=1)))
            stats[str(key)] = {
                "sample_count": total,
                "working_rate": working / total if total else 0.0,
                "failed_rate": failed / total if total else 0.0,
                "trap_avoided_rate": trap_avoided / total if total else 0.0,
                # Dirichlet smoothing avoids treating a small exact bucket as
                # a precise forecast. The remaining mass is explicit no-edge.
                "upside_probability": (working + 1) / (total + 3),
                "downside_probability": (failed + 1) / (total + 3),
                "no_edge_probability": (no_edge + trap_avoided + 1) / (total + 3),
                "avg_score": float(scores.mean()) if not scores.empty else 0.0,
                "avg_return_pct": float(returns.mean()) if not returns.empty else None,
                "execution_sample_count": execution_total,
                "execution_working_rate": float((execution_labels == "WORKING").sum()) / execution_total if execution_total else 0.0,
                "execution_failed_rate": float((execution_labels == "FAILED").sum()) / execution_total if execution_total else 0.0,
                "execution_trap_avoided_rate": float((execution_labels == "TRAP_AVOIDED").sum()) / execution_total if execution_total else 0.0,
                "execution_avg_score": float(execution_scores.mean()) if not execution_scores.empty else 0.0,
                "execution_avg_return_pct": float(execution_returns.mean()) if not execution_returns.empty else None,
                "execution_distinct_ticker_count": execution_tickers,
                "execution_evaluation_date_count": execution_dates,
                "scope": scope,
                "distinct_ticker_count": distinct_tickers,
                "evaluation_date_count": evaluation_dates,
                "evaluation_date_min": evaluation_date_min,
                "evaluation_date_max": evaluation_date_max,
                "model_version": LEARNING_MODEL_VERSION,
                "calibration_sample_count": int(len(calibration)),
                "brier_score": brier_score,
            }
    return stats


def fillability_key(execution_style: object, setup: object, personality: object = "ANY") -> str:
    return "|".join([
        str(execution_style or "NONE").upper(),
        str(setup or "NONE").upper(),
        str(personality or "ANY").upper(),
    ])


def fillability_key_candidates(row: dict) -> list[tuple[str, str]]:
    style = row.get("execution_style") or row.get("prior_execution_style") or execution_style_for_setup(
        row.get("setup") or row.get("prior_setup")
    )
    setup = row.get("setup") or row.get("prior_setup") or "NONE"
    personality = row.get("personality_type") or row.get("prior_personality_type") or "ANY"
    return [
        (fillability_key(style, setup, personality), "setup/personality"),
        (fillability_key(style, setup), "setup family"),
        (fillability_key(style, "ANY"), "execution style"),
    ]


def build_fillability_stats(outcome_history: pd.DataFrame) -> dict[str, dict]:
    """Learn whether a structurally valid entry plan trades, including NOT_FILLED.

    Fillability is an execution property, not a directional forecast. SETUP
    plans therefore provide valid evidence when the market, ticker, risk, and
    personality gates allowed the plan, even if walk-forward direction evidence
    was still accumulating. This avoids a cold-start loop where BUY needs proven
    fillability but fillability could previously learn only from existing BUYs.
    """
    required = {"entry_model_version", "path_status", "prior_action", "ticker", "signal_run_date"}
    if outcome_history is None or outcome_history.empty or not required.issubset(outcome_history.columns):
        return {}
    usable = outcome_history[
        (outcome_history["entry_model_version"].astype(str) == LEARNING_MODEL_VERSION)
        & outcome_history["prior_action"].astype(str).isin({"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"})
        & outcome_history["path_status"].astype(str).str.upper().isin({"SETTLED", "NOT_FILLED"})
    ].copy()
    for gate in ("prior_market_permission", "prior_ticker_permission", "prior_risk_permission"):
        if gate not in usable.columns:
            return {}
        usable = usable[usable[gate].astype(str).str.upper() == "ALLOW"]
    if "prior_personality_setup_allowed" not in usable.columns:
        return {}
    usable = usable[usable["prior_personality_setup_allowed"].map(is_affirmative)]
    if usable.empty:
        return {}
    usable["_style"] = usable.apply(
        lambda row: row.get("prior_execution_style") or execution_style_for_setup(row.get("prior_setup")),
        axis=1,
    )
    usable["_filled"] = usable["path_status"].astype(str).str.upper() == "SETTLED"
    usable["_key_exact"] = usable.apply(
        lambda row: fillability_key(row.get("_style"), row.get("prior_setup"), row.get("prior_personality_type")), axis=1
    )
    usable["_key_setup"] = usable.apply(
        lambda row: fillability_key(row.get("_style"), row.get("prior_setup")), axis=1
    )
    usable["_key_style"] = usable.apply(
        lambda row: fillability_key(row.get("_style"), "ANY"), axis=1
    )
    stats: dict[str, dict] = {}
    for column, scope in (("_key_exact", "setup/personality"), ("_key_setup", "setup family"), ("_key_style", "execution style")):
        for key, group in usable.groupby(column):
            total = int(len(group))
            filled = int(group["_filled"].sum())
            evaluation_dates = int(pd.to_datetime(group["signal_run_date"], errors="coerce").dropna().dt.normalize().nunique())
            tickers = int(group["ticker"].dropna().astype(str).str.upper().nunique())
            stats[str(key)] = {
                "sample_count": total,
                "filled_count": filled,
                "not_filled_count": total - filled,
                "fill_rate": filled / total if total else 0.0,
                "fill_probability": (filled + 2.0) / (total + 4.0),
                "distinct_ticker_count": tickers,
                "evaluation_date_count": evaluation_dates,
                "scope": scope,
                "model_version": LEARNING_MODEL_VERSION,
            }
    return stats


def apply_fillability_adjustments(rows: list[dict], fillability_stats: dict[str, dict]) -> None:
    for row in rows:
        candidates = fillability_key_candidates(row)
        available = [(key, scope, fillability_stats[key]) for key, scope in candidates if key in fillability_stats]
        qualified = next((item for item in available if (
            int(item[2].get("sample_count", 0)) >= FILLABILITY_MIN_SAMPLES
            and int(item[2].get("distinct_ticker_count", 0)) >= FILLABILITY_MIN_DISTINCT_TICKERS
            and int(item[2].get("evaluation_date_count", 0)) >= FILLABILITY_MIN_EVALUATION_DATES
        )), None)
        selected = qualified or (max(available, key=lambda item: int(item[2].get("sample_count", 0))) if available else None)
        stats = selected[2] if selected else {}
        probability = float(stats.get("fill_probability", 0.0)) if stats else 0.0
        row["execution_fill_sample_count"] = int(stats.get("sample_count", 0)) if stats else 0
        row["execution_fill_distinct_ticker_count"] = int(stats.get("distinct_ticker_count", 0)) if stats else 0
        row["execution_fill_evaluation_date_count"] = int(stats.get("evaluation_date_count", 0)) if stats else 0
        row["execution_fill_rate"] = round(float(stats.get("fill_rate", 0.0)), 3) if stats else ""
        row["execution_fill_probability"] = round(probability, 3) if stats else ""
        row["execution_fill_scope"] = selected[1] if selected else "none"
        row["execution_fill_model_version"] = LEARNING_MODEL_VERSION
        row["execution_fill_state"] = "VALIDATED" if qualified else "INSUFFICIENT"

        if str(row.get("action") or "") not in {"BUY CANDIDATE", "STRONG CONTINUATION"}:
            continue
        adjusted = float(numeric_or_none(row.get("adjusted_score")) or numeric_or_none(row.get("score")) or 0.0)
        if not qualified:
            row["action"] = "SETUP FORMING"
            row["signal_stage"] = signal_stage("SETUP FORMING")
            row["adjusted_score"] = min(adjusted, 79.0)
            row["execution_fill_state"] = "INSUFFICIENT"
            row["next_day_plan"] = "Direction is constructive, but historical entry fillability is not proven; keep this as a setup."
            append_unique_reason(row, "fillability_evidence_insufficient")
        elif probability < FILLABILITY_MIN_RATE:
            row["action"] = "SETUP FORMING"
            row["signal_stage"] = signal_stage("SETUP FORMING")
            row["adjusted_score"] = min(adjusted, 76.0)
            row["execution_fill_state"] = "LOW"
            row["next_day_plan"] = "Comparable entry plans were filled too rarely; do not present this as an executable BUY."
            append_unique_reason(row, "fillability_below_threshold")
        else:
            row["execution_fill_state"] = "VALIDATED"
            row["execution_plan"] = row.get("entry_zone_plan") or row.get("next_day_plan")


def attach_walk_forward_predictions(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Freeze predictions using only outcomes settled before each signal date."""
    if outcomes.empty or "signal_run_date" not in outcomes.columns or "evaluation_run_date" not in outcomes.columns:
        return outcomes

    result = outcomes.copy()
    signal_dates = pd.to_datetime(result["signal_run_date"], errors="coerce")
    evaluation_dates = pd.to_datetime(result["evaluation_run_date"], errors="coerce")
    for signal_date in sorted(signal_dates.dropna().dt.normalize().unique()):
        signal_timestamp = pd.Timestamp(signal_date)
        prediction_indices = result.index[signal_dates.dt.normalize() == signal_timestamp]
        training = result.loc[evaluation_dates.dt.normalize() < signal_timestamp].copy()
        stats = build_learning_stats(training, signal_timestamp.date().isoformat(), LEARNING_LOOKBACK_DAYS)
        for index in prediction_indices:
            row = result.loc[index]
            exact_key = str(row.get("learning_key") or "")
            action_setup_key = learning_action_setup_key(row.get("prior_action"), row.get("prior_setup"))
            action_key = learning_action_key(row.get("prior_action"))
            selected = next((stats[key] for key in (exact_key, action_setup_key, action_key) if key in stats), None)
            if not selected or int(selected.get("sample_count", 0)) < LEARNING_MIN_SAMPLES:
                for column in (
                    "prior_prediction_upside_probability",
                    "prior_prediction_downside_probability",
                    "prior_prediction_no_edge_probability",
                    "prior_prediction_confidence",
                    "prior_prediction_key",
                    "prior_prediction_scope",
                ):
                    result.at[index, column] = np.nan
                result.at[index, "prior_prediction_state"] = "INSUFFICIENT_EVIDENCE"
                continue
            result.at[index, "prior_prediction_upside_probability"] = selected["upside_probability"]
            result.at[index, "prior_prediction_downside_probability"] = selected["downside_probability"]
            result.at[index, "prior_prediction_no_edge_probability"] = selected["no_edge_probability"]
            sample_count = int(selected.get("sample_count", 0))
            result.at[index, "prior_prediction_confidence"] = min(0.90, sample_count / (sample_count + 12.0))
            result.at[index, "prior_prediction_key"] = next(
                key for key in (exact_key, action_setup_key, action_key) if key in stats and stats[key] is selected
            )
            result.at[index, "prior_prediction_scope"] = selected.get("scope")
            result.at[index, "prior_prediction_state"] = "WALK_FORWARD"
    return result


DIRECTIONAL_NUMERIC_FEATURES = (
    "day_change_pct",
    "rsi",
    "atr_pct",
    "trend_efficiency",
    "relative_volume",
    "close_location",
    "range_atr",
    "signed_volume_pressure_5",
    "demand_supply_balance_5",
    "ema_fast_distance_pct",
    "ema_slow_distance_pct",
    "return_5d_pct",
    "return_20d_pct",
    "gap_pct",
)
DIRECTIONAL_PERSONALITIES = ("ETF", "COMPOUNDER", "BALANCED", "RANGE_BOUND", "HIGH_BETA")
DIRECTIONAL_LABELS = ("UP", "DOWN", "NO_EDGE")


def directional_feature_vector(row: dict) -> Optional[np.ndarray]:
    values = [numeric_or_none(row.get(field)) for field in DIRECTIONAL_NUMERIC_FEATURES]
    if any(value is None or not math.isfinite(float(value)) for value in values):
        return None
    personality = str(row.get("personality_type") or "BALANCED").upper()
    one_hot = [1.0 if personality == label else 0.0 for label in DIRECTIONAL_PERSONALITIES]
    return np.asarray([float(value) for value in values] + one_hot, dtype=float)


def build_directional_raw_history(ticker: str, raw: pd.DataFrame, days: int = DIRECTIONAL_RAW_LOOKBACK_DAYS) -> list[dict]:
    """Build compact direct OHLCV features without replaying the rule engine."""
    d = prepare(raw)
    if len(d) < 220:
        return []
    start = max(220, len(d) - max(1, days))
    output: list[dict] = []
    is_etf = ticker in ETF_HINTS
    for index in range(start, len(d)):
        row = d.iloc[index]
        prev = d.iloc[index - 1]
        close = float(row.close)
        travel = d["close"].diff().abs().iloc[index - PERSONALITY_LOOKBACK_BARS + 1 : index + 1].sum()
        trend_efficiency = abs(close - float(d.iloc[index - PERSONALITY_LOOKBACK_BARS].close)) / travel if travel > 0 else 0.0
        personality = stock_personality_profile(d, index, is_etf, float(trend_efficiency))["personality_type"]
        output.append({
            "ticker": display_ticker(ticker),
            "date": str(pd.to_datetime(row.date).date()),
            "close": close,
            "day_change_pct": (close / float(prev.close) - 1.0) * 100.0,
            "rsi": float(row.rsi),
            "atr_pct": float(row.atr_pct),
            "trend_efficiency": float(trend_efficiency),
            "relative_volume": float(row.relative_volume),
            "close_location": float(row.close_loc),
            "range_atr": float(row.range_atr),
            "signed_volume_pressure_5": float(row.signed_volume_pressure_5),
            "demand_supply_balance_5": float(row.demand_days_5 - row.supply_days_5),
            "ema_fast_distance_pct": (close / float(row.ema_fast) - 1.0) * 100.0,
            "ema_slow_distance_pct": (close / float(row.ema_slow) - 1.0) * 100.0,
            "return_5d_pct": (close / float(d.iloc[index - 5].close) - 1.0) * 100.0,
            "return_20d_pct": (close / float(d.iloc[index - 20].close) - 1.0) * 100.0,
            "gap_pct": (float(row.open) / float(prev.close) - 1.0) * 100.0,
            "personality_type": personality,
            "volume_state": "NEUTRAL",
        })
    return output


def build_directional_samples(history_rows: list[dict], horizon_sessions: int = LEARNING_HORIZON_SESSIONS) -> pd.DataFrame:
    records: list[dict] = []
    ordered = sorted(history_rows, key=lambda item: (str(item.get("ticker") or ""), str(item.get("date") or "")))
    for _, ticker_rows in itertools.groupby(ordered, key=lambda item: str(item.get("ticker") or "")):
        rows = list(ticker_rows)
        for index in range(0, max(0, len(rows) - horizon_sessions)):
            current = rows[index]
            future = rows[index + horizon_sessions]
            features = directional_feature_vector(current)
            close = numeric_or_none(current.get("close"))
            future_close = numeric_or_none(future.get("close"))
            atr_pct = numeric_or_none(current.get("atr_pct"))
            if features is None or close is None or future_close is None or close <= 0 or atr_pct is None:
                continue
            forward_return = (float(future_close) / float(close) - 1.0) * 100.0
            move_threshold = max(1.0, min(4.0, float(atr_pct) * 0.60))
            label = "UP" if forward_return >= move_threshold else "DOWN" if forward_return <= -move_threshold else "NO_EDGE"
            ema_fast_distance = float(numeric_or_none(current.get("ema_fast_distance_pct")) or 0.0)
            ema_slow_distance = float(numeric_or_none(current.get("ema_slow_distance_pct")) or 0.0)
            return_20d = float(numeric_or_none(current.get("return_20d_pct")) or 0.0)
            trend_bucket = "UPTREND" if ema_fast_distance > 0 and ema_slow_distance > 0 and return_20d > 0 else "DOWNTREND" if ema_fast_distance < 0 and ema_slow_distance < 0 and return_20d < 0 else "MIXED"
            records.append({
                "ticker": current.get("ticker"),
                "signal_run_date": current.get("date"),
                "evaluation_run_date": future.get("date"),
                "features": features,
                "label": label,
                "forward_return_pct": round(forward_return, 4),
                "move_threshold_pct": round(move_threshold, 4),
                "personality_type": str(current.get("personality_type") or "BALANCED").upper(),
                "trend_bucket": trend_bucket,
                "volume_state": str(current.get("volume_state") or "NEUTRAL").upper(),
            })
    return pd.DataFrame(records)


def fit_directional_ridge(samples: pd.DataFrame) -> Optional[dict]:
    if len(samples) < DIRECTIONAL_MODEL_MIN_TRAIN_SAMPLES or "features" not in samples.columns:
        return None
    labels = samples["label"].astype(str)
    class_counts = labels.value_counts()
    if any(int(class_counts.get(label, 0)) < 10 for label in DIRECTIONAL_LABELS):
        return None
    matrix = np.vstack(samples["features"].to_list()).astype(float)
    center = np.nanmedian(matrix, axis=0)
    scale = np.nanpercentile(matrix, 75, axis=0) - np.nanpercentile(matrix, 25, axis=0)
    scale = np.where(np.isfinite(scale) & (scale > 1e-6), scale, 1.0)
    standardized = np.clip((matrix - center) / scale, -5.0, 5.0)
    design = np.column_stack([np.ones(len(standardized)), standardized])
    targets = np.column_stack([(labels == label).astype(float) for label in DIRECTIONAL_LABELS])
    penalty = np.eye(design.shape[1]) * DIRECTIONAL_MODEL_RIDGE
    penalty[0, 0] = 0.0
    # Some NumPy/BLAS builds emit spurious matmul overflow warnings even for
    # finite, clipped matrices. Validate the products explicitly before solve.
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        gram = design.T @ design
        cross = design.T @ targets
    if not np.isfinite(gram).all() or not np.isfinite(cross).all():
        return None
    coefficients = np.linalg.solve(gram + penalty, cross)
    if not np.isfinite(coefficients).all():
        return None
    priors = (np.asarray([int(class_counts.get(label, 0)) for label in DIRECTIONAL_LABELS], dtype=float) + 1.0)
    priors /= priors.sum()
    return {"center": center, "scale": scale, "coefficients": coefficients, "priors": priors, "sample_count": len(samples)}


def predict_directional_probabilities(model: dict, features: np.ndarray) -> np.ndarray:
    standardized = np.clip((features - model["center"]) / model["scale"], -5.0, 5.0)
    raw = np.concatenate([[1.0], standardized]) @ model["coefficients"]
    clipped = np.clip(raw, 0.01, 0.98)
    return clipped / clipped.sum()


def directional_walk_forward_predictions(samples: pd.DataFrame) -> pd.DataFrame:
    if samples.empty:
        return samples.copy()
    result = samples.copy()
    result["prediction"] = None
    result["baseline_prediction"] = None
    signal_dates = pd.to_datetime(result["signal_run_date"], errors="coerce")
    evaluation_dates = pd.to_datetime(result["evaluation_run_date"], errors="coerce")
    model = None
    for date_index, signal_date in enumerate(sorted(signal_dates.dropna().dt.normalize().unique())):
        timestamp = pd.Timestamp(signal_date)
        if date_index % max(1, DIRECTIONAL_REFIT_INTERVAL_DAYS) == 0 or model is None:
            train = result.loc[evaluation_dates.dt.normalize() < timestamp]
            model = fit_directional_ridge(train)
        if model is None:
            continue
        for index in result.index[signal_dates.dt.normalize() == timestamp]:
            result.at[index, "prediction"] = predict_directional_probabilities(model, result.at[index, "features"])
            result.at[index, "baseline_prediction"] = model["priors"].copy()
    return result


def directional_validation_metrics(predictions: pd.DataFrame) -> dict:
    if predictions.empty or "prediction" not in predictions.columns:
        return {"sample_count": 0, "date_count": 0, "brier_score": None, "baseline_brier_score": None, "brier_skill_score": None, "validated_personalities": [], "passed": False}
    valid = predictions[predictions["prediction"].map(lambda value: isinstance(value, np.ndarray))].copy()
    if valid.empty:
        return {"sample_count": 0, "date_count": 0, "brier_score": None, "baseline_brier_score": None, "brier_skill_score": None, "validated_personalities": [], "passed": False}
    probabilities = np.vstack(valid["prediction"].to_list())
    baseline_probabilities = np.vstack(valid["baseline_prediction"].to_list())
    labels = valid["label"].astype(str)
    targets = np.column_stack([(labels == label).astype(float) for label in DIRECTIONAL_LABELS])
    brier = float(np.mean(np.sum((probabilities - targets) ** 2, axis=1)))
    baseline_brier = float(np.mean(np.sum((baseline_probabilities - targets) ** 2, axis=1)))
    skill = 1.0 - brier / baseline_brier if baseline_brier > 0 else None
    date_count = int(pd.to_datetime(valid["signal_run_date"], errors="coerce").dt.normalize().nunique())
    validated_personalities: list[str] = []
    for personality, group in valid.groupby("personality_type"):
        if len(group) < DIRECTIONAL_MODEL_MIN_PERSONALITY_SAMPLES:
            continue
        group_dates = int(pd.to_datetime(group["signal_run_date"], errors="coerce").dt.normalize().nunique())
        if group_dates < DIRECTIONAL_MODEL_MIN_PERSONALITY_DATES:
            continue
        group_probabilities = np.vstack(group["prediction"].to_list())
        group_baselines = np.vstack(group["baseline_prediction"].to_list())
        group_labels = group["label"].astype(str)
        group_targets = np.column_stack([(group_labels == label).astype(float) for label in DIRECTIONAL_LABELS])
        group_brier = float(np.mean(np.sum((group_probabilities - group_targets) ** 2, axis=1)))
        group_baseline_brier = float(np.mean(np.sum((group_baselines - group_targets) ** 2, axis=1)))
        group_skill = 1.0 - group_brier / group_baseline_brier if group_baseline_brier > 0 else None
        if group_skill is not None and group_skill >= DIRECTIONAL_MODEL_MIN_BRIER_SKILL:
            validated_personalities.append(str(personality))
    passed = (
        len(valid) >= DIRECTIONAL_MODEL_MIN_OOS_SAMPLES
        and date_count >= DIRECTIONAL_MODEL_MIN_OOS_DATES
        and skill is not None
        and skill >= DIRECTIONAL_MODEL_MIN_BRIER_SKILL
        and bool(validated_personalities)
    )
    return {
        "sample_count": int(len(valid)),
        "date_count": date_count,
        "brier_score": brier,
        "baseline_brier_score": baseline_brier,
        "brier_skill_score": skill,
        "validated_personalities": validated_personalities,
        "passed": bool(passed),
    }


def build_directional_calibration_artifact(
    rows: list[dict],
    history_rows: list[dict],
    source_publication_id: str,
) -> dict:
    samples = build_directional_samples(history_rows)
    walk_forward = directional_walk_forward_predictions(samples)
    metrics = directional_validation_metrics(walk_forward)
    latest_signal_date = max((str(row.get("date") or "") for row in rows), default="")
    settled = samples[pd.to_datetime(samples.get("evaluation_run_date"), errors="coerce") < pd.Timestamp(latest_signal_date)] if not samples.empty and latest_signal_date else pd.DataFrame()
    model = fit_directional_ridge(settled)
    model_payload = None
    if model is not None:
        model_payload = {
            "center": model["center"].tolist(),
            "scale": model["scale"].tolist(),
            "coefficients": model["coefficients"].tolist(),
            "priors": model["priors"].tolist(),
            "sample_count": int(model["sample_count"]),
        }
    payload = {
        "source_publication_id": source_publication_id,
        "artifact_version": CALIBRATION_ARTIFACT_VERSION,
        "scanner_version": SCANNER_VERSION,
        "learning_model_version": LEARNING_MODEL_VERSION,
        "directional_model_version": DIRECTIONAL_MODEL_VERSION,
        "feature_count": len(DIRECTIONAL_NUMERIC_FEATURES) + len(DIRECTIONAL_PERSONALITIES),
        "label_count": len(DIRECTIONAL_LABELS),
        "cutoff_date": latest_signal_date,
        "metrics": metrics,
        "model": model_payload,
        "train_sample_count": int(len(settled)),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    payload["content_hash"] = digest
    payload["artifact_id"] = f"cal-v1-{latest_signal_date.replace('-', '')}-{digest[:16]}"
    return payload


def calibration_payload_bytes(payload: dict) -> int:
    return len(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def directional_model_from_artifact(artifact: dict) -> Optional[dict]:
    model = artifact.get("model") if isinstance(artifact, dict) else None
    if not isinstance(model, dict):
        return None
    try:
        restored = {
            "center": np.asarray(model["center"], dtype=float),
            "scale": np.asarray(model["scale"], dtype=float),
            "coefficients": np.asarray(model["coefficients"], dtype=float),
            "priors": np.asarray(model["priors"], dtype=float),
            "sample_count": int(model.get("sample_count") or 0),
        }
        feature_count = len(DIRECTIONAL_NUMERIC_FEATURES) + len(DIRECTIONAL_PERSONALITIES)
        if (
            restored["center"].shape != (feature_count,)
            or restored["scale"].shape != (feature_count,)
            or restored["coefficients"].shape != (feature_count + 1, len(DIRECTIONAL_LABELS))
            or restored["priors"].shape != (len(DIRECTIONAL_LABELS),)
            or not all(np.isfinite(restored[key]).all() for key in ("center", "scale", "coefficients", "priors"))
        ):
            return None
        return restored
    except (KeyError, TypeError, ValueError):
        return None


def apply_directional_calibration_artifact(rows: list[dict], artifact: dict) -> dict:
    metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
    model = directional_model_from_artifact(artifact)
    settled_count = int(artifact.get("train_sample_count") or 0)
    validated_personalities = set(metrics.get("validated_personalities") or [])
    globally_validated = bool(metrics.get("passed")) and model is not None
    for row in rows:
        row["directional_model_version"] = DIRECTIONAL_MODEL_VERSION
        row["directional_model_train_samples"] = settled_count
        row["directional_model_oos_samples"] = int(metrics.get("sample_count") or 0)
        row["directional_model_oos_dates"] = int(metrics.get("date_count") or 0)
        row["directional_model_brier_score"] = round(float(metrics["brier_score"]), 4) if metrics.get("brier_score") is not None else ""
        row["directional_model_baseline_brier"] = round(float(metrics["baseline_brier_score"]), 4) if metrics.get("baseline_brier_score") is not None else ""
        row["directional_model_brier_skill"] = round(float(metrics["brier_skill_score"]), 4) if metrics.get("brier_skill_score") is not None else ""
        row_validated = globally_validated and str(row.get("personality_type") or "BALANCED").upper() in validated_personalities
        row["directional_model_state"] = "VALIDATED" if row_validated else "REPORTING_ONLY"
        features = directional_feature_vector(row)
        if not row_validated or features is None:
            continue
        probabilities = predict_directional_probabilities(model, features)
        upside, downside, no_edge = (float(value) for value in probabilities)
        row["prediction_horizon_sessions"] = LEARNING_HORIZON_SESSIONS
        row["prediction_upside_probability"] = round(upside, 3)
        row["prediction_downside_probability"] = round(downside, 3)
        row["prediction_no_edge_probability"] = round(no_edge, 3)
        row["prediction_confidence"] = round(max(probabilities) - min(probabilities), 3)
        row["prediction_model_version"] = DIRECTIONAL_MODEL_VERSION
        row["prediction_state"] = "DIRECT_OHLCV_WALK_FORWARD"
        confidence = max(probabilities) - min(probabilities)
        if str(row.get("action") or "") == "BUY CANDIDATE" and confidence >= 0.12 and (downside >= upside + 0.10 or no_edge >= upside + 0.15):
            prior_adjustment = max(0.0, float(numeric_or_none(row.get("learning_adjustment")) or 0.0))
            row["action"] = "SETUP FORMING"
            row["signal_stage"] = signal_stage("SETUP FORMING")
            current_score = float(numeric_or_none(row.get("adjusted_score")) or numeric_or_none(row.get("score")) or 0)
            row["adjusted_score"] = min(current_score - prior_adjustment, 79.0)
            row["learning_adjustment"] = 0.0
            row["learning_promotion_eligible"] = False
            row["learning_reporting_only"] = True
            row["learning_promotion_state"] = "PROMOTION_BLOCKED"
            row["reason_codes"] = list(dict.fromkeys([*(row.get("reason_codes") or []), "directional_model_not_confirmed"]))
            row["next_day_plan"] = "The validated OHLCV model does not confirm upside dominance; keep this as a setup, not an entry."
    return metrics


def apply_directional_ohlcv_model(rows: list[dict], history_rows: list[dict], source_publication_id: str) -> dict:
    artifact = build_directional_calibration_artifact(rows, history_rows, source_publication_id)
    metrics = apply_directional_calibration_artifact(rows, artifact)
    return {**metrics, "_artifact": artifact}


def fetch_active_calibration_artifact() -> Optional[dict]:
    try:
        candidates = supabase_select(
            "watchlist_calibration_artifacts?select=artifact_id,source_publication_id,cutoff_date,artifact_version,scanner_version,learning_model_version,directional_model_version,content_hash,payload_bytes,payload,created_at&"
            "state=eq.validated&order=cutoff_date.desc,created_at.desc&limit=5"
        )
        for candidate in candidates:
            publication_id = str(candidate.get("source_publication_id") or "")
            if not publication_id:
                continue
            runs = supabase_select(
                "watchlist_refresh_runs?select=publication_id,status,payload&"
                f"publication_id=eq.{urllib.parse.quote(publication_id)}&status=in.(ok,degraded)&limit=1"
            )
            if not runs:
                continue
            payload = candidate.get("payload")
            if not isinstance(payload, dict):
                continue
            typed_contract = {
                "artifact_id": candidate.get("artifact_id"),
                "source_publication_id": candidate.get("source_publication_id"),
                "cutoff_date": str(candidate.get("cutoff_date") or ""),
                "artifact_version": candidate.get("artifact_version"),
                "scanner_version": candidate.get("scanner_version"),
                "learning_model_version": candidate.get("learning_model_version"),
                "directional_model_version": candidate.get("directional_model_version"),
                "content_hash": candidate.get("content_hash"),
            }
            payload_contract = {key: payload.get(key) for key in typed_contract}
            if typed_contract != payload_contract:
                continue
            if (
                payload.get("artifact_version") != CALIBRATION_ARTIFACT_VERSION
                or payload.get("scanner_version") != SCANNER_VERSION
                or payload.get("learning_model_version") != LEARNING_MODEL_VERSION
                or payload.get("directional_model_version") != DIRECTIONAL_MODEL_VERSION
                or str(payload.get("cutoff_date") or "") > local_run_date()
                or int(candidate.get("payload_bytes") or 0) != calibration_payload_bytes(payload)
            ):
                continue
            expected_hash = payload.get("content_hash")
            unhashed = {key: value for key, value in payload.items() if key not in {"content_hash", "artifact_id"}}
            actual_hash = hashlib.sha256(json.dumps(unhashed, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
            if expected_hash == actual_hash and directional_model_from_artifact(payload) is not None:
                return payload
    except RuntimeError as exc:
        print(f"Calibration artifact fetch skipped: {exc}")
    return None


def apply_reporting_only_directional_state(rows: list[dict]) -> dict:
    """Fail closed between weekly calibrations when no fitted artifact is active."""
    metrics = {
        "sample_count": 0,
        "date_count": 0,
        "brier_score": None,
        "baseline_brier_score": None,
        "brier_skill_score": None,
        "validated_personalities": [],
        "passed": False,
    }
    for row in rows:
        row["directional_model_version"] = DIRECTIONAL_MODEL_VERSION
        row["directional_model_state"] = "REPORTING_ONLY"
        row["prediction_state"] = "AWAITING_WEEKLY_CALIBRATION"
    return metrics


def apply_learning_adjustments(rows: list[dict], learning_stats: dict[str, dict]) -> None:
    for row in rows:
        candidates = learning_key_candidates_for(row)
        exact_key, exact_scope, _ = candidates[0]
        exact_stats = learning_stats.get(exact_key)
        fallback = next(((key, scope, weight, learning_stats[key]) for key, scope, weight in candidates[1:] if key in learning_stats), None)
        report_key = exact_key if exact_stats else (fallback[0] if fallback else "")
        report_scope = str((exact_stats or (fallback[3] if fallback else {})).get("scope") or (exact_scope if exact_stats else (fallback[1] if fallback else "none")))
        report_stats = exact_stats or (fallback[3] if fallback else None)

        # Exact behavior evidence is the only source that can promote a score.
        # Broad pools remain visible and can apply negative caution only.
        selected_key = exact_key
        selected_scope = exact_scope
        selected_weight = 1.0
        stats = exact_stats
        if (not stats or int(stats.get("sample_count", 0)) < LEARNING_MIN_SAMPLES) and fallback:
            selected_key, selected_scope, selected_weight, stats = fallback

        if not stats or int(stats.get("sample_count", 0)) < LEARNING_MIN_SAMPLES:
            row["learning_sample_count"] = int(report_stats.get("sample_count", 0)) if report_stats else 0
            row["learning_working_rate"] = round(float(report_stats.get("working_rate", 0.0)), 3) if report_stats else ""
            row["learning_failed_rate"] = round(float(report_stats.get("failed_rate", 0.0)), 3) if report_stats else ""
            row["learning_trap_avoided_rate"] = round(float(report_stats.get("trap_avoided_rate", 0.0)), 3) if report_stats else ""
            row["learning_avg_score"] = round(float(report_stats.get("avg_score", 0.0)), 3) if report_stats else ""
            row["learning_distinct_ticker_count"] = int(report_stats.get("distinct_ticker_count", 0)) if report_stats else 0
            row["learning_evaluation_date_count"] = int(report_stats.get("evaluation_date_count", 0)) if report_stats else 0
            row["learning_evaluation_date_min"] = report_stats.get("evaluation_date_min", "") if report_stats else ""
            row["learning_evaluation_date_max"] = report_stats.get("evaluation_date_max", "") if report_stats else ""
            row["learning_calibration_sample_count"] = int(report_stats.get("calibration_sample_count", 0)) if report_stats else 0
            row["learning_execution_sample_count"] = int(report_stats.get("execution_sample_count", 0)) if report_stats else 0
            row["learning_execution_distinct_ticker_count"] = int(report_stats.get("execution_distinct_ticker_count", 0)) if report_stats else 0
            row["learning_execution_evaluation_date_count"] = int(report_stats.get("execution_evaluation_date_count", 0)) if report_stats else 0
            report_brier = report_stats.get("brier_score") if report_stats else None
            row["learning_brier_score"] = round(float(report_brier), 4) if report_brier is not None else ""
            row["learning_window_start"] = row["learning_evaluation_date_min"]
            row["learning_window_end"] = row["learning_evaluation_date_max"]
            row["learning_model_version"] = str(report_stats.get("model_version") or LEARNING_MODEL_VERSION) if report_stats else LEARNING_MODEL_VERSION
            row["learning_promotion_eligible"] = False
            row["learning_reporting_only"] = True
            row["learning_promotion_state"] = "REPORTING_ONLY"
            row["learning_adjustment"] = 0.0
            row["learning_scope"] = report_scope
            row["learning_key_used"] = report_key
            row["learning_plan"] = (
                f"Learning pending: needs at least {LEARNING_MIN_SAMPLES} settled samples; "
                f"currently has {row['learning_sample_count']} from {row['learning_scope']}."
            )
            row["prediction_horizon_sessions"] = LEARNING_HORIZON_SESSIONS
            row["prediction_upside_probability"] = ""
            row["prediction_downside_probability"] = ""
            row["prediction_no_edge_probability"] = ""
            row["prediction_confidence"] = 0.0
            row["prediction_model_version"] = LEARNING_MODEL_VERSION
            row["prediction_state"] = "INSUFFICIENT_EVIDENCE"
            continue

        avg_score = float(stats.get("execution_avg_score", 0.0))
        working_rate = float(stats.get("execution_working_rate", 0.0))
        failed_rate = float(stats.get("execution_failed_rate", 0.0))
        trap_rate = float(stats.get("execution_trap_avoided_rate", 0.0))
        execution_samples = int(stats.get("execution_sample_count", 0))
        adjustment = avg_score * 8.0 + (working_rate - failed_rate) * 4.0 + trap_rate * 2.0
        adjustment *= selected_weight
        adjustment = max(-LEARNING_ADJUSTMENT_CAP, min(LEARNING_ADJUSTMENT_CAP, adjustment))

        anti_level = str(row.get("anti_signal_level") or "NONE").upper()
        stale = str(row.get("freshness_block") or "").upper() == "YES"
        # Learning may warn from imperfect contexts, but it must never promote a
        # setup that the live execution governor would reject.
        execution_gates_allow = (
            is_affirmative(row.get("personality_setup_allowed"))
            and str(row.get("market_permission") or "").upper() == "ALLOW"
            and str(row.get("ticker_permission") or "").upper() == "ALLOW"
            and str(row.get("walk_forward_permission") or "").upper() == "ALLOW"
            and str(row.get("risk_permission") or "").upper() == "ALLOW"
        )
        if execution_samples < LEARNING_MIN_SAMPLES:
            effective_adjustment = 0.0
            plan = (
                "Forecast calibration is reporting-only; score adjustment needs "
                f"{LEARNING_MIN_SAMPLES} historically executable outcomes and currently has {execution_samples}."
            )
        elif stale:
            effective_adjustment = 0.0
            plan = f"Learning observed from {selected_scope}, but data is stale; no score adjustment applied."
        elif anti_level == "BLOCK":
            effective_adjustment = min(0.0, adjustment)
            plan = f"Learning observed from {selected_scope}, but anti-signal BLOCK prevents positive promotion."
        elif anti_level == "CAUTION":
            effective_adjustment = min(4.0, adjustment)
            plan = f"Learning adjustment from {selected_scope} capped by anti-signal caution."
        else:
            effective_adjustment = adjustment
            plan = f"Learning adjustment applied from settled {selected_scope} outcomes."

        distinct_tickers = int(stats.get("distinct_ticker_count", 0))
        evaluation_dates = int(stats.get("evaluation_date_count", 0))
        execution_distinct_tickers = int(stats.get("execution_distinct_ticker_count", 0))
        execution_evaluation_dates = int(stats.get("execution_evaluation_date_count", 0))
        calibration_samples = int(stats.get("calibration_sample_count", 0))
        brier_score = stats.get("brier_score")
        calibration_ok = (
            calibration_samples >= LEARNING_CALIBRATION_MIN_SAMPLES
            and brier_score is not None
            and float(brier_score) <= LEARNING_CALIBRATION_MAX_BRIER
        )
        promotion_evidence_ok = (
            selected_scope == "exact signal personality"
            and execution_samples >= LEARNING_CONFIRM_MIN_SAMPLES
            and execution_distinct_tickers >= LEARNING_CONFIRM_MIN_DISTINCT_TICKERS
            and execution_evaluation_dates >= LEARNING_CONFIRM_MIN_EVALUATION_DATES
            and calibration_ok
        )
        if effective_adjustment > 0 and not promotion_evidence_ok:
            effective_adjustment = 0.0
            if selected_scope != "exact signal personality":
                plan = f"Broad {selected_scope} outcomes are reporting-only for positive learning; no promotion applied."
            else:
                if not calibration_ok:
                    brier_text = "pending" if brier_score is None else f"{float(brier_score):.3f}"
                    plan = (
                        "Exact learning remains reporting-only until walk-forward calibration passes: "
                        f"{calibration_samples}/{LEARNING_CALIBRATION_MIN_SAMPLES} predictions, Brier {brier_text}."
                    )
                else:
                    plan = (
                        "Exact learning evidence is not diverse enough for promotion: "
                        f"needs {LEARNING_CONFIRM_MIN_SAMPLES} executable outcomes across "
                        f"{LEARNING_CONFIRM_MIN_DISTINCT_TICKERS} tickers and {LEARNING_CONFIRM_MIN_EVALUATION_DATES} evaluation dates."
                    )

        if effective_adjustment > 0 and not execution_gates_allow:
            effective_adjustment = 0.0
            plan = "Learning evidence is reporting-only until every execution and personality gate is ALLOW."

        action = str(row.get("action") or "")
        if action in {"EXIT PRESSURE", "WAIT", "WAIT / AVOID"} and effective_adjustment > 0:
            effective_adjustment = 0.0
            plan = f"Learning supports the defensive {action} read from {selected_scope}; no bullish score promotion applied."

        promotion_eligible = (
            promotion_evidence_ok
            and execution_gates_allow
            and not stale
            and anti_level != "BLOCK"
            and action not in {"EXIT PRESSURE", "WAIT", "WAIT / AVOID"}
        )
        reporting_only = not promotion_evidence_ok or not execution_gates_allow
        promotion_state = (
            "REPORTING_ONLY" if reporting_only
            else "PROMOTION_ELIGIBLE" if promotion_eligible
            else "PROMOTION_BLOCKED"
        )

        base_adjusted = float(numeric_or_none(row.get("adjusted_score")) or numeric_or_none(row.get("score")) or 0)
        row["adjusted_score"] = round(max(0.0, min(128.0, base_adjusted + effective_adjustment)), 1)
        if "adjusted_score" not in row and effective_adjustment:
            row["score"] = round(max(0.0, min(128.0, float(numeric_or_none(row.get("score")) or 0) + effective_adjustment)), 1)
        row["learning_sample_count"] = int(stats.get("sample_count", 0))
        row["learning_working_rate"] = round(working_rate, 3)
        row["learning_failed_rate"] = round(failed_rate, 3)
        row["learning_trap_avoided_rate"] = round(trap_rate, 3)
        row["learning_avg_score"] = round(avg_score, 3)
        row["learning_distinct_ticker_count"] = distinct_tickers
        row["learning_evaluation_date_count"] = evaluation_dates
        row["learning_evaluation_date_min"] = stats.get("evaluation_date_min", "")
        row["learning_evaluation_date_max"] = stats.get("evaluation_date_max", "")
        row["learning_calibration_sample_count"] = calibration_samples
        row["learning_execution_sample_count"] = execution_samples
        row["learning_execution_distinct_ticker_count"] = execution_distinct_tickers
        row["learning_execution_evaluation_date_count"] = execution_evaluation_dates
        row["learning_brier_score"] = round(float(brier_score), 4) if brier_score is not None else ""
        row["learning_window_start"] = row["learning_evaluation_date_min"]
        row["learning_window_end"] = row["learning_evaluation_date_max"]
        row["learning_model_version"] = str(stats.get("model_version") or LEARNING_MODEL_VERSION)
        row["learning_promotion_eligible"] = promotion_eligible
        row["learning_reporting_only"] = reporting_only
        row["learning_promotion_state"] = promotion_state
        row["learning_adjustment"] = round(float(effective_adjustment), 2)
        row["learning_scope"] = selected_scope
        row["learning_key_used"] = selected_key
        row["learning_plan"] = plan
        sample_confidence = min(0.90, int(stats.get("sample_count", 0)) / (int(stats.get("sample_count", 0)) + 12.0))
        diversity_confidence = min(1.0, distinct_tickers / LEARNING_CONFIRM_MIN_DISTINCT_TICKERS) * min(1.0, evaluation_dates / LEARNING_CONFIRM_MIN_EVALUATION_DATES)
        row["prediction_horizon_sessions"] = LEARNING_HORIZON_SESSIONS
        row["prediction_upside_probability"] = round(float(stats.get("upside_probability", 0.0)), 3)
        row["prediction_downside_probability"] = round(float(stats.get("downside_probability", 0.0)), 3)
        row["prediction_no_edge_probability"] = round(float(stats.get("no_edge_probability", 0.0)), 3)
        row["prediction_confidence"] = round(sample_confidence * diversity_confidence, 3)
        row["prediction_model_version"] = LEARNING_MODEL_VERSION
        row["prediction_state"] = "CALIBRATED" if promotion_eligible else "REPORTING_ONLY"


def clamp_entry_to_current_zone(entry: float, close: float, atr_now: float, max_pullback_pct: float) -> tuple[float, str]:
    if math.isnan(entry) or entry <= 0 or close <= 0:
        return entry, ""

    max_pullback = close * (1 - max_pullback_pct / 100)
    if atr_now > 0:
        max_pullback = max(max_pullback, close - atr_now * 1.5)

    if entry < max_pullback:
        return max_pullback, f"Reference zone capped near current price; original retest {entry:.2f} was stale"
    return entry, ""


def execution_style_for_setup(setup: str) -> str:
    if str(setup or "").upper() in {"BREAKOUT BUY", "MOMENTUM BUY"}:
        return "BREAKOUT TRIGGER"
    if str(setup or "").upper() in {"PULLBACK BUY", "EARLY PULLBACK BUY", "REVERSAL BUY"}:
        return "PULLBACK LIMIT"
    return "NONE"


def breakout_trigger_band(
    close: float,
    high: float,
    atr_now: float,
    personality_type: str,
    volatility_regime: str,
) -> tuple[float, float]:
    """Create a next-session trigger band without paying an unlimited gap."""
    buffer = max(close * 0.001, atr_now * 0.05 if atr_now > 0 else 0.0)
    trigger = max(close, high) + buffer
    personality_width = {
        "ETF": 0.22,
        "COMPOUNDER": 0.28,
        "BALANCED": 0.34,
        "RANGE_BOUND": 0.28,
        "HIGH_BETA": 0.40,
    }.get(str(personality_type or "").upper(), 0.34)
    regime_multiplier = {
        "TREND VOLATILITY": 1.10,
        "REVERSAL VOLATILITY": 0.85,
        "CHAOTIC VOLATILITY": 0.0,
    }.get(str(volatility_regime or "NORMAL").upper(), 1.0)
    width = max(trigger * 0.0025, atr_now * personality_width * regime_multiplier)
    width = min(width, trigger * (0.018 if str(personality_type or "").upper() == "HIGH_BETA" else 0.012))
    return trigger, trigger + max(0.0, width)


def entry_zone_width_pct(
    setup: str,
    personality_type: str,
    atr_pct: float,
    volatility_regime: str = "NORMAL",
) -> float:
    personality_floor = {
        "ETF": 0.55,
        "COMPOUNDER": 0.75,
        "BALANCED": 0.95,
        "RANGE_BOUND": 1.05,
        "HIGH_BETA": 1.35,
    }.get(str(personality_type or "").upper(), 0.95)
    setup_mult = {
        "BREAKOUT BUY": 0.90,
        "MOMENTUM BUY": 0.95,
        "PULLBACK BUY": 1.12,
        "EARLY PULLBACK BUY": 1.05,
        "REVERSAL BUY": 1.18,
    }.get(setup, 1.0)
    atr_component = max(0.0, float(atr_pct or 0.0)) * 0.22
    regime_mult = {
        "TREND VOLATILITY": 1.10,
        "REVERSAL VOLATILITY": 1.05,
        "CHAOTIC VOLATILITY": 1.15,
    }.get(str(volatility_regime or "NORMAL").upper(), 1.0)
    width = max(personality_floor, atr_component) * setup_mult * regime_mult
    cap = 3.50 if str(personality_type or "").upper() == "HIGH_BETA" else 2.45
    return clamp_float(width, 0.50, cap)


def minimum_stop_pct(personality_type: str, volatility_regime: str = "NORMAL") -> float:
    base = {
        "ETF": 0.75,
        "COMPOUNDER": 0.95,
        "BALANCED": 1.15,
        "RANGE_BOUND": 1.20,
        "HIGH_BETA": 1.60,
    }.get(str(personality_type or "").upper(), 1.10)
    regime_floor = {
        "TREND VOLATILITY": 2.00,
        "REVERSAL VOLATILITY": 1.80,
        "CHAOTIC VOLATILITY": 2.20,
    }.get(str(volatility_regime or "NORMAL").upper(), 0.0)
    return max(base, regime_floor)


def profit_management_plan(
    trade_entry: float,
    stop: float,
    target: float,
    atr_now: float,
    personality_type: object,
    volatility_regime: object,
) -> dict:
    risk = float(trade_entry) - float(stop)
    if trade_entry <= 0 or risk <= 0 or target <= trade_entry:
        return {
            "take_profit_1": np.nan,
            "take_profit_1_r": np.nan,
            "take_profit_1_reduce_pct": np.nan,
            "post_tp1_stop": np.nan,
            "profit_management_plan": "",
        }

    personality = str(personality_type or "BALANCED").upper()
    regime = str(volatility_regime or "NORMAL").upper()
    if regime == "REVERSAL VOLATILITY":
        tp1_r, reduce_pct, trail_atr = 1.0, 50.0, 1.0
    elif regime == "TREND VOLATILITY":
        tp1_r, reduce_pct, trail_atr = 1.5, 30.0, 1.5
    elif personality == "HIGH_BETA":
        tp1_r, reduce_pct, trail_atr = 1.25, 33.0, 1.25
    else:
        tp1_r, reduce_pct, trail_atr = 1.5, 33.0, 1.25

    take_profit_1 = min(float(target), float(trade_entry) + risk * tp1_r)
    effective_tp1_r = (take_profit_1 - float(trade_entry)) / risk
    atr_trail = float(atr_now) * trail_atr if atr_now > 0 else 0.0
    post_tp1_stop = max(float(trade_entry), take_profit_1 - atr_trail)
    plan = (
        f"At {take_profit_1:.2f} ({effective_tp1_r:.2f}R), trim {reduce_pct:.0f}% and raise the remaining stop "
        f"to at least {post_tp1_stop:.2f}; keep the balance for {float(target):.2f} while structure holds."
    )
    return {
        "take_profit_1": take_profit_1,
        "take_profit_1_r": effective_tp1_r,
        "take_profit_1_reduce_pct": reduce_pct,
        "post_tp1_stop": post_tp1_stop,
        "profit_management_plan": plan,
    }


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


def personality_weight_profile(personality_type: object) -> dict:
    personality = str(personality_type or "BALANCED").upper()
    profiles = {
        "HIGH_BETA": {
            "emotion": 0.40,
            "transition": 0.38,
            "setup": 0.16,
            "trend": 0.06,
            "label": "high-beta transition",
        },
        "COMPOUNDER": {
            "emotion": 0.30,
            "transition": 0.24,
            "setup": 0.26,
            "trend": 0.20,
            "label": "compounder quality-trend",
        },
        "RANGE_BOUND": {
            "emotion": 0.38,
            "transition": 0.40,
            "setup": 0.17,
            "trend": 0.05,
            "label": "range-bound reversal",
        },
        "ETF": {
            "emotion": 0.32,
            "transition": 0.24,
            "setup": 0.24,
            "trend": 0.20,
            "label": "ETF regime-trend",
        },
        "BALANCED": {
            "emotion": 0.38,
            "transition": 0.32,
            "setup": 0.20,
            "trend": 0.10,
            "label": "balanced transition",
        },
    }
    return profiles.get(personality, profiles["BALANCED"])


def classify_volatility_regime(
    personality_type: object,
    atr_pct: float,
    personality_atr_pct: float,
    trend_efficiency: float,
    ema_alignment_clean: bool,
    slow_slope_up: bool,
    buyer_score: float,
    signed_volume_pressure_5: float,
    demand_days_5: int,
    supply_days_5: int,
    accum_vol: bool,
    breakout_vol: bool,
    dist_vol: bool,
    breakdown_vol: bool,
    transition_buy_setup: bool,
    fear_rejected: bool,
    right_side: bool,
) -> dict:
    """Separate directional volatility from noise without fragmenting ML samples."""
    personality = str(personality_type or "BALANCED").upper()
    current_atr = max(0.0, float(atr_pct or 0.0))
    normal_atr = max(0.0, float(personality_atr_pct or 0.0))
    volatile = personality == "HIGH_BETA" or current_atr >= max(5.5, normal_atr * 0.90)
    if not volatile:
        return {
            "regime": "NORMAL",
            "permission": "ALLOW",
            "position_size_factor": 1.0,
            "plan": "Use the standard entry, stop, and position plan for this personality.",
        }

    reversal_confirmed = (
        transition_buy_setup
        and (fear_rejected or right_side)
        and buyer_score >= 68.0
        and not dist_vol
        and not breakdown_vol
    )
    reversal_developing = (
        transition_buy_setup
        and (fear_rejected or right_side)
        and not breakdown_vol
    )
    trend_structure = ema_alignment_clean and slow_slope_up and trend_efficiency >= 0.18
    trend_tape = (
        demand_days_5 >= max(1, supply_days_5 - 1)
        and signed_volume_pressure_5 >= -0.35
        and not dist_vol
        and not breakdown_vol
    )
    trend_confirmed = trend_structure and trend_tape and buyer_score >= 60.0 and (
        accum_vol or breakout_vol or signed_volume_pressure_5 >= 0.0
    )

    if reversal_developing:
        return {
            "regime": "REVERSAL VOLATILITY",
            "permission": "ALLOW" if reversal_confirmed else "CAUTION",
            "position_size_factor": 0.50 if reversal_confirmed else 0.35,
            "plan": (
                "A volatile reversal is confirmed; use half normal size and enter only near the reclaim zone."
                if reversal_confirmed
                else "A volatile reversal is developing; wait for buyer confirmation before entering."
            ),
        }
    if trend_structure and trend_tape:
        return {
            "regime": "TREND VOLATILITY",
            "permission": "ALLOW" if trend_confirmed else "CAUTION",
            "position_size_factor": 0.70 if trend_confirmed else 0.50,
            "plan": (
                "Volatility is directional; use 70% of normal size and do not exceed the plan's maximum entry."
                if trend_confirmed
                else "Trend structure exists, but buyer tape is not confirmed; keep it on watch."
            ),
        }
    return {
        "regime": "CHAOTIC VOLATILITY",
        "permission": "BLOCK",
        "position_size_factor": 0.0,
        "plan": "Volatility is not directional; do not open a new position until trend or reversal evidence forms.",
    }


def personality_setup_execution_allowed(
    personality_type: object,
    setup: str,
    mode: str,
    transition_buy_setup: bool,
    buyer_score: float,
    fear_rejected: bool,
    right_side: bool,
    quiet_absorption: bool,
    accum_vol: bool,
    breakout_vol: bool,
    volatility_regime: str = "NORMAL",
    volatility_permission: str = "ALLOW",
) -> bool:
    personality = str(personality_type or "BALANCED").upper()
    if setup == "NONE":
        return False
    if volatility_permission != "ALLOW":
        return False
    if personality == "HIGH_BETA" and volatility_regime == "REVERSAL VOLATILITY":
        return (
            setup in {"REVERSAL BUY", "EARLY PULLBACK BUY"}
            and transition_buy_setup
            and buyer_score >= 68.0
            and (fear_rejected or right_side)
        )
    if personality == "HIGH_BETA" and volatility_regime == "TREND VOLATILITY":
        return (
            setup in {"BREAKOUT BUY", "MOMENTUM BUY", "PULLBACK BUY", "EARLY PULLBACK BUY"}
            and buyer_score >= 60.0
            and (accum_vol or breakout_vol)
        )
    if personality == "RANGE_BOUND":
        return (
            setup == "REVERSAL BUY"
            and transition_buy_setup
            and buyer_score >= 68.0
            and (fear_rejected or right_side or (quiet_absorption and (accum_vol or breakout_vol)))
        )
    if personality == "BALANCED" and setup == "MOMENTUM BUY":
        return mode == "POWER TREND" and breakout_vol and buyer_score >= 75.0
    if personality == "COMPOUNDER" and setup == "EARLY PULLBACK BUY":
        return transition_buy_setup and buyer_score >= 65.0
    return True


def personality_exit_pressure(
    personality_type: object,
    hard_exit_pressure: bool,
    early_distribution_pressure: bool,
    trend_damage: bool,
) -> bool:
    personality = str(personality_type or "BALANCED").upper()
    if personality == "RANGE_BOUND":
        return hard_exit_pressure
    return hard_exit_pressure or (early_distribution_pressure and trend_damage)


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
    vol_ready = not math.isnan(row.vol_ma) and row.vol_ma > 0
    body_for_ratio = max(float(row.body), 0.01)
    lower_wick = min(open_, close) - low
    breakdown_vol = vol_ready and row.volume > row.vol_ma * 1.2 and close < open_ and close < row.ema_fast and close < prev.low and row.close_loc <= 0.45
    quiet_absorption = vol_ready and row.volume < row.vol_ma and row.close_loc >= 0.45 and close >= row.ema_slow and (low <= row.ema_fast * 1.02 or low <= row.bb_basis)
    fear_rejected = lower_wick > body_for_ratio * 1.5 and row.close_loc >= 0.60 and (low <= row.lower_bb or low <= row.ema_fast or low < prev.low) and not breakdown_vol

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

    trend_condition = close > row.ema_slow and row.ema_fast >= row.ema_slow
    transition_reclaim = close > prev.high or (close > row.ema_fast and prev.close <= prev.ema_fast)
    reclaiming_slow = close > row.ema_slow and prev.close <= prev.ema_slow
    local_higher_low = low >= min(float(prev.low), float(d.iloc[i - 2].low)) and close >= prev.close
    early_reclaim_context = (
        close >= row.ema_slow
        or reclaiming_slow
        or (back_inside_bb and close >= row.bb_basis)
        or (close > row.ema_fast and row.ema_fast >= row.ema_slow * 0.985)
    )
    uptrend = close > row.ema_slow and row.ema_fast > row.ema_slow and row.ema_slow >= d.iloc[i - ema_slope_bars].ema_slow
    strong_momentum = close > row.ema_fast and row.ema_fast > row.ema_slow and row.ema_fast >= d.iloc[i - ema_slope_bars].ema_fast and row.ema_slow >= d.iloc[i - ema_slope_bars].ema_slow
    pullback_support = low <= row.ema_fast or low <= row.bb_basis or close <= row.ema_fast * 1.02
    shallow_pullback = low <= row.ema_fast * 1.015 or low <= row.bb_basis or close <= row.ema_fast * 1.025
    support_held = close > row.ema_slow and close > row.lower_bb
    early_support_held = (close > row.ema_slow or early_reclaim_context) and close >= row.lower_bb and row.close_loc >= 0.50
    pullback_reversal = 40 <= row.rsi <= 60 and row.rsi > prev.rsi and (price_follow or constructive_close)
    pullback = uptrend and (pullback_support or (strong_momentum and shallow_pullback)) and support_held and pullback_reversal

    early_pullback = (
        (uptrend or early_reclaim_context)
        and (low <= row.ema_fast * 1.03 or low <= row.bb_basis * 1.02 or close <= row.ema_fast * 1.04)
        and early_support_held
        and 38 <= row.rsi <= 68
        and row.rsi >= prev.rsi - 2
        and (demand_tail or constructive_close)
        and not breakdown_vol
    )

    recent_momentum_high = d["high"].iloc[i - 10 : i].max()
    momentum_dip = d["low"].iloc[i - 2 : i + 1].min() <= recent_momentum_high * 0.97
    momentum = strong_momentum and momentum_dip and close > open_ and close > prev.close and close > row.ema_fast and 55 <= row.rsi <= 85 and close <= row.ema_fast * 1.35

    breakout_level = d["close"].iloc[i - 20 : i].max()
    breakout_ext = (close - row.ema_fast) / atr_now if atr_now > 0 else 0
    breakout = strong_momentum and close >= breakout_level and close > prev.high and wide_bullish and 55 <= row.rsi <= 82 and breakout_ext <= 3.5 and row.macd_hist >= prev.macd_hist

    frequent_buy_setup = back_inside_bb and (recent_oversold_bb or row.rsi < 45 or row.rsi > prev.rsi)
    transition_buy_setup = (
        (fear_rejected or quiet_absorption or demand_tail or right_side)
        and early_reclaim_context
        and (transition_reclaim or local_higher_low or row.rsi > prev.rsi)
        and not breakdown_vol
    )
    reversal = right_side or (
        frequent_buy_setup
        or (fear_rejected and recent_oversold_bb and back_inside_bb)
        or transition_buy_setup
    ) and (trend_condition or early_reclaim_context)

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


def ensure_setup_names(d: pd.DataFrame) -> pd.DataFrame:
    if "setup_name" in d.columns and d["setup_name"].notna().any():
        return d

    out = d.copy()
    setups = ["NONE"] * len(out)
    for i in range(210, len(out)):
        setups[i] = detect_setup_at(out, i)
    out["setup_name"] = setups
    return out


def historical_setup_stats(d: pd.DataFrame, setup: str, holding_days: int = 10, lookback_days: int = 500) -> dict:
    if setup == "NONE":
        return {"hist_trades": "", "hist_win_rate": "", "hist_avg_return": ""}

    d = ensure_setup_names(d)
    returns: list[float] = []
    end = len(d) - holding_days - 1
    start = max(210, end - lookback_days)
    for i in range(start, end):
        if d.iloc[i].setup_name != setup:
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


def summarize_returns(returns: list[float], prefix: str = "") -> dict:
    if not returns:
        return {
            f"{prefix}trades": 0,
            f"{prefix}win_rate": "",
            f"{prefix}avg_return": "",
            f"{prefix}worst_return": "",
        }

    wins = sum(1 for value in returns if value > 0)
    return {
        f"{prefix}trades": len(returns),
        f"{prefix}win_rate": round(wins / len(returns) * 100, 1),
        f"{prefix}avg_return": round(float(np.mean(returns)), 2),
        f"{prefix}worst_return": round(float(np.min(returns)), 2),
    }


def setup_forward_returns(
    d: pd.DataFrame,
    setup: str,
    *,
    start_index: int,
    end_index: int,
    holding_days: int = 10,
) -> list[float]:
    if setup == "NONE":
        return []

    d = ensure_setup_names(d)
    returns: list[float] = []
    start = max(210, start_index)
    end = min(end_index, len(d) - holding_days - 1)
    for i in range(start, end):
        if d.iloc[i].setup_name != setup:
            continue
        entry = float(d.iloc[i].close)
        exit_ = float(d.iloc[i + holding_days].close)
        if entry > 0:
            returns.append((exit_ / entry - 1) * 100)
    return returns


def ticker_learning_profile(d: pd.DataFrame, holding_days: int = 10, lookback_days: int = 500) -> dict:
    d = ensure_setup_names(d)
    start = max(210, len(d) - holding_days - lookback_days)
    end = len(d) - holding_days - 1
    returns: list[float] = []
    for i in range(start, end):
        setup = d.iloc[i].setup_name
        if setup == "NONE":
            continue
        entry = float(d.iloc[i].close)
        exit_ = float(d.iloc[i + holding_days].close)
        if entry > 0:
            returns.append((exit_ / entry - 1) * 100)

    stats = summarize_returns(returns, prefix="ticker_")
    trades = int(stats["ticker_trades"] or 0)
    win_rate = stats["ticker_win_rate"]
    avg_return = stats["ticker_avg_return"]
    worst_return = stats["ticker_worst_return"]
    permission = "INSUFFICIENT"
    reasons: list[str] = []
    if trades >= TICKER_EDGE_MIN_TRADES:
        weak_avg = avg_return != "" and avg_return <= 0
        weak_win = win_rate != "" and win_rate < 42
        severe_left_tail = worst_return != "" and worst_return <= -8
        if weak_avg or weak_win:
            permission = "BLOCK"
            reasons.append("ticker edge weak")
        elif severe_left_tail:
            permission = "CAUTION"
            reasons.append("ticker left-tail risk")
        else:
            permission = "ALLOW"

    stats["ticker_permission"] = permission
    stats["ticker_learning_notes"] = "; ".join(reasons)
    return stats


def walk_forward_setup_stats(d: pd.DataFrame, setup: str, holding_days: int = 10, lookback_days: int = 720) -> dict:
    if setup == "NONE":
        return {
            "wf_train_trades": "",
            "wf_train_win_rate": "",
            "wf_train_avg_return": "",
            "wf_test_trades": "",
            "wf_test_win_rate": "",
            "wf_test_avg_return": "",
            "walk_forward_permission": "NONE",
            "wf_notes": "",
        }

    start = max(210, len(d) - holding_days - lookback_days)
    end = len(d) - holding_days - 1
    split = start + int((end - start) * 0.60)
    train = setup_forward_returns(d, setup, start_index=start, end_index=split, holding_days=holding_days)
    test = setup_forward_returns(d, setup, start_index=split, end_index=end, holding_days=holding_days)
    train_stats = summarize_returns(train, prefix="wf_train_")
    test_stats = summarize_returns(test, prefix="wf_test_")

    test_trades = int(test_stats["wf_test_trades"] or 0)
    test_win = test_stats["wf_test_win_rate"]
    test_avg = test_stats["wf_test_avg_return"]
    permission = "INSUFFICIENT"
    notes = ""
    if test_trades >= WALK_FORWARD_MIN_TEST_TRADES:
        if test_avg != "" and test_avg > 0 and test_win != "" and test_win >= 40:
            permission = "ALLOW"
        else:
            permission = "BLOCK"
            notes = "failed walk-forward"

    return {
        **train_stats,
        **test_stats,
        "walk_forward_permission": permission,
        "wf_notes": notes,
    }


def market_regime_snapshot(frame: Optional[pd.DataFrame]) -> dict:
    if frame is None or len(frame) < 60:
        return {"ok": False, "note": "missing"}
    d = prepare(frame) if "ema_slow" not in frame.columns else frame
    row = d.iloc[-1]
    close = float(row.close)
    ok = close > float(row.ema_slow) and float(row.ema_fast) > float(row.ema_slow)
    return {"ok": ok, "note": "risk-on" if ok else "risk-off", "close": round(close, 2)}


def market_permission_from_frames(benchmarks: dict[str, pd.DataFrame]) -> dict:
    probes = {symbol: market_regime_snapshot(benchmarks.get(symbol)) for symbol in ("SPY", "QQQ", "SMH")}
    ok_count = sum(1 for item in probes.values() if item.get("ok"))
    permission = "ALLOW" if ok_count >= 2 else "BLOCK"
    summary = ", ".join(f"{symbol} {item.get('note', 'unknown')}" for symbol, item in probes.items())
    return {"market_permission": permission, "market_ok_count": ok_count, "market_regime_summary": summary}


def market_permission_for_replay_date(benchmarks: dict[str, pd.DataFrame], replay_date: object) -> dict:
    """Calculate replay market permission using only data known on that date."""
    truncated: dict[str, pd.DataFrame] = {}
    replay_day = pd.to_datetime(replay_date, errors="coerce")
    if pd.isna(replay_day):
        return market_permission_from_frames({})
    for symbol in ("SPY", "QQQ", "SMH"):
        frame = benchmarks.get(symbol)
        if frame is None or frame.empty or "date" not in frame.columns:
            continue
        frame_dates = pd.to_datetime(frame["date"], errors="coerce")
        truncated[symbol] = frame.loc[frame_dates <= replay_day].copy()
    return market_permission_from_frames(truncated)


def select_signal_action(
    *,
    filters_ok: bool,
    continuation_ok: bool,
    setup_forming: bool,
    exit_pressure: bool,
    seller_control: bool,
    trend_damage: bool,
    mode: str,
) -> tuple[str, int]:
    if exit_pressure or (seller_control and trend_damage):
        return "EXIT PRESSURE", 20
    if filters_ok:
        return "BUY CANDIDATE", 100
    if continuation_ok:
        return "STRONG CONTINUATION", 85
    if setup_forming:
        return "SETUP FORMING", 70
    if mode in {"POWER TREND", "STEADY TREND"}:
        return "WATCH TREND", 50
    if mode == "WAIT / AVOID":
        return "WAIT / AVOID", 0
    return "WAIT", 30


def classify_and_score(
    ticker: str,
    raw: pd.DataFrame,
    prepared: bool = False,
    include_setup_stats: bool = True,
    include_audit_gates: bool = True,
    market_permission: Optional[dict] = None,
    audit_gate_cache: Optional[dict[str, dict]] = None,
    include_climax_gate: bool = True,
) -> dict:
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
    climax_state = momentum_climax_state(d, i, is_etf)
    climax_execution_block = bool(climax_state["execution_block"]) if include_climax_gate else False

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
    demand_days_5 = int(row.demand_days_5) if not pd.isna(row.demand_days_5) else 0
    supply_days_5 = int(row.supply_days_5) if not pd.isna(row.supply_days_5) else 0
    signed_volume_pressure_5 = float(row.signed_volume_pressure_5) if not pd.isna(row.signed_volume_pressure_5) else 0.0
    volatility_contraction = bool(row.volatility_contraction_5) if not pd.isna(row.volatility_contraction_5) else False
    volume_contraction = bool(row.volume_contraction_5) if not pd.isna(row.volume_contraction_5) else False
    bull_trap_confirmed = bool(row.bull_trap_confirmed)
    bear_trap_confirmed = bool(row.bear_trap_confirmed)

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
    transition_reclaim = close > prev.high or (close > row.ema_fast and prev.close <= prev.ema_fast)
    reclaiming_slow = close > row.ema_slow and prev.close <= prev.ema_slow
    local_higher_low = low >= min(float(prev.low), float(d.iloc[i - 2].low)) and close >= prev.close
    early_reclaim_context = (
        close >= row.ema_slow
        or reclaiming_slow
        or (back_inside_bb and close >= row.bb_basis)
        or (close > row.ema_fast and row.ema_fast >= row.ema_slow * 0.985)
    )
    uptrend = close > row.ema_slow and row.ema_fast > row.ema_slow and row.ema_slow >= d.iloc[i - ema_slope_bars].ema_slow
    strong_momentum = close > row.ema_fast and row.ema_fast > row.ema_slow and row.ema_fast >= d.iloc[i - ema_slope_bars].ema_fast and row.ema_slow >= d.iloc[i - ema_slope_bars].ema_slow
    pullback_support = low <= row.ema_fast or low <= row.bb_basis or close <= row.ema_fast * 1.02
    shallow_pullback = low <= row.ema_fast * 1.015 or low <= row.bb_basis or close <= row.ema_fast * 1.025
    support_held = close > row.ema_slow and close > row.lower_bb
    early_support_zone = low <= row.ema_fast * 1.03 or low <= row.bb_basis * 1.02 or close <= row.ema_fast * 1.04
    early_support_held = (close > row.ema_slow or early_reclaim_context) and close >= row.lower_bb and row.close_loc >= 0.50
    early_pullback_candle = demand_tail or constructive_close or (close >= prev.close and row.close_loc >= 0.50)
    standard_pullback_reversal = 40 <= row.rsi <= 60 and row.rsi > prev.rsi and (price_follow or constructive_close)
    momentum_pullback_reversal = 45 <= row.rsi <= 70 and row.rsi >= prev.rsi and (close > row.ema_fast or price_follow or constructive_close)
    pullback_reversal = standard_pullback_reversal or (strong_momentum and momentum_pullback_reversal)
    pullback = uptrend and (pullback_support or (strong_momentum and shallow_pullback)) and support_held and pullback_reversal
    early_pullback = (
        (uptrend or early_reclaim_context)
        and early_support_zone
        and early_support_held
        and 38 <= row.rsi <= 68
        and row.rsi >= prev.rsi - 2
        and early_pullback_candle
        and not breakdown_vol
    )
    recent_momentum_high = d["high"].iloc[i - 10 : i].max()
    momentum_dip = d["low"].iloc[i - 2 : i + 1].min() <= recent_momentum_high * 0.97
    momentum_reclaim = close > open_ and close > prev.close and close > row.ema_fast and row.close_loc >= 0.55
    momentum = strong_momentum and momentum_dip and momentum_reclaim and 55 <= row.rsi <= 85 and close <= row.ema_fast * 1.35
    breakout_level = d["close"].iloc[i - 20 : i].max()
    breakout_ext = (close - row.ema_fast) / atr_now if atr_now > 0 else 0
    breakout = strong_momentum and close >= breakout_level and close > prev.high and wide_bullish and 55 <= row.rsi <= 82 and breakout_ext <= 3.5 and row.macd_hist >= prev.macd_hist
    frequent_buy_setup = bb_touch_or_pierce and back_inside_bb and (rsi_near_oversold or rsi_turning_up)
    transition_buy_setup = (
        (fear_rejected or quiet_absorption or demand_tail or right_side)
        and early_reclaim_context
        and (transition_reclaim or local_higher_low or row.rsi > prev.rsi)
        and not breakdown_vol
    )
    profile_buy = (
        frequent_buy_setup
        or (fear_rejected and recent_oversold_bb and back_inside_bb)
        or transition_buy_setup
    ) and (trend_condition or early_reclaim_context)
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
    volatility_state = classify_volatility_regime(
        personality_profile["personality_type"],
        float(row.atr_pct),
        float(personality_profile["personality_atr_pct"]),
        float(trend_efficiency),
        ema_alignment_clean,
        slow_slope_up,
        float(buyer_score),
        signed_volume_pressure_5,
        demand_days_5,
        supply_days_5,
        accum_vol,
        breakout_vol,
        dist_vol,
        breakdown_vol,
        transition_buy_setup,
        fear_rejected,
        right_side,
    )
    volatility_regime = str(volatility_state["regime"])
    volatility_permission = str(volatility_state["permission"])
    position_size_factor = float(volatility_state["position_size_factor"])
    volatility_plan = str(volatility_state["plan"])
    if climax_execution_block:
        position_size_factor = 0.0
    elif include_climax_gate and climax_state["state"] == "RECLAIM CONFIRMED":
        position_size_factor = min(position_size_factor, 0.50)
    if include_setup_stats or include_audit_gates:
        d = ensure_setup_names(d)
    setup_stats = (
        historical_setup_stats(d, setup)
        if include_setup_stats
        else {"hist_trades": "", "hist_win_rate": "", "hist_avg_return": ""}
    )
    cached_audit_gates = (audit_gate_cache or {}).get(setup)
    ticker_profile = (
        cached_audit_gates["ticker_profile"]
        if include_audit_gates and cached_audit_gates
        else ticker_learning_profile(d)
        if include_audit_gates
        else {
            "ticker_trades": "",
            "ticker_win_rate": "",
            "ticker_avg_return": "",
            "ticker_worst_return": "",
            "ticker_permission": "UNKNOWN",
            "ticker_learning_notes": "",
        }
    )
    walk_forward_stats = (
        cached_audit_gates["walk_forward_stats"]
        if include_audit_gates and cached_audit_gates
        else walk_forward_setup_stats(d, setup)
        if include_audit_gates
        else {
            "wf_train_trades": "",
            "wf_train_win_rate": "",
            "wf_train_avg_return": "",
            "wf_test_trades": "",
            "wf_test_win_rate": "",
            "wf_test_avg_return": "",
            "walk_forward_permission": "UNKNOWN",
            "wf_notes": "",
        }
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
    filters_ok = setup_forming and volume_ok and setup_atr_ok and close_ok and buyer_quality_ok and no_chase and high_beta_no_chase and personality_entry_ok and volatility_permission == "ALLOW" and not avoid and not seller_control and not fomo and not greed_rejected
    continuation_ok = (
        setup_forming
        and not filters_ok
        and mode in {"POWER TREND", "STEADY TREND"}
        and volume_ok
        and setup_atr_ok
        and close_ok
        and high_beta_no_chase
        and personality_entry_ok
        and volatility_permission == "ALLOW"
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
    failed_intraday_strength = high > prev.high and close <= max(prev.close, open_) and row.close_loc <= 0.50
    early_distribution_pressure = (
        (dist_vol and (close_off_high or failed_intraday_strength))
        or (seller_control and close_off_high)
        or (greed_rejected and row.close_loc <= 0.50)
        or (upper_wick > body_for_ratio * 1.8 and row.close_loc <= 0.45 and vol_ready and row.volume >= row.vol_ma)
    )
    profit_protect_pressure = atr_extension_exhaustion or early_distribution_pressure
    hard_exit_pressure = (
        (confirmed_exhaustion and confirmed_break)
        or (confirmed_break and (breakdown_vol or seller_control))
        or (seller_control and trend_damage and close < row.ema_slow)
    )
    # Range-bound names frequently mean-revert after one-day supply. Only
    # structural damage is an EXIT; softer supply remains profit protection.
    exit_pressure = personality_exit_pressure(
        personality_profile["personality_type"],
        hard_exit_pressure,
        early_distribution_pressure,
        trend_damage,
    )

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

    execution_style = execution_style_for_setup(setup)
    entry_zone_plan = ""
    if setup_forming and execution_style == "BREAKOUT TRIGGER":
        entry_zone_low, entry_zone_high = breakout_trigger_band(
            close,
            high,
            atr_now,
            str(personality_profile["personality_type"]),
            volatility_regime,
        )
        entry_est = entry_zone_high
        zone_width_pct = (entry_zone_high / entry_zone_low - 1) * 100 if entry_zone_low > 0 else np.nan
        entry_zone_plan = "Enter only after price reaches the trigger band; skip the trade if it opens or runs above the maximum entry."
    elif setup_forming and not math.isnan(entry_est) and float(entry_est) > 0:
        zone_width_pct = entry_zone_width_pct(
            setup,
            str(personality_profile["personality_type"]),
            float(row.atr_pct),
            volatility_regime,
        )
        entry_zone_high = float(entry_est)
        entry_zone_low = entry_zone_high * (1 - zone_width_pct / 100)
        entry_zone_plan = "Use a limit entry inside the pullback zone; require the zone to hold and do not chase above it."
    else:
        zone_width_pct = np.nan
        entry_zone_high = np.nan
        entry_zone_low = np.nan
        execution_style = "NONE"

    trade_entry = entry_zone_high if setup_forming and not math.isnan(entry_zone_high) else close
    stop_pct = 6.0 if setup == "BREAKOUT BUY" else 4.0 if setup == "MOMENTUM BUY" else 7.0 if setup == "PULLBACK BUY" else 6.0 if setup == "EARLY PULLBACK BUY" else 5.0
    atr_stop_mult = 4.0 if setup in {"BREAKOUT BUY", "MOMENTUM BUY"} else 3.5 if setup == "PULLBACK BUY" else 3.25 if setup == "EARLY PULLBACK BUY" else 3.0
    max_risk_stop = trade_entry * (1 - stop_pct / 100)
    min_stop_distance_pct = minimum_stop_pct(
        str(personality_profile["personality_type"]),
        volatility_regime,
    )
    min_stop_distance = max(trade_entry * (min_stop_distance_pct / 100), atr_now * 0.20 if atr_now > 0 else 0.0)
    zone_stop_buffer = max(trade_entry * 0.0045, atr_now * 0.18 if atr_now > 0 else 0.0)
    zone_stop = entry_zone_low - zone_stop_buffer if setup_forming and not math.isnan(entry_zone_low) else max_risk_stop
    atr_stop = trade_entry - atr_now * atr_stop_mult if atr_now > 0 else max_risk_stop
    stop = max(max_risk_stop, min(zone_stop, atr_stop, trade_entry - min_stop_distance))
    target = trade_entry + atr_now * 3.0 if atr_now > 0 else trade_entry * (1 + (12.0 if setup == "MOMENTUM BUY" else 10.0 if "PULLBACK" in setup else 8.0) / 100)
    profit_plan = profit_management_plan(
        trade_entry,
        stop,
        target,
        atr_now,
        personality_profile["personality_type"],
        volatility_regime,
    )
    reward_risk = (target - trade_entry) / (trade_entry - stop) if trade_entry > stop else np.nan
    risk_pct_to_stop = (trade_entry - stop) / trade_entry * 100 if trade_entry > stop else np.nan
    position_value_1k_risk = SCANNER_RISK_DOLLARS / (risk_pct_to_stop / 100) if not math.isnan(risk_pct_to_stop) and risk_pct_to_stop > 0 else np.nan
    market_permission_value = (market_permission or {}).get("market_permission", "UNKNOWN")
    ticker_permission = ticker_profile["ticker_permission"]
    walk_forward_permission = walk_forward_stats["walk_forward_permission"]
    risk_permission = (
        "ALLOW"
        if (
            not setup_forming
            or (
                not math.isnan(risk_pct_to_stop)
                and risk_pct_to_stop <= MAX_SIGNAL_RISK_PCT + NUMERIC_TOLERANCE
                and not math.isnan(position_value_1k_risk)
                and position_value_1k_risk <= MAX_SCANNER_POSITION_VALUE + NUMERIC_TOLERANCE
            )
        )
        else "BLOCK"
    )
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

    personality_setup_allowed = personality_setup_execution_allowed(
        personality_profile["personality_type"],
        setup,
        mode,
        transition_buy_setup,
        buyer_score,
        fear_rejected,
        right_side,
        quiet_absorption,
        accum_vol,
        breakout_vol,
        volatility_regime,
        volatility_permission,
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

    emotion_score = 50.0
    emotion_score += (buyer_score - seller_score) * 0.32
    emotion_score += 9.0 if fear_rejected else 0.0
    emotion_score += 7.0 if quiet_absorption else 0.0
    emotion_score += 6.0 if accum_vol or breakout_vol else 0.0
    emotion_score += 4.0 if demand_tail or constructive_close else 0.0
    emotion_score -= 10.0 if dist_vol or breakdown_vol else 0.0
    emotion_score -= 12.0 if greed_rejected or fomo else 0.0
    emotion_score -= 8.0 if seller_control else 0.0
    emotion_score = clamp_float(emotion_score, 0.0, 100.0)

    trend_location_score = 50.0
    trend_location_score += 13.0 if ema_alignment_clean else 0.0
    trend_location_score += 8.0 if close > row.ema_fast else -8.0
    trend_location_score += 7.0 if close > row.ema_slow else -10.0
    trend_location_score += 6.0 if slow_slope_up else -4.0
    trend_location_score += min(max(trend_efficiency * 45.0, 0.0), 12.0)
    trend_location_score += 4.0 if rs_up else -3.0
    trend_location_score -= 10.0 if ema_alignment_bearish else 0.0
    trend_location_score -= 8.0 if atr_extension >= 3.5 else 0.0
    trend_location_score = clamp_float(trend_location_score, 0.0, 100.0)

    setup_context_score = 45.0
    setup_context_score += 18.0 if filters_ok else 0.0
    setup_context_score += 12.0 if continuation_ok else 0.0
    setup_context_score += 8.0 if setup_forming else 0.0
    setup_context_score += 8.0 if profile_buy_ok else -8.0
    setup_context_score += 6.0 if reward_risk_ok else -6.0
    setup_context_score += 5.0 if volume_ok else -6.0
    setup_context_score += 4.0 if close_ok and buyer_quality_ok else -7.0
    setup_context_score += 5.0 if fast_breakout_entry or pullback_reclaim_entry or high_quality_entry_override else 0.0
    setup_context_score -= 14.0 if profile_extended_from_zone or extended_from_zone else 0.0
    setup_context_score -= 10.0 if avoid or exit_pressure else 0.0
    setup_context_score = clamp_float(setup_context_score, 0.0, 100.0)

    transition_edge_score = 45.0
    transition_edge_score += 18.0 if fear_rejected else 0.0
    transition_edge_score += 15.0 if quiet_absorption else 0.0
    transition_edge_score += 14.0 if transition_buy_setup else 0.0
    transition_edge_score += 12.0 if right_side else 0.0
    transition_edge_score += 10.0 if transition_reclaim or reclaiming_slow else 0.0
    transition_edge_score += 8.0 if local_higher_low and row.rsi >= prev.rsi else 0.0
    transition_edge_score += 6.0 if accum_vol or breakout_vol else 0.0
    transition_edge_score -= 18.0 if early_distribution_pressure else 0.0
    transition_edge_score -= 16.0 if fomo or greed_rejected else 0.0
    transition_edge_score -= 14.0 if breakdown_vol or seller_control else 0.0
    transition_edge_score -= 10.0 if profile_extended_from_zone or extended_from_zone else 0.0
    transition_edge_score = clamp_float(transition_edge_score, 0.0, 100.0)

    market_risk_adjustment = 0.0
    market_risk_adjustment -= 10.0 if market_permission_value == "BLOCK" else 0.0
    market_risk_adjustment -= 14.0 if risk_permission == "BLOCK" else 0.0
    personality_bias_bonus = 0.0
    personality_bias_bonus += 4.0 if personality_profile["personality_type"] == "HIGH_BETA" and (fast_breakout_entry or momentum) else 0.0
    personality_bias_bonus += 4.0 if personality_profile["personality_type"] == "COMPOUNDER" and steady_trend and not profile_extended_from_zone else 0.0
    personality_bias_bonus += 3.0 if personality_profile["personality_type"] == "RANGE_BOUND" and (fear_rejected or quiet_absorption) else 0.0
    score_weights = personality_weight_profile(personality_profile["personality_type"])
    next_day_bias_score = clamp_float(
        emotion_score * float(score_weights["emotion"])
        + transition_edge_score * float(score_weights["transition"])
        + setup_context_score * float(score_weights["setup"])
        + trend_location_score * float(score_weights["trend"])
        + market_risk_adjustment
        + personality_bias_bonus,
        0.0,
        100.0,
    )

    distribution_score = 0.0
    distribution_score += 22.0 if dist_vol else 0.0
    distribution_score += 26.0 if breakdown_vol else 0.0
    distribution_score += 18.0 if seller_control else 0.0
    distribution_score += 14.0 if greed_rejected else 0.0
    distribution_score += 10.0 if fomo and row.close_loc < 0.55 else 0.0
    distribution_score += 14.0 if confirmed_break else 0.0
    distribution_score += 10.0 if trend_damage and close < row.ema_fast else 0.0
    distribution_score += 8.0 if upper_wick > body_for_ratio * 1.5 and row.close_loc <= 0.50 else 0.0
    distribution_score += 8.0 if vol_ready and row.volume > row.vol_ma * 1.4 and close < prev.close else 0.0
    distribution_score += 16.0 if supply_days_5 >= 3 and signed_volume_pressure_5 < -0.25 else 0.0
    distribution_score = clamp_float(distribution_score, 0.0, 100.0)

    absorption_score = 0.0
    absorption_score += 24.0 if fear_rejected else 0.0
    absorption_score += 20.0 if quiet_absorption else 0.0
    absorption_score += 16.0 if accum_vol else 0.0
    absorption_score += 12.0 if buyer_control else 0.0
    absorption_score += 10.0 if lower_wick > body_for_ratio * 1.5 and row.close_loc >= 0.55 else 0.0
    absorption_score += 8.0 if vol_ready and row.volume >= row.vol_ma and low <= row.ema_fast * 1.02 and close >= row.ema_slow else 0.0
    absorption_score += 16.0 if demand_days_5 >= 3 and signed_volume_pressure_5 > 0.20 else 0.0
    absorption_score -= 18.0 if breakdown_vol else 0.0
    absorption_score -= 12.0 if seller_control else 0.0
    absorption_score = clamp_float(absorption_score, 0.0, 100.0)

    short_pressure_proxy = 0.0
    short_pressure_proxy += 18.0 if breakdown_vol and close < prev.low else 0.0
    short_pressure_proxy += 16.0 if confirmed_break else 0.0
    short_pressure_proxy += 12.0 if vol_ready and close < row.ema_fast and row.volume > row.vol_ma * 1.2 else 0.0
    short_pressure_proxy += 10.0 if close < open_ and row.close_loc <= 0.35 else 0.0
    short_pressure_proxy += 8.0 if trend_damage and row.macd_hist < prev.macd_hist else 0.0
    short_pressure_proxy -= 16.0 if absorption_score >= 55.0 and close >= row.ema_slow else 0.0
    short_pressure_proxy = clamp_float(short_pressure_proxy, 0.0, 100.0)

    prior_high_retest = high >= prior_high or high >= breakout_level
    failed_reclaim = prior_high_retest and close < max(prior_high, row.ema_fast) and row.close_loc <= 0.50
    failed_breakout = setup in {"BREAKOUT BUY", "MOMENTUM BUY"} and prior_high_retest and close <= prior_high and row.close_loc <= 0.55
    bull_trap_score = 0.0
    bull_trap_score += 40.0 if bull_trap_confirmed else 28.0 if failed_breakout else 0.0
    bull_trap_score += 24.0 if greed_rejected else 0.0
    bull_trap_score += 18.0 if fomo and row.close_loc < 0.60 else 0.0
    bull_trap_score += 14.0 if upper_wick > body_for_ratio * 1.5 and row.close_loc <= 0.50 else 0.0
    bull_trap_score += 10.0 if vol_ready and row.volume > row.vol_ma * 1.3 and failed_reclaim else 0.0
    bull_trap_score += 8.0 if close < open_ and high > prev.high and close <= prev.close else 0.0
    bull_trap_score = clamp_float(bull_trap_score, 0.0, 100.0)

    support_flush = low < prev.low or low <= row.ema_fast or low <= row.lower_bb
    false_breakdown = support_flush and close >= min(prev.close, row.ema_slow) and row.close_loc >= 0.55 and not confirmed_break
    bear_trap_score = 0.0
    bear_trap_score += 40.0 if bear_trap_confirmed else 28.0 if false_breakdown else 0.0
    bear_trap_score += 24.0 if fear_rejected else 0.0
    bear_trap_score += 14.0 if lower_wick > body_for_ratio * 1.5 and row.close_loc >= 0.55 else 0.0
    bear_trap_score += 10.0 if vol_ready and row.volume >= row.vol_ma and close > open_ and support_flush else 0.0
    bear_trap_score += 8.0 if row.rsi > prev.rsi and close >= prev.close else 0.0
    bear_trap_score = clamp_float(bear_trap_score, 0.0, 100.0)

    demand_control_score = 0.0
    demand_control_score += 22.0 if setup in {"BREAKOUT BUY", "MOMENTUM BUY"} else 0.0
    demand_control_score += 18.0 if mode in {"POWER TREND", "STEADY TREND"} else 10.0 if mode == "MEAN REVERSION" and setup in {"BREAKOUT BUY", "MOMENTUM BUY"} else 0.0
    demand_control_score += 18.0 if buyer_score >= 70.0 else 12.0 if buyer_score >= 58.0 else 0.0
    demand_control_score += 16.0 if breakout_vol else 12.0 if accum_vol else 8.0 if row.close_loc >= 0.62 and close > prev.close else 0.0
    demand_control_score += 12.0 if close > row.ema_fast and close > row.ema_slow else 0.0
    demand_control_score += 8.0 if next_day_bias_score >= 70.0 else 0.0
    demand_control_score += 10.0 if volatility_contraction and volume_contraction and breakout_vol else 0.0
    demand_control_score -= 18.0 if distribution_score >= 35.0 else 0.0
    demand_control_score -= 16.0 if bull_trap_score >= 40.0 else 0.0
    demand_control_score -= 14.0 if fomo or greed_rejected or seller_control else 0.0
    demand_control_score -= 18.0 if confirmed_break or exit_pressure else 0.0
    demand_control_score = clamp_float(demand_control_score, 0.0, 100.0)

    squeeze_watch = (
        short_pressure_proxy >= 30.0
        and max(absorption_score, bear_trap_score) >= 52.0
        and close >= row.ema_slow
        and row.close_loc >= 0.52
        and not confirmed_break
    )
    operator_pressure_risk_score = clamp_float(
        distribution_score * 0.48
        + short_pressure_proxy * 0.32
        - absorption_score * 0.25
        + (12.0 if market_permission_value == "BLOCK" else 0.0),
        0.0,
        100.0,
    )

    if squeeze_watch:
        operator_pressure = "SQUEEZE WATCH"
        operator_plan = "Short-pressure proxy is present, but buyers are absorbing supply; confirm reclaim before chasing."
    elif distribution_score >= 65.0 and short_pressure_proxy >= 38.0:
        operator_pressure = "SHORT / DISTRIBUTION PRESSURE"
        operator_plan = "Supply is pressing price; avoid fresh BUY until reclaim and seller pressure cool."
    elif distribution_score >= 55.0:
        operator_pressure = "DISTRIBUTION"
        operator_plan = "Supply is in control; treat rallies as suspect until close and volume improve."
    elif absorption_score >= 60.0:
        operator_pressure = "ACCUMULATION / ABSORPTION"
        operator_plan = "Buyers are absorbing supply; wait for either a controlled pullback or a confirmed trigger."
    elif short_pressure_proxy >= 38.0:
        operator_pressure = "SHORT PRESSURE"
        operator_plan = "Short-pressure proxy is elevated; require a stronger reclaim before treating it as buyable."
    else:
        operator_pressure = "NEUTRAL"
        operator_plan = "No clear big-money pressure edge from the current candle and volume evidence."
    if operator_pressure == "SQUEEZE WATCH":
        operator_pressure_score = max(absorption_score, short_pressure_proxy)
    elif operator_pressure == "ACCUMULATION / ABSORPTION":
        operator_pressure_score = absorption_score
    elif operator_pressure in {"SHORT / DISTRIBUTION PRESSURE", "DISTRIBUTION", "SHORT PRESSURE"}:
        operator_pressure_score = max(operator_pressure_risk_score, distribution_score, short_pressure_proxy)
    else:
        operator_pressure_score = operator_pressure_risk_score
    operator_blocks_buy = operator_pressure in {"SHORT / DISTRIBUTION PRESSURE", "DISTRIBUTION"}

    if bull_trap_confirmed or (bull_trap_score >= 58.0 and bull_trap_score >= bear_trap_score and distribution_score >= 35.0):
        operator_state = "BULL_TRAP"
        operator_state_score = max(bull_trap_score, distribution_score)
        operator_state_plan = "Breakout strength was rejected; avoid chasing until price reclaims the failed breakout area."
    elif bear_trap_confirmed or (bear_trap_score >= 58.0 and bear_trap_score >= bull_trap_score and not confirmed_break):
        operator_state = "BEAR_TRAP / SQUEEZE WATCH"
        operator_state_score = max(bear_trap_score, absorption_score, short_pressure_proxy)
        operator_state_plan = "Support break was rejected; wait for reclaim confirmation before treating it as a squeeze setup."
    elif distribution_score >= 55.0 or operator_pressure in {"SHORT / DISTRIBUTION PRESSURE", "DISTRIBUTION", "SHORT PRESSURE"}:
        operator_state = "DISTRIBUTION"
        operator_state_score = max(distribution_score, short_pressure_proxy, operator_pressure_score)
        operator_state_plan = "Supply is in control; avoid fresh BUY until seller pressure cools and price reclaims."
    elif demand_control_score >= 58.0:
        operator_state = "MARKUP / DEMAND CONTROL"
        operator_state_score = max(demand_control_score, next_day_bias_score, buyer_score)
        operator_state_plan = "Demand is controlling the markup phase; avoid late chase and require the planned trigger or pullback entry."
    elif absorption_score >= 55.0:
        operator_state = "ACCUMULATION"
        operator_state_score = absorption_score
        operator_state_plan = "Buyers are absorbing supply; prefer controlled pullback or reclaim entries."
    else:
        operator_state = "NEUTRAL"
        operator_state_score = max(operator_pressure_score, bull_trap_score, bear_trap_score)
        operator_state_plan = "No clear trap or accumulation/distribution edge from the current candle sequence."

    if operator_state == "BULL_TRAP":
        operator_blocks_buy = True
        if operator_pressure == "NEUTRAL":
            operator_pressure = "DISTRIBUTION"
        operator_pressure_score = max(operator_pressure_score, operator_state_score)
        operator_plan = operator_state_plan
    elif operator_state == "BEAR_TRAP / SQUEEZE WATCH":
        squeeze_watch = True
        operator_pressure = "SQUEEZE WATCH"
        operator_pressure_score = max(operator_pressure_score, operator_state_score)
        operator_plan = operator_state_plan
    elif operator_state == "ACCUMULATION" and operator_pressure == "NEUTRAL":
        operator_pressure = "ACCUMULATION / ABSORPTION"
        operator_pressure_score = operator_state_score
        operator_plan = operator_state_plan
    elif operator_state == "MARKUP / DEMAND CONTROL" and operator_pressure == "NEUTRAL":
        operator_pressure = "ACCUMULATION / ABSORPTION"
        operator_pressure_score = operator_state_score
        operator_plan = operator_state_plan

    execution_safety_ok = market_permission_value != "BLOCK" and risk_permission == "ALLOW"
    next_day_constructive = next_day_bias_score >= 62.0 and not exit_pressure and not avoid
    next_day_buyable = (
        next_day_bias_score >= 70.0
        and execution_safety_ok
        and personality_setup_allowed
        and volatility_permission == "ALLOW"
        and not operator_blocks_buy
        and not profile_extended_from_zone
        and not extended_from_zone
        and not fomo
        and not greed_rejected
        and not seller_control
        and not climax_execution_block
    )

    if exit_pressure or (seller_control and trend_damage):
        next_day_bias = "DEFENSIVE / EXIT RISK"
        next_day_plan = "Protect capital first; wait for buyer reclaim before considering new exposure."
    elif include_climax_gate and climax_state["state"] == "CLIMAX LOCKOUT":
        next_day_bias = "WAIT FOR RECLAIM"
        next_day_plan = "Momentum is unusually extended; wait one session for the event midpoint to hold before considering entry."
    elif include_climax_gate and climax_state["state"] == "RECLAIM FAILED":
        next_day_bias = "AVOID CHASE"
        next_day_plan = "The prior momentum event failed to hold its midpoint; wait for a fresh base or reclaim."
    elif include_climax_gate and climax_state["state"] == "RECLAIM PENDING":
        next_day_bias = "WAIT FOR RECLAIM"
        next_day_plan = "The prior momentum event has not confirmed or failed; keep execution paused."
    elif profile_extended_from_zone or extended_from_zone or fomo or greed_rejected:
        next_day_bias = "AVOID CHASE"
        next_day_plan = (
            "Do not chase strength; wait for a new breakout base and trigger."
            if execution_style == "BREAKOUT TRIGGER"
            else "Do not chase strength; wait for price to reset into the pullback zone."
        )
    elif market_permission_value == "BLOCK" or risk_permission == "BLOCK":
        next_day_bias = "EXECUTION BLOCKED"
        next_day_plan = "Structure is not enough; market or risk governor blocks fresh execution."
    elif volatility_permission == "BLOCK":
        next_day_bias = "EXECUTION BLOCKED"
        next_day_plan = volatility_plan
    elif volatility_permission == "CAUTION":
        next_day_bias = "WATCH TREND"
        next_day_plan = volatility_plan
    elif next_day_buyable and setup_forming:
        next_day_bias = "BULLISH CONFIRM"
        next_day_plan = (
            "Use the breakout trigger band and skip any move above the maximum entry."
            if execution_style == "BREAKOUT TRIGGER"
            else "Use a limit entry only inside the pullback zone and require that zone to hold."
        )
    elif next_day_constructive and setup_forming:
        next_day_bias = "CONSTRUCTIVE PULLBACK"
        next_day_plan = (
            "Setup is forming; wait for price to confirm the trigger without exceeding the maximum entry."
            if execution_style == "BREAKOUT TRIGGER"
            else "Setup is forming; wait for a controlled pullback into the planned limit zone."
        )
    elif mode in {"POWER TREND", "STEADY TREND"} and next_day_bias_score >= 55.0:
        next_day_bias = "WATCH TREND"
        next_day_plan = "Trend personality is healthy; wait for a cleaner trigger or pullback plan."
    else:
        next_day_bias = "NEUTRAL"
        next_day_plan = "No clean next-day edge; wait for stronger buyer tape or cleaner structure."

    if operator_blocks_buy and next_day_bias in {"BULLISH CONFIRM", "CONSTRUCTIVE PULLBACK"}:
        next_day_bias = "CONSTRUCTIVE PULLBACK" if setup_forming and not exit_pressure else "WATCH TREND"
        next_day_plan = operator_plan
    elif squeeze_watch and next_day_bias in {"NEUTRAL", "WATCH TREND"}:
        next_day_bias = "WATCH TREND"
        next_day_plan = operator_plan

    if setup_forming and include_audit_gates:
        filters_ok = (filters_ok and profile_buy_ok) or high_quality_entry_override
        filters_ok = filters_ok and next_day_buyable and personality_setup_allowed
        continuation_ok = continuation_ok and personality_setup_allowed and not profile_extended_from_zone and execution_safety_ok and next_day_constructive and not operator_blocks_buy
    filters_ok = filters_ok and not climax_execution_block
    continuation_ok = continuation_ok and not climax_execution_block
    extension_state = "EXTENDED" if extended_from_zone or profile_extended_from_zone else "NEAR_ZONE" if setup_forming else ""

    action, rank = select_signal_action(
        filters_ok=filters_ok,
        continuation_ok=continuation_ok,
        setup_forming=setup_forming,
        exit_pressure=exit_pressure,
        seller_control=seller_control,
        trend_damage=trend_damage,
        mode=mode,
    )

    score = rank
    score += 4 if mode == "POWER TREND" else 3 if mode == "STEADY TREND" else 4 if mode == "MEAN REVERSION" else 0
    score += 8 if psych in {"FR", "QA", "BUYERS"} else -8 if psych in {"FOMO", "GR", "SELLERS"} else 0
    score += min(max(trend_efficiency * 10, 0), 4)
    score += max(0.0, min((transition_edge_score - 55.0) * 0.20, 8.0))
    score -= min(max(row.atr_pct - setup_max_atr, 0), 15)
    score -= max(0.0, (float(personality_profile["min_buy_quality"]) - buy_quality_score) * 0.25) if setup_forming else 0.0
    score += 4 if operator_pressure == "ACCUMULATION / ABSORPTION" else 0
    score += 3 if squeeze_watch else 0
    score -= 12 if operator_pressure == "SHORT / DISTRIBUTION PRESSURE" else 8 if operator_pressure == "DISTRIBUTION" else 0
    score -= 4 if operator_pressure == "SHORT PRESSURE" else 0
    score -= 12 if volatility_permission == "BLOCK" else 4 if volatility_permission == "CAUTION" else 0
    if setup_forming and market_permission_value == "BLOCK":
        score -= 12
    legacy_history_caution = ticker_permission in {"BLOCK", "CAUTION"} or walk_forward_permission == "BLOCK"
    if setup_forming and legacy_history_caution and next_day_bias_score < 72.0:
        score -= 4
    if setup_forming and risk_permission != "ALLOW":
        score -= 8

    notes = []
    if fear_rejected:
        notes.append("Fear rejected")
    if quiet_absorption:
        notes.append("Quiet absorption")
    if transition_edge_score >= 65:
        notes.append("Transition edge")
    if breakout:
        notes.append("Breakout attempt")
    if continuation_ok:
        notes.append("Strong continuation")
    if entry_note:
        notes.append(entry_note)
    if setup_forming and not math.isnan(entry_zone_low) and not math.isnan(entry_zone_high):
        notes.append(
            "Execution uses a personality-adjusted breakout trigger band"
            if execution_style == "BREAKOUT TRIGGER"
            else "Execution uses a personality-adjusted pullback limit zone"
        )
    if profile_extended_from_zone:
        notes.append("Personality-adjusted zone is extended")
    if high_quality_entry_override:
        notes.append("High-beta breakout entry quality accepted")
    if setup_forming and not reward_risk_ok:
        notes.append("Reward/risk is below personality threshold")
    if setup_forming and market_permission_value == "BLOCK":
        notes.append("Market regime hostile")
    if setup_forming and risk_permission != "ALLOW":
        notes.append("Risk governor blocked")
    if setup_forming and not personality_setup_allowed:
        notes.append("Personality requires another confirmation before execution")
    if volatility_regime != "NORMAL":
        notes.append(volatility_plan)
    if include_climax_gate and climax_state["state"] == "CLIMAX LOCKOUT":
        notes.append("Momentum climax; wait for midpoint reclaim")
    elif include_climax_gate and climax_state["state"] == "RECLAIM CONFIRMED":
        notes.append("Prior momentum climax reclaimed its event close")
    elif include_climax_gate and climax_state["state"] in {"RECLAIM FAILED", "RECLAIM PENDING"}:
        notes.append("Prior momentum climax has not produced a valid reclaim")
    if profit_protect_pressure and not exit_pressure:
        notes.append("Profit protect only; structure is not broken")
    if next_day_plan:
        notes.append(next_day_plan)
    if operator_plan and operator_pressure != "NEUTRAL" and operator_plan != next_day_plan:
        notes.append(operator_plan)
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
    if transition_buy_setup:
        reason_codes.append("transition_buy_setup")
    if transition_reclaim or reclaiming_slow:
        reason_codes.append("early_reclaim")
    if early_distribution_pressure:
        reason_codes.append("early_distribution_pressure")
    if buyer_control:
        reason_codes.append("buyer_tape")
    if seller_control:
        reason_codes.append("seller_pressure")
    if exit_pressure:
        reason_codes.append("exit_pressure")
    elif profit_protect_pressure:
        reason_codes.append("profit_protect_pressure")
    if setup_forming and not personality_setup_allowed:
        reason_codes.append("personality_setup_gate")
    if volatility_regime == "TREND VOLATILITY":
        reason_codes.append("trend_volatility")
    elif volatility_regime == "REVERSAL VOLATILITY":
        reason_codes.append("reversal_volatility")
    elif volatility_regime == "CHAOTIC VOLATILITY":
        reason_codes.append("chaotic_volatility")
    if volatility_permission != "ALLOW":
        reason_codes.append("volatility_execution_gate")
    if include_climax_gate and climax_state["state"] == "CLIMAX LOCKOUT":
        reason_codes.append("momentum_climax_lockout")
    elif include_climax_gate and climax_state["state"] == "RECLAIM CONFIRMED":
        reason_codes.append("momentum_climax_reclaimed")
    elif include_climax_gate and climax_state["state"] == "RECLAIM FAILED":
        reason_codes.append("momentum_climax_failed")
    elif include_climax_gate and climax_state["state"] == "RECLAIM PENDING":
        reason_codes.append("momentum_climax_pending")
    if next_day_bias == "BULLISH CONFIRM":
        reason_codes.append("next_day_bullish_confirm")
    elif next_day_bias == "CONSTRUCTIVE PULLBACK":
        reason_codes.append("next_day_constructive_pullback")
    elif next_day_bias == "WATCH TREND":
        reason_codes.append("next_day_watch_trend")
    elif next_day_bias == "AVOID CHASE":
        reason_codes.append("avoid_chase")
    elif next_day_bias in {"DEFENSIVE / EXIT RISK", "EXECUTION BLOCKED"}:
        reason_codes.append("execution_risk")
    if operator_pressure == "ACCUMULATION / ABSORPTION":
        reason_codes.append("operator_accumulation")
    elif operator_pressure in {"DISTRIBUTION", "SHORT / DISTRIBUTION PRESSURE"}:
        reason_codes.append("operator_distribution")
    if operator_pressure in {"SHORT PRESSURE", "SHORT / DISTRIBUTION PRESSURE"}:
        reason_codes.append("operator_short_pressure")
    if squeeze_watch:
        reason_codes.append("operator_squeeze_watch")
    if operator_state == "BULL_TRAP":
        reason_codes.append("operator_bull_trap")
    elif operator_state == "BEAR_TRAP / SQUEEZE WATCH":
        reason_codes.append("operator_bear_trap")
    elif operator_state == "MARKUP / DEMAND CONTROL":
        reason_codes.append("operator_markup_demand")
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
    if setup_forming and market_permission_value == "BLOCK":
        reason_codes.append("market_regime_block")
    if setup_forming and legacy_history_caution and next_day_bias_score < 62.0:
        reason_codes.append("historical_edge_caution")
    if setup_forming and risk_permission != "ALLOW":
        reason_codes.append("risk_governor_block")
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
        "open": round(open_, 2),
        "high": round(high, 2),
        "low": round(low, 2),
        "close": round(close, 2),
        "day_change_pct": round((close / prev.close - 1) * 100, 2),
        "rsi": round(float(row.rsi), 1),
        "atr_pct": round(float(row.atr_pct), 2),
        "relative_volume": round(float(row.relative_volume), 3),
        "close_location": round(float(row.close_loc), 3),
        "range_atr": round(float(row.range_atr), 3),
        "signed_volume_pressure_5": round(float(row.signed_volume_pressure_5), 3),
        "demand_supply_balance_5": round(float(row.demand_days_5 - row.supply_days_5), 2),
        "ema_fast_distance_pct": round((close / float(row.ema_fast) - 1) * 100, 3),
        "ema_slow_distance_pct": round((close / float(row.ema_slow) - 1) * 100, 3),
        "return_5d_pct": round((close / float(d.iloc[-6].close) - 1) * 100, 3),
        "return_20d_pct": round((close / float(d.iloc[-21].close) - 1) * 100, 3),
        "gap_pct": round((open_ / float(prev.close) - 1) * 100, 3),
        "momentum_climax_state": climax_state["state"],
        "momentum_climax_type": climax_state["event_type"],
        "momentum_climax_evidence": int(climax_state["evidence_count"]),
        "momentum_climax_midpoint": round(float(climax_state["event_midpoint"]), 2) if not math.isnan(float(climax_state["event_midpoint"])) else np.nan,
        "momentum_climax_day_change_atr": round(float(climax_state["day_change_atr"]), 3),
        "setup_atr_limit": setup_max_atr,
        "trend_efficiency": round(float(trend_efficiency), 2),
        "personality_type": personality_profile["personality_type"],
        "personality_atr_pct": personality_profile["personality_atr_pct"],
        "personality_abs_move_pct": personality_profile["personality_abs_move_pct"],
        "buy_quality_score": round(float(buy_quality_score), 1),
        "buy_quality_minimum": round(float(personality_profile["min_buy_quality"]), 1),
        "entry_quality_label": entry_quality_label,
        "entry_quality_score": round(float(entry_quality_score), 1),
        "next_day_bias": next_day_bias,
        "next_day_bias_score": round(float(next_day_bias_score), 1),
        "next_day_plan": next_day_plan,
        "emotion_score": round(float(emotion_score), 1),
        "trend_location_score": round(float(trend_location_score), 1),
        "setup_context_score": round(float(setup_context_score), 1),
        "transition_edge_score": round(float(transition_edge_score), 1),
        "personality_weight_label": score_weights["label"],
        "personality_weight_emotion": round(float(score_weights["emotion"]), 2),
        "personality_weight_transition": round(float(score_weights["transition"]), 2),
        "personality_weight_setup": round(float(score_weights["setup"]), 2),
        "personality_weight_trend": round(float(score_weights["trend"]), 2),
        "personality_setup_allowed": bool_text(personality_setup_allowed),
        "volatility_regime": volatility_regime,
        "volatility_permission": volatility_permission,
        "volatility_plan": volatility_plan,
        "position_size_factor": round(position_size_factor, 2),
        "operator_pressure": operator_pressure,
        "operator_pressure_score": round(float(operator_pressure_score), 1),
        "operator_plan": operator_plan,
        "operator_state": operator_state,
        "operator_state_score": round(float(operator_state_score), 1),
        "operator_state_plan": operator_state_plan,
        "demand_control_score": round(float(demand_control_score), 1),
        "bull_trap_score": round(float(bull_trap_score), 1),
        "bear_trap_score": round(float(bear_trap_score), 1),
        "distribution_score": round(float(distribution_score), 1),
        "absorption_score": round(float(absorption_score), 1),
        "short_pressure_proxy": round(float(short_pressure_proxy), 1),
        "squeeze_watch": bool_text(squeeze_watch),
        "profile_zone_limit_pct": round(float(personality_profile["max_zone_distance_pct"]), 2),
        "buyer_score": round(float(buyer_score), 0),
        "seller_score": round(float(seller_score), 0),
        "volume_state": "BREAKDOWN" if breakdown_vol else "DISTRIBUTION" if dist_vol else "BREAKOUT" if breakout_vol else "DEMAND" if accum_vol else "DRY-UP" if dry_up_vol else "NEUTRAL",
        "entry_est": round(float(entry_est), 2) if setup_forming and not math.isnan(entry_est) else "",
        "entry_zone_low": round(float(entry_zone_low), 2) if setup_forming and not math.isnan(entry_zone_low) else "",
        "entry_zone_high": round(float(entry_zone_high), 2) if setup_forming and not math.isnan(entry_zone_high) else "",
        "entry_zone_width_pct": round(float(zone_width_pct), 2) if setup_forming and not math.isnan(zone_width_pct) else "",
        "entry_zone_plan": entry_zone_plan,
        "execution_style": execution_style,
        "execution_window_sessions": 5 if setup_forming else "",
        "stop_est": round(float(stop), 2) if setup_forming else "",
        "target_est": round(float(target), 2) if setup_forming else "",
        "take_profit_1": round(float(profit_plan["take_profit_1"]), 2) if setup_forming and not math.isnan(profit_plan["take_profit_1"]) else "",
        "take_profit_1_r": round(float(profit_plan["take_profit_1_r"]), 2) if setup_forming and not math.isnan(profit_plan["take_profit_1_r"]) else "",
        "take_profit_1_reduce_pct": round(float(profit_plan["take_profit_1_reduce_pct"]), 0) if setup_forming and not math.isnan(profit_plan["take_profit_1_reduce_pct"]) else "",
        "post_tp1_stop": round(float(profit_plan["post_tp1_stop"]), 2) if setup_forming and not math.isnan(profit_plan["post_tp1_stop"]) else "",
        "profit_management_plan": profit_plan["profit_management_plan"] if setup_forming else "",
        "reward_risk": round(float(reward_risk), 2) if setup_forming and not math.isnan(reward_risk) else "",
        "risk_pct_to_stop": round(float(risk_pct_to_stop), 2) if setup_forming and not math.isnan(risk_pct_to_stop) else "",
        "position_value_1k_risk": round(float(position_value_1k_risk), 0) if setup_forming and not math.isnan(position_value_1k_risk) else "",
        "market_permission": market_permission_value,
        "ticker_permission": ticker_permission,
        "walk_forward_permission": walk_forward_permission,
        "risk_permission": risk_permission,
        "ticker_trades": ticker_profile["ticker_trades"],
        "ticker_win_rate": ticker_profile["ticker_win_rate"],
        "ticker_avg_return": ticker_profile["ticker_avg_return"],
        "ticker_worst_return": ticker_profile["ticker_worst_return"],
        "wf_test_trades": walk_forward_stats["wf_test_trades"],
        "wf_test_win_rate": walk_forward_stats["wf_test_win_rate"],
        "wf_test_avg_return": walk_forward_stats["wf_test_avg_return"],
        "distance_from_ref_zone_pct": round(float(distance_from_ref_zone_pct), 2) if setup_forming and not math.isnan(distance_from_ref_zone_pct) else "",
        "extension_state": extension_state,
        "reason_codes": reason_codes,
        "signal_stage": signal_stage(action),
        "hist_trades": setup_stats["hist_trades"],
        "hist_win_rate": setup_stats["hist_win_rate"],
        "hist_avg_return": setup_stats["hist_avg_return"],
        "exit_pressure": bool_text(exit_pressure),
        "profit_protect_pressure": bool_text(profit_protect_pressure and not exit_pressure),
        "hard_exit_pressure": bool_text(hard_exit_pressure),
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
        context_adjustment = 0.0

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

        selected_overlay, context_adjustment, overlay_transition = resolve_context_overlay(row, history_rows, index, enriched)
        if overlay_transition:
            transition_label = overlay_transition
        if selected_overlay and selected_overlay.get("transition_score_override") is not None:
            transition_score = float(selected_overlay["transition_score_override"])
        action = row.get("action", "")

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

        adjusted_score = max(0.0, min(128.0, float(numeric_or_none(row.get("score")) or 0) + transition_score + context_adjustment - stale_penalty))
        row.update(
            {
                "signal_stage": signal_stage(action),
                "transition_label": transition_label,
                "transition_score": round(float(transition_score + context_adjustment - stale_penalty), 1),
                "signal_age_days": signal_age_days,
                "price_progress_since_signal_pct": round(float(price_progress), 2) if price_progress is not None else "",
                "freshness_penalty": round(float(stale_penalty), 1),
                "adjusted_score": round(float(adjusted_score), 1),
                "reason_codes": list(dict.fromkeys(reason_codes)),
            }
        )
        enriched.append(row)
    return enriched


def build_behavior_history(
    ticker: str,
    raw: pd.DataFrame,
    days: int = 30,
    benchmark_frames: Optional[dict[str, pd.DataFrame]] = None,
) -> list[dict]:
    # Setup detection is history-wide but immutable for a fixed replay frame.
    # Compute it once; each truncated replay slice then reuses only prior data.
    d = ensure_setup_names(prepare(raw))
    if len(d) < 220:
        return []

    history_rows: list[dict] = []
    audit_gate_cache: dict[str, dict] = {}
    start = max(220, len(d) - days + 1)
    for replay_index, end in enumerate(range(start, len(d) + 1)):
        try:
            replay_market_permission = market_permission_for_replay_date(
                benchmark_frames or {},
                d.iloc[end - 1].date,
            )
            # A newly observed setup is calculated immediately. Cached gates
            # only originate from earlier bars and are refreshed every five
            # sessions; daily OHLCV and market gates remain live.
            cache_for_snapshot = (
                None
                if replay_index % REPLAY_AUDIT_GATE_REFRESH_BARS == 0
                else audit_gate_cache
            )
            snapshot = classify_and_score(
                ticker,
                d.iloc[:end].copy(),
                prepared=True,
                include_setup_stats=False,
                # Replay must use the same executable gates as production;
                # otherwise learning can reward signals the app would block.
                include_audit_gates=True,
                market_permission=replay_market_permission,
                audit_gate_cache=cache_for_snapshot,
            )
        except Exception:
            continue
        audit_gate_cache[snapshot["setup"]] = {
            "ticker_profile": {
                "ticker_trades": snapshot.get("ticker_trades", ""),
                "ticker_win_rate": snapshot.get("ticker_win_rate", ""),
                "ticker_avg_return": snapshot.get("ticker_avg_return", ""),
                "ticker_worst_return": snapshot.get("ticker_worst_return", ""),
                "ticker_permission": snapshot.get("ticker_permission", "UNKNOWN"),
                "ticker_learning_notes": snapshot.get("ticker_learning_notes", ""),
            },
            "walk_forward_stats": {
                "wf_train_trades": snapshot.get("wf_train_trades", ""),
                "wf_train_win_rate": snapshot.get("wf_train_win_rate", ""),
                "wf_train_avg_return": snapshot.get("wf_train_avg_return", ""),
                "wf_test_trades": snapshot.get("wf_test_trades", ""),
                "wf_test_win_rate": snapshot.get("wf_test_win_rate", ""),
                "wf_test_avg_return": snapshot.get("wf_test_avg_return", ""),
                "walk_forward_permission": snapshot.get("walk_forward_permission", "UNKNOWN"),
                "wf_notes": snapshot.get("wf_notes", ""),
            },
        }
        snapshot["history_day"] = len(d) - end
        history_rows.append(snapshot)
    return [apply_anti_signal_penalty(row) for row in enrich_signal_transitions(history_rows)]


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
    "next_day_bias",
    "next_day_bias_score",
    "next_day_plan",
    "emotion_score",
    "trend_location_score",
    "setup_context_score",
    "transition_edge_score",
    "personality_weight_label",
    "personality_weight_emotion",
    "personality_weight_transition",
    "personality_weight_setup",
    "personality_weight_trend",
    "personality_setup_allowed",
    "volatility_regime",
    "volatility_permission",
    "volatility_plan",
    "position_size_factor",
    "take_profit_1",
    "take_profit_1_r",
    "take_profit_1_reduce_pct",
    "post_tp1_stop",
    "profit_management_plan",
    "profit_stage",
    "take_profit_1_hit",
    "profit_peak_r",
    "profit_giveback_r",
    "active_protective_stop",
    "profit_protect_pressure",
    "hard_exit_pressure",
    "operator_pressure",
    "operator_pressure_score",
    "operator_plan",
    "operator_state",
    "operator_state_score",
    "operator_state_plan",
    "demand_control_score",
    "bull_trap_score",
    "bear_trap_score",
    "distribution_score",
    "absorption_score",
    "short_pressure_proxy",
    "squeeze_watch",
    "anti_signal_score",
    "anti_signal_level",
    "anti_signal_plan",
    "prediction_horizon_sessions",
    "prediction_upside_probability",
    "prediction_downside_probability",
    "prediction_no_edge_probability",
    "prediction_confidence",
    "prediction_model_version",
    "prediction_state",
    "contextual_overlay",
    "contextual_score_adjustment",
    "contextual_plan",
    "execution_block",
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
    latest_date = str(latest.get("date") or "")
    row_date = str(row.get("date") or "")
    if latest_date and latest_date == row_date:
        overlay = str(latest.get("contextual_overlay") or "").upper()
        if latest.get("execution_block") == "YES" and row.get("action") in {"BUY CANDIDATE", "STRONG CONTINUATION"}:
            row["action"] = "SETUP FORMING"
            row["signal_stage"] = "SETUP"
            row["adjusted_score"] = min(row_float(row, "adjusted_score", row_float(row, "score")), 49.0)
            append_unique_reason(row, "latest_context_execution_block")
        elif overlay == "VOLATILE TREND HOLD" and row.get("action") == "EXIT PRESSURE":
            row["action"] = "WATCH TREND"
            row["signal_stage"] = "WATCH"
            row["adjusted_score"] = max(row_float(row, "adjusted_score", row_float(row, "score")), 50.0)
            append_unique_reason(row, "latest_context_volatile_hold")
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

    next_day_bias = row.get("next_day_bias", "")
    overlay = str(row.get("contextual_overlay") or "").upper()
    if overlay == "POST-EXIT COOLDOWN":
        signal_quality = "COOLDOWN"
    elif overlay == "POST-EXIT RISK PERSISTENCE":
        signal_quality = "EXIT RISK"
    elif overlay == "PROFIT PROTECT":
        signal_quality = "PROFIT PROTECT"
    elif overlay == "TAKE PROFIT 1":
        signal_quality = "TAKE PROFIT 1"
    elif overlay == "PROFIT ACTIVE":
        signal_quality = "PROFIT ACTIVE"
    elif overlay == "VOLATILE TREND HOLD":
        signal_quality = "VOLATILE HOLD"
    elif row.get("extension_state") == "EXTENDED":
        signal_quality = "EXTENDED"
    elif event_risk and actionable:
        signal_quality = "EVENT RISK"
    elif next_day_bias == "BULLISH CONFIRM" and actionable:
        signal_quality = "NEXT-DAY BULLISH"
    elif next_day_bias == "CONSTRUCTIVE PULLBACK" and actionable:
        signal_quality = "NEXT-DAY BUILDING"
    elif next_day_bias in {"AVOID CHASE", "DEFENSIVE / EXIT RISK", "EXECUTION BLOCKED"}:
        signal_quality = next_day_bias
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

    feedback_quality = row.get("feedback_quality", "")
    if actionable and feedback_quality == "FAILED":
        adjusted_score = max(0.0, adjusted_score - 18.0)
        signal_quality = "FEEDBACK FAILED"
        reason_codes.append("feedback_failed")
    elif actionable and feedback_quality == "STALE":
        adjusted_score = max(0.0, adjusted_score - 12.0)
        signal_quality = "FEEDBACK STALE"
        reason_codes.append("feedback_stale")
    elif actionable and feedback_quality == "WORKING":
        adjusted_score = min(128.0, adjusted_score + 4.0)
        reason_codes.append("feedback_working")

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
      const actionLabels = __ACTION_DISPLAY_LABELS__;
      return actionLabels[action] || action || "WAIT";
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
      const latestUrl = `${baseUrl}/rest/v1/watchlist_refresh_runs?select=publication_id,run_date,status&status=in.(ok,degraded)&order=run_date.desc,created_at.desc&limit=1`;
      const latestResponse = await fetch(latestUrl, { headers: supabaseHeaders(config) });
      if (!latestResponse.ok) throw new Error("Could not read latest Supabase run.");
      const latestRuns = await latestResponse.json();
      if (!latestRuns.length) return [];

      const runDate = latestRuns[0].run_date;
      const publicationId = latestRuns[0].publication_id;
      const selectedTicker = ticker.trim().toUpperCase();
      const historyUrl = `${baseUrl}/rest/v1/watchlist_behavior_history?select=payload&publication_id=eq.${encodeURIComponent(publicationId)}&run_date=eq.${encodeURIComponent(runDate)}&ticker=eq.${encodeURIComponent(selectedTicker)}&order=history_date.asc`;
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
    path.write_text(
        html_page.replace(
            "__ACTION_DISPLAY_LABELS__",
            json.dumps(ACTION_DISPLAY_LABELS, sort_keys=True),
        )
    )


def write_html(df: pd.DataFrame, path: Path, status_text: Optional[str] = None, preflight_text: Optional[str] = None) -> None:
    display_columns = [
        "ticker", "name", "action", "score", "close", "day_change_pct",
        "buy_tier",
        "contextual_overlay",
        "last_outcome_label", "last_outcome_return_pct",
        "next_day_bias", "next_day_bias_score", "next_day_plan",
        "operator_state", "operator_state_score", "operator_state_plan",
        "volatility_regime", "volatility_permission", "position_size_factor",
        "data_provider", "data_provider_status",
        "setup", "adaptive_mode", "psychology", "reward_risk",
        "risk_pct_to_stop", "position_value_1k_risk",
        "market_permission", "risk_permission",
        "volume_state", "entry_zone_low", "entry_zone_high", "entry_zone_width_pct",
        "entry_est", "stop_est", "target_est", "notes",
    ]
    display_columns = [col for col in display_columns if col in df.columns]
    visible_df = df[display_columns].copy()

    summary_items = [
        (ACTION_DISPLAY_LABELS["BUY CANDIDATE"], int((df["action"] == "BUY CANDIDATE").sum()), "buy"),
        (ACTION_DISPLAY_LABELS["STRONG CONTINUATION"], int((df["action"] == "STRONG CONTINUATION").sum()), "continue"),
        (ACTION_DISPLAY_LABELS["SETUP FORMING"], int((df["action"] == "SETUP FORMING").sum()), "setup"),
        (ACTION_DISPLAY_LABELS["WATCH TREND"], int((df["action"] == "WATCH TREND").sum()), "watch"),
        (ACTION_DISPLAY_LABELS["EXIT PRESSURE"], int((df["action"] == "EXIT PRESSURE").sum()), "exit"),
        (ACTION_DISPLAY_LABELS["WAIT / AVOID"], int(df["action"].isin(["WAIT", "WAIT / AVOID"]).sum()), "avoid"),
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
        "buy_tier": "Exec Tier",
        "last_outcome_label": "Self Score",
        "last_outcome_return_pct": "Self Ret%",
        "next_day_bias": "Next Day",
        "next_day_bias_score": "Bias",
        "next_day_plan": "Plan",
        "operator_state": "Operator",
        "operator_state_score": "Op Score",
        "operator_state_plan": "Operator Read",
        "data_provider": "Data Src",
        "data_provider_status": "Src Status",
        "setup": "Setup",
        "adaptive_mode": "Mode",
        "psychology": "Tape",
        "reward_risk": "R/R",
        "risk_pct_to_stop": "Risk%",
        "position_value_1k_risk": "Pos@1k",
        "market_permission": "Mkt",
        "risk_permission": "Risk",
        "volume_state": "Vol",
        "entry_zone_low": "Zone Low",
        "entry_zone_high": "Zone High",
        "entry_zone_width_pct": "Zone%",
        "entry_est": "Ref Zone",
        "stop_est": "Stop",
        "target_est": "Target",
        "notes": "Read",
    }
    action_labels = ACTION_DISPLAY_LABELS
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
        if col == "next_day_bias":
            return f"<span class='badge setup'>{escaped}</span>" if text else "<span class='dash'>-</span>"
        if col == "buy_tier":
            klass = "buy" if text == "A+ BUY" else "setup" if text in {"BUY WATCH", "SETUP ONLY"} else "exit" if text == "EXIT RISK" else "watch"
            return f"<span class='badge action {klass}'>{escaped}</span>" if text else "<span class='dash'>-</span>"
        if col == "operator_state":
            if not text:
                return "<span class='dash'>-</span>"
            klass = "exit" if "DISTRIBUTION" in text or "BULL_TRAP" in text else "setup" if "BEAR_TRAP" in text or "ACCUMULATION" in text or "MARKUP" in text else "watch"
            return f"<span class='badge action {klass}'>{escaped}</span>"
        if col in {"score", "next_day_bias_score", "operator_state_score", "reward_risk", "day_change_pct", "risk_pct_to_stop", "last_outcome_return_pct", "entry_zone_width_pct"}:
            try:
                return f"{float(value):.1f}"
            except (TypeError, ValueError):
                return escaped
        if col == "position_value_1k_risk":
            try:
                return f"{float(value):,.0f}"
            except (TypeError, ValueError):
                return escaped
        if col in {"close", "entry_est", "entry_zone_low", "entry_zone_high", "stop_est", "target_est"}:
            try:
                return f"{float(value):.2f}"
            except (TypeError, ValueError):
                return escaped
        return escaped

    numeric_columns = {"score", "next_day_bias_score", "operator_state_score", "reward_risk", "day_change_pct", "risk_pct_to_stop", "position_value_1k_risk", "close", "entry_est", "entry_zone_low", "entry_zone_high", "entry_zone_width_pct", "stop_est", "target_est"}

    rows = []
    for _, row in visible_df.iterrows():
        search_text = " ".join(str(row.get(col, "")) for col in visible_df.columns).lower()
        action_kind = action_class(row["action"])
        score_value = row.get("score", "")
        change_value = row.get("day_change_pct", "")
        priority_value = row.get("execution_priority", "")
        data_attrs = (
            f"data-action='{action_kind}' "
            f"data-score='{html.escape(str(score_value))}' "
            f"data-change='{html.escape(str(change_value))}' "
            f"data-priority='{html.escape(str(priority_value))}' "
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
        <option value="priority-asc">Execution tier first</option>
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
        if (field === "priority") {{
          return ((Number.parseFloat(a.dataset.priority) || 99) - (Number.parseFloat(b.dataset.priority) || 99)) * multiplier;
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
    parser.add_argument("--refresh", action="store_true", help="Fetch fresh data from configured market data providers instead of using cached CSV files.")
    parser.add_argument("--years", type=int, default=1)
    parser.add_argument("--history-days", type=int, default=30, help="Number of recent trading days to include in behavior history.")
    parser.add_argument("--learning-lookback-days", type=int, default=DEFAULT_LEARNING_LOOKBACK_DAYS, help="Number of recent trading days to replay for learning samples.")
    parser.add_argument(
        "--full-ohlcv-refresh",
        action="store_true",
        help="Maintenance-only full provider refetch; weekly learning rebuilds normally reuse the canonical 400-bar store.",
    )
    parser.add_argument(
        "--allow-calibration-bootstrap",
        action="store_true",
        help="Allow an explicit baseline rebuild when no compatible prior daily incremental state exists.",
    )
    parser.add_argument(
        "--refresh-mode",
        choices=("auto", "daily", "weekly_rebuild"),
        default="auto",
        help="Daily appends state and settles new samples; weekly_rebuild replays and recalibrates the full learning window.",
    )
    parser.add_argument("--no-supabase", action="store_true", help="Skip Supabase sync even if credentials are configured.")
    parser.add_argument("--cache-only", action="store_true", help="Use only existing cached price CSV files and skip live Yahoo chart fetches.")
    parser.add_argument(
        "--skip-profiles",
        action="store_true",
        help="Skip Yahoo company profile enrichment so signal and Supabase refreshes cannot stall on non-signal data.",
    )
    args = parser.parse_args()
    refresh_mode = resolve_refresh_mode(args.refresh_mode)
    today = local_run_date()

    tickers = read_watchlist(Path(args.watchlist))
    live_access_ok = True
    live_access_message = "Live market data access available."
    if args.refresh:
        live_access_ok, live_access_message = check_live_data_access()

    rows = []
    history_rows = []
    learning_history_rows = []
    raw_frames: dict[str, pd.DataFrame] = {}
    directional_history_by_ticker: dict[str, list[dict]] = {}
    failures = []
    stale_cache_fallbacks = []
    previous_history_rows = fetch_previous_behavior_history(today) if not args.no_supabase else load_local_behavior_history()
    previous_run_metadata = fetch_previous_run_metadata(today) if not args.no_supabase else load_local_run_metadata()
    previous_incremental_metadata = compatible_incremental_metadata(previous_run_metadata)
    previous_history_by_ticker = behavior_history_by_ticker(previous_history_rows)
    daily_state_ready = bool(previous_history_rows and previous_incremental_metadata)
    state_compatible = bool(previous_incremental_metadata)
    needs_bootstrap = (refresh_mode == "daily" and not daily_state_ready) or (
        refresh_mode == "weekly_rebuild" and not state_compatible
    )
    if needs_bootstrap and not args.allow_calibration_bootstrap:
        raise SystemExit(
            "No compatible incremental state is available. Run an explicit calibration bootstrap; parity must never be bypassed implicitly."
        )
    effective_mode = "weekly_rebuild" if needs_bootstrap else refresh_mode
    if needs_bootstrap:
        print("Explicit calibration bootstrap enabled; rebuilding the bounded 60-session state.")
    benchmark_frames: dict[str, pd.DataFrame] = {}
    for benchmark in ("SPY", "QQQ", "SMH"):
        try:
            if args.cache_only or (args.refresh and not live_access_ok):
                benchmark_frames[benchmark] = cached_chart(benchmark, years=args.years)
            else:
                benchmark_frames[benchmark] = load_or_refresh_ohlcv(
                    benchmark,
                    years=args.years,
                    refresh=args.refresh,
                    force_full=args.full_ohlcv_refresh,
                )
        except Exception as exc:
            print(f"Benchmark context unavailable for {benchmark}: {exc}")
    market_permission = market_permission_from_frames(benchmark_frames)
    replay_days = max(args.history_days, args.learning_lookback_days)

    for ticker in tickers:
        try:
            if args.cache_only or (args.refresh and not live_access_ok):
                df = cached_chart(ticker, years=args.years)
                if args.refresh and not live_access_ok:
                    stale_cache_fallbacks.append(
                        {"ticker": display_ticker(ticker), "error": live_access_message}
                    )
            else:
                df = load_or_refresh_ohlcv(
                    ticker,
                    years=args.years,
                    refresh=args.refresh,
                    force_full=args.full_ohlcv_refresh,
                )
            raw_frames[ticker] = df
            row = classify_and_score(ticker, df, market_permission=market_permission)
            row = apply_data_provider_context(row, df)
            row["indicator_state_version"] = INDICATOR_STATE_VERSION
            row["raw_window_hash"] = ohlcv_window_hash(df)
            if effective_mode == "weekly_rebuild":
                ticker_learning_history = build_behavior_history(
                    ticker, df, days=replay_days, benchmark_frames=benchmark_frames
                )
                ticker_learning_history = apply_data_provider_context_to_rows(ticker_learning_history, df)
                ticker_history = ticker_learning_history[-args.history_days:]
            else:
                ticker_history = append_incremental_behavior_row(
                    previous_history_by_ticker.get(display_ticker(ticker), []),
                    row,
                    args.history_days,
                )
                ticker_history = apply_data_provider_context_to_rows(ticker_history, df)
                ticker_learning_history = []
            row = apply_latest_signal_context(row, ticker_history)
            row.update(signal_outcome_from_history(row, ticker_history))
            if not args.skip_profiles:
                row.update(fetch_company_profile(ticker, refresh=args.refresh and live_access_ok))
            row = apply_quality_overlays(row, market_context_for(df, benchmark_frames))
            rows.append(row)
            history_rows.extend(ticker_history)
            learning_history_rows.extend(ticker_learning_history)
            if effective_mode == "weekly_rebuild":
                directional_history_by_ticker[ticker] = build_directional_raw_history(ticker, df)
            if args.refresh:
                record_stale_cache_fallback(stale_cache_fallbacks, ticker, df, live_access_message)
        except URLError as exc:
            if not args.refresh or args.cache_only:
                failures.append({"ticker": display_ticker(ticker), "error": str(exc)})
                continue
            try:
                df = cached_chart(ticker, years=args.years)
                raw_frames[ticker] = df
                row = classify_and_score(ticker, df, market_permission=market_permission)
                row = apply_data_provider_context(row, df)
                row["indicator_state_version"] = INDICATOR_STATE_VERSION
                row["raw_window_hash"] = ohlcv_window_hash(df)
                if effective_mode == "weekly_rebuild":
                    ticker_learning_history = build_behavior_history(
                        ticker, df, days=replay_days, benchmark_frames=benchmark_frames
                    )
                    ticker_learning_history = apply_data_provider_context_to_rows(ticker_learning_history, df)
                    ticker_history = ticker_learning_history[-args.history_days:]
                else:
                    ticker_history = append_incremental_behavior_row(
                        previous_history_by_ticker.get(display_ticker(ticker), []),
                        row,
                        args.history_days,
                    )
                    ticker_history = apply_data_provider_context_to_rows(ticker_history, df)
                    ticker_learning_history = []
                row = apply_latest_signal_context(row, ticker_history)
                row.update(signal_outcome_from_history(row, ticker_history))
                if not args.skip_profiles:
                    row.update(fetch_company_profile(ticker, refresh=False))
                row = apply_quality_overlays(row, market_context_for(df, benchmark_frames))
                rows.append(row)
                history_rows.extend(ticker_history)
                learning_history_rows.extend(ticker_learning_history)
                if effective_mode == "weekly_rebuild":
                    directional_history_by_ticker[ticker] = build_directional_raw_history(ticker, df)
                stale_cache_fallbacks.append(
                    {"ticker": display_ticker(ticker), "error": f"live refresh failed; used cache ({exc})"}
                )
            except Exception as cache_exc:
                failures.append({"ticker": display_ticker(ticker), "error": f"{exc}; fallback failed: {cache_exc}"})
        except Exception as exc:
            failures.append({"ticker": display_ticker(ticker), "error": str(exc)})

    if not rows:
        raise SystemExit("No symbols could be analyzed.")

    history_rows = preserve_failed_ticker_history(
        history_rows,
        previous_history_by_ticker,
        {display_ticker(ticker) for ticker in tickers},
        args.history_days,
    )

    report = pd.DataFrame(rows)
    sort_score_col = "adjusted_score" if "adjusted_score" in report.columns else "score"
    report = report.sort_values([sort_score_col, "score", "action", "ticker"], ascending=[False, False, True, True]).reset_index(drop=True)

    publication_id = f"{today}-{int(time.time() * 1000)}-{os.getpid()}"
    for item in rows:
        item["publication_id"] = publication_id
    for item in history_rows:
        item["publication_id"] = publication_id
    csv_path = Path(f"daily_watchlist_overview_{today}.csv")
    html_path = Path(f"daily_watchlist_overview_{today}.html")
    data_dates = sorted(str(value) for value in pd.to_datetime(report["date"]).dt.date.unique())
    latest_data_date = data_dates[-1]
    earliest_data_date = data_dates[0]
    cached_tickers = {str(item.get("ticker", "")).upper() for item in stale_cache_fallbacks}
    rows = [apply_anti_signal_penalty(apply_data_freshness_gate(row, today, cached_tickers)) for row in rows]
    prior_outcomes = fetch_signal_outcome_history(today)
    if needs_bootstrap:
        # An explicit state migration starts a new canonical outcome identity
        # space; never mix samples from an incompatible model contract.
        prior_outcomes = pd.DataFrame()
    parity_report = {
        "passed": None,
        "state": "EXPLICIT_BOOTSTRAP" if needs_bootstrap else "NOT_REQUIRED",
    }
    if effective_mode == "weekly_rebuild":
        if previous_incremental_metadata:
            newly_settled_outcomes = build_incremental_signal_outcomes(
                previous_history_rows,
                raw_frames,
                prior_outcomes,
            )
            canonical_outcomes = combine_signal_outcomes(prior_outcomes, newly_settled_outcomes)
            backfilled_outcomes = rebuild_canonical_signal_outcomes(canonical_outcomes, raw_frames)
            parity_report = calibration_parity_report(
                canonical_outcomes,
                backfilled_outcomes,
                replay_start_dates(raw_frames, args.learning_lookback_days),
            )
            parity_report["state"] = "PASSED" if parity_report["passed"] else "FAILED"
            if not parity_report["passed"]:
                raise SystemExit(f"Weekly calibration parity failed closed: {json.dumps(parity_report, sort_keys=True)}")
        else:
            # Explicit first-run bootstrap has no frozen production decisions;
            # seed from the bounded no-lookahead rule replay once.
            backfilled_outcomes = attach_walk_forward_predictions(
                build_backfilled_signal_outcomes(learning_history_rows)
            )
            newly_settled_outcomes = backfilled_outcomes
        outcome_candidates = combine_signal_outcomes(prior_outcomes, backfilled_outcomes)
    else:
        newly_settled_outcomes = build_incremental_signal_outcomes(
            previous_history_rows,
            raw_frames,
            prior_outcomes,
        )
        backfilled_outcomes = pd.DataFrame()
        outcome_candidates = combine_signal_outcomes(prior_outcomes, newly_settled_outcomes)
    learning_history = restrict_learning_outcomes_to_window(
        outcome_candidates,
        today,
        args.learning_lookback_days,
    )
    learning_stats = build_learning_stats(learning_history, today, args.learning_lookback_days)
    apply_learning_adjustments(rows, learning_stats)
    fillability_stats = build_fillability_stats(learning_history)
    apply_fillability_adjustments(rows, fillability_stats)
    calibration_artifact = None
    calibration_artifact_id = ""
    if effective_mode == "weekly_rebuild":
        directional_history_rows = [
            item
            for ticker_rows in directional_history_by_ticker.values()
            for item in ticker_rows
        ]
        directional_metrics = apply_directional_ohlcv_model(rows, directional_history_rows, publication_id)
        calibration_artifact = directional_metrics.pop("_artifact", None)
        if calibration_artifact and directional_model_from_artifact(calibration_artifact) is None:
            calibration_artifact = None
    else:
        active_calibration = fetch_active_calibration_artifact()
        if active_calibration:
            directional_metrics = apply_directional_calibration_artifact(rows, active_calibration)
            calibration_artifact_id = active_calibration.get("artifact_id", "")
        else:
            directional_metrics = apply_reporting_only_directional_state(rows)
            calibration_artifact_id = ""
    if calibration_artifact:
        calibration_artifact_id = calibration_artifact.get("artifact_id", "")
    rows = sorted(
        rows,
        key=lambda item: (
            -float(numeric_or_none(item.get("adjusted_score")) or numeric_or_none(item.get("score")) or 0),
            -float(numeric_or_none(item.get("score")) or 0),
            str(item.get("action", "")),
            str(item.get("ticker", "")),
        ),
    )
    rows = apply_buy_tiers(rows)
    history_rows = freeze_final_signal_history(history_rows, rows, args.history_days)
    outcomes = learning_history.copy()
    if not outcomes.empty:
        outcomes["publication_id"] = publication_id
    attach_latest_outcomes(rows, outcomes)
    report = pd.DataFrame(rows)
    sort_score_col = "adjusted_score" if "adjusted_score" in report.columns else "score"
    report = report.sort_values(["execution_priority", sort_score_col, "score", "action", "ticker"], ascending=[True, False, False, True, True]).reset_index(drop=True)
    status_parts = [f"Report data as of {latest_data_date}", f"refresh {effective_mode}"]
    if earliest_data_date != latest_data_date:
        status_parts.append(f"mixed source dates {earliest_data_date} to {latest_data_date}")
    if stale_cache_fallbacks:
        status_parts.append(f"{len(stale_cache_fallbacks)} symbols used cached data")
    if "data_provider" in report.columns:
        provider_counts = report["data_provider"].fillna("").replace("", "unknown").value_counts().to_dict()
        provider_summary = ", ".join(f"{provider} {count}" for provider, count in provider_counts.items())
        status_parts.append(f"providers {provider_summary}")
    stale_blocks = int((report.get("freshness_block", pd.Series(dtype=str)) == "YES").sum())
    outcome_summary = summarize_signal_outcomes(outcomes)
    learning_window = learning_history.attrs.get("learning_window", {})
    if stale_blocks:
        status_parts.append(f"{stale_blocks} execution-blocked for stale data")
    if outcome_summary["total"]:
        status_parts.append(f"self-score {outcome_summary['avg_score']} across {outcome_summary['total']} prior signals")
    if failures:
        status_parts.append(f"{len(failures)} symbols failed")
    status_parts.append(f"market {market_permission['market_permission']}: {market_permission['market_regime_summary']}")
    status_text = " | ".join(status_parts)
    preflight_text = None if live_access_ok else f"{live_access_message} Running cache-backed refresh."
    run_status = "ok"
    # A partial scan is usable for context, but must never be reported as a
    # fully healthy daily run when symbols failed to refresh.
    if not live_access_ok or stale_cache_fallbacks or failures:
        run_status = "degraded"
    if failures and not rows:
        run_status = "failed"
    run_metadata = {
        "publication_id": publication_id,
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
        "learning_history_rows": len(learning_history_rows),
        "scanner_version": SCANNER_VERSION,
        "notes": status_text,
        "payload": {
            "publication_id": publication_id,
            "refresh_mode_requested": refresh_mode,
            "refresh_mode": effective_mode,
            "incremental_state_version": INCREMENTAL_STATE_VERSION,
            "incremental_state_ready": True,
            "indicator_state_version": INDICATOR_STATE_VERSION,
            "calibration_artifact_version": CALIBRATION_ARTIFACT_VERSION,
            "calibration_artifact_id": calibration_artifact_id,
            "data_provider_priority": configured_data_providers(),
            "data_provider_counts": provider_counts if "data_provider" in report.columns else {},
            "failures": failures[:25],
            "stale_cache_fallbacks": stale_cache_fallbacks[:25],
            "stale_execution_blocks": stale_blocks,
            "signal_outcomes": outcome_summary,
            "backfilled_signal_outcomes": int(len(backfilled_outcomes)),
            "newly_settled_signal_outcomes": int(len(newly_settled_outcomes)),
            "calibration_parity": parity_report,
            "learning_lookback_days": args.learning_lookback_days,
            "learning_model_version": LEARNING_MODEL_VERSION,
            "learning_horizon_sessions": LEARNING_HORIZON_SESSIONS,
            "learning_evaluation_date_min": learning_window.get("evaluation_date_min", ""),
            "learning_evaluation_date_max": learning_window.get("evaluation_date_max", ""),
            "learning_evaluation_session_count": learning_window.get("evaluation_session_count", 0),
            "directional_model_version": DIRECTIONAL_MODEL_VERSION,
            "directional_feature_count": len(DIRECTIONAL_NUMERIC_FEATURES) + len(DIRECTIONAL_PERSONALITIES),
            "directional_label_count": len(DIRECTIONAL_LABELS),
            "directional_model_oos_samples": directional_metrics.get("sample_count", 0),
            "directional_model_oos_dates": directional_metrics.get("date_count", 0),
            "directional_model_brier_score": directional_metrics.get("brier_score"),
            "directional_model_baseline_brier": directional_metrics.get("baseline_brier_score"),
            "directional_model_brier_skill": directional_metrics.get("brier_skill_score"),
            "directional_model_validated_personalities": directional_metrics.get("validated_personalities", []),
            "directional_model_validated": directional_metrics.get("passed", False),
            "max_execution_data_age_days": MAX_EXECUTION_DATA_AGE_DAYS,
        },
    }

    report.to_csv(csv_path, index=False)
    write_html(report, html_path, status_text=status_text, preflight_text=preflight_text)
    report.to_csv("daily_watchlist_overview_latest.csv", index=False)
    write_html(report, Path("daily_watchlist_overview_latest.html"), status_text=status_text, preflight_text=preflight_text)
    run_metadata_path = Path(f"daily_watchlist_run_metadata_{today}.json")
    run_metadata_path.write_text(json.dumps(run_metadata, separators=(",", ":"), default=str))
    Path("daily_watchlist_run_metadata_latest.json").write_text(json.dumps(run_metadata, separators=(",", ":"), default=str))
    if not outcomes.empty:
        outcomes_path = Path(f"daily_signal_outcomes_{today}.csv")
        outcomes.to_csv(outcomes_path, index=False)
        outcomes.to_csv("daily_signal_outcomes_latest.csv", index=False)
    elif Path("daily_signal_outcomes_latest.csv").exists():
        Path("daily_signal_outcomes_latest.csv").unlink()

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
        sync_ok, sync_reason = should_sync_supabase_snapshot(report, today)
        if sync_ok:
            sync_supabase(
                report,
                history,
                outcomes,
                today,
                run_metadata,
                calibration_artifact=calibration_artifact,
                learning_stats=learning_stats,
            )
        else:
            print(f"Supabase sync skipped: {sync_reason}")

    columns = [
        "ticker", "action", "setup", "adaptive_mode", "psychology", "score", "close", "day_change_pct",
        "data_provider", "data_provider_status",
        "market_permission", "ticker_permission", "walk_forward_permission", "risk_permission",
        "entry_zone_low", "entry_zone_high", "entry_zone_width_pct",
        "risk_pct_to_stop", "position_value_1k_risk", "notes",
    ]
    print(report[columns].to_string(index=False))
    print(live_access_message)
    print(f"\nWrote {csv_path}, {html_path}, daily_watchlist_overview_latest.csv, daily_watchlist_overview_latest.html, watchlist_behavior_history_latest.csv, and history.html")
    if failures:
        print(f"Skipped {len(failures)} symbol(s); see daily_watchlist_overview_failures.csv")
    if stale_cache_fallbacks:
        print(f"Used cached data for {len(stale_cache_fallbacks)} symbol(s); see daily_watchlist_overview_stale_cache.csv")


if __name__ == "__main__":
    main()
