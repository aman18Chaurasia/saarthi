"use client";

import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { type ProductAnalytics, fetchJson, productLabel } from "@/lib/api";

export default function ProductsPage() {
  const { data = [], isLoading } = useQuery({
    queryKey: ["analytics", "by_product"],
    queryFn: () => fetchJson<ProductAnalytics[]>("/api/analytics/by_product"),
  });

  return (
    <div className="space-y-6">
      <section className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Product Performance</h2>
          <span className="text-xs font-medium uppercase tracking-[0.18em] text-[#5d6b65]">
            Calls by product
          </span>
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d7e0db" />
              <XAxis
                dataKey="product"
                stroke="#5d6b65"
                tickFormatter={(value) => productLabel(String(value)).replace(" Loan", "")}
              />
              <YAxis stroke="#5d6b65" />
              <Tooltip labelFormatter={(value) => productLabel(String(value))} />
              <Bar dataKey="call_count" fill="#2d6a4f" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="overflow-hidden rounded-md border border-[#c9d6cf] bg-white shadow-sm">
        <table className="min-w-full divide-y divide-[#d7e0db] text-sm">
          <thead className="bg-[#f5f7f5] text-left text-xs uppercase tracking-[0.12em] text-[#5d6b65]">
            <tr>
              <th className="px-4 py-3">Product</th>
              <th className="px-4 py-3">Calls</th>
              <th className="px-4 py-3">Qualified Rate</th>
              <th className="px-4 py-3">Avg Duration</th>
              <th className="px-4 py-3">Lead Score</th>
              <th className="px-4 py-3">Follow-ups</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#edf1ee]">
            {data.map((product) => (
              <tr key={product.product} className="hover:bg-[#f8faf8]">
                <td className="px-4 py-3 font-medium">{productLabel(product.product)}</td>
                <td className="px-4 py-3 text-[#5d6b65]">{product.call_count}</td>
                <td className="px-4 py-3 text-[#5d6b65]">{product.qualified_rate}%</td>
                <td className="px-4 py-3 text-[#5d6b65]">{product.avg_duration}s</td>
                <td className="px-4 py-3 text-[#5d6b65]">{product.avg_lead_score}</td>
                <td className="px-4 py-3 text-[#5d6b65]">{product.follow_up_queue}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {!isLoading && data.length === 0 && (
          <p className="px-4 py-10 text-center text-sm text-[#5d6b65]">
            No product analytics available.
          </p>
        )}
      </section>
    </div>
  );
}
