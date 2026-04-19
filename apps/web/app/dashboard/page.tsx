"use client";

import { useQuery } from "@tanstack/react-query";

export default function DashboardPage() {
  const { data } = useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/analytics/summary`);
      return res.json();
    },
    refetchInterval: 30000,
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard Overview</h1>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard title="Total Calls" value={data?.total_calls ?? 0} />
        <MetricCard title="Qualified" value={`${data?.qualified_rate ?? 0}%`} />
        <MetricCard title="Avg Duration" value={`${data?.avg_duration_s ?? 0}s`} />
        <MetricCard title="p50 Latency" value={`${data?.p50_latency ?? 0}ms`} />
      </div>
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
        <dd className="mt-1 text-3xl font-semibold text-gray-900">{value}</dd>
      </div>
    </div>
  );
}
