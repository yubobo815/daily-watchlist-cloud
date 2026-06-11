const { staticLatestPayload } = require("../api/_static_data");
const { rowDto } = require("../api/_supabase");

const REQUIRED_GATES = [
  "market_permission",
  "ticker_permission",
  "walk_forward_permission",
  "risk_permission",
];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function gateValues(row) {
  const payload = row.payload || {};
  return REQUIRED_GATES.map((field) => row[field] || payload[field] || "");
}

function isBuyLike(row) {
  return row.action === "BUY CANDIDATE" || row.action === "STRONG CONTINUATION";
}

function allGatesAllow(row) {
  return gateValues(row).every((value) => value === "ALLOW");
}

function auditStaticFallback() {
  const payload = staticLatestPayload();
  assert(Array.isArray(payload.rows), "static fallback rows must be an array");
  assert(payload.rows.length > 0, "static fallback must include rows");

  const missingGates = payload.rows.filter((row) => gateValues(row).some((value) => !value));
  const unsafeBuys = payload.rows.filter((row) => isBuyLike(row) && !allGatesAllow(row));

  assert(missingGates.length === 0, `static fallback rows missing gate payloads: ${missingGates.length}`);
  assert(unsafeBuys.length === 0, `static fallback exposes ungated BUY-like rows: ${unsafeBuys.length}`);

  return {
    rows: payload.rows.length,
    missingGates: missingGates.length,
    unsafeBuys: unsafeBuys.length,
  };
}

function auditSupabaseFallback() {
  const legacy = rowDto({
    ticker: "TEST",
    action: "BUY CANDIDATE",
    setup: "BREAKOUT BUY",
    score: 99,
    payload: {},
  });
  assert(legacy.action === "SETUP FORMING", "legacy ungated BUY row must be downgraded");
  assert(gateValues(legacy).every((value) => value === "UNKNOWN"), "legacy row must carry UNKNOWN gates");

  const gated = rowDto({
    ticker: "TEST",
    action: "BUY CANDIDATE",
    setup: "BREAKOUT BUY",
    score: 99,
    payload: {
      market_permission: "ALLOW",
      ticker_permission: "ALLOW",
      walk_forward_permission: "ALLOW",
      risk_permission: "ALLOW",
    },
  });
  assert(gated.action === "BUY CANDIDATE", "fully gated BUY row must be preserved");
  assert(allGatesAllow(gated), "fully gated BUY row must carry ALLOW gates");

  return {
    legacyAction: legacy.action,
    legacyGates: gateValues(legacy),
    gatedAction: gated.action,
    gatedGates: gateValues(gated),
  };
}

const result = {
  staticFallback: auditStaticFallback(),
  supabaseFallback: auditSupabaseFallback(),
};

console.log(JSON.stringify(result, null, 2));
