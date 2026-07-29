#!/usr/bin/env python3
"""Download one complete, integrity-checked Pages publication for rollback."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath


MAX_FILES = 1000
MAX_BYTES = 50_000_000


def safe_path(relative_path: str) -> str:
    parsed = urllib.parse.urlparse(relative_path)
    clean = PurePosixPath(parsed.path.lstrip("/"))
    if parsed.scheme or parsed.netloc or clean.is_absolute() or ".." in clean.parts or not clean.parts:
        raise ValueError(f"Unsafe published path: {relative_path}")
    return clean.as_posix()


def fetch(base_url: str, relative_path: str) -> bytes:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", safe_path(relative_path))
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


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
        or not isinstance(site_files, dict)
        or not site_files
    ):
        raise RuntimeError("Current Pages manifest is incomplete; rollback artifact cannot be built.")

    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    total_bytes = 0
    restored_files = 0
    for relative_path, expected_integrity in sorted(site_files.items()):
        content = fetch(args.base_url, relative_path)
        if integrity(content) != expected_integrity:
            raise RuntimeError(f"Published site file failed integrity validation: {relative_path}")
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
        expected_integrity = manifest.get("files", {}).get(relative_path)
        if integrity(payload_bytes, ticker) != expected_integrity:
            raise RuntimeError(f"Rollback payload {relative_path} failed integrity validation.")
        write_file(args.output, f"data/{relative_path}", payload_bytes)
        file_inventory[relative_path] = expected_integrity

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
