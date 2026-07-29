#!/usr/bin/env python3
"""Download the complete current Pages site into a deployable rollback artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import urllib.parse
import urllib.request
import urllib.error
from collections import deque
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath


MAX_FILES = 1000
MAX_BYTES = 50_000_000


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: set[str] = set()

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.references.add(value)


def safe_path(current_path: str, reference: str) -> str | None:
    parsed = urllib.parse.urlparse(reference)
    if parsed.scheme or parsed.netloc or reference.startswith("#"):
        return None
    joined = urllib.parse.urljoin(current_path, parsed.path)
    clean = PurePosixPath(joined.lstrip("/"))
    if clean.is_absolute() or ".." in clean.parts or not clean.parts:
        return None
    return clean.as_posix()


def fetch(base_url: str, relative_path: str) -> bytes:
    clean = safe_path("index.html", relative_path)
    if not clean:
        raise ValueError(f"Unsafe published path: {relative_path}")
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", clean)
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def integrity(content: bytes, ticker: str = "") -> dict[str, int | str]:
    result: dict[str, int | str] = {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
    if ticker:
        result["ticker"] = ticker
    return result


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
    if not publication_id or not latest_path or not isinstance(ticker_paths, dict) or not ticker_paths:
        raise RuntimeError("Current Pages manifest is incomplete; rollback artifact cannot be built.")

    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    queue = deque([
        ("index.html", True),
        ("ticker.html", True),
        ("history.html", False),
        ("manifest.webmanifest", True),
    ])
    visited: set[str] = set()
    total_bytes = 0
    while queue:
        relative_path, required = queue.popleft()
        if relative_path in visited:
            continue
        try:
            content = fetch(args.base_url, relative_path)
        except urllib.error.HTTPError as exc:
            if not required and exc.code == 404:
                continue
            raise
        visited.add(relative_path)
        total_bytes += len(content)
        if len(visited) > MAX_FILES or total_bytes > MAX_BYTES:
            raise RuntimeError("Rollback site exceeds the bounded download budget.")
        destination = args.output / PurePosixPath(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

        references: set[str] = set()
        if relative_path.endswith(".html"):
            asset_parser = AssetParser()
            asset_parser.feed(content.decode("utf-8"))
            references = asset_parser.references
        elif relative_path.endswith(".css"):
            references = set(re.findall(r"url\(['\"]?([^)'\"]+)", content.decode("utf-8")))
        elif relative_path.endswith(".webmanifest"):
            parsed_manifest = json.loads(content)
            references = {str(icon.get("src") or "") for icon in parsed_manifest.get("icons", [])}
        for reference in references:
            discovered = safe_path(relative_path, reference)
            if discovered and (discovered.startswith("assets/") or discovered in {"index.html", "ticker.html", "history.html", "manifest.webmanifest"}):
                queue.append((discovered, True))

    file_inventory: dict[str, dict[str, int | str]] = {}
    data_paths = {latest_path: "", **{str(path): ticker for ticker, path in ticker_paths.items()}}
    for relative_path, ticker in sorted(data_paths.items()):
        payload_bytes = fetch(args.base_url, f"data/{relative_path}")
        payload = json.loads(payload_bytes)
        if str(payload.get("publication_id") or "") != publication_id:
            raise RuntimeError(f"Rollback payload {relative_path} does not match its manifest.")
        destination = args.output / "data" / PurePosixPath(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload_bytes)
        file_inventory[relative_path] = integrity(payload_bytes, ticker)

    manifest["files"] = file_inventory
    (args.output / "data" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (args.output / "rollback_publication_id.txt").write_text(publication_id + "\n", encoding="utf-8")
    print(f"Rollback artifact preserves complete publication {publication_id} ({len(visited)} site files).")


if __name__ == "__main__":
    main()
