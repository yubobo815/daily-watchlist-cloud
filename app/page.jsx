"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ACTION_LABELS, SETUP_LABELS, actionKind, downloadCsv, fmtNumber, latestRunDate, supabaseFetch } from "./lib";

const columns = [
  ["ticker", "Sym"],
  ["name", "Name"],
  ["action", "Signal"],
  ["score", "Score"],
  ["close", "Last"],
  ["day_change_pct", "Chg%"],
  ["setup", "Setup"],
  ["adaptive_mode", "Mode"],
  ["psychology", "Tape"],
  ["entry_est", "Entry"],
  ["stop_est", "Stop"],
  ["target_est", "Target"],
  ["notes", "Read"]
];

const summaryCards = [
  ["buy", "BUY"],
  ["setup", "SETUP"],
  ["watch", "WATCH"],
  ["exit", "EXIT"],
  ["avoid", "AVOID"]
];

function renderCell(row, key) {
  if (key === "ticker") {
    return (
      <Link className="ticker" href={`/history?ticker=${encodeURIComponent(row.ticker)}`}>
        {row.ticker}
      </Link>
    );
  }
  if (key === "action") {
    const kind = actionKind(row.action);
    return <span className={`badge ${kind}`}>{ACTION_LABELS[row.action] || row.action}</span>;
  }
  if (key === "setup") {
    return SETUP_LABELS[row.setup] ? <span className="badge">{SETUP_LABELS[row.setup]}</span> : row.setup;
  }
  if (["score", "day_change_pct"].includes(key)) return fmtNumber(row[key], 1);
  if (["close", "entry_est", "stop_est", "target_est"].includes(key)) return fmtNumber(row[key], 2);
  return row[key] || "";
}

export default function HomePage() {
  const [rows, setRows] = useState([]);
  const [runDate, setRunDate] = useState("");
  const [status, setStatus] = useState("Loading Supabase watchlist...");
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("score-desc");

  useEffect(() => {
    let cancelled = false;
    async function loadRows() {
      try {
        const latest = await latestRunDate();
        if (!latest) throw new Error("No Supabase run found yet.");
        const data = await supabaseFetch(
          `watchlist_snapshots?select=*&run_date=eq.${encodeURIComponent(latest)}&order=score.desc`
        );
        if (!cancelled) {
          setRows(data);
          setRunDate(latest);
          setStatus(`Live from Supabase run ${latest}. Confirm BUY CANDIDATE entries on the TradingView Pine chart before acting.`);
        }
      } catch (error) {
        if (!cancelled) setStatus(error.message);
      }
    }
    loadRows();
    return () => {
      cancelled = true;
    };
  }, []);

  const counts = useMemo(() => {
    const result = { buy: 0, setup: 0, watch: 0, exit: 0, avoid: 0 };
    rows.forEach((row) => {
      result[actionKind(row.action)] += 1;
    });
    return result;
  }, [rows]);

  const visibleRows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const [sortKey, direction] = sort.split("-");
    const multiplier = direction === "asc" ? 1 : -1;
    return rows
      .filter((row) => filter === "all" || actionKind(row.action) === filter)
      .filter((row) => {
        if (!needle) return true;
        return columns.some(([key]) => String(row[key] || "").toLowerCase().includes(needle));
      })
      .sort((a, b) => {
        if (sortKey === "ticker") return a.ticker.localeCompare(b.ticker) * multiplier;
        const av = Number(a[sortKey] || 0);
        const bv = Number(b[sortKey] || 0);
        return (av - bv) * multiplier;
      });
  }, [filter, query, rows, sort]);

  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Vercel trading cockpit</p>
          <h1>Daily Watchlist</h1>
          <p className="subtle meta">
            {status} Daily refresh still comes from GitHub Actions at 8:00am Australia/Melbourne; this Vercel app reads the database instantly.
          </p>
          {runDate ? <div className="status">Database run: {runDate}</div> : <div className="status bad">Waiting for database config</div>}
        </div>
        <div className="actions">
          <button className="button primary" type="button" onClick={() => downloadCsv("daily_watchlist_vercel.csv", visibleRows, columns.map(([key]) => key))}>
            Download CSV
          </button>
          <Link className="button" href="/history?ticker=ORCL">ORCL History</Link>
          <a className="button" href="https://yubobo815.github.io/daily-watchlist-cloud/">GitHub Pages</a>
        </div>
      </section>

      <section className="cards">
        {summaryCards.map(([kind, label]) => (
          <button key={kind} className={`card tone-${kind} ${filter === kind ? "active" : ""}`} type="button" onClick={() => setFilter(filter === kind ? "all" : kind)}>
            <span>{label}</span>
            <strong>{counts[kind] || 0}</strong>
          </button>
        ))}
      </section>

      <section className="controls">
        <input className="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search ticker, setup, note, mode..." />
        <button className={`chip ${filter === "all" ? "active" : ""}`} type="button" onClick={() => setFilter("all")}>All</button>
        <select className="control" value={sort} onChange={(event) => setSort(event.target.value)}>
          <option value="score-desc">Score high to low</option>
          <option value="day_change_pct-desc">Best day change</option>
          <option value="day_change_pct-asc">Worst day change</option>
          <option value="ticker-asc">Ticker A to Z</option>
        </select>
        <div className="count">{visibleRows.length} / {rows.length} shown</div>
      </section>

      <section className="table-wrap">
        <table>
          <thead>
            <tr>{columns.map(([key, label]) => <th key={key}>{label}</th>)}</tr>
          </thead>
          <tbody>
            {visibleRows.map((row) => (
              <tr key={row.ticker} className={`row-${actionKind(row.action)}`}>
                {columns.map(([key]) => (
                  <td key={key} className={["score", "close", "day_change_pct", "entry_est", "stop_est", "target_est"].includes(key) ? "num" : ""}>
                    {renderCell(row, key)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {!visibleRows.length ? <div className="empty">No matching rows yet.</div> : null}
      </section>
    </main>
  );
}
