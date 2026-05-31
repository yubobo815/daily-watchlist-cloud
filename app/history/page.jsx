"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { ACTION_LABELS, actionKind, downloadCsv, fmtNumber, supabaseFetch } from "../lib";

const columns = ["history_date", "action", "setup", "adaptive_mode", "psychology", "score", "close", "day_change_pct", "entry_est", "stop_est", "target_est", "notes"];

function normaliseTicker(value) {
  return (value || "ORCL").trim().toUpperCase().replace("BRK.B", "BRK-B");
}

function HistoryContent() {
  const params = useSearchParams();
  const initialTicker = normaliseTicker(params.get("ticker"));
  const [ticker, setTicker] = useState(initialTicker);
  const [input, setInput] = useState(initialTicker);
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState("Loading ticker behavior...");
  const [runDate, setRunDate] = useState("");

  useEffect(() => {
    setInput(initialTicker);
    setTicker(initialTicker);
  }, [initialTicker]);

  useEffect(() => {
    let cancelled = false;
    async function loadHistory() {
      try {
        const runRows = await supabaseFetch(
          `watchlist_behavior_history?select=run_date&ticker=eq.${encodeURIComponent(ticker)}&order=run_date.desc&limit=1`
        );
        const latest = runRows[0]?.run_date;
        if (!latest) throw new Error(`No 30-day history found for ${ticker}.`);
        const data = await supabaseFetch(
          `watchlist_behavior_history?select=*&ticker=eq.${encodeURIComponent(ticker)}&run_date=eq.${encodeURIComponent(latest)}&order=history_date.desc`
        );
        if (!cancelled) {
          setRows(data);
          setRunDate(latest);
          setStatus(`${ticker} behavior history from Supabase run ${latest}.`);
        }
      } catch (error) {
        if (!cancelled) {
          setRows([]);
          setRunDate("");
          setStatus(error.message);
        }
      }
    }
    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  const latest = rows[0];
  const trendRows = useMemo(() => [...rows].reverse(), [rows]);

  function submit(event) {
    event.preventDefault();
    const nextTicker = normaliseTicker(input);
    setTicker(nextTicker);
    window.history.replaceState(null, "", `/history?ticker=${encodeURIComponent(nextTicker)}`);
  }

  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Behavior rewind</p>
          <h1>{ticker} 30-Day History</h1>
          <p className="subtle meta">
            {status} This is scanner behavior history, not TradingView confirmation.
          </p>
          {runDate ? <div className="status">Database run: {runDate}</div> : <div className="status bad">No history loaded</div>}
        </div>
        <div className="actions">
          <Link className="button" href="/">Back to Watchlist</Link>
          <button className="button primary" type="button" onClick={() => downloadCsv(`${ticker}_history.csv`, rows, columns)}>
            Download CSV
          </button>
        </div>
      </section>

      <section className="history-grid">
        <aside className="panel">
          <form onSubmit={submit}>
            <label className="subtle" htmlFor="ticker">Ticker</label>
            <input id="ticker" className="ticker-input" value={input} onChange={(event) => setInput(event.target.value)} />
            <button className="button primary" type="submit">Show History</button>
          </form>
          {latest ? (
            <div className="timeline">
              <div><strong>Latest signal</strong></div>
              <span className={`badge ${actionKind(latest.action)}`}>{ACTION_LABELS[latest.action] || latest.action}</span>
              <p className="subtle">
                Close {fmtNumber(latest.close, 2)}, score {fmtNumber(latest.score, 1)}, entry {fmtNumber(latest.entry_est, 2)}.
              </p>
              {latest.notes ? <p className="subtle">{latest.notes}</p> : null}
            </div>
          ) : null}
        </aside>

        <section className="panel">
          <h2>Behavior Change</h2>
          <div className="timeline">
            {trendRows.map((row) => (
              <div className="timeline-row" key={`${row.ticker}-${row.history_date}`}>
                <strong>{row.history_date}</strong>
                <div>
                  <span className={`badge ${actionKind(row.action)}`}>{ACTION_LABELS[row.action] || row.action}</span>
                  <span className="subtle"> {row.setup || "NONE"} · {row.adaptive_mode || "Mixed"}</span>
                  <div className="bar"><span style={{ width: `${Math.max(2, Math.min(100, Number(row.score) || 0))}%` }} /></div>
                </div>
                <span className="num">{fmtNumber(row.close, 2)}</span>
              </div>
            ))}
            {!rows.length ? <div className="empty">No history found for this ticker.</div> : null}
          </div>
        </section>
      </section>
    </main>
  );
}

export default function HistoryPage() {
  return (
    <Suspense fallback={<main className="shell"><div className="status">Loading history...</div></main>}>
      <HistoryContent />
    </Suspense>
  );
}
