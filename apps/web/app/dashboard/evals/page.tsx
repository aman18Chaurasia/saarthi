"use client";

import { useQuery } from "@tanstack/react-query";
import { type EvalLabResponse, fetchJson, productLabel } from "@/lib/api";

export default function EvalsPage() {
  const { data } = useQuery({
    queryKey: ["evals", "lab"],
    queryFn: () => fetchJson<EvalLabResponse>("/api/evals/lab"),
  });

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric title="Total Personas" value={data?.total_personas ?? 0} />
        <Metric title="Baseline Accuracy" value={`${Math.round((data?.baseline_accuracy ?? 0) * 100)}%`} />
        <Metric title="Improved Accuracy" value={`${Math.round((data?.improved_accuracy ?? 0) * 100)}%`} />
        <Metric title="Win-rate Gain" value={`${data?.win_rate_gain ?? 0}%`} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <div className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold">Product Coverage</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {data?.products.map((item) => (
              <div key={item.product} className="rounded-md border border-slate-200 p-4">
                <p className="font-medium text-slate-900">{productLabel(item.product)}</p>
                <p className="mt-1 text-sm text-slate-500">{item.personas} personas</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold">Failure Clusters</h2>
          <div className="mt-4 space-y-3">
            {data?.failure_clusters.map((cluster) => (
              <div key={cluster.cluster} className="rounded-md border border-slate-200 p-4">
                <p className="font-medium text-slate-900">{cluster.cluster.replaceAll("_", " ")}</p>
                <p className="mt-1 text-sm text-slate-500">{cluster.count} observed patterns</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
