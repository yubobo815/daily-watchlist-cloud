const { test, expect } = require("@playwright/test");

const baseUrl = process.env.BASE_URL || "http://web:4178";

async function useLocalPublishedData(page) {
  await page.route("https://yubobo815.github.io/daily-watchlist-cloud/data/**", async (route) => {
    const source = new URL(route.request().url());
    const localPath = source.pathname.replace("/daily-watchlist-cloud", "");
    const response = await page.request.get(`${baseUrl}${localPath}`);
    await route.fulfill({ response });
  });
}

test("watchlist and ticker page preserve the frozen plan", async ({ page }) => {
  await useLocalPublishedData(page);
  await page.goto(`${baseUrl}/index.html`);
  await expect(page.getByText("Waiting for price to reach 100.00-105.00", { exact: false }).first()).toBeVisible();
  await page.goto(`${baseUrl}/ticker.html?ticker=TEST`);
  await expect(page.getByText("Frozen execution plan")).toBeVisible();
  await expect(page.getByText("Waiting for entry")).toBeVisible();
  await expect(page.getByText("100.00-105.00", { exact: true })).toBeVisible();
  await expect(page.locator("#latest-panel").getByText("BUILDING", { exact: true })).toBeVisible();
});

test("mobile ticker plan is readable without page overflow", async ({ page }) => {
  await useLocalPublishedData(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${baseUrl}/ticker.html?ticker=TEST`);
  await expect(page.getByText("Frozen execution plan")).toBeVisible();
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: window.innerWidth }));
  expect(dimensions.width).toBeLessThanOrEqual(dimensions.viewport + 1);
});
