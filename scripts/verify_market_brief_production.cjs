const fs = require('node:fs');
const { chromium } = require('@playwright/test');
const { stable } = require('./publish_market_brief.cjs');
const URL = 'https://dailytradingcopilot.vercel.app/';

async function main() {
  const expected = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  let ready = false;
  for (let attempt = 0; attempt < 40 && !ready; attempt++) {
    try {
      const response = await fetch(`${URL}data/market-brief.json?verification=${attempt}`, {cache:'no-store', signal:AbortSignal.timeout(15000)});
      ready = response.ok && stable(await response.json()) === stable(expected);
    } catch { /* bounded deployment wait; never substitute older data */ }
    if (!ready) await new Promise(resolve => setTimeout(resolve, 10000));
  }
  if (!ready) throw new Error('Production JSON did not reach the exact tested snapshot; inspect Vercel deployment before retiring the old sync.');
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(URL, {waitUntil:'domcontentloaded'});
    await page.locator('#market-brief .brief-date').waitFor();
    const date = await page.locator('#market-brief .brief-date').innerText();
    const outlook = await page.locator('#market-brief .brief-outlook h3').innerText();
    const probabilities = await page.locator('#market-brief .probability-strip').getAttribute('aria-label');
    const expectedProbabilities = ['bull','base','bear'].map(key => `${key[0].toUpperCase()+key.slice(1)} ${expected.forecast.probabilities[key]}%`).join(', ');
    if (!date.includes(`US session ${expected.session_date}`) || outlook !== expected.forecast.outlook || probabilities !== expectedProbabilities || errors.length) throw new Error('Production rendered brief does not match the tested session/outlook/probabilities, or has a page error.');
    console.log(JSON.stringify({production:'verified',session_date:expected.session_date,forecast_id:expected.forecast.id,rendered_outlook:outlook}));
  } finally {
    await browser.close();
  }
}

main().catch(error => {console.error(error.message);process.exitCode=1;});
