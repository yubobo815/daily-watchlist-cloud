const {
  encodeFilterValue,
  isValidTicker,
  normalizeTicker,
  supabaseRequest,
  supabaseSelect,
} = require("./_supabase");

const LIST_ID = "default";
const MAX_FOCUS_TICKERS = 150;

function configuredPin() {
  return process.env.FOCUS_LIST_PIN || process.env.WATCHLIST_FOCUS_PIN || "";
}

function requestPin(request, body = {}) {
  return String(request.headers["x-focus-pin"] || body.pin || "").trim();
}

function parseBody(request) {
  if (!request.body) return {};
  if (typeof request.body === "object") return request.body;
  try {
    return JSON.parse(request.body);
  } catch {
    return {};
  }
}

function assertPin(request, body) {
  const pin = configuredPin();
  if (!pin) {
    const error = new Error("Focus List PIN is not configured.");
    error.statusCode = 503;
    throw error;
  }
  if (requestPin(request, body) !== pin) {
    const error = new Error("Focus List PIN is incorrect.");
    error.statusCode = 401;
    throw error;
  }
}

function cleanTickers(values) {
  return [...new Set((Array.isArray(values) ? values : [])
    .map(normalizeTicker)
    .filter((ticker) => ticker && isValidTicker(ticker)))]
    .sort()
    .slice(0, MAX_FOCUS_TICKERS);
}

async function readFocusTickers() {
  const rows = await supabaseSelect(`focus_tickers?select=ticker&list_id=eq.${encodeFilterValue(LIST_ID)}&order=ticker.asc`);
  return rows.map((row) => row.ticker).filter(Boolean);
}

async function replaceFocusTickers(nextTickers) {
  const currentTickers = await readFocusTickers();
  const currentSet = new Set(currentTickers);
  const nextSet = new Set(nextTickers);
  const toAdd = nextTickers.filter((ticker) => !currentSet.has(ticker));
  const toDelete = currentTickers.filter((ticker) => !nextSet.has(ticker));

  await Promise.all(toDelete.map(async (ticker) => {
    const response = await supabaseRequest(
      `focus_tickers?list_id=eq.${encodeFilterValue(LIST_ID)}&ticker=eq.${encodeFilterValue(ticker)}`,
      { method: "DELETE" }
    );
    if (!response.ok) {
      const text = await response.text();
      console.error(`Focus List delete failed (${response.status}): ${text.slice(0, 500)}`);
      throw new Error("Could not save Focus List.");
    }
  }));

  if (toAdd.length) {
    const response = await supabaseRequest("focus_tickers?on_conflict=list_id,ticker", {
      method: "POST",
      headers: {
        Prefer: "resolution=merge-duplicates,return=minimal",
      },
      body: toAdd.map((ticker) => ({ list_id: LIST_ID, ticker })),
    });
    if (!response.ok) {
      const text = await response.text();
      console.error(`Focus List upsert failed (${response.status}): ${text.slice(0, 500)}`);
      throw new Error("Could not save Focus List.");
    }
  }

  return readFocusTickers();
}

module.exports = async function handler(request, response) {
  try {
    if (request.method === "OPTIONS") {
      response.status(204).end();
      return;
    }

    const body = parseBody(request);
    assertPin(request, body);

    if (request.method === "GET") {
      response.setHeader("Cache-Control", "private, no-store");
      response.status(200).json({ tickers: await readFocusTickers() });
      return;
    }

    if (request.method === "PUT") {
      const tickers = await replaceFocusTickers(cleanTickers(body.tickers));
      response.setHeader("Cache-Control", "private, no-store");
      response.status(200).json({ tickers });
      return;
    }

    response.status(405).json({ error: "Method not allowed." });
  } catch (error) {
    console.error(error);
    response.status(error.statusCode || 500).json({ error: error.message || "Focus List unavailable." });
  }
};
