"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { type CallDetail, type CallsResponse, type FollowUpsResponse, type OpsSummary, apiUrl, fetchJson } from "@/lib/api";

const channels = ["whatsapp", "sms", "email"] as const;

export default function OpsPage() {
  const [selectedCallId, setSelectedCallId] = useState<string>("");
  const [channel, setChannel] = useState<(typeof channels)[number]>("whatsapp");
  const [preview, setPreview] = useState("");
  const [recipient, setRecipient] = useState("");
  const [deliveryState, setDeliveryState] = useState("");
  const [errorState, setErrorState] = useState("");

  const { data } = useQuery({
    queryKey: ["analytics", "ops"],
    queryFn: () => fetchJson<OpsSummary>("/api/analytics/ops"),
    refetchInterval: 30_000,
  });
  const { data: calls } = useQuery({
    queryKey: ["calls", "ops-shortlist"],
    queryFn: () => fetchJson<CallsResponse>("/api/calls?limit=20"),
  });
  const { data: tasks, refetch: refetchTasks } = useQuery({
    queryKey: ["followups"],
    queryFn: () => fetchJson<FollowUpsResponse>("/api/followups"),
  });
  const { data: detail } = useQuery({
    queryKey: ["call-detail-ops", selectedCallId],
    queryFn: () => fetchJson<CallDetail>(`/api/calls/${selectedCallId}`),
    enabled: Boolean(selectedCallId),
  });

  const suggestedRecipient = useMemo(() => {
    if (!detail) {
      return "";
    }
    const slots = detail.slots_redacted ?? {};
    const candidateKeys = channel === "email"
      ? ["email", "email_address", "customer_email"]
      : ["phone", "phone_number", "mobile", "mobile_number", "customer_phone", "contact_number"];
    for (const key of candidateKeys) {
      const value = slots[key];
      if (typeof value === "string" && value.trim()) {
        return value.trim();
      }
    }
    return "";
  }, [channel, detail]);

  useEffect(() => {
    setPreview("");
    setDeliveryState("");
    setErrorState("");
  }, [selectedCallId, channel]);

  useEffect(() => {
    setRecipient(suggestedRecipient);
  }, [suggestedRecipient]);

  function validateInputs(requireRecipient: boolean) {
    if (!selectedCallId) {
      setErrorState("Select a call first.");
      return false;
    }
    if (requireRecipient && !recipient.trim()) {
      setErrorState(channel === "email" ? "Enter a recipient email address." : "Enter a recipient phone number.");
      return false;
    }
    setErrorState("");
    return true;
  }

  async function generatePreview() {
    if (!validateInputs(false)) return;
    const response = await fetch(apiUrl("/api/followups/preview"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ call_id: selectedCallId, channel }),
    });
    const payload = await response.json();
    if (!response.ok) {
      setErrorState(payload.detail ?? "Preview failed.");
      return;
    }
    setPreview(payload.preview ?? "");
  }

  async function schedule() {
    if (!validateInputs(true)) return;
    const response = await fetch(apiUrl("/api/followups/schedule"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        call_id: selectedCallId,
        channel,
        recipient,
        scheduled_for: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      setErrorState(payload.detail ?? "Scheduling failed.");
      return;
    }
    await refetchTasks();
    setDeliveryState("scheduled");
  }

  async function sendNow() {
    if (!validateInputs(true)) return;
    setDeliveryState("sending");
    const response = await fetch(apiUrl("/api/followups/dispatch"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ call_id: selectedCallId, channel, recipient }),
    });
    const payload = await response.json();
    if (!response.ok) {
      setDeliveryState(payload.detail ?? "delivery_failed");
      return;
    }
    setDeliveryState(`sent via ${payload.provider ?? "provider"}`);
    await refetchTasks();
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Stat title="High Priority" value={data?.high_priority_calls ?? 0} />
        <Stat title="Follow-up Queue" value={data?.follow_up_queue ?? 0} />
        <Stat title="Handoff Queue" value={data?.handoff_queue ?? 0} />
        <Stat title="Avg Lead Score" value={data?.avg_lead_score ?? 0} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[420px_1fr]">
        <div className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold">Multi-Channel Follow-up</h2>
          <div className="mt-5 space-y-4">
            <select
              value={selectedCallId}
              onChange={(e) => setSelectedCallId(e.target.value)}
              className="w-full rounded-md border border-slate-200 p-3"
            >
              <option value="">Select call</option>
              {calls?.calls.map((call) => (
                <option key={call.call_id} value={call.call_id}>
                  {call.call_id} · {call.product} · {call.outcome ?? "unknown"}
                </option>
              ))}
            </select>
            {!calls?.calls.length && (
              <p className="text-sm text-amber-700">No saved calls yet. Complete one call first so follow-up actions have context.</p>
            )}
            <select
              value={channel}
              onChange={(e) => setChannel(e.target.value as (typeof channels)[number])}
              className="w-full rounded-md border border-slate-200 p-3"
            >
              {channels.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <label className="block text-sm font-medium text-slate-700">
              Recipient {channel === "email" ? "Email" : "Phone"}
            </label>
            <input
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              placeholder={channel === "email" ? "recipient@example.com" : "+919876543210"}
              className="w-full rounded-md border border-slate-200 p-3"
            />
            {suggestedRecipient && (
              <p className="text-xs text-slate-500">Auto-filled from saved call details. You can edit it before sending.</p>
            )}
            <div className="flex gap-3">
              <button type="button" onClick={generatePreview} className="rounded-md bg-slate-900 px-4 py-3 font-semibold text-white">
                Preview
              </button>
              <button type="button" onClick={sendNow} className="rounded-md bg-blue-600 px-4 py-3 font-semibold text-white">
                Send Now
              </button>
              <button type="button" onClick={schedule} className="rounded-md bg-emerald-600 px-4 py-3 font-semibold text-white">
                Schedule Callback
              </button>
            </div>
            {errorState && <div className="rounded-md bg-rose-50 p-3 text-sm text-rose-700">{errorState}</div>}
            {preview && <div className="rounded-md bg-slate-50 p-4 text-sm text-slate-700">{preview}</div>}
            {deliveryState && <div className="text-sm text-slate-600">{deliveryState}</div>}
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Selected Lead Context</h2>
            {!detail ? (
              <p className="mt-4 text-sm text-slate-500">Choose a call to inspect follow-up context.</p>
            ) : (
              <div className="mt-4 space-y-3">
                <p className="text-sm text-slate-700">{detail.intelligence.summary}</p>
                <p className="text-sm text-slate-600">
                  Action: {detail.intelligence.follow_up_action}
                </p>
                <div className="flex flex-wrap gap-2">
                  {detail.intelligence.objections.map((item) => (
                    <span key={item} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                      {item.replaceAll("_", " ")}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="rounded-md border border-[#c9d6cf] bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Scheduled Tasks</h2>
            <div className="mt-4 space-y-3">
              {tasks?.tasks.length ? (
                tasks.tasks.map((task) => (
                  <div key={task.task_id} className="rounded-md border border-slate-200 p-3">
                    <p className="font-medium text-slate-900">{task.task_id} · {task.channel}</p>
                    <p className="text-sm text-slate-500">{task.call_id} · {new Date(task.scheduled_for).toLocaleString()}</p>
                    {task.recipient && <p className="text-sm text-slate-500">{task.recipient}</p>}
                    {task.provider && <p className="text-xs text-slate-400">{task.provider} · {task.status}</p>}
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">No follow-ups scheduled yet.</p>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
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
