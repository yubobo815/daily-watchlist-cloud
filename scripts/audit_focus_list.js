#!/usr/bin/env node
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const helpers = require("../api/_supabase");

async function invoke({body, method = "PUT", pin = "test-only", configured = true, failAddition = false}) {
  let tickers = ["AAPL"];
  const calls = [];
  const sandbox = {
    module: {exports: {}},
    process: {env: configured ? {FOCUS_LIST_PIN: "test-only"} : {}},
    console: {error() {}},
    require: () => ({
      ...helpers,
      supabaseSelect: async () => {
        calls.push("GET");
        return tickers.map((ticker) => ({ticker}));
      },
      supabaseRequest: async (_url, options) => {
        calls.push(options.method);
        if (options.method === "POST" && failAddition) {
          return {ok: false, status: 503, text: async () => "fixture failure"};
        }
        if (options.method === "POST") tickers.push(...options.body.map((row) => row.ticker));
        if (options.method === "DELETE") tickers = [];
        return {ok: true};
      },
    }),
  };
  const source = fs.readFileSync(path.join(__dirname, "../api/focus-list.js"), "utf8");
  vm.runInNewContext(source, sandbox);
  const result = {};
  const response = {
    setHeader() {},
    status(code) {result.status = code; return this;},
    json(value) {result.body = value;},
    end() {},
  };
  await sandbox.module.exports({method, headers: {"x-focus-pin": pin}, body}, response);
  return {result, calls, saved: tickers};
}

(async () => {
  const invalidBodies = [
    '{"tickers":', {}, "null", [],
    {tickers: "AAPL"}, {tickers: ["AAPL", 42]},
    {tickers: ["AAPL", "bad ticker"]},
    {tickers: Array.from({length: 151}, (_, i) => `T${i}`)},
  ];
  for (const body of invalidBodies) {
    const {result, calls, saved} = await invoke({body});
    assert.equal(result.status, 400);
    assert.deepEqual(calls, [], "invalid input must not reach the database");
    assert.deepEqual(saved, ["AAPL"]);
  }
  const unauthorised = await invoke({body: {tickers: []}, pin: "wrong"});
  assert.equal(unauthorised.result.status, 401);
  assert.deepEqual(unauthorised.calls, []);
  const unconfigured = await invoke({method: "GET", configured: false});
  assert.equal(unconfigured.result.status, 503);
  assert.deepEqual(unconfigured.calls, []);
  const read = await invoke({method: "GET"});
  assert.equal(read.result.status, 200);
  assert.deepEqual(read.saved, ["AAPL"]);
  const update = await invoke({body: {tickers: ["msft", "AAPL", " MSFT "]}});
  assert.equal(update.result.status, 200);
  assert.deepEqual([...update.result.body.tickers], ["AAPL", "MSFT"]);
  const clear = await invoke({body: {tickers: []}});
  assert.equal(clear.result.status, 200);
  assert.deepEqual(clear.saved, []);
  const failedAddition = await invoke({body: {tickers: ["MSFT"]}, failAddition: true});
  assert.equal(failedAddition.result.status, 500);
  assert.deepEqual(failedAddition.calls, ["GET", "POST"]);
  assert.deepEqual(failedAddition.saved, ["AAPL"], "failed additions must preserve the saved list");
  console.log("Focus List audit passed: invalid requests, authentication, updates and failed-addition preservation.");
})().catch((error) => {console.error(error); process.exitCode = 1;});
