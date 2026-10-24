const { test, expect } = require("@playwright/test");

const baseUrl = process.env.BASE_URL || "http://web:4178";
const marketBrief = require(process.env.MARKET_BRIEF_FILE || "../data/market-brief.json");

test("market research is readable on desktop and mobile, with accessible sources", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await useLocalPublishedData(page);
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto(`${baseUrl}/index.html`);
    const section = page.locator("#market-brief");
    await expect(section.getByRole("heading", { name: marketBrief.headline })).toBeVisible();
    await expect(section.getByRole("progressbar", { name: "Base probability" })).toHaveAttribute("value", String(marketBrief.forecast.probabilities.base));
    await section.locator("summary").click();
    await expect(section.getByText(`Forecast ID: ${marketBrief.forecast.id}`, { exact: false })).toBeVisible();
    await expect(section.getByRole("link").first()).toHaveAttribute("href", marketBrief.sources[0].url);
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
      await expect(section.locator(".brief-change-up")).toHaveCSS("color", scheme === "light" ? "rgb(20, 115, 68)" : "rgb(110, 231, 166)");
      await expect(section.locator(".brief-change-down")).toHaveCSS("color", scheme === "light" ? "rgb(180, 35, 24)" : "rgb(255, 146, 137)");
      await expect(section.locator(".brief-metrics > div").last().locator("small")).toHaveText("+0.00% · US close");
      await expect(section.locator(".brief-metrics > div").last().locator("small span")).toHaveCount(0);
    }
  }
});

test("market research fails safely without hiding the watchlist", async ({ page }) => {
  await useLocalPublishedData(page);
  await page.route("**/data/market-brief.json", (route) => route.fulfill({ status: 200, contentType: "application/json", body: '{"schema_version":99}' }));
  await page.goto(`${baseUrl}/index.html`);
  await expect(page.locator("#market-brief")).toContainText("Daily research is unavailable");
  await expect(page.getByText("Waiting for price to reach 100.00-105.00", { exact: false }).first()).toBeVisible();
});

async function useLocalPublishedData(page) {
  await page.route("https://yubobo815.github.io/daily-watchlist-cloud/data/**", async (route) => {
    const source = new URL(route.request().url());
    const localPath = source.pathname.replace("/daily-watchlist-cloud", "");
    const response = await page.request.get(`${baseUrl}${localPath}`);
    await route.fulfill({ response });
  });
}

test("watchlist and ticker page preserve the frozen plan", async ({ page }) => {
  const runtimeErrors = [];
  page.on("pageerror", (error) => runtimeErrors.push(error.message));
  await useLocalPublishedData(page);
  await page.goto(`${baseUrl}/index.html`);
  await expect(page.getByText("Waiting for price to reach 100.00-105.00", { exact: false }).first()).toBeVisible();
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
  await page.goto(`${baseUrl}/ticker.html?ticker=TEST`);
  await expect(page.getByText("Frozen execution plan")).toBeVisible();
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: window.innerWidth }));
  expect(dimensions.width).toBeLessThanOrEqual(dimensions.viewport + 1);
  expect(runtimeErrors).toEqual([]);
});
