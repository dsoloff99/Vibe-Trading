/**
 * Sample "Investments" section for the finance app. Plain React, no UI library,
 * so it drops into Next.js or Vite. Wire `loadHoldings` to your aggregator.
 */
import { useEffect, useState } from "react";
import { AdvisorClient, HoldingsIn, Recommendation, Review, ReviewPerformance, Scorecard } from "./advisorClient";

// Next.js inlines NEXT_PUBLIC_* at build time; Vite users can swap in import.meta.env.
declare const process: { env: Record<string, string | undefined> };
const client = new AdvisorClient(process.env.NEXT_PUBLIC_ADVISOR_URL ?? "http://127.0.0.1:8899", process.env.NEXT_PUBLIC_ADVISOR_KEY);

const pct = (x: number | null | undefined) => (x == null ? "–" : `${(x * 100).toFixed(1)}%`);
const usd = (x: number | null | undefined) => (x == null ? "–" : x.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }));

export function InvestmentsSection({ loadHoldings }: { loadHoldings: () => Promise<HoldingsIn> }) {
  const [review, setReview] = useState<Review | null>(null);
  const [open, setOpen] = useState<Recommendation[]>([]);
  const [perf, setPerf] = useState<{ scorecard: Scorecard; reviews: ReviewPerformance[] } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    const [reviews, recs, p] = await Promise.all([client.listReviews(1), client.listRecommendations("open"), client.performance()]);
    if (reviews[0]) setReview(await client.getReview(reviews[0].id));
    setOpen(recs); setPerf(p);
  };
  useEffect(() => { refresh().catch((e) => setError(String(e))); }, []);

  const runReview = async () => {
    setBusy("Syncing holdings and running the review…"); setError(null);
    try {
      await client.pushHoldings(await loadHoldings());
      setReview(await client.review({ risk_tolerance: "aggressive", horizon_years: 15, single_stock_sleeve_cap: 0.4, max_position_weight: 0.15 }));
      await refresh();
    } catch (e) { setError(String(e)); } finally { setBusy(null); }
  };

  const decide = async (id: string, status: "accepted" | "rejected") => { await client.decide(id, status); await refresh(); };

  return (
    <section>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Investments</h2>
        <button onClick={runReview} disabled={!!busy}>{busy ?? "Run wealth-manager review"}</button>
      </header>
      {error && <p role="alert">{error}</p>}

      {perf && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
          <Stat label="Reviews" value={String(perf.scorecard.reviews)} />
          <Stat label="Hit rate vs SPY" value={pct(perf.scorecard.hit_rate)} />
          <Stat label="Avg excess return" value={pct(perf.scorecard.avg_excess_return)} />
          <Stat label="Advice delta (all reviews)" value={usd(perf.scorecard.advice_delta_usd_total)} />
        </div>
      )}

      {review && (
        <article>
          <h3>Latest review · {review.created_at.slice(0, 10)} · book {usd(review.total_value_usd)}</h3>
          <p>{review.summary}</p>
          <Findings title="Allocation" items={review.allocation_findings} />
          <Findings title="Risk" items={review.risk_findings} />
          <Findings title="Tax" items={review.tax_findings} />
          {review.data_gaps.length > 0 && <Findings title="Data gaps" items={review.data_gaps} />}
          {review.watchlist.length > 0 && <p>Watchlist: {review.watchlist.join(", ")}</p>}
        </article>
      )}

      <h3>Open recommendations</h3>
      <table>
        <thead><tr><th>Action</th><th>Symbol</th><th>Account</th><th>Amount</th><th>Price</th><th>Confidence</th><th>Why</th><th /></tr></thead>
        <tbody>
          {open.map((r) => (
            <tr key={r.id}>
              <td>{r.action.toUpperCase()}{r.is_new_position ? " (new)" : ""}</td>
              <td>{r.symbol}</td><td>{r.resolved_account_id ?? "–"}</td>
              <td>{usd(r.amount_usd)}</td><td>{r.price_at_rec ?? "–"}</td><td>{pct(r.confidence)}</td>
              <td>{r.rationale}{r.tax_note && <em> · {r.tax_note}</em>}</td>
              <td>
                <button onClick={() => decide(r.id, "accepted")}>Did it</button>{" "}
                <button onClick={() => decide(r.id, "rejected")}>Skip</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {perf?.reviews.filter((p) => p.status === "ok").map((p) => (
        <details key={p.review_id}>
          <summary>
            Since {p.since}: your book {pct(p.actual_return)} · advised book {pct(p.hypothetical_return)} · SPY {pct(p.benchmark_return)} · advice delta {usd(p.advice_delta_usd)}
          </summary>
          <table>
            <thead><tr><th>Call</th><th>Then</th><th>Now</th><th>Symbol</th><th>SPY</th><th>Excess</th><th>Hit</th></tr></thead>
            <tbody>
              {p.recommendations?.map((s) => (
                <tr key={s.id}><td>{s.action} {s.symbol}</td><td>{s.price_at_rec}</td><td>{s.price_now ?? "–"}</td>
                  <td>{pct(s.symbol_return)}</td><td>{pct(s.benchmark_return)}</td><td>{pct(s.excess)}</td><td>{s.hit == null ? "–" : s.hit ? "✓" : "✗"}</td></tr>
              ))}
            </tbody>
          </table>
        </details>
      ))}
    </section>
  );
}

const Stat = ({ label, value }: { label: string; value: string }) => (
  <div><div style={{ fontSize: 12, opacity: 0.7 }}>{label}</div><div style={{ fontSize: 22 }}>{value}</div></div>
);
const Findings = ({ title, items }: { title: string; items: string[] }) =>
  items.length ? (<><h4>{title}</h4><ul>{items.map((i, n) => <li key={n}>{i}</li>)}</ul></>) : null;
