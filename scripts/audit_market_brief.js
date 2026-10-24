const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const brief = require("../assets/market-brief.js");
const data = JSON.parse(fs.readFileSync(process.argv[2] || path.join(__dirname, "../data/market-brief.json"), "utf8"));
brief.validate(data);
assert.equal(brief.renderChange("+3.14% · settlement"), '<span class="brief-change-up">+3.14%</span> · settlement');
assert.equal(brief.renderChange("−0.52% · US close"), '<span class="brief-change-down">−0.52%</span> · US close');
assert.equal(brief.renderChange("-0.21% · US close"), '<span class="brief-change-down">-0.21%</span> · US close');
assert.equal(brief.renderChange("+4 bp · Treasury par yield"), '<span class="brief-change-up">+4 bp</span> · Treasury par yield');
for (const neutral of ["0.00% · unchanged", "+0.00%", "−0.00%", "Not available", "26–28 October"]) {
  assert.equal(brief.renderChange(neutral), neutral);
}
assert.ok(!brief.renderChange('+1% <img src=x onerror="alert(1)">').includes("<img"));
const fixture = structuredClone(data);
fixture.session_date = "2026-10-23";
fixture.issued_at = "2026-10-23T23:12:41.730Z";
fixture.forecast.evaluates_at = "2026-10-28T20:00:00Z";
assert.equal(brief.status(fixture, new Date("2026-10-24T01:00:00Z")).dated, false, "Weekend remains current");
assert.equal(brief.status(fixture, new Date("2026-10-26T20:01:00Z")).dated, true);
assert.equal(brief.status(fixture, new Date("2026-10-28T20:00:00Z")).expired, true);
assert.equal(brief.status(fixture, new Date("2026-10-23T22:00:00Z")).dated, true, "Future publication is not current");
function rejects(change) { const copy = structuredClone(fixture); change(copy); assert.throws(() => brief.validate(copy)); }
rejects((d) => { d.forecast.probabilities.bull = 99; });
rejects((d) => { d.forecast.probabilities.bear = -1; });
rejects((d) => { d.sources[0].url = "javascript:alert(1)"; });
rejects((d) => { d.sources[0].url = "https://user:password@example.com"; });
rejects((d) => { d.forecast.lower_bound = d.forecast.upper_bound; });
rejects((d) => { d.forecast.evaluates_at = "2020-01-01T00:00:00Z"; });
rejects((d) => { d.session_date = "2026-02-30"; });
rejects((d) => { d.highlights = []; });
rejects((d) => { d.forecast.completed_sample = -1; });
const unsafe = structuredClone(fixture);
unsafe.headline = '<img src=x onerror="alert(1)">';
assert.ok(!brief.render(unsafe).includes("<img"));
assert.ok(brief.render(fixture, new Date("2026-10-29T01:00:00Z")).includes("ARCHIVED OUTLOOK"));
assert.ok(brief.render(fixture).includes('rel="noopener noreferrer"'));
console.log("Market brief: schema, probability boundaries, freshness, expiry and escaping passed.");
