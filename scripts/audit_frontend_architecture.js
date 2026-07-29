#!/usr/bin/env node

const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const { pressureComparison } = require("../assets/history_summary");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function filesBelow(root) {
  return fs.readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(root, entry.name);
    return entry.isDirectory() ? filesBelow(target) : [target];
  });
}

function treeDigest(root) {
  const hash = crypto.createHash("sha256");
  filesBelow(root).sort().forEach((file) => {
    hash.update(path.relative(root, file));
    hash.update(fs.readFileSync(file));
  });
  return hash.digest("hex");
}

function main() {
  const app = fs.readFileSync("assets/app.js", "utf8");
  const publishedApi = fs.readFileSync("api/_published_data.js", "utf8");
  const tickerApi = fs.readFileSync("api/ticker/[ticker].js", "utf8");
  const workflow = fs.readFileSync(".github/workflows/daily-watchlist-pages.yml", "utf8");

  assert(app.includes("isGithubPagesHost()\n      ? await loadStaticLatestRows()"), "GitHub Pages must bypass the unavailable API route");
  assert(app.includes("isGithubPagesHost()\n      ? await loadStaticTickerHistory(state.ticker)"), "GitHub Pages ticker view must bypass the unavailable API route");
  assert(!app.includes("history.json") && !app.includes("watchlist_behavior_history_latest.csv"), "browser code must not reference global history payloads");
  assert(!publishedApi.includes("history.json"), "published API fallback must not reference global history payloads");
  assert(!publishedApi.includes("Date.now()") && publishedApi.includes('cache: mutable ? "no-cache" : "force-cache"'), "publication-scoped API data must use deterministic caching");
  assert(tickerApi.indexOf("recentRunDates(1)") < tickerApi.indexOf("getPublishedFallback(profile)"), "ticker API must not fetch published fallback before Supabase");
  assert(app.includes("const INITIAL_WATCHLIST_ROWS = 40"), "initial watchlist DOM budget must be 40 rows");
  assert(app.includes("renderWatchlist({ refreshOverview: false })"), "search and list interactions must support partial rendering");
  assert(app.includes("if (!state.focusPin || isGithubPagesHost()) return false;"), "GitHub Pages Focus List must not request an unavailable API");
  assert(app.includes("manifest.ticker_paths?.[safeTicker]") && app.includes("payload.ticker") && app.includes('path.includes("..")'), "browser ticker loading must validate the manifest path and ticker identity");
  assert(workflow.includes("scripts/build_pages_data.py") && !workflow.includes("cp watchlist_behavior_history_latest.csv public/"), "Pages must publish versioned data rather than a global history CSV");

  execFileSync("python3", ["-m", "py_compile", "scripts/build_pages_data.py"], { stdio: "pipe" });
  const fixtureInputs = [
    "daily_watchlist_overview_latest.csv",
    "watchlist_behavior_history_latest.csv",
    "daily_watchlist_run_metadata_latest.json",
  ];
  if (!fixtureInputs.every((file) => fs.existsSync(file))) {
    console.log(JSON.stringify({
      fixture: "skipped",
      reason: "Scanner output is generated later in the production workflow.",
      initialRows: 40,
      staticArchitecture: "pass",
    }, null, 2));
    return;
  }

  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "watchlist-pages-audit-"));
  const metadata = JSON.parse(fs.readFileSync("daily_watchlist_run_metadata_latest.json", "utf8"));
  metadata.publication_id = metadata.publication_id || "qa-publication";
  metadata.run_date = metadata.run_date || "2026-01-01";
  const metadataPath = path.join(temp, "metadata.json");
  fs.writeFileSync(metadataPath, `${JSON.stringify(metadata)}\n`);
  const first = path.join(temp, "first");
  const second = path.join(temp, "second");
  const build = (output, history = "watchlist_behavior_history_latest.csv") => execFileSync("python3", [
    "scripts/build_pages_data.py",
    "--latest", "daily_watchlist_overview_latest.csv",
    "--history", history,
    "--metadata", metadataPath,
    "--output", output,
  ], { stdio: "pipe" });
  build(first);
  build(second);
  assert(treeDigest(first) === treeDigest(second), "static publication build must be deterministic");

  const sourceHistory = fs.readFileSync("watchlist_behavior_history_latest.csv", "utf8").trimEnd().split(/\r?\n/);
  const overflowHistory = path.join(temp, "history-overflow.csv");
  fs.writeFileSync(overflowHistory, `${sourceHistory.join("\n")}\n${sourceHistory[1]}\n`);
  build(path.join(temp, "overflow"), overflowHistory);
  const overflowManifest = JSON.parse(fs.readFileSync(path.join(temp, "overflow", "manifest.json"), "utf8"));
  filesBelow(path.join(temp, "overflow", overflowManifest.ticker_base_path)).forEach((file) => {
    const payload = JSON.parse(fs.readFileSync(file, "utf8"));
    assert((payload.historyRows || []).length <= 30, `${path.basename(file)} is not capped after a 31-row input`);
  });

  const manifest = JSON.parse(fs.readFileSync(path.join(first, "manifest.json"), "utf8"));
  const latestPath = path.join(first, manifest.latest_path);
  const latest = JSON.parse(fs.readFileSync(latestPath, "utf8"));
  const latestBytes = fs.statSync(latestPath).size;
  assert(latest.publication_id === manifest.publication_id && latest.run_date === manifest.run_date, "latest payload must match manifest publication");
  const manifestPaths = new Set([manifest.latest_path, ...Object.values(manifest.ticker_paths)]);
  assert(manifest.files && Object.keys(manifest.files).length === manifestPaths.size, "manifest must inventory every immutable payload");
  manifestPaths.forEach((relativePath) => {
    const content = fs.readFileSync(path.join(first, relativePath));
    const integrity = manifest.files[relativePath];
    assert(integrity?.bytes === content.length, `${relativePath} byte size is not covered by the manifest`);
    assert(integrity?.sha256 === crypto.createHash("sha256").update(content).digest("hex"), `${relativePath} hash is not covered by the manifest`);
  });
  assert(latest.rows.every((row) => row.execution_priority !== undefined && row.execution_priority !== ""), "static watchlist must retain scanner execution priority");
  assert(latestBytes <= 600 * 1024, "latest payload exceeds the 600 KB raw budget");

  const tickerFiles = filesBelow(path.join(first, manifest.ticker_base_path)).filter((file) => file.endsWith(".json"));
  assert(tickerFiles.length === manifest.ticker_count, "manifest ticker count must match per-ticker files");
  let maximumTickerBytes = 0;
  tickerFiles.forEach((file) => {
    const payload = JSON.parse(fs.readFileSync(file, "utf8"));
    const bytes = fs.statSync(file).size;
    maximumTickerBytes = Math.max(maximumTickerBytes, bytes);
    assert(bytes <= 128 * 1024, `${path.basename(file)} exceeds the 128 KB raw budget`);
    assert(payload.publication_id === manifest.publication_id && payload.run_date === manifest.run_date, `${path.basename(file)} does not match manifest publication`);
    assert((payload.historyRows || []).every((row) => row.ticker === payload.ticker), `${path.basename(file)} contains another ticker's history`);
    assert((payload.historyRows || []).length <= 30, `${path.basename(file)} exceeds the 30-session frontend history budget`);
    assert((payload.historyRows || []).every((row) => !Object.prototype.hasOwnProperty.call(row, "payload")), `${path.basename(file)} duplicates row payload data`);
    if ((payload.historyRows || []).length === 30) {
      assert((payload.historyRows || []).every((row) => row.buyer_score !== undefined && row.seller_score !== undefined), `${path.basename(file)} omits pressure scores required by the 30-session summary`);
      assert(pressureComparison(payload.historyRows).available, `${path.basename(file)} cannot calculate the published pressure summary`);
    }
  });

  fs.rmSync(temp, { recursive: true, force: true });
  console.log(JSON.stringify({
    publication: manifest.publication_id,
    tickers: tickerFiles.length,
    latestBytes,
    maximumTickerBytes,
    initialRows: 40,
    deterministic: true,
  }, null, 2));
}

main();
