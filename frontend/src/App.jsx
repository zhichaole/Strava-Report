import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

function metersToMiles(m) {
  return m * 0.000621371;
}
function secToHMS(sec) {
  const s = Math.round(sec);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  return `${h}h ${m}m ${r}s`;
}
function paceFromTotals(totalSeconds, totalMeters) {
  const miles = metersToMiles(totalMeters);
  if (miles <= 0) return "—";
  const secPerMile = totalSeconds / miles;
  const min = Math.floor(secPerMile / 60);
  const sec = Math.round(secPerMile % 60);
  return `${min}:${String(sec).padStart(2, "0")} /mi`;
}

export default function App() {
  const [status, setStatus] = useState("loading");
  const [lastSync, setLastSync] = useState(null);
  const [newCount, setNewCount] = useState(0);
  const [summaries, setSummaries] = useState({ weekly: [], monthly: [], yearly: [] });
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/sync`);
        const data = await res.json();

        if (data.status === "needs_auth") {
          window.location.href = data.auth_url;
          return;
        }

        if (data.status !== "ok") {
          setStatus("error");
          setError(data.message || "Unknown error");
          return;
        }

        setSummaries(data.summaries);
        setLastSync(data.last_sync);
        setNewCount(data.new_activities_fetched || 0);
        setStatus("ok");
      } catch (e) {
        setStatus("error");
        setError(String(e));
      }
    })();
  }, []);

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif", maxWidth: 980, margin: "40px auto", padding: 16 }}>
      <h1>Strava Personal Report (Local)</h1>

      {status === "loading" && <p>Syncing from Strava…</p>}

      {status === "error" && (
        <div>
          <p style={{ color: "crimson" }}>Error: {error}</p>
          <p>
            First run? Set backend <code>.env</code> and Strava callback domain <code>localhost</code>.
          </p>
        </div>
      )}

      {status === "ok" && (
        <>
          <p>
            Last sync: <b>{new Date(lastSync * 1000).toLocaleString()}</b> • New activities fetched: <b>{newCount}</b>
          </p>

          <Section title="Weekly" rows={summaries.weekly} />
          <Section title="Monthly" rows={summaries.monthly} />
          <Section title="Yearly" rows={summaries.yearly} />
        </>
      )}
    </div>
  );

  function Section({ title, rows }) {
    return (
      <div style={{ marginTop: 28 }}>
        <h2>{title}</h2>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th align="left">Period start</th>
              <th align="right">Runs</th>
              <th align="right">Miles</th>
              <th align="right">Time</th>
              <th align="right">Avg pace</th>
              <th align="right">Avg HR</th>
              <th align="right">Elev gain (m)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={`${r.period_type}-${r.period_start}`} style={{ borderTop: "1px solid #ddd" }}>
                <td>{r.period_start}</td>
                <td align="right">{r.run_count}</td>
                <td align="right">{metersToMiles(r.total_meters).toFixed(2)}</td>
                <td align="right">{secToHMS(r.total_seconds)}</td>
                <td align="right">{paceFromTotals(r.total_seconds, r.total_meters)}</td>
                <td align="right">{r.avg_hr_time_weighted == null ? "—" : r.avg_hr_time_weighted.toFixed(1)}</td>
                <td align="right">{Number(r.elevation_gain).toFixed(0)}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan="7" style={{ padding: 12, color: "#555" }}>
                  No data yet. Record a run, then refresh the page to auto-sync again.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    );
  }
}
