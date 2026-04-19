"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, Clock, Gauge, PhoneCall } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { type AnalyticsSummary, fetchJson } from "@/lib/api";

const metrics = [
  { key: "total_calls", title: "Total Calls", suffix: "", icon: PhoneCall },
  { key: "qualified_rate", title: "Qualified Rate", suffix: "%", icon: Activity },
  { key: "avg_duration_s", title: "Avg Duration", suffix: "s", icon: Clock },
  { key: "p95_latency", title: "p95 Latency", suffix: "ms", icon: Gauge },
] as const;

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: () => fetchJson<AnalyticsSummary>("/api/analytics/summary"),
    refetchInterval: 30_000,
  });

  const chartData = data
    ? [
        { name: "p50", latency: data.p50_latency },
        { name: "p95", latency: data.p95_latency },
      ]
    : [];

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map(({ key, title, suffix, icon: Icon }) => (
          <div key={key} className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-[#5d6b65]">{title}</p>
              <Icon className="h-4 w-4 text-[#2d6a4f]" aria-hidden="true" />
            </div>
            <p className="mt-3 text-3xl font-semibold tracking-tight">
              {isLoading ? "..." : `${data?.[key] ?? 0}${suffix}`}
            </p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Latency Profile</h2>
            <span className="text-xs font-medium uppercase tracking-[0.18em] text-[#5d6b65]">
              E2E ms
            </span>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#d7e0db" />
                <XAxis dataKey="name" stroke="#5d6b65" />
                <YAxis stroke="#5d6b65" />
                <Tooltip />
                <Bar dataKey="latency" fill="#2d6a4f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-md border border-[#c9d6cf] bg-[#11231f] p-5 text-white shadow-sm">
          <h2 className="text-lg font-semibold">Qualification Snapshot</h2>
          <p className="mt-6 text-5xl font-semibold">{data?.qualified_count ?? 0}</p>
          <p className="mt-2 text-sm text-white/70">qualified calls out of {data?.total_calls ?? 0}</p>
          <div className="mt-8 h-2 overflow-hidden rounded-full bg-white/15">
            <div
              className="h-full rounded-full bg-[#99c8b5]"
              style={{ width: `${Math.min(data?.qualified_rate ?? 0, 100)}%` }}
            />
          </div>
          {error && <p className="mt-5 text-sm text-red-200">Analytics API unavailable</p>}
        </div>
      </section>
    </div>
  );
}
