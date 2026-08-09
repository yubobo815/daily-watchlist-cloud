#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compose=(docker compose -f "$root/docker-compose.uat.yml")

cleanup() {
  "${compose[@]}" down --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT
cleanup

"${compose[@]}" build audit
"${compose[@]}" run --rm audit
"${compose[@]}" run --rm browser
