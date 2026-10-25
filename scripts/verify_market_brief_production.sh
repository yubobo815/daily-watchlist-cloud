#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
candidate="$(realpath "${1:?Expected candidate JSON path}")"
docker run --rm \
  -v "$root:/work:ro" \
  -v "$candidate:/expected.json:ro" \
  mcr.microsoft.com/playwright:v1.58.2-noble \
  sh -lc 'cd /tmp && npm init -y >/dev/null && npm install --silent @playwright/test@1.58.2 && NODE_PATH=/tmp/node_modules node /work/scripts/verify_market_brief_production.cjs /expected.json'
