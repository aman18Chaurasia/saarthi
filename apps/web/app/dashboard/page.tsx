"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, Clock, Gauge, PhoneCall, PhoneForwarded, ShieldAlert, TrendingUp, ArrowUp, ArrowDown } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { type AnalyticsSummary, fetchJson } from "@/lib/api";
import { motion } from "framer-motion";

const metrics = [
  { key: "total_calls", title: "Total Calls", suffix: "", icon: PhoneCall, trend: 12 },
  { key: "qualified_rate", title: "Success Rate", suffix: "%", icon: Activity, trend: 5 },
  { key: "avg_duration_s", title: "Avg Duration", suffix: "s", icon: Clock, trend: -3 },
  { key: "p95_latency", title: "P95 Latency", suffix: "ms", icon: Gauge, trend: -8 },
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
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent mb-2">
          Dashboard
        </h1>
        <p className="text-slate-400">Real-time analytics and insights</p>
      </div>

      {/* Metrics Grid */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4 mb-6">
        {metrics.map(({ key, title, suffix, icon: Icon, trend }, idx) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="p-6 bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl shadow-xl hover:bg-white/10 transition-all group"
          >
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-slate-400">{title}</p>
              <div className="p-2 bg-blue-500/20 rounded-lg group-hover:bg-blue-500/30 transition-colors">
                <Icon className="h-5 w-5 text-blue-400" aria-hidden="true" />
              </div>
            </div>

            <p className="text-4xl font-bold text-white mb-2">
              {isLoading ? (
                <span className="text-slate-600">...</span>
              ) : (
                `${data?.[key] ?? 0}${suffix}`
              )}
            </p>

            {/* Trend indicator */}
            {trend && (
              <div className={`flex items-center gap-1 text-xs font-medium ${
                trend > 0 ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {trend > 0 ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
                <span>{Math.abs(trend)}% vs last week</span>
              </div>
            )}
          </motion.div>
        ))}
      </section>

      {/* Charts Section */}
      <section className="grid gap-6 lg:grid-cols-2 mb-6">
        {/* Latency Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="p-6 bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl shadow-xl"
        >
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Latency Profile</h2>
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400 px-3 py-1 bg-slate-800/50 rounded-full">
              E2E ms
            </span>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.8} />
                    <stop offset="100%" stopColor="#8B5CF6" stopOpacity={0.6} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                <XAxis dataKey="name" stroke="#94A3B8" fontSize={12} />
                <YAxis stroke="#94A3B8" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Bar dataKey="latency" fill="url(#barGradient)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Qualification Stats */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="p-6 bg-gradient-to-br from-blue-500/10 to-violet-500/10 backdrop-blur-md border border-blue-500/20 rounded-2xl shadow-glow"
        >
          <h2 className="text-lg font-semibold text-white mb-4">Qualification Snapshot</h2>
          <p className="text-6xl font-bold text-white mb-2">{data?.qualified_count ?? 0}</p>
          <p className="text-sm text-slate-400 mb-6">
            qualified calls out of <span className="text-white font-semibold">{data?.total_calls ?? 0}</span>
          </p>

          {/* Progress bar */}
          <div className="h-3 overflow-hidden rounded-full bg-white/10 mb-4">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(data?.qualified_rate ?? 0, 100)}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-green-500 shadow-glowGreen"
            />
          </div>

          {/* Additional stats */}
          <div className="grid grid-cols-2 gap-4 mt-6">
            <div className="p-3 bg-white/5 rounded-lg border border-white/10">
              <p className="text-xs text-slate-400 mb-1">Follow-ups</p>
              <p className="text-xl font-bold text-white">{data?.follow_up_queue ?? 0}</p>
            </div>
            <div className="p-3 bg-white/5 rounded-lg border border-white/10">
              <p className="text-xs text-slate-400 mb-1">Handoffs</p>
              <p className="text-xl font-bold text-white">{data?.handoff_queue ?? 0}</p>
            </div>
          </div>

          {error && (
            <p className="mt-4 text-sm text-red-400 px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-lg">
              Analytics API unavailable
            </p>
          )}
        </motion.div>
      </section>

      {/* Nudge Analytics (if available) */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="p-6 bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl shadow-xl"
      >
        <h2 className="text-lg font-semibold text-white mb-4">💡 Nudge Effectiveness</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-white/5 rounded-xl border border-white/10">
            <p className="text-3xl font-bold text-white mb-1">85%</p>
            <p className="text-xs text-slate-400">Viewed Rate</p>
          </div>
          <div className="text-center p-4 bg-white/5 rounded-xl border border-white/10">
            <p className="text-3xl font-bold text-white mb-1">62%</p>
            <p className="text-xs text-slate-400">Usage Rate</p>
          </div>
          <div className="text-center p-4 bg-white/5 rounded-xl border border-white/10">
            <p className="text-3xl font-bold text-white mb-1">91%</p>
            <p className="text-xs text-slate-400">Helpfulness</p>
          </div>
          <div className="text-center p-4 bg-white/5 rounded-xl border border-white/10">
            <p className="text-3xl font-bold text-white mb-1">1,247</p>
            <p className="text-xs text-slate-400">Total Nudges</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
