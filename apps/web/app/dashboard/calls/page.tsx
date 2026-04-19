"use client";

import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { type CallsResponse, fetchJson, productLabel } from "@/lib/api";

const products = [
  "personal_loan",
  "home_loan",
  "education_loan",
  "gold_loan",
  "credit_card",
  "unsecured_loan",
  "lap_secured",
  "commercial_vehicle",
  "four_wheeler",
  "msme_business",
];

export default function CallHistoryPage() {
  const [product, setProduct] = useState("");
  const [outcome, setOutcome] = useState("");

  const queryPath = useMemo(() => {
    const params = new URLSearchParams();
    if (product) params.set("product", product);
    if (outcome) params.set("outcome", outcome);
    return `/api/calls${params.toString() ? `?${params}` : ""}`;
  }, [product, outcome]);

  const { data, isLoading } = useQuery({
    queryKey: ["calls", product, outcome],
    queryFn: () => fetchJson<CallsResponse>(queryPath),
  });

  return (
    <div className="space-y-5">
      <section className="rounded-md border border-[#c9d6cf] bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-semibold">Call History</h2>
            <p className="text-sm text-[#5d6b65]">{data?.total ?? 0} matching calls</p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <FilterSelect value={product} onChange={setProduct} label="Product">
              <option value="">All products</option>
              {products.map((item) => (
                <option key={item} value={item}>
                  {productLabel(item)}
                </option>
              ))}
            </FilterSelect>
            <FilterSelect value={outcome} onChange={setOutcome} label="Outcome">
              <option value="">All outcomes</option>
              <option value="qualified">Qualified</option>
              <option value="not_qualified">Not qualified</option>
              <option value="dropped">Dropped</option>
              <option value="no_consent">No consent</option>
            </FilterSelect>
          </div>
        </div>
      </section>

      <section className="overflow-hidden rounded-md border border-[#c9d6cf] bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-[#d7e0db] text-sm">
            <thead className="bg-[#f5f7f5] text-left text-xs uppercase tracking-[0.12em] text-[#5d6b65]">
              <tr>
                <th className="px-4 py-3">Call</th>
                <th className="px-4 py-3">Product</th>
                <th className="px-4 py-3">Outcome</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">Turns</th>
                <th className="px-4 py-3">Started</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#edf1ee]">
              {data?.calls.map((call) => (
                <tr key={call.call_id} className="hover:bg-[#f8faf8]">
                  <td className="px-4 py-3 font-medium text-[#111816]">{call.call_id}</td>
                  <td className="px-4 py-3 text-[#5d6b65]">{productLabel(call.product)}</td>
                  <td className="px-4 py-3">
                    <span className="rounded-sm bg-[#e7f0eb] px-2 py-1 text-xs font-medium text-[#22533d]">
                      {call.outcome ?? "unknown"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[#5d6b65]">{call.duration_s ?? 0}s</td>
                  <td className="px-4 py-3 text-[#5d6b65]">{call.turn_count}</td>
                  <td className="px-4 py-3 text-[#5d6b65]">
                    {new Date(call.started_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {!isLoading && data?.calls.length === 0 && (
          <div className="flex items-center justify-center gap-2 px-4 py-10 text-sm text-[#5d6b65]">
            <Search className="h-4 w-4" aria-hidden="true" />
            No calls match the current filters.
          </div>
        )}
      </section>
    </div>
  );
}

function FilterSelect({
  value,
  onChange,
  label,
  children,
}: {
  value: string;
  onChange: (value: string) => void;
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium uppercase tracking-[0.12em] text-[#5d6b65]">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 min-w-44 rounded-md border border-[#c9d6cf] bg-white px-3 text-sm normal-case tracking-normal text-[#111816]"
      >
        {children}
      </select>
    </label>
  );
}
