"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Radio, StopCircle, AlertTriangle } from "lucide-react";

interface TranscriptTurn {
  speaker: string;
  text: string;
  timestamp: number;
}

interface Nudge {
  route: string;
  title: string;
  suggestion: string;
  priority: number;
  confidence: number;
  transcript: string;
  timestamp: number;
}

export function LiveTranscriptMonitor() {
  const searchParams = useSearchParams();
  const [callId, setCallId] = useState(searchParams?.get("call_id") || "");
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptTurn[]>([]);
  const [nudges, setNudges] = useState<Nudge[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startMonitoring = () => {
    if (!callId.trim()) {
      setError("Enter call ID");
      return;
    }

    setError(null);
    setTranscript([]);
    setNudges([]);

    const apiUrl = process.env.NEXT_PUBLIC_SUPERVISOR_URL || "http://localhost:8001";
    const wsUrl = apiUrl.replace(/^http/, "ws");
    const socket = new WebSocket(`${wsUrl}/ws/supervisor/feed/${callId.trim()}`);

    socket.onopen = () => {
      console.log("[Supervisor] Connected");
      setIsMonitoring(true);
    };

    socket.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);

        if (msg.type === "transcript") {
          setTranscript((prev) => [...prev, {
            speaker: msg.speaker,
            text: msg.text,
            timestamp: msg.timestamp,
          }]);
        }

        if (msg.type === "nudge") {
          setNudges((prev) => [msg, ...prev].slice(0, 10)); // Keep last 10
        }
      } catch (err) {
        console.error("[Supervisor] Parse error:", err);
      }
    };

    socket.onerror = () => {
      setError("WebSocket connection failed");
      setIsMonitoring(false);
    };

    socket.onclose = () => {
      console.log("[Supervisor] Disconnected");
      setIsMonitoring(false);
    };

    setWs(socket);
  };

  const stopMonitoring = () => {
    ws?.close();
    setWs(null);
    setIsMonitoring(false);
  };

  useEffect(() => {
    return () => {
      ws?.close();
    };
  }, [ws]);

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
        <div className="flex gap-3 items-center">
          <input
            type="text"
            placeholder="Enter Call ID to monitor (e.g. call_1234567890)"
            value={callId}
            onChange={(e) => setCallId(e.target.value)}
            disabled={isMonitoring}
            className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-slate-100 disabled:cursor-not-allowed"
          />
          {!isMonitoring ? (
            <button
              onClick={startMonitoring}
              className="px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition flex items-center gap-2"
            >
              <Radio className="w-4 h-4" />
              Start Monitoring
            </button>
          ) : (
            <button
              onClick={stopMonitoring}
              className="px-6 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition flex items-center gap-2"
            >
              <StopCircle className="w-4 h-4" />
              Stop
            </button>
          )}
        </div>

        {error && (
          <div className="mt-3 px-4 py-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <span className="text-sm text-red-700">{error}</span>
          </div>
        )}

        {isMonitoring && (
          <div className="mt-3 px-4 py-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-green-700">
                Monitoring call: {callId}
              </span>
            </div>
          </div>
        )}
      </div>

      {isMonitoring && (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Left: Transcript */}
          <div className="border border-slate-200 rounded-lg bg-white shadow-sm flex flex-col h-[700px]">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex-shrink-0">
              <h2 className="text-lg font-semibold text-slate-900">Live Transcript</h2>
              <p className="text-xs text-slate-500 mt-1">
                Real-time speaker-separated transcription
              </p>
            </div>
            <div className="p-6 space-y-3 overflow-y-auto flex-1">
              {transcript.length === 0 && (
                <div className="h-full flex items-center justify-center">
                  <p className="text-slate-400 text-sm">Waiting for transcript...</p>
                </div>
              )}
              {transcript.map((turn, i) => (
                <div
                  key={i}
                  className={`p-4 rounded-lg border-l-4 ${
                    turn.speaker === "agent"
                      ? "bg-blue-50 border-blue-500"
                      : "bg-green-50 border-green-500"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                      {turn.speaker === "agent" ? "🎙️ Agent" : "👤 Customer"}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(turn.timestamp * 1000).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm text-slate-900 leading-relaxed">{turn.text}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Nudges */}
          <div className="border border-slate-200 rounded-lg bg-white shadow-sm flex flex-col h-[700px]">
            <div className="px-6 py-4 border-b border-slate-200 bg-amber-50 flex-shrink-0">
              <h2 className="text-lg font-semibold text-amber-900">Real-time Nudges</h2>
              <p className="text-xs text-amber-700 mt-1">
                Contextual suggestions for agent
              </p>
            </div>
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              {nudges.length === 0 && (
                <div className="h-full flex items-center justify-center">
                  <p className="text-slate-400 text-sm">No nudges yet...</p>
                </div>
              )}
              {nudges.map((nudge, i) => (
                <div
                  key={i}
                  className={`p-4 rounded-lg border-l-4 shadow-sm ${
                    nudge.priority === 1
                      ? "bg-red-50 border-red-500"
                      : nudge.priority === 2
                        ? "bg-amber-50 border-amber-500"
                        : "bg-blue-50 border-blue-500"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold uppercase bg-white px-2 py-1 rounded border border-slate-200">
                      {nudge.route.replace(/_/g, " ")}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-600">
                        {(nudge.confidence * 100).toFixed(0)}%
                      </span>
                      {nudge.priority === 1 && (
                        <AlertTriangle className="w-4 h-4 text-red-600" />
                      )}
                    </div>
                  </div>
                  <h3 className="font-semibold text-slate-900 mb-2">{nudge.title}</h3>
                  <p className="text-sm text-slate-700 leading-relaxed mb-2">
                    {nudge.suggestion}
                  </p>
                  {nudge.transcript && (
                    <div className="mt-2 pt-2 border-t border-slate-200">
                      <p className="text-xs text-slate-500 italic">
                        Context: "{nudge.transcript}"
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
