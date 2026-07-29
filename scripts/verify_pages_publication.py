#!/usr/bin/env python3
"""Verify a deployed Pages publication against its immutable integrity manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import PurePosixPath


def fetch(base_url: str, relative_path: str, cache_key: str) -> bytes:
    path = PurePosixPath(relative_path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe publication path: {relative_path}")
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.as_posix())
    separator = "&" if "?" in url else "?"
    with urllib.request.urlopen(f"{url}{separator}verify={cache_key}", timeout=30) as response:
        return response.read()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-publication", required=True)
    args = parser.parse_args()

    manifest = json.loads(fetch(args.base_url, "data/manifest.json", args.expected_publication))
    publication_id = str(manifest.get("publication_id") or "")
    run_date = str(manifest.get("run_date") or "")
    schema_version = manifest.get("schema_version")
    ticker_paths = manifest.get("ticker_paths")
    files = manifest.get("files")
    site_files = manifest.get("site_files")
    if publication_id != args.expected_publication or not run_date or not schema_version:
        raise RuntimeError("Deployed manifest identity does not match the expected publication.")
    if not isinstance(ticker_paths, dict) or not ticker_paths or len(ticker_paths) != manifest.get("ticker_count"):
        raise RuntimeError("Deployed manifest ticker count is inconsistent.")
    if len(set(ticker_paths.values())) != len(ticker_paths):
        raise RuntimeError("Deployed manifest maps multiple tickers to the same payload.")
    expected_paths = {str(manifest.get("latest_path") or ""), *map(str, ticker_paths.values())}
    if not isinstance(files, dict) or set(files) != expected_paths or "" in expected_paths:
        raise RuntimeError("Deployed manifest integrity inventory is incomplete.")
    if not isinstance(site_files, dict) or not site_files:
        raise RuntimeError("Deployed site-file integrity inventory is incomplete.")

    for relative_path, integrity in sorted(site_files.items()):
        content = fetch(args.base_url, relative_path, args.expected_publication)
        if len(content) != integrity.get("bytes") or hashlib.sha256(content).hexdigest() != integrity.get("sha256"):
            raise RuntimeError(f"Site integrity check failed for {relative_path}.")

    for relative_path in sorted(expected_paths):
        content = fetch(args.base_url, f"data/{relative_path}", args.expected_publication)
        integrity = files[relative_path]
        if len(content) != integrity.get("bytes") or hashlib.sha256(content).hexdigest() != integrity.get("sha256"):
            raise RuntimeError(f"Integrity check failed for {relative_path}.")
        payload = json.loads(content)
        if payload.get("publication_id") != publication_id or payload.get("run_date") != run_date or payload.get("schema_version") != schema_version:
            raise RuntimeError(f"Identity check failed for {relative_path}.")
        if relative_path == manifest["latest_path"]:
            rows = payload.get("rows")
            tickers = [str(row.get("ticker") or "") for row in rows] if isinstance(rows, list) else []
            if not tickers or len(tickers) != len(set(tickers)) or not set(tickers).issubset(ticker_paths):
                raise RuntimeError("Latest payload has missing, duplicate, or unknown tickers.")
        else:
            expected_ticker = str(integrity.get("ticker") or "")
            if payload.get("ticker") != expected_ticker or ticker_paths.get(expected_ticker) != relative_path:
                raise RuntimeError(f"Ticker mapping check failed for {relative_path}.")
            if not isinstance(payload.get("historyRows"), list) or "snapshot" not in payload:
                raise RuntimeError(f"Ticker payload structure is incomplete for {relative_path}.")
    print(
        f"Verified publication {publication_id}: {len(expected_paths)} payloads and "
        f"{len(site_files)} site files with SHA-256 integrity."
    )


if __name__ == "__main__":
    main()
