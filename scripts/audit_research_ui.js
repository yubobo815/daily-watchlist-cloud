const assert = require("node:assert/strict");
const fs = require("node:fs");
const ui = require("../assets/research-ui.js");
const row = (close, low = 100, high = 110) => ({ ticker: "TEST", close, entry_zone_low: low, entry_zone_high: high });
assert.equal(ui.distance(row(95)), -5);
assert.equal(ui.distance(row(115)), 5 / 110 * 100);
for (const price of [100, 105, 110]) assert.equal(ui.distance(row(price)), 0);
assert.equal(ui.formatDistance(row(100.00001)), "Inside");
assert.equal(ui.formatDistance(row(100)), "Inside");
assert.equal(ui.formatDistance(row(110)), "Inside");
assert.equal(ui.formatDistance(row(99.99999)), "−<0.01%");
assert.equal(ui.formatDistance(row(110.00001)), "+<0.01%");
assert.equal(ui.formatDistance(row(95)), "−5.00%");
assert.equal(ui.formatDistance(row(115)), "+4.55%");
for (const invalid of [row(null), row(""), row(0), row(-5), row(Infinity), row(100, 110, 90), row(100, 0, 110)]) assert.equal(ui.distance(invalid), null);
assert.equal(ui.distance({ ticker: "TEST", close: 100 }), null);
assert.equal(ui.distance({ ticker: "TEST", close: 110, entry_est: 100 }), 10);
assert.equal(ui.distance({ ticker: "TEST", payload: { close: 105, entry_zone_low: 100, entry_zone_high: 110 } }), 0);
const frozen = { ...row(105, 200, 220), execution_plan_status: "ARMED", execution_plan_zone_low: 100, execution_plan_zone_high: 110 };
assert.equal(ui.distance(frozen), 0, "Frozen zone takes precedence over current reference");
assert.equal(ui.distance({ ...frozen, execution_plan_zone_low: null }), null, "Incomplete frozen plan must not fall back to another zone");
const ordered = [{ ...row(95), ticker: "FAR" }, { ...row(102), ticker: "B" }, { ...row(102), ticker: "A" }, { ticker: "NONE" }, { ...row(99), ticker: "NEAR" }].sort(ui.compareDistance);
assert.deepEqual(ordered.map(r => r.ticker), ["A", "B", "NEAR", "FAR", "NONE"]);
for (const close of [1, 95, 100, 105, 110, 120, 5000]) {
  const position = ui.pricePosition(row(close));
  assert.ok(position.closePosition > 0 && position.closePosition < 100);
  assert.ok(position.lowPosition > 0 && position.highPosition < 100);
  assert.ok(position.lowPosition <= position.highPosition);
}
assert.equal(ui.pricePosition(row(95)).relation, "Below planned zone");
assert.equal(ui.pricePosition(row(105)).relation, "Inside planned zone");
assert.equal(ui.pricePosition(row(120)).relation, "Above planned zone");
assert.equal(ui.pricePosition(row(null)), null);
const history = [
  { date: "2026-10-23", action: "SETUP FORMING" },
  { date: "2026-10-19", action: "WATCH TREND" },
  { date: "2026-10-16", action: "WAIT / AVOID" },
  { date: "2026-10-22", action: "SETUP FORMING" },
];
const original = JSON.stringify(history);
const changes = ui.transitions(history);
assert.equal(JSON.stringify(history), original, "Do not mutate history");
assert.equal(changes.changes.length, 2);
assert.deepEqual(changes.changes[0], { date: "2026-10-22", from: "WATCH TREND", to: "SETUP FORMING" });
assert.equal(ui.transitions([{ date: "2026-10-23", action: "WAIT" }]).changes.length, 0);
const coverage = ui.coverage({ symbols_failed: 1, latest_data_date: "2026-10-23", payload: { failed_symbols: [{ ticker: "MISS", error: "No stored data" }], stale_execution_blocks: 2 } }, [{ ticker: "OLD", data_date: "2026-10-20", freshness_block: "YES" }]);
assert.equal(coverage.missing[0].ticker, "MISS");
assert.equal(coverage.stale[0].ticker, "OLD");
assert.equal(coverage.staleCount, 2);
const packageVersion = JSON.parse(fs.readFileSync("package.json", "utf8")).version;
assert.equal(packageVersion, "5.1.1");
for (const file of ["index.html", "ticker.html"]) {
  const source = fs.readFileSync(file, "utf8");
  assert.ok(source.includes('data-ui-version="5.1.1"'));
  assert.ok(source.includes("research-ui.js?v=v5.1.1"));
  assert.ok(source.includes("research-workspace.css?v=v5.1.1"));
  assert.ok(!source.includes('class="app-version"'), "Version belongs in release metadata, not the visible brand");
}
assert.ok(!fs.readFileSync("index.html", "utf8").includes("Scanner rank first"));
console.log("Research UI v5: distance, frozen bounds, sorting, rulers, recorded transitions, coverage and version checks passed.");
