"use client";

import { useState } from "react";
import { apiUrl, type RecommendationResponse, productLabel } from "@/lib/api";

export default function RecommendPage() {
  const [customerNeed, setCustomerNeed] = useState("");
  const [income, setIncome] = useState("50000");
  const [hasCollateral, setHasCollateral] = useState(false);
  const [businessUse, setBusinessUse] = useState(false);
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    const response = await fetch(apiUrl("/api/recommendations/product"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_need: customerNeed,
        monthly_income_inr: Number(income),
        has_collateral: hasCollateral,
        business_use: businessUse,
      }),
    });
    setResult(await response.json());
    setLoading(false);
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
      <section className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Product Recommendation Engine</h2>
        <div className="mt-5 space-y-4">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Customer Need</span>
            <textarea
              value={customerNeed}
              onChange={(e) => setCustomerNeed(e.target.value)}
              className="min-h-32 w-full rounded-md border border-slate-200 p-3"
              placeholder="Example: I need funding for home renovation and wedding expenses"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Monthly Income</span>
            <input
              value={income}
              onChange={(e) => setIncome(e.target.value)}
              className="w-full rounded-md border border-slate-200 p-3"
            />
          </label>
          <label className="flex items-center gap-3 text-sm text-slate-700">
            <input type="checkbox" checked={hasCollateral} onChange={(e) => setHasCollateral(e.target.checked)} />
            Has collateral / property
          </label>
          <label className="flex items-center gap-3 text-sm text-slate-700">
            <input type="checkbox" checked={businessUse} onChange={(e) => setBusinessUse(e.target.checked)} />
            Business use case
          </label>
          <button
            type="button"
            onClick={submit}
            disabled={loading || !customerNeed.trim()}
            className="w-full rounded-md bg-primary px-4 py-3 font-semibold text-white disabled:opacity-50"
          >
            {loading ? "Recommending..." : "Recommend Product"}
          </button>
        </div>
      </section>

      <section className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
        {!result ? (
          <p className="text-sm text-slate-500">Run the recommender to see primary and secondary product fit.</p>
        ) : (
          <div className="space-y-5">
            <div>
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Primary Recommendation</p>
              <h3 className="mt-2 text-2xl font-semibold text-slate-900">
                {productLabel(result.recommended_product)}
              </h3>
              <p className="mt-2 text-sm text-slate-600">{result.reason}</p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <Metric label="Confidence" value={`${Math.round(result.confidence * 100)}%`} />
              <Metric label="Secondary Product" value={productLabel(result.secondary_product)} />
            </div>
            <a
              href={result.routing_target}
              className="inline-flex rounded-md bg-emerald-600 px-4 py-3 font-semibold text-white"
            >
              Route to Recommended Flow
            </a>
          </div>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-[0.14em] text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}
