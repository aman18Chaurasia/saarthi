"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Radio } from "lucide-react";
import { type SupervisorLiveResponse, fetchJson, productLabel } from "@/lib/api";
import { LiveTranscriptMonitor } from "@/components/supervisor/LiveTranscriptMonitor";

export default function SupervisorPage() {
  const [activeTab, setActiveTab] = useState<"overview" | "live">("overview");

  const { data, isLoading } = useQuery({
    queryKey: ["supervisor", "live"],
    queryFn: () => fetchJson<SupervisorLiveResponse>("/api/supervisor/live"),
    refetchInterval: 5000,
    enabled: activeTab === "overview",
  });

  return (
    <div className="space-y-6">
      {/* Tab Switcher */}
      <div className="flex gap-2 border-b border-slate-200">
        <button
          onClick={() => setActiveTab("overview")}
          className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium transition ${
            activeTab === "overview"
              ? "border-blue-500 text-blue-600"
              : "border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300"
          }`}
        >
          <Activity className="w-4 h-4" />
          Overview
        </button>
        <button
          onClick={() => setActiveTab("live")}
          className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium transition ${
            activeTab === "live"
              ? "border-blue-500 text-blue-600"
              : "border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300"
          }`}
        >
          <Radio className="w-4 h-4" />
          Live Monitor
        </button>
      </div>

      {/* Content */}
      {activeTab === "overview" && (
        <OverviewTab data={data} isLoading={isLoading} />
      )}

      {activeTab === "live" && (
        <LiveTranscriptMonitor />
      )}
    </div>
  );
}

function OverviewTab({
  data,
  isLoading,
}: {
  data: SupervisorLiveResponse | undefined;
  isLoading: boolean;
}) {
  return (
    <>
      <section className="grid gap-4 md:grid-cols-3">
        <Stat title="Active Calls" value={data?.active_calls.length ?? 0} />
        <Stat title="Watchlist" value={data?.watchlist.length ?? 0} />
        <Stat
          title="Flags Raised"
          value={(data?.active_calls ?? []).reduce((sum, call) => sum + call.compliance_flags.length, 0)}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Live Calls</h2>
            <span className="text-xs uppercase tracking-[0.16em] text-slate-500">5s refresh</span>
          </div>
          <div className="space-y-4">
            {!isLoading && !(data?.active_calls.length) && (
              <p className="text-sm text-slate-500">No active browser or Twilio calls right now.</p>
            )}
            {data?.active_calls.map((call) => (
              <div key={call.call_id} className="rounded-md border border-slate-200 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-slate-900">{call.call_id}</p>
                    <p className="text-sm text-slate-500">{productLabel(call.product)}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {call.compliance_flags.map((flag) => (
                      <span key={flag} className="rounded-full bg-amber-100 px-2 py-1 text-xs text-amber-800">
                        {flag.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="mt-3 space-y-2 rounded-md bg-slate-50 p-3">
                  {call.transcript_preview.map((turn, index) => (
                    <p key={`${turn.turn_index}-${index}`} className="text-sm text-slate-600">
                      <span className="font-medium text-slate-700">{turn.speaker}:</span> {turn.text}
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent Watchlist</h2>
            <span className="text-xs uppercase tracking-[0.16em] text-slate-500">handoff candidates</span>
          </div>
          <div className="space-y-3">
            {data?.watchlist.map((call) => (
              <div key={call.call_id} className="flex items-center justify-between rounded-md border border-slate-200 p-4">
                <div>
                  <p className="font-medium text-slate-900">{call.call_id}</p>
                  <p className="text-sm text-slate-500">{productLabel(call.product)} · {call.outcome ?? "unknown"}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-slate-900">{call.lead_score}</p>
                  <p className="text-xs text-slate-500">
                    {call.handoff_recommended ? "handoff" : "monitor"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

function Stat({ title, value }: { title: string; value: number }) {
  return (
    <div className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
