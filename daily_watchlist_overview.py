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
SCANNER_VERSION = "2026.06.12-candle-operator-demand-control"
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
SCANNER_RISK_DOLLARS = 1000.0
MAX_SCANNER_POSITION_VALUE = 25000.0
MAX_SIGNAL_RISK_PCT = 7.0
NUMERIC_TOLERANCE = 1e-6
TICKER_EDGE_MIN_TRADES = 6
WALK_FORWARD_MIN_TEST_TRADES = 3
MAX_EXECUTION_DATA_AGE_DAYS = int(os.getenv("MAX_EXECUTION_DATA_AGE_DAYS", "3"))
TOP_BUY_TIER_LIMIT = int(os.getenv("TOP_BUY_TIER_LIMIT", "8"))
BUY_WATCH_TIER_LIMIT = int(os.getenv("BUY_WATCH_TIER_LIMIT", "24"))
SELF_SCORE_ACTIONS = {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING", "WATCH TREND", "EXIT PRESSURE"}
SELF_SCORE_WORKING_RETURN_PCT = 2.0
SELF_SCORE_FAILED_RETURN_PCT = -2.0
SELF_SCORE_EXIT_AVOIDED_RETURN_PCT = -1.0
LEARNING_MIN_SAMPLES = int(os.getenv("LEARNING_MIN_SAMPLES", "3"))
LEARNING_ADJUSTMENT_CAP = float(os.getenv("LEARNING_ADJUSTMENT_CAP", "10"))
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
        return symbol.replace("BRK.B", "BRK.B")
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
    payload, latency_ms = request_json(url, "polygon")
    results = payload.get("results") or []
    if not results:
        message = payload.get("error") or payload.get("message") or "no aggregate bars returned"
        raise RuntimeError(f"Polygon/Massive returned no bars for {display_ticker(ticker)}: {message}")
    df = pd.DataFrame(
        {
            "date": pd.to_datetime([item.get("t") for item in results], unit="ms", utc=True).tz_convert(None).date,
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
    payload, latency_ms = request_json(f"https://api.twelvedata.com/time_series?{params}", "twelvedata")
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
        with urllib.request.urlopen(req, timeout=30) as resp:
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
    payload, latency_ms = request_json(url, "yahoo")
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
    "next_day_bias",
    "next_day_bias_score",
    "next_day_plan",
    "emotion_score",
    "trend_location_score",
    "setup_context_score",
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
    "last_outcome_label",
    "last_outcome_score",
    "last_outcome_reason",
    "last_outcome_return_pct",
    "learning_sample_count",
    "learning_working_rate",
    "learning_failed_rate",
    "learning_trap_avoided_rate",
    "learning_avg_score",
    "learning_adjustment",
    "learning_plan",
    "data_provider",
    "data_provider_status",
    "data_provider_latency_ms",
    "data_provider_error",
    "data_age_days",
    "freshness_status",
    "freshness_block",
    "freshness_plan",
    "buy_tier",
    "execution_priority",
    "execution_plan",
    "feedback_window_days",
    "feedback_return_pct",
    "feedback_max_drawdown_pct",
    "feedback_stop_hit",
    "feedback_quality",
    "feedback_plan",
    "reason_codes",
}

SUPABASE_RETENTION_DAYS = int(os.getenv("SUPABASE_RETENTION_DAYS", "180"))
SUPABASE_UPSERT_BATCH_SIZE = int(os.getenv("SUPABASE_UPSERT_BATCH_SIZE", "100"))
ALLOW_STALE_SUPABASE_SYNC = os.getenv("ALLOW_STALE_SUPABASE_SYNC", "").strip().lower() in {"1", "true", "yes"}


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
    data_age_days = days_between_dates(run_date, latest_data_date)
    if data_age_days is None or data_age_days > MAX_EXECUTION_DATA_AGE_DAYS:
        return False, (
            f"Latest market data is {data_age_days if data_age_days is not None else 'unknown'} day(s) old "
            f"({latest_data_date}); not overwriting Supabase snapshots."
        )

    stale_count = int((report.get("freshness_block", pd.Series(dtype=str)) == "YES").sum())
    if stale_count >= len(report):
        return False, "Every row is execution-blocked for stale data; not overwriting Supabase snapshots."

    return True, f"Latest market data is fresh enough for Supabase sync ({latest_data_date}, age {data_age_days} day(s))."


def batched_records(records: list[dict], batch_size: int = SUPABASE_UPSERT_BATCH_SIZE) -> list[list[dict]]:
    size = max(1, int(batch_size or 100))
    return [records[index : index + size] for index in range(0, len(records), size)]


def supabase_upsert_batches(table: str, records: list[dict], conflict_columns: list[str]) -> None:
    for batch in batched_records(records):
        supabase_upsert(table, batch, conflict_columns)


def supabase_upsert_with_optional_signal_columns(table: str, records: list[dict], conflict_columns: list[str]) -> None:
    try:
        supabase_upsert_batches(table, records, conflict_columns)
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
        supabase_upsert_batches(table, stripped_records, conflict_columns)


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
        ("watchlist_signal_outcomes", "evaluation_run_date"),
        ("watchlist_refresh_runs", "run_date"),
    ]
    for table, date_column in cleanup_targets:
        supabase_delete_older_than(table, date_column, cutoff)
    print(f"Supabase retention cleanup complete: kept rows from {cutoff} onward ({SUPABASE_RETENTION_DAYS} days).")


def optional_signal_values(row: dict) -> dict:
    return {
        "next_day_bias": row.get("next_day_bias"),
        "next_day_bias_score": numeric_or_none(row.get("next_day_bias_score")),
        "next_day_plan": row.get("next_day_plan"),
        "emotion_score": numeric_or_none(row.get("emotion_score")),
        "trend_location_score": numeric_or_none(row.get("trend_location_score")),
        "setup_context_score": numeric_or_none(row.get("setup_context_score")),
        "operator_pressure": row.get("operator_pressure"),
        "operator_pressure_score": numeric_or_none(row.get("operator_pressure_score")),
        "operator_plan": row.get("operator_plan"),
        "operator_state": row.get("operator_state"),
        "operator_state_score": numeric_or_none(row.get("operator_state_score")),
        "operator_state_plan": row.get("operator_state_plan"),
        "demand_control_score": numeric_or_none(row.get("demand_control_score")),
        "bull_trap_score": numeric_or_none(row.get("bull_trap_score")),
        "bear_trap_score": numeric_or_none(row.get("bear_trap_score")),
        "distribution_score": numeric_or_none(row.get("distribution_score")),
        "absorption_score": numeric_or_none(row.get("absorption_score")),
        "short_pressure_proxy": numeric_or_none(row.get("short_pressure_proxy")),
        "squeeze_watch": row.get("squeeze_watch"),
        "anti_signal_score": numeric_or_none(row.get("anti_signal_score")),
        "anti_signal_level": row.get("anti_signal_level"),
        "anti_signal_plan": row.get("anti_signal_plan"),
        "last_outcome_label": row.get("last_outcome_label"),
        "last_outcome_score": numeric_or_none(row.get("last_outcome_score")),
        "last_outcome_reason": row.get("last_outcome_reason"),
        "last_outcome_return_pct": numeric_or_none(row.get("last_outcome_return_pct")),
        "learning_sample_count": numeric_or_none(row.get("learning_sample_count")),
        "learning_working_rate": numeric_or_none(row.get("learning_working_rate")),
        "learning_failed_rate": numeric_or_none(row.get("learning_failed_rate")),
        "learning_trap_avoided_rate": numeric_or_none(row.get("learning_trap_avoided_rate")),
        "learning_avg_score": numeric_or_none(row.get("learning_avg_score")),
        "learning_adjustment": numeric_or_none(row.get("learning_adjustment")),
        "learning_plan": row.get("learning_plan"),
        "data_provider": row.get("data_provider"),
        "data_provider_status": row.get("data_provider_status"),
        "data_provider_latency_ms": numeric_or_none(row.get("data_provider_latency_ms")),
        "data_provider_error": row.get("data_provider_error"),
        "data_age_days": numeric_or_none(row.get("data_age_days")),
        "freshness_status": row.get("freshness_status"),
        "freshness_block": row.get("freshness_block"),
        "freshness_plan": row.get("freshness_plan"),
        "buy_tier": row.get("buy_tier"),
        "execution_priority": numeric_or_none(row.get("execution_priority")),
        "execution_plan": row.get("execution_plan"),
        "feedback_window_days": numeric_or_none(row.get("feedback_window_days")),
        "feedback_return_pct": numeric_or_none(row.get("feedback_return_pct")),
        "feedback_max_drawdown_pct": numeric_or_none(row.get("feedback_max_drawdown_pct")),
        "feedback_stop_hit": row.get("feedback_stop_hit"),
        "feedback_quality": row.get("feedback_quality"),
        "feedback_plan": row.get("feedback_plan"),
    }


def sync_supabase(report: pd.DataFrame, history: pd.DataFrame, outcomes: pd.DataFrame, run_date: str, run_metadata: Optional[dict] = None) -> None:
    url, key = supabase_credentials()
    if not url or not key:
        print("Supabase sync skipped: SUPABASE_URL and SUPABASE_SECRET_KEY are not set.")
        print("Legacy fallback: SUPABASE_SERVICE_ROLE_KEY is also supported.")
        return

    print(f"Supabase sync target: {urllib.parse.urlparse(url).netloc} ({describe_supabase_key(key)})")

    report_records = []
    for record in report.to_dict(orient="records"):
        row = clean_record(record)
        report_record = {
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
        report_record.update(optional_signal_values(row))
        report_records.append(report_record)

    history_records = []
    if not history.empty:
        for record in history.to_dict(orient="records"):
            row = clean_record(record)
            history_record = {
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
            history_record.update(optional_signal_values(row))
            history_records.append(history_record)

    outcome_records = []
    if not outcomes.empty:
        for record in outcomes.to_dict(orient="records"):
            row = clean_record(record)
            outcome_records.append(
                {
                    "signal_run_date": row.get("signal_run_date"),
                    "evaluation_run_date": row.get("evaluation_run_date"),
                    "ticker": row.get("ticker"),
                    "prior_action": row.get("prior_action"),
                    "prior_setup": row.get("prior_setup"),
                    "prior_buy_tier": row.get("prior_buy_tier"),
                    "prior_operator_state": row.get("prior_operator_state"),
                    "prior_anti_signal_level": row.get("prior_anti_signal_level"),
                    "prior_close": numeric_or_none(row.get("prior_close")),
                    "current_action": row.get("current_action"),
                    "current_operator_state": row.get("current_operator_state"),
                    "current_close": numeric_or_none(row.get("current_close")),
                    "close_return_pct": numeric_or_none(row.get("close_return_pct")),
                    "outcome_label": row.get("outcome_label"),
                    "outcome_score": numeric_or_none(row.get("outcome_score")),
                    "outcome_reason": row.get("outcome_reason"),
                    "learning_key": row.get("learning_key"),
                    "payload": row,
                }
            )

    if run_metadata:
        try:
            supabase_upsert("watchlist_refresh_runs", [clean_record(run_metadata)], ["run_date"])
        except RuntimeError as exc:
            print(f"Supabase run-health sync skipped: {exc}")

    snapshot_synced = 0
    history_synced = 0
    outcome_synced = 0
    try:
        supabase_upsert_with_optional_signal_columns("watchlist_snapshots", report_records, ["run_date", "ticker"])
        snapshot_synced = len(report_records)
    except RuntimeError as exc:
        print(f"Supabase snapshot sync skipped: {exc}")
    try:
        supabase_upsert_with_optional_signal_columns("watchlist_behavior_history", history_records, ["run_date", "ticker", "history_date"])
        history_synced = len(history_records)
    except RuntimeError as exc:
        print(f"Supabase behavior-history sync skipped: {exc}")
    try:
        supabase_upsert("watchlist_signal_outcomes", outcome_records, ["signal_run_date", "evaluation_run_date", "ticker"])
        outcome_synced = len(outcome_records)
    except RuntimeError as exc:
        print(f"Supabase signal-outcome sync skipped: {exc}")
    print(
        f"Synced {snapshot_synced}/{len(report_records)} snapshot rows, "
        f"{history_synced}/{len(history_records)} history rows, and "
        f"{outcome_synced}/{len(outcome_records)} signal-outcome rows to Supabase."
    )
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


def days_between_dates(later: str, earlier: str) -> Optional[int]:
    try:
        later_date = datetime.fromisoformat(str(later)).date()
        earlier_date = datetime.fromisoformat(str(earlier)).date()
    except (TypeError, ValueError):
        return None
    return (later_date - earlier_date).days


def append_unique_reason(row: dict, code: str) -> None:
    codes = list(row.get("reason_codes") or [])
    if code not in codes:
        codes.append(code)
    row["reason_codes"] = codes


def apply_data_freshness_gate(row: dict, run_date: str, cached_tickers: set[str]) -> dict:
    ticker = str(row.get("ticker", "")).upper()
    data_date = row.get("date") or row.get("data_date") or row.get("history_date")
    data_age_days = days_between_dates(run_date, str(data_date)) if data_date else None
    cached_source = ticker in cached_tickers
    freshness_block = data_age_days is None or data_age_days > MAX_EXECUTION_DATA_AGE_DAYS

    if freshness_block:
        freshness_status = "STALE_BLOCK"
        freshness_plan = (
            f"Execution blocked: market data is {data_age_days if data_age_days is not None else 'unknown'} day(s) old; refresh live data before acting."
        )
        append_unique_reason(row, "data_stale_block")
        actionable_stale = row.get("action") in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}
        if row.get("action") in {"BUY CANDIDATE", "STRONG CONTINUATION"}:
            row["action"] = "SETUP FORMING"
            row["signal_stage"] = "SETUP"
        if actionable_stale:
            row["adjusted_score"] = min(float(numeric_or_none(row.get("adjusted_score")) or numeric_or_none(row.get("score")) or 0), 49.0)
            row["score"] = min(float(numeric_or_none(row.get("score")) or 0), 49.0)
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
    raw_score = float(numeric_or_none(row.get("score")) or 0)
    if level == "BLOCK":
        if row.get("action") in {"BUY CANDIDATE", "STRONG CONTINUATION"}:
            row["action"] = "SETUP FORMING"
            row["signal_stage"] = "SETUP"
        if actionable:
            row["adjusted_score"] = min(adjusted_score, 49.0)
            row["score"] = min(raw_score, 49.0)
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
    market_ok = row.get("market_permission") != "BLOCK"
    absorption_or_neutral = (
        operator_state in {"", "NEUTRAL", "ACCUMULATION", "MARKUP / DEMAND CONTROL", "BEAR_TRAP / SQUEEZE WATCH"}
        or operator_pressure in {"NEUTRAL", "ACCUMULATION / ABSORPTION", "SQUEEZE WATCH"}
    )

    if anti_level == "BLOCK" and action in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}:
        return "SETUP ONLY", 4, anti_plan or "Anti-signal block; do not execute directly."
    if anti_level == "CAUTION" and action in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}:
        return "SETUP ONLY", 3, anti_plan or "Anti-signal caution; wait for a cleaner reset."
    if action == "BUY CANDIDATE" and fresh and risk_ok and market_ok and next_day == "BULLISH CONFIRM" and absorption_or_neutral and adjusted_score >= 92 and rank_index < TOP_BUY_TIER_LIMIT:
        return "A+ BUY", 1, "Highest execution tier; still confirm on Pine before acting."
    if action == "BUY CANDIDATE" and fresh and next_day == "BULLISH CONFIRM" and adjusted_score >= 78 and rank_index < BUY_WATCH_TIER_LIMIT:
        return "BUY WATCH", 2, "Qualified buy watch; prefer reference-zone entry and Pine confirmation."
    if action in {"BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"}:
        if quality in {"STALE DATA", "EVENT RISK", "EXTENDED"} or row.get("freshness_block") == "YES":
            return "SETUP ONLY", 4, "Do not execute directly; treat as a setup until the blocker clears."
        return "SETUP ONLY", 3, "Setup is useful, but not in the top execution tier."
    if action == "WATCH TREND":
        return "WATCH", 5, "Trend is worth monitoring, not an entry signal."
    if action == "EXIT PRESSURE":
        return "EXIT RISK", 8, "Risk pressure is elevated."
    return "NO TRADE", 9 if score >= 25 else 10, "No actionable edge."


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
    merged = {**payload, **{key: value for key, value in row.items() if key != "payload"}}
    if "date" not in merged:
        merged["date"] = merged.get("data_date") or merged.get("history_date") or merged.get("run_date")
    return merged


def fetch_previous_snapshot_rows(run_date: str) -> list[dict]:
    try:
        date_rows = supabase_select(
            f"watchlist_snapshots?select=run_date&run_date=lt.{urllib.parse.quote(run_date)}&order=run_date.desc&limit=1"
        )
        if not date_rows:
            return []
        previous_run_date = date_rows[0].get("run_date")
        rows = supabase_select(
            f"watchlist_snapshots?select=*&run_date=eq.{urllib.parse.quote(str(previous_run_date))}&limit=1000"
        )
        return [merge_payload_row(row) for row in rows]
    except RuntimeError as exc:
        print(f"Previous snapshot fetch skipped: {exc}")
        return []


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


def self_score_prior_signal(prior: dict, current: dict, evaluation_run_date: str) -> dict:
    prior_action = prior.get("action", "")
    prior_close = numeric_or_none(prior.get("close"))
    current_close = numeric_or_none(current.get("close"))
    current_stale = str(current.get("freshness_block") or "").upper() == "YES"
    if not prior_close or not current_close or float(prior_close) <= 0:
        outcome = "PENDING"
        score = 0.0
        reason = "No valid close-to-close result yet."
        return_pct = ""
    else:
        return_pct = (float(current_close) / float(prior_close) - 1) * 100
        current_action = current.get("action", "")
        prior_anti = str(prior.get("anti_signal_level") or "NONE").upper()
        prior_operator = str(prior.get("operator_state") or "").upper()
        current_operator = str(current.get("operator_state") or "").upper()
        current_risk = current_action == "EXIT PRESSURE" or current_operator in {"BULL_TRAP", "DISTRIBUTION"}
        prior_trap_warning = prior_anti in {"BLOCK", "CAUTION"} or prior_operator in {"BULL_TRAP", "DISTRIBUTION"}

        if current_stale:
            outcome = "PENDING"
            score = 0.0
            reason = "Current market data is stale; do not learn from this comparison."
        elif prior_trap_warning and prior_action in {"SETUP FORMING", "WATCH TREND", "EXIT PRESSURE"} and return_pct <= 1.0 and current_action != "BUY CANDIDATE":
            outcome = "TRAP_AVOIDED"
            score = 1.0
            reason = "Prior risk warning avoided a low-quality chase."
        elif prior_action in {"BUY CANDIDATE", "STRONG CONTINUATION"}:
            if return_pct >= SELF_SCORE_WORKING_RETURN_PCT:
                outcome = "WORKING"
                score = 1.0
                reason = "BUY followed through close-to-close."
            elif return_pct <= SELF_SCORE_FAILED_RETURN_PCT or current_risk:
                outcome = "FAILED"
                score = -1.0
                reason = "BUY failed or moved into risk pressure."
            else:
                outcome = "STALE"
                score = 0.0
                reason = "BUY did not progress enough yet."
        elif prior_action == "SETUP FORMING":
            if current_action in {"BUY CANDIDATE", "STRONG CONTINUATION"} and return_pct >= 1.0:
                outcome = "WORKING"
                score = 1.0
                reason = "SETUP upgraded with positive follow-through."
            elif return_pct <= -2.5 or current_risk:
                outcome = "FAILED"
                score = -1.0
                reason = "SETUP broke down instead of improving."
            else:
                outcome = "STALE"
                score = 0.0
                reason = "SETUP remains unresolved."
        elif prior_action == "WATCH TREND":
            if return_pct >= SELF_SCORE_WORKING_RETURN_PCT or current_action in {"BUY CANDIDATE", "SETUP FORMING", "STRONG CONTINUATION"}:
                outcome = "WORKING"
                score = 0.7
                reason = "WATCH trend improved or upgraded."
            elif return_pct <= -3.0 or current_risk:
                outcome = "FAILED"
                score = -0.7
                reason = "WATCH trend deteriorated."
            else:
                outcome = "STALE"
                score = 0.0
                reason = "WATCH trend stayed neutral."
        elif prior_action == "EXIT PRESSURE":
            if return_pct <= SELF_SCORE_EXIT_AVOIDED_RETURN_PCT or current_action in {"EXIT PRESSURE", "WAIT", "WAIT / AVOID"}:
                outcome = "TRAP_AVOIDED"
                score = 1.0
                reason = "EXIT pressure warning helped avoid weak follow-through."
            elif return_pct >= 2.5 and current_action in {"BUY CANDIDATE", "SETUP FORMING", "STRONG CONTINUATION"}:
                outcome = "FAILED"
                score = -0.7
                reason = "EXIT pressure was too defensive."
            else:
                outcome = "STALE"
                score = 0.0
                reason = "EXIT pressure remains unresolved."
        else:
            outcome = "PENDING"
            score = 0.0
            reason = "Prior row was not a scored signal type."

    learning_key = "|".join(
        [
            str(prior_action or "UNKNOWN"),
            str(prior.get("setup") or "NONE"),
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
        "prior_operator_state": prior.get("operator_state"),
        "prior_anti_signal_level": prior.get("anti_signal_level"),
        "prior_close": round(float(prior_close), 2) if prior_close else "",
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


def attach_latest_outcomes(rows: list[dict], outcomes: pd.DataFrame) -> None:
    if outcomes.empty:
        return
    outcome_by_ticker = {str(row["ticker"]).upper(): row for row in outcomes.to_dict(orient="records")}
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
            str(row.get("operator_state") or "NEUTRAL"),
            str(row.get("anti_signal_level") or "NONE"),
        ]
    )


def load_local_signal_outcomes(run_date: str) -> pd.DataFrame:
    frames = []
    for path in sorted(Path(".").glob("daily_signal_outcomes_*.csv")):
        stem_date = path.stem.replace("daily_signal_outcomes_", "")
        if stem_date == "latest" or stem_date >= run_date or len(stem_date) != 10:
            continue
        try:
            frames.append(pd.read_csv(path))
        except Exception as exc:
            print(f"Local signal-outcome history load skipped ({path}): {exc}")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def fetch_signal_outcome_history(run_date: str) -> pd.DataFrame:
    try:
        rows = supabase_select(
            "watchlist_signal_outcomes?"
            "select=*&"
            f"evaluation_run_date=lt.{urllib.parse.quote(run_date)}&"
            "outcome_label=neq.PENDING&"
            "order=evaluation_run_date.desc&limit=5000"
        )
        if rows:
            return pd.DataFrame([merge_payload_row(row) for row in rows])
    except RuntimeError as exc:
        print(f"Signal-outcome history fetch skipped: {exc}")
    return load_local_signal_outcomes(run_date)


def build_learning_stats(outcome_history: pd.DataFrame) -> dict[str, dict]:
    if outcome_history.empty or "learning_key" not in outcome_history.columns:
        return {}
    usable = outcome_history[outcome_history["outcome_label"].astype(str).str.upper() != "PENDING"].copy()
    if usable.empty:
        return {}

    stats: dict[str, dict] = {}
    for key, group in usable.groupby("learning_key"):
        labels = group["outcome_label"].astype(str).str.upper()
        scores = pd.to_numeric(group.get("outcome_score"), errors="coerce").dropna()
        returns = pd.to_numeric(group.get("close_return_pct"), errors="coerce").dropna()
        total = int(len(group))
        working = int((labels == "WORKING").sum())
        failed = int((labels == "FAILED").sum())
        trap_avoided = int((labels == "TRAP_AVOIDED").sum())
        stats[str(key)] = {
            "sample_count": total,
            "working_rate": working / total if total else 0.0,
            "failed_rate": failed / total if total else 0.0,
            "trap_avoided_rate": trap_avoided / total if total else 0.0,
            "avg_score": float(scores.mean()) if not scores.empty else 0.0,
            "avg_return_pct": float(returns.mean()) if not returns.empty else None,
        }
    return stats


def apply_learning_adjustments(rows: list[dict], learning_stats: dict[str, dict]) -> None:
    for row in rows:
        key = learning_key_for(row)
        stats = learning_stats.get(key)
        if not stats or int(stats.get("sample_count", 0)) < LEARNING_MIN_SAMPLES:
            row["learning_sample_count"] = int(stats.get("sample_count", 0)) if stats else 0
            row["learning_working_rate"] = round(float(stats.get("working_rate", 0.0)), 3) if stats else ""
            row["learning_failed_rate"] = round(float(stats.get("failed_rate", 0.0)), 3) if stats else ""
            row["learning_trap_avoided_rate"] = round(float(stats.get("trap_avoided_rate", 0.0)), 3) if stats else ""
            row["learning_avg_score"] = round(float(stats.get("avg_score", 0.0)), 3) if stats else ""
            row["learning_adjustment"] = 0.0
            row["learning_plan"] = f"Learning pending: needs at least {LEARNING_MIN_SAMPLES} settled samples for this signal personality."
            continue

        avg_score = float(stats.get("avg_score", 0.0))
        working_rate = float(stats.get("working_rate", 0.0))
        failed_rate = float(stats.get("failed_rate", 0.0))
        trap_rate = float(stats.get("trap_avoided_rate", 0.0))
        adjustment = avg_score * 8.0 + (working_rate - failed_rate) * 4.0 + trap_rate * 2.0
        adjustment = max(-LEARNING_ADJUSTMENT_CAP, min(LEARNING_ADJUSTMENT_CAP, adjustment))

        anti_level = str(row.get("anti_signal_level") or "NONE").upper()
        stale = str(row.get("freshness_block") or "").upper() == "YES"
        if stale:
            effective_adjustment = 0.0
            plan = "Learning observed, but data is stale; no score adjustment applied."
        elif anti_level == "BLOCK":
            effective_adjustment = min(0.0, adjustment)
            plan = "Learning observed, but anti-signal BLOCK prevents positive promotion."
        elif anti_level == "CAUTION":
            effective_adjustment = min(4.0, adjustment)
            plan = "Learning adjustment capped by anti-signal caution."
        else:
            effective_adjustment = adjustment
            plan = "Learning adjustment applied from settled prior outcomes."

        base_adjusted = float(numeric_or_none(row.get("adjusted_score")) or numeric_or_none(row.get("score")) or 0)
        row["adjusted_score"] = round(max(0.0, min(128.0, base_adjusted + effective_adjustment)), 1)
        if "adjusted_score" not in row and effective_adjustment:
            row["score"] = round(max(0.0, min(128.0, float(numeric_or_none(row.get("score")) or 0) + effective_adjustment)), 1)
        row["learning_sample_count"] = int(stats.get("sample_count", 0))
        row["learning_working_rate"] = round(working_rate, 3)
        row["learning_failed_rate"] = round(failed_rate, 3)
        row["learning_trap_avoided_rate"] = round(trap_rate, 3)
        row["learning_avg_score"] = round(avg_score, 3)
        row["learning_adjustment"] = round(float(effective_adjustment), 2)
        row["learning_plan"] = plan


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


def classify_and_score(
    ticker: str,
    raw: pd.DataFrame,
    prepared: bool = False,
    include_setup_stats: bool = True,
    include_audit_gates: bool = True,
    market_permission: Optional[dict] = None,
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
    if include_setup_stats or include_audit_gates:
        d = ensure_setup_names(d)
    setup_stats = (
        historical_setup_stats(d, setup)
        if include_setup_stats
        else {"hist_trades": "", "hist_win_rate": "", "hist_avg_return": ""}
    )
    ticker_profile = (
        ticker_learning_profile(d)
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
        walk_forward_setup_stats(d, setup)
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

    market_risk_adjustment = 0.0
    market_risk_adjustment -= 10.0 if market_permission_value == "BLOCK" else 0.0
    market_risk_adjustment -= 14.0 if risk_permission == "BLOCK" else 0.0
    personality_bias_bonus = 0.0
    personality_bias_bonus += 4.0 if personality_profile["personality_type"] == "HIGH_BETA" and (fast_breakout_entry or momentum) else 0.0
    personality_bias_bonus += 4.0 if personality_profile["personality_type"] == "COMPOUNDER" and steady_trend and not profile_extended_from_zone else 0.0
    personality_bias_bonus += 3.0 if personality_profile["personality_type"] == "RANGE_BOUND" and (fear_rejected or quiet_absorption) else 0.0
    next_day_bias_score = clamp_float(
        emotion_score * 0.36
        + trend_location_score * 0.34
        + setup_context_score * 0.30
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
    distribution_score = clamp_float(distribution_score, 0.0, 100.0)

    absorption_score = 0.0
    absorption_score += 24.0 if fear_rejected else 0.0
    absorption_score += 20.0 if quiet_absorption else 0.0
    absorption_score += 16.0 if accum_vol else 0.0
    absorption_score += 12.0 if buyer_control else 0.0
    absorption_score += 10.0 if lower_wick > body_for_ratio * 1.5 and row.close_loc >= 0.55 else 0.0
    absorption_score += 8.0 if vol_ready and row.volume >= row.vol_ma and low <= row.ema_fast * 1.02 and close >= row.ema_slow else 0.0
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
    bull_trap_score += 28.0 if failed_breakout else 0.0
    bull_trap_score += 24.0 if greed_rejected else 0.0
    bull_trap_score += 18.0 if fomo and row.close_loc < 0.60 else 0.0
    bull_trap_score += 14.0 if upper_wick > body_for_ratio * 1.5 and row.close_loc <= 0.50 else 0.0
    bull_trap_score += 10.0 if vol_ready and row.volume > row.vol_ma * 1.3 and failed_reclaim else 0.0
    bull_trap_score += 8.0 if close < open_ and high > prev.high and close <= prev.close else 0.0
    bull_trap_score = clamp_float(bull_trap_score, 0.0, 100.0)

    support_flush = low < prev.low or low <= row.ema_fast or low <= row.lower_bb
    false_breakdown = support_flush and close >= min(prev.close, row.ema_slow) and row.close_loc >= 0.55 and not confirmed_break
    bear_trap_score = 0.0
    bear_trap_score += 28.0 if false_breakdown else 0.0
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
        operator_plan = "Buyers are absorbing supply; watch pullback or reclaim entries near the reference zone."
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

    if bull_trap_score >= 58.0 and bull_trap_score >= bear_trap_score and distribution_score >= 35.0:
        operator_state = "BULL_TRAP"
        operator_state_score = max(bull_trap_score, distribution_score)
        operator_state_plan = "Breakout strength was rejected; avoid chasing until price reclaims the failed breakout area."
    elif bear_trap_score >= 58.0 and bear_trap_score >= bull_trap_score and not confirmed_break:
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
        operator_state_plan = "Demand is controlling the markup phase; avoid late chase, but favor controlled pullback or Pine-confirmed reclaim entries."
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
        and not operator_blocks_buy
        and not profile_extended_from_zone
        and not extended_from_zone
        and not fomo
        and not greed_rejected
        and not seller_control
    )

    if exit_pressure or (seller_control and trend_damage):
        next_day_bias = "DEFENSIVE / EXIT RISK"
        next_day_plan = "Protect capital first; wait for buyer reclaim before considering new exposure."
    elif profile_extended_from_zone or extended_from_zone or fomo or greed_rejected:
        next_day_bias = "AVOID CHASE"
        next_day_plan = "Do not chase strength; wait for price to reset into the reference zone."
    elif next_day_buyable and setup_forming:
        next_day_bias = "BULLISH CONFIRM"
        next_day_plan = "Confirm on Pine chart; prefer entry near the reference zone with the listed stop."
    elif next_day_constructive and setup_forming:
        next_day_bias = "CONSTRUCTIVE PULLBACK"
        next_day_plan = "Setup is forming; wait for reclaim or a controlled pullback into the reference zone."
    elif mode in {"POWER TREND", "STEADY TREND"} and next_day_bias_score >= 55.0:
        next_day_bias = "WATCH TREND"
        next_day_plan = "Trend personality is healthy; wait for a cleaner setup or reference-zone entry."
    elif market_permission_value == "BLOCK" or risk_permission == "BLOCK":
        next_day_bias = "EXECUTION BLOCKED"
        next_day_plan = "Structure is not enough; market or risk governor blocks fresh execution."
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
        filters_ok = filters_ok and next_day_buyable
        continuation_ok = continuation_ok and not profile_extended_from_zone and execution_safety_ok and next_day_constructive and not operator_blocks_buy
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
    score += 4 if operator_pressure == "ACCUMULATION / ABSORPTION" else 0
    score += 3 if squeeze_watch else 0
    score -= 12 if operator_pressure == "SHORT / DISTRIBUTION PRESSURE" else 8 if operator_pressure == "DISTRIBUTION" else 0
    score -= 4 if operator_pressure == "SHORT PRESSURE" else 0
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
    if setup_forming and market_permission_value == "BLOCK":
        notes.append("Market regime hostile")
    if setup_forming and risk_permission != "ALLOW":
        notes.append("Risk governor blocked")
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
    if buyer_control:
        reason_codes.append("buyer_tape")
    if seller_control:
        reason_codes.append("seller_pressure")
    if exit_pressure:
        reason_codes.append("exit_pressure")
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
        "next_day_bias": next_day_bias,
        "next_day_bias_score": round(float(next_day_bias_score), 1),
        "next_day_plan": next_day_plan,
        "emotion_score": round(float(emotion_score), 1),
        "trend_location_score": round(float(trend_location_score), 1),
        "setup_context_score": round(float(setup_context_score), 1),
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
        "stop_est": round(float(stop), 2) if setup_forming else "",
        "target_est": round(float(target), 2) if setup_forming else "",
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
            snapshot = classify_and_score(
                ticker,
                d.iloc[:end].copy(),
                prepared=True,
                include_setup_stats=False,
                include_audit_gates=False,
            )
        except Exception:
            continue
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

    next_day_bias = row.get("next_day_bias", "")
    if row.get("extension_state") == "EXTENDED":
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
        "buy_tier",
        "last_outcome_label", "last_outcome_return_pct",
        "next_day_bias", "next_day_bias_score", "next_day_plan",
        "operator_state", "operator_state_score", "operator_state_plan",
        "data_provider", "data_provider_status",
        "setup", "adaptive_mode", "psychology", "reward_risk",
        "risk_pct_to_stop", "position_value_1k_risk",
        "market_permission", "risk_permission",
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
        if col in {"score", "next_day_bias_score", "operator_state_score", "reward_risk", "day_change_pct", "risk_pct_to_stop", "last_outcome_return_pct"}:
            try:
                return f"{float(value):.1f}"
            except (TypeError, ValueError):
                return escaped
        if col == "position_value_1k_risk":
            try:
                return f"{float(value):,.0f}"
            except (TypeError, ValueError):
                return escaped
        if col in {"close", "entry_est", "stop_est", "target_est"}:
            try:
                return f"{float(value):.2f}"
            except (TypeError, ValueError):
                return escaped
        return escaped

    numeric_columns = {"score", "next_day_bias_score", "operator_state_score", "reward_risk", "day_change_pct", "risk_pct_to_stop", "position_value_1k_risk", "close", "entry_est", "stop_est", "target_est"}

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
    parser.add_argument("--years", type=int, default=3)
    parser.add_argument("--history-days", type=int, default=30, help="Number of recent trading days to include in behavior history.")
    parser.add_argument("--no-supabase", action="store_true", help="Skip Supabase sync even if credentials are configured.")
    parser.add_argument("--cache-only", action="store_true", help="Use only existing cached price CSV files and skip live Yahoo chart fetches.")
    parser.add_argument(
        "--skip-profiles",
        action="store_true",
        help="Skip Yahoo company profile enrichment so signal and Supabase refreshes cannot stall on non-signal data.",
    )
    args = parser.parse_args()

    tickers = read_watchlist(Path(args.watchlist))
    live_access_ok = True
    live_access_message = "Live market data access available."
    if args.refresh:
        live_access_ok, live_access_message = check_live_data_access()

    rows = []
    history_rows = []
    failures = []
    stale_cache_fallbacks = []
    benchmark_frames: dict[str, pd.DataFrame] = {}
    for benchmark in ("SPY", "QQQ", "SMH"):
        try:
            if args.cache_only or (args.refresh and not live_access_ok):
                benchmark_frames[benchmark] = cached_chart(benchmark, years=args.years)
            else:
                benchmark_frames[benchmark] = fetch_chart(benchmark, years=args.years, refresh=args.refresh)
        except Exception as exc:
            print(f"Benchmark context unavailable for {benchmark}: {exc}")
    market_permission = market_permission_from_frames(benchmark_frames)

    for ticker in tickers:
        try:
            if args.cache_only or (args.refresh and not live_access_ok):
                df = cached_chart(ticker, years=args.years)
                if args.refresh and not live_access_ok:
                    stale_cache_fallbacks.append(
                        {"ticker": display_ticker(ticker), "error": live_access_message}
                    )
            else:
                df = fetch_chart(ticker, years=args.years, refresh=args.refresh)
            row = classify_and_score(ticker, df, market_permission=market_permission)
            row = apply_data_provider_context(row, df)
            ticker_history = build_behavior_history(ticker, df, days=args.history_days)
            ticker_history = apply_data_provider_context_to_rows(ticker_history, df)
            row = apply_latest_signal_context(row, ticker_history)
            row.update(signal_outcome_from_history(row, ticker_history))
            if not args.skip_profiles:
                row.update(fetch_company_profile(ticker, refresh=args.refresh and live_access_ok))
            row = apply_quality_overlays(row, market_context_for(df, benchmark_frames))
            rows.append(row)
            history_rows.extend(ticker_history)
            if args.refresh:
                record_stale_cache_fallback(stale_cache_fallbacks, ticker, df, live_access_message)
        except URLError as exc:
            if not args.refresh or args.cache_only:
                failures.append({"ticker": display_ticker(ticker), "error": str(exc)})
                continue
            try:
                df = cached_chart(ticker, years=args.years)
                row = classify_and_score(ticker, df, market_permission=market_permission)
                row = apply_data_provider_context(row, df)
                ticker_history = build_behavior_history(ticker, df, days=args.history_days)
                ticker_history = apply_data_provider_context_to_rows(ticker_history, df)
                row = apply_latest_signal_context(row, ticker_history)
                row.update(signal_outcome_from_history(row, ticker_history))
                if not args.skip_profiles:
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
    data_dates = sorted(str(value) for value in pd.to_datetime(report["date"]).dt.date.unique())
    latest_data_date = data_dates[-1]
    earliest_data_date = data_dates[0]
    cached_tickers = {str(item.get("ticker", "")).upper() for item in stale_cache_fallbacks}
    rows = [apply_anti_signal_penalty(apply_data_freshness_gate(row, today, cached_tickers)) for row in rows]
    learning_history = fetch_signal_outcome_history(today)
    learning_stats = build_learning_stats(learning_history)
    apply_learning_adjustments(rows, learning_stats)
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
    previous_rows = fetch_previous_snapshot_rows(today) or load_previous_local_report(today)
    outcomes = build_daily_signal_outcomes(previous_rows, rows, today)
    attach_latest_outcomes(rows, outcomes)
    report = pd.DataFrame(rows)
    sort_score_col = "adjusted_score" if "adjusted_score" in report.columns else "score"
    report = report.sort_values(["execution_priority", sort_score_col, "score", "action", "ticker"], ascending=[True, False, False, True, True]).reset_index(drop=True)
    status_parts = [f"Report data as of {latest_data_date}"]
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
            "data_provider_priority": configured_data_providers(),
            "data_provider_counts": provider_counts if "data_provider" in report.columns else {},
            "failures": failures[:25],
            "stale_cache_fallbacks": stale_cache_fallbacks[:25],
            "stale_execution_blocks": stale_blocks,
            "signal_outcomes": outcome_summary,
            "max_execution_data_age_days": MAX_EXECUTION_DATA_AGE_DAYS,
        },
    }

    report.to_csv(csv_path, index=False)
    write_html(report, html_path, status_text=status_text, preflight_text=preflight_text)
    report.to_csv("daily_watchlist_overview_latest.csv", index=False)
    write_html(report, Path("daily_watchlist_overview_latest.html"), status_text=status_text, preflight_text=preflight_text)
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
            sync_supabase(report, history, outcomes, today, run_metadata)
        else:
            print(f"Supabase sync skipped: {sync_reason}")

    columns = [
        "ticker", "action", "setup", "adaptive_mode", "psychology", "score", "close", "day_change_pct",
        "data_provider", "data_provider_status",
        "market_permission", "ticker_permission", "walk_forward_permission", "risk_permission",
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
