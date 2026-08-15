#!/usr/bin/env python3
"""Download one complete, integrity-checked Pages publication for rollback."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import time
import urllib.parse
import urllib.request
import urllib.error
from collections import deque
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath


MAX_FILES = 1000
MAX_BYTES = 50_000_000
FETCH_MAX_ATTEMPTS = 4
RETRYABLE_HTTP_STATUS = {408, 429, 500, 502, 503, 504}


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: set[str] = set()

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.references.add(value)


def safe_path(relative_path: str) -> str:
    parsed = urllib.parse.urlparse(relative_path)
    clean = PurePosixPath(parsed.path.lstrip("/"))
    if parsed.scheme or parsed.netloc or clean.is_absolute() or ".." in clean.parts or not clean.parts:
        raise ValueError(f"Unsafe published path: {relative_path}")
    return clean.as_posix()


def fetch(base_url: str, relative_path: str) -> bytes:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", safe_path(relative_path))
    for attempt in range(1, FETCH_MAX_ATTEMPTS + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "daily-watchlist-rollback/1"})
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRYABLE_HTTP_STATUS or attempt == FETCH_MAX_ATTEMPTS:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == FETCH_MAX_ATTEMPTS:
                raise
        delay = 2 ** (attempt - 1)
        print(f"Temporary Pages fetch failure for {relative_path}; retrying in {delay}s.", flush=True)
        time.sleep(delay)
    raise RuntimeError(f"Pages fetch retries exhausted: {relative_path}")


def integrity(content: bytes, ticker: str = "") -> dict[str, int | str]:
    result: dict[str, int | str] = {
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    if ticker:
        result["ticker"] = ticker
    return result


def write_file(root: Path, relative_path: str, content: bytes) -> None:
    destination = root / PurePosixPath(safe_path(relative_path))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)


def resolve_path(current_path: str, reference: str) -> str | None:
    parsed = urllib.parse.urlparse(reference)
    if parsed.scheme or parsed.netloc or reference.startswith("#"):
        return None
    joined = urllib.parse.urljoin(current_path, parsed.path)
    try:
        return safe_path(joined)
    except ValueError:
        return None


def legacy_site_files(base_url: str) -> dict[str, bytes]:
    """Inventory the pre-integrity-manifest site during the one-time migration."""
    queue = deque([
        ("index.html", True),
        ("ticker.html", True),
        ("history.html", False),
        ("manifest.webmanifest", True),
        ("daily_watchlist_overview_latest.csv", False),
        ("daily_watchlist_overview_failures.csv", False),
        ("daily_watchlist_overview_stale_cache.csv", False),
        ("data/run_metadata.json", False),
    ])
    content_by_path: dict[str, bytes] = {}
    while queue:
        relative_path, required = queue.popleft()
        if relative_path in content_by_path or relative_path == "data/manifest.json":
            continue
        try:
            content = fetch(base_url, relative_path)
        except urllib.error.HTTPError as exc:
            if not required and exc.code == 404:
                continue
            raise
        content_by_path[relative_path] = content
        if len(content_by_path) > MAX_FILES or sum(map(len, content_by_path.values())) > MAX_BYTES:
            raise RuntimeError("Legacy rollback site exceeds the bounded download budget.")
        references: set[str] = set()
        if relative_path.endswith(".html"):
            parser = AssetParser()
            parser.feed(content.decode("utf-8"))
            references = parser.references
        elif relative_path.endswith(".css"):
            references = set(re.findall(r"url\(['\"]?([^)\'\"]+)", content.decode("utf-8")))
        elif relative_path.endswith(".webmanifest"):
            value = json.loads(content)
            references = {str(icon.get("src") or "") for icon in value.get("icons", [])}
        for reference in references:
            discovered = resolve_path(relative_path, reference)
            if discovered and not discovered.startswith("data/runs/"):
                queue.append((discovered, False))
    return content_by_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest_bytes = fetch(args.base_url, "data/manifest.json")
    manifest = json.loads(manifest_bytes)
    publication_id = str(manifest.get("publication_id") or "").strip()
    latest_path = str(manifest.get("latest_path") or "").strip()
    ticker_paths = manifest.get("ticker_paths")
    site_files = manifest.get("site_files")
    if (
        not publication_id
        or not latest_path
        or not isinstance(ticker_paths, dict)
        or not ticker_paths
    ):
        raise RuntimeError("Current Pages manifest is incomplete; rollback artifact cannot be built.")

    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    if isinstance(site_files, dict) and site_files:
        site_content = {}
        for relative_path, expected_integrity in sorted(site_files.items()):
            content = fetch(args.base_url, relative_path)
            if integrity(content) != expected_integrity:
                raise RuntimeError(f"Published site file failed integrity validation: {relative_path}")
            site_content[relative_path] = content
    else:
        site_content = legacy_site_files(args.base_url)
        site_files = {path: integrity(content) for path, content in site_content.items()}
        manifest["site_files"] = site_files

    total_bytes = 0
    restored_files = 0
    for relative_path, content in sorted(site_content.items()):
        write_file(args.output, relative_path, content)
        restored_files += 1
        total_bytes += len(content)
        if restored_files > MAX_FILES or total_bytes > MAX_BYTES:
            raise RuntimeError("Rollback site exceeds the bounded download budget.")

    file_inventory: dict[str, dict[str, int | str]] = {}
    data_paths = {latest_path: "", **{str(path): ticker for ticker, path in ticker_paths.items()}}
    for relative_path, ticker in sorted(data_paths.items()):
        payload_bytes = fetch(args.base_url, f"data/{relative_path}")
        payload = json.loads(payload_bytes)
        if str(payload.get("publication_id") or "") != publication_id:
            raise RuntimeError(f"Rollback payload {relative_path} does not match its manifest.")
        calculated_integrity = integrity(payload_bytes, ticker)
        expected_integrity = manifest.get("files", {}).get(relative_path)
        if expected_integrity is not None and calculated_integrity != expected_integrity:
            raise RuntimeError(f"Rollback payload {relative_path} failed integrity validation.")
        write_file(args.output, f"data/{relative_path}", payload_bytes)
        file_inventory[relative_path] = calculated_integrity

    manifest["files"] = file_inventory
    write_file(
        args.output,
        "data/manifest.json",
        (json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(),
    )
    write_file(args.output, "rollback_publication_id.txt", (publication_id + "\n").encode())
    print(f"Rollback artifact preserves complete publication {publication_id} ({restored_files} site files).")


if __name__ == "__main__":
    main()
