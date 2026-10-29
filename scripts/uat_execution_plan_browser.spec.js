const { test, expect } = require("@playwright/test");

const baseUrl = process.env.BASE_URL || "http://web:4178";
const marketBrief = require(process.env.MARKET_BRIEF_FILE || "../data/market-brief.json");

async function useResearchDataset(page, { optionalPlan = false, missingZone = false, matchLatestAction = false, readinessCases = false } = {}) {
  const rows = Array.from({ length: 61 }, (_, index) => ({
    ticker: `V${String(index).padStart(3, "0")}`, name: `Research Stock ${index}`,
    publication_id: "v5-browser-uat", run_date: "2026-10-23", data_date: index === 1 ? "2026-10-20" : "2026-10-23",
    action: index === 60 ? "WAIT / AVOID" : "SETUP FORMING", setup: "PULLBACK BUY",
    close: 100 - index * 0.05, entry_zone_low: 100, entry_zone_high: 105,
    market_permission: "BLOCK", risk_permission: "ALLOW", ticker_permission: "ALLOW", walk_forward_permission: "ALLOW",
    freshness_block: index === 1 ? "YES" : "NO", freshness_plan: "Published fixture market data",
    score: 60, adjusted_score: 49, day_change_pct: 0.2,
    shadow_action: "SETUP FORMING", shadow_readiness_score: 57.1,
    shadow_decision_explanation: "The broader market is not supportive.",
  }));
  if (optionalPlan) Object.assign(rows[0], { execution_plan_status: "ARMED", execution_plan_zone_low: 100, execution_plan_zone_high: 105, execution_plan_stop: 95, execution_plan_risk_pct: 7, execution_plan_id: "fixture-only-plan" });
  if (missingZone) { delete rows[0].entry_zone_low; delete rows[0].entry_zone_high; }
  if (readinessCases) {
    Object.assign(rows[0], { shadow_readiness_score: 78.4, market_permission: "ALLOW", shadow_readiness_trend: 85, shadow_readiness_entry: 72 });
    Object.assign(rows[1], { shadow_readiness_score: 92.2 });
    delete rows[2].shadow_readiness_score;
    Object.assign(rows[3], { shadow_readiness_score: 0 });
  }
  const runInfo = { publication_id: "v5-browser-uat", run_date: "2026-10-23", latest_data_date: "2026-10-23", symbols_total: 63, symbols_analyzed: 61, symbols_failed: 2, status: "degraded", live_access_ok: true,
    payload: { failed_symbols: [{ ticker: "MISS1", error: "No stored OHLCV" }, { ticker: "MISS2", error: "Not enough history" }], stale_execution_blocks: 1 } };
  await page.route("**/api/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/watchlist/latest") return route.fulfill({ json: { latest: "2026-10-23", rows, previousRows: [], runInfo } });
    if (path.startsWith("/api/ticker/")) {
      const ticker = decodeURIComponent(path.split("/").at(-1));
      const source = rows.find(row => row.ticker === ticker) || rows[0];
      const actions = ["WAIT / AVOID", "WATCH TREND", "SETUP FORMING", "WAIT / AVOID", "WATCH TREND", "SETUP FORMING", "SETUP FORMING"];
      if (matchLatestAction) actions[actions.length - 1] = source.action;
      const historyRows = actions.map((action, i) => ({ ...source, action, history_date: `2026-10-${17 + i}`, data_date: `2026-10-${17 + i}` })).reverse();
      return route.fulfill({ json: { ticker, latest: "2026-10-23", snapshot: source, historyRows, runInfo } });
    }
    if (path === "/api/focus-list") return route.fulfill({ json: { tickers: [] } });
    return route.fulfill({ status: 404, body: "Fixture route unavailable" });
  });
  return rows;
}

test("readiness uses one source, keeps blockers and never invents missing scores", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2026-10-24T01:00:00Z"));
  await useResearchDataset(page, { readinessCases: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(baseUrl);
  const first = page.locator('#watchlist-body tr[data-select-ticker="V000"] .col-readiness');
  await expect(first).toContainText("78");
  await expect(first.locator(".readiness-value")).toHaveText("78");
  await expect(first.locator("meter")).toHaveAttribute("value", "78.4");
  await expect(first.locator(".readiness-compact")).toHaveAttribute("data-readiness-tone", "high");
  await expect(first.locator(".readiness-compact")).toHaveCSS("--readiness-fill", "#4f775b");
  const stale = page.locator('#watchlist-body tr[data-select-ticker="V001"] .col-readiness');
  await expect(stale.locator(".readiness-status, .readiness-date")).toHaveCount(0);
  await expect(stale.locator(".readiness-compact")).toHaveAttribute("title", /As of 2026-10-20/);
  await expect(stale.locator(".readiness-compact")).toHaveClass(/is-dated/);
  await expect(stale.locator(".readiness-compact")).toHaveCSS("--readiness-fill", "#a7a49b");
  await expect(page.locator('#watchlist-body tr[data-select-ticker="V002"] .col-readiness')).toContainText("Not scored");
  await expect(page.locator('#watchlist-body tr[data-select-ticker="V002"] .col-readiness meter')).toHaveCount(0);
  await expect(page.locator('#watchlist-body tr[data-select-ticker="V003"] .col-readiness meter')).toHaveAttribute("value", "0");
  await expect(page.locator('#watchlist-body tr[data-select-ticker="V003"] .col-readiness .readiness-compact')).toHaveCSS("--readiness-fill", "#a45d50");
  await expect(page.locator('#watchlist-body tr[data-select-ticker="V004"] .col-readiness .readiness-compact')).toHaveCSS("--readiness-fill", "#a27b35");
  await page.locator("#ticker-detail-panel .readiness-factors summary").click();
  await expect(page.locator("#ticker-detail-panel .readiness-factors dd").first()).toHaveText("85");
  await expect(page.locator("#ticker-detail-panel .readiness-factors")).toContainText("Unavailable");
  await expect(page.locator("#ticker-detail-panel")).toContainText("not a win probability");
  await page.selectOption("#sort", "score-desc");
  await expect(page.locator("#watchlist-body tr").first().locator(".ticker-link")).toHaveText("V001");
  await page.goto(baseUrl + "/ticker.html?ticker=V000");
  await expect(page.locator(".readiness-meter > strong")).toContainText("78");
  await expect(page.locator(".readiness-meter > strong")).toHaveText("78");
  await expect(page.locator(".readiness-meter meter")).toHaveAttribute("value", "78.4");
  await expect(page.locator(".readiness-meter")).toHaveCSS("--readiness-fill", "#4f775b");
  await expect(page.locator(".readiness-meter p, .readiness-meter .readiness-status, .readiness-meter details")).toHaveCount(0);
});

test("notification center is visible on desktop/mobile and preserves read state", async ({ page }) => {
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.clock.setFixedTime(new Date("2026-10-24T01:00:00Z"));
  const rows = await useResearchDataset(page);
  Object.assign(rows[0], { profit_stage: "TP1 REACHED", take_profit_1: 110, take_profit_1_reduce_pct: 33 });
  Object.assign(rows[1], { data_date: "2026-10-23", profit_stage: "PROTECT REMAINDER", active_protective_stop: 99 });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(baseUrl);
  await expect(page).toHaveTitle("Daily Trade Copilot");
  const center = page.locator(".notification-center");
  await expect(center).toBeVisible();
  await expect(center.locator("summary")).toContainText("2 unread");
  await center.locator("summary").click();
  await expect(center.locator(".notification-item")).toHaveCount(2);
  await expect(center).toContainText("V000 · Take Profit 1 reached");
  await expect(center).toContainText("V001 · Protect remaining profit");
  await page.screenshot({ path: `${process.env.SCREENSHOT_DIR || "/tmp"}/notification-center-desktop.png` });
  await page.getByRole("button", { name: "Mark all read", exact: true }).click();
  await expect(center).toHaveAttribute("open", "");
  await expect(center.locator("summary")).toContainText("All read");
  await expect(center.locator(".notification-item.unread")).toHaveCount(0);
  await page.reload();
  await expect(center.locator("summary")).toContainText("All read");
  await page.setViewportSize({ width: 390, height: 844 });
  await center.locator("summary").click();
  await expect(center.locator(".notification-item")).toHaveCount(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.screenshot({ path: `${process.env.SCREENSHOT_DIR || "/tmp"}/notification-center-mobile.png` });
  await center.locator('[data-notification-id="2026-10-23:V000:take-profit-1"]').click();
  await expect(page).toHaveURL(/ticker\.html\?ticker=V000/);
  expect(errors).toEqual([]);
});

test("notification center shows an honest empty state without browser permissions", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2026-10-24T01:00:00Z"));
  await useResearchDataset(page);
  await page.goto(baseUrl);
  await page.locator(".notification-center summary").click();
  await expect(page.locator(".notification-empty")).toContainText("TP1 and profit-protection events");
  await expect(page.locator(".notification-item")).toHaveCount(0);
});

test("WAIT remains distinct from AVOID on the watchlist and stock page", async ({ page }) => {
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  const rows = await useResearchDataset(page, { matchLatestAction: true });
  Object.assign(rows[0], { action: "WAIT", shadow_action: "WAIT" });
  await page.goto(baseUrl);
  await expect(page.locator('#watchlist-body tr[data-select-ticker="V000"] .badge')).toHaveText(["WAIT", "WAIT"]);
  await page.getByRole("button", { name: "V000", exact: true }).click();
  await expect(page.locator("#ticker-detail-panel h2")).toHaveText("V000");
  await page.locator("#ticker-detail-panel .full-detail-link").click();
  await expect(page.locator("#latest-panel .latest-head > .badge")).toHaveText("WAIT");
  await expect(page.locator("#history-visual")).toContainText("current view remains Wait.");
  await page.goto(`${baseUrl}/ticker.html?ticker=V060`);
  await expect(page.locator("#latest-panel .latest-head > .badge")).toHaveText("AVOID");
  await expect(page.locator("#history-visual")).toContainText("current view remains Avoid.");
  expect(errors).toEqual([]);
});

test("v5 research workspace: coverage, distance order, selected reasons, filters and pagination", async ({ page }) => {
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.setViewportSize({ width: 1440, height: 1100 });
  await useResearchDataset(page);
  await page.goto(baseUrl);
  await expect(page.locator("#sort")).toHaveValue("distance-asc");
  await expect(page.locator(".rail-home")).toHaveText("Daily Trade Copilot");
  await expect(page.locator("body")).not.toContainText("v5.1.1");
  await expect(page.locator("#watchlist-body tr")).toHaveCount(40);
  await expect(page.locator("#watchlist-body tr").first().locator(".ticker-link")).toHaveText("V000");
  await expect(page.locator("#watchlist-head")).not.toContainText("Protection");
  await expect(page.locator("#watchlist-head")).not.toContainText("Loss if stopped");
  await expect(page.locator("#watchlist-head")).not.toContainText("What it means");
  await expect(page.locator("#watchlist-head th")).toHaveCount(5);
  await expect(page.locator("#watchlist-body tr").first().locator(".col-distance")).toHaveText("Inside");
  await expect(page.locator("#watchlist-body tr").first().locator(".col-distance")).toHaveCSS("text-align", "right");
  const topAlignment = await page.evaluate(() => ({ brief: document.querySelector('#market-brief').getBoundingClientRect().top, detail: document.querySelector('#ticker-detail-panel').getBoundingClientRect().top }));
  expect(Math.abs(topAlignment.brief - topAlignment.detail)).toBeLessThanOrEqual(1);
  await page.locator(".controls .near-zone-control input").check();
  await expect(page.locator("#count")).toContainText("21 of 21");
  await expect(page.locator("#watchlist-body tr")).toHaveCount(21);
  await page.locator(".controls .near-zone-control input").uncheck();
  await expect(page.locator("#watchlist-body tr")).toHaveCount(40);
  await page.locator(".coverage-disclosure > summary").click();
  await expect(page.locator(".coverage-content")).toContainText("MISS1");
  await expect(page.locator(".coverage-content")).toContainText("MISS2");
  await expect(page.locator(".coverage-content")).toContainText("V001");
  await page.locator(".coverage-disclosure > summary").click();
  await page.getByRole("button", { name: "V002", exact: true }).click();
  await expect(page.locator("#ticker-detail-panel h2")).toHaveText("V002");
  await expect(page.locator("#ticker-detail-panel .state-timeline li")).toHaveCount(5);
  await expect(page.locator("#ticker-detail-panel .state-timeline li:visible")).toHaveCount(2);
  await page.locator("#ticker-detail-panel .earlier-changes summary").click();
  await expect(page.locator("#ticker-detail-panel .state-timeline li:visible")).toHaveCount(5);
  await expect(page.locator("#ticker-detail-panel")).not.toContainText("Wait for stronger confirmation");
  await page.locator('#ticker-detail-panel [data-research-step="1"]').click();
  await expect(page.locator("#ticker-detail-panel h2")).toHaveText("V003");
  await page.locator('#ticker-detail-panel [data-research-step="-1"]').click();
  await expect(page.locator("#ticker-detail-panel h2")).toHaveText("V002");
  await expect(page.locator('#watchlist-body tr[data-select-ticker="V002"]')).toHaveAttribute("aria-selected", "true");
  await expect(page.locator('#watchlist-body tr[data-select-ticker="V003"]')).toHaveCSS("box-shadow", "none");
  const marker = await page.locator('#watchlist-body tr[data-select-ticker="V002"] td').first().evaluate(e => getComputedStyle(e).boxShadow);
  expect(marker).toContain("inset");
  await page.evaluate(() => window.scrollTo(0, document.querySelector("#watchlist-table").getBoundingClientRect().top + scrollY + 700));
  const sticky = await page.evaluate(() => Object.fromEntries([["rail", "#market-rail"], ["controls", ".controls"], ["detail", "#ticker-detail-panel"]].map(([key, selector]) => { const box = document.querySelector(selector).getBoundingClientRect(); return [key, { top: box.top, bottom: box.bottom }]; })));
  expect(sticky.rail.top).toBeGreaterThanOrEqual(-1);
  expect(sticky.controls.top).toBeGreaterThanOrEqual(sticky.rail.bottom - 1);
  expect(sticky.detail.top).toBeGreaterThanOrEqual(sticky.rail.bottom - 1);
  await expect(page.locator("#ticker-detail-panel")).toHaveCSS("position", "sticky");
  await expect(page.locator("#watchlist-head th").first()).toHaveCSS("position", "sticky");
  await expect(page.locator(".controls")).toHaveCSS("position", "sticky");
  await page.locator('#research-pagination [data-page-step="1"]').click();
  await expect(page.locator("#watchlist-body tr")).toHaveCount(21);
  await expect(page.locator("#research-pagination")).toContainText("Page 2 of 2");
  await page.locator('#cards [data-filter="buy"]').click();
  await expect(page.locator("#empty")).toBeVisible();
  await expect(page.locator('#cards [data-filter="buy"]')).toHaveAttribute("aria-pressed", "true");
  await page.locator('#cards [data-filter="risk"]').click();
  await expect(page.locator("#watchlist-body tr")).toHaveCount(1);
  await expect(page.locator("#watchlist-body .ticker-link")).toHaveText("V060");
  expect(errors).toEqual([]);
});

test("v5 stock page: price ruler, source readiness and previous/next navigation", async ({ page }) => {
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await useResearchDataset(page);
  await page.goto(`${baseUrl}/ticker.html?ticker=V002`);
  await expect(page.locator(".price-ruler")).toHaveAttribute("aria-label", /planned zone 100.00 to 105.00/);
  await expect(page.locator(".rail-home")).toHaveText("Daily Trade Copilot");
  await expect(page.locator("body")).not.toContainText("v5.1.1");
  await expect(page.locator(".readiness-meter > strong")).toContainText("57");
  await expect(page.locator(".readiness-meter meter")).toHaveAttribute("value", "57.1");
  await expect(page.locator("#timeline .state-timeline li")).toHaveCount(5);
  await expect(page.getByRole("link", { name: /Previous stock/ })).toHaveAttribute("href", /ticker=V001$/);
  await page.getByRole("link", { name: /Next stock/ }).click();
  await expect(page).toHaveURL(/ticker=V003$/);
  await expect(page.locator("#history-title")).toContainText("V003");
  expect(errors).toEqual([]);
});

test("v5 mobile cards: no wide table, intact percentages and inline evidence", async ({ page }) => {
  await useResearchDataset(page);
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto(baseUrl);
    await expect(page.locator(".v5-stock-card").first()).toBeVisible();
    await expect(page.locator(".v5-stock-card").first().locator(".zone-distance")).toHaveText("Inside");
    const size = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: innerWidth }));
    expect(size.width).toBeLessThanOrEqual(size.viewport + 1);
    await page.locator(".v5-stock-link").first().click();
    await expect(page).toHaveURL(/ticker=V000$/);
    await expect(page.locator(".mobile-inline-detail")).toBeVisible();
    await expect(page.locator(".mobile-inline-detail")).toContainText("Why we see it this way");
    await expect(page.locator(".mobile-inline-detail .detail-panel-head")).toHaveCount(0);
    await expect(page.locator(".app-tabbar")).toBeHidden();
    await expect(page.locator(".mobile-inline-detail .score-factors > div").first()).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
    await expect(page.locator(".mobile-inline-detail .score-factors > div").first()).toHaveCSS("text-align", "left");
    await expect(page.locator("#watchlist-body tr").first().locator(".mobile-inline-detail")).toHaveCount(1);
    await expect(page.locator(".v5-stock-link").first()).toHaveAttribute("aria-expanded", "true");
    await page.locator(".v5-stock-link").first().click();
    await expect(page.locator(".mobile-inline-detail")).toHaveCount(0);
    await page.locator('[data-mobile-filter="favourites"]').click();
    await expect(page.locator("#empty")).toBeVisible();
    await page.locator('[data-mobile-filter="favourites"]').click();
    await expect(page.locator(".v5-stock-card")).toHaveCount(40);
  }
});

test("v5.1 moves genuine plan risk into evidence without table clutter", async ({ page }) => {
  await useResearchDataset(page, { optionalPlan: true });
  await page.goto(baseUrl);
  await expect(page.locator("#watchlist-head")).not.toContainText("Protection");
  await expect(page.locator("#watchlist-head")).not.toContainText("Loss if stopped");
  await expect(page.locator("#ticker-detail-panel .recorded-plan")).toContainText("95.00");
  await expect(page.locator("#ticker-detail-panel .recorded-plan")).toContainText("−7.0%");
});

test("v5 omits a price ruler when the planned zone is absent", async ({ page }) => {
  await useResearchDataset(page, { missingZone: true });
  await page.goto(`${baseUrl}/ticker.html?ticker=V000`);
  await expect(page.locator(".ruler-unavailable")).toBeVisible();
  await expect(page.locator(".price-ruler")).toHaveCount(0);
});

test("market research is readable on desktop and mobile without the source disclosure", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await useLocalPublishedData(page);
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto(`${baseUrl}/index.html`);
    const section = page.locator("#market-brief");
    await expect(section.getByRole("heading", { name: marketBrief.headline })).toBeVisible();
    await expect(section.getByRole("progressbar")).toHaveCount(0);
    await expect(section.locator('.full-brief')).not.toHaveAttribute('open', '');
    await section.locator('.full-brief > summary').click();
    await expect(section.locator('.brief-developments p')).toHaveCount(marketBrief.highlights.length);
    for (const [index, key] of ["bull", "base", "bear"].entries()) {
      await expect(section.locator(".probability-segment strong").nth(index)).toHaveText(`${marketBrief.forecast.probabilities[key]}%`);
      await expect(section.locator(".scenario-ranges small").nth(index)).toBeVisible();
    }
    await expect(section.locator("details.research-brief")).toHaveAttribute("open", "");
    await section.locator(".brief-toggle").click();
    await expect(section.locator("details.research-brief")).not.toHaveAttribute("open", "");
    await expect(section.getByRole("heading", { name: marketBrief.headline })).toBeVisible();
    await expect(section.locator(".brief-summary.when-closed")).toBeVisible();
    await section.locator(".brief-toggle").click();
    await expect(section.getByRole("link")).toHaveCount(0);
    await expect(section.locator(".brief-date")).toContainText(marketBrief.session_date);
    await expect(section.locator(".brief-note")).toHaveCount(0);
    await expect(section).not.toContainText("Completed forecast sample");
    await expect(section).not.toContainText("Subjective research probabilities");
    await expect(section.locator(".brief-outlook .brief-eyebrow")).toContainText(/NOT A TRADE SIGNAL|ARCHIVED OUTLOOK/);
    const dimensions = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: innerWidth }));
    expect(dimensions.width).toBeLessThanOrEqual(dimensions.viewport + 1);
    await section.screenshot({ path: `${process.env.SCREENSHOT_DIR || "/tmp"}/market-brief-${width}.png` });
  }
  expect(errors).toEqual([]);
});

test("daily brief moves are green up, red down and neutral when unchanged", async ({ page }) => {
  await useLocalPublishedData(page);
  const fixture = structuredClone(marketBrief);
  fixture.metrics = [
    { label: "Positive test", value: "100", detail: "+1.20% · US close" },
    { label: "Negative test", value: "100", detail: "−0.52% · US close" },
    { label: "Unchanged test", value: "100", detail: "+0.00% · US close" },
  ];
  await page.route("**/data/market-brief.json", (route) => route.fulfill({ json: fixture }));
  await page.goto(`${baseUrl}/index.html`);
  const section = page.locator("#market-brief");
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const scheme of ["light", "dark"]) {
      await page.emulateMedia({ colorScheme: scheme });
      await expect(page.locator("html")).toHaveCSS("color-scheme", "light");
      await expect(section).toHaveCSS("background-color", "rgb(250, 247, 240)");
      await expect(section.locator(".brief-change-up")).toHaveCSS("color", "rgb(20, 115, 68)");
      await expect(section.locator(".brief-change-down")).toHaveCSS("color", "rgb(180, 35, 24)");
      await expect(section.locator(".brief-metrics > div").last().locator("small")).toHaveText("+0.00%");
      await expect(section.locator(".brief-metrics > div").last().locator("small")).toHaveAttribute("title", "+0.00% · US close");
      await expect(section.locator(".brief-metrics > div").last().locator("small span")).toHaveCount(0);
    }
  }
});

test("market research fails safely without hiding the watchlist", async ({ page }) => {
  await useLocalPublishedData(page);
  await page.route("**/data/market-brief.json", (route) => route.fulfill({ status: 200, contentType: "application/json", body: '{"schema_version":99}' }));
  await page.goto(`${baseUrl}/index.html`);
  await expect(page.locator("#market-brief")).toContainText("Daily research is unavailable");
  await expect(page.locator("#watchlist-body .col-zone")).toContainText("100.00–105.00");
});

async function useLocalPublishedData(page) {
  await page.route("https://yubobo815.github.io/daily-watchlist-cloud/data/**", async (route) => {
    const source = new URL(route.request().url());
    const localPath = source.pathname.replace("/daily-watchlist-cloud", "");
    const response = await page.request.get(`${baseUrl}${localPath}`);
    await route.fulfill({ response });
  });
}

test("readability: larger research text, unclipped tools and complete mobile conditions", async ({ page }) => {
  await useLocalPublishedData(page);
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(`${baseUrl}/index.html`);
    await expect(page.locator(".brief-developments p").first()).toHaveCSS("font-size", "14px");
    await expect(page.locator(".brief-headline")).toHaveCSS("text-transform", "none");
    await expect(page.locator(".brief-metrics small").first()).toHaveCSS("font-size", "12px");
    if (width < 961) {
      await expect(page.locator(".mobile-execution")).toHaveCount(0);
      await page.locator(".coverage-disclosure > summary").click();
      await expect(page.locator(".coverage-content")).toBeVisible();
      await page.locator(".coverage-disclosure > summary").click();
      await page.locator("#mobile-search").fill("NO_MATCH_READABILITY");
      await expect(page.locator("#watchlist-body tr")).toHaveCount(0);
      await page.locator("#mobile-clear-search").click();
      await expect(page.locator("#watchlist-body tr")).toHaveCount(1);
    }
    const dimensions = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: innerWidth }));
    expect(dimensions.width).toBeLessThanOrEqual(dimensions.viewport + 1);
  }
});

test("watchlist and ticker page preserve the frozen plan", async ({ page }) => {
  const runtimeErrors = [];
  page.on("pageerror", (error) => runtimeErrors.push(error.message));
  await useLocalPublishedData(page);
  await page.goto(`${baseUrl}/index.html`);
  await expect(page.locator("#watchlist-body .col-zone")).toContainText("100.00–105.00");
  await page.goto(`${baseUrl}/ticker.html?ticker=TEST`);
  await expect(page.getByText("Frozen execution plan")).toBeVisible();
  await expect(page.getByText("Waiting for entry")).toBeVisible();
  await expect(page.getByText("100.00-105.00", { exact: true })).toBeVisible();
  await expect(page.locator("#latest-panel").getByText("BUILDING", { exact: true })).toBeVisible();
  expect(runtimeErrors).toEqual([]);
});

test("mobile ticker plan is readable without page overflow", async ({ page }) => {
  const runtimeErrors = [];
  page.on("pageerror", (error) => runtimeErrors.push(error.message));
  await useLocalPublishedData(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ colorScheme: "dark" });
  await page.goto(`${baseUrl}/ticker.html?ticker=TEST`);
  await expect(page.getByText("Frozen execution plan")).toBeVisible();
  await expect(page.locator("html")).toHaveCSS("color-scheme", "light");
  await expect(page.locator("body")).toHaveCSS("background-color", "rgb(239, 235, 227)");
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: window.innerWidth }));
  expect(dimensions.width).toBeLessThanOrEqual(dimensions.viewport + 1);
  expect(runtimeErrors).toEqual([]);
});
