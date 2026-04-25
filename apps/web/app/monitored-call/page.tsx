"use client";

import { useEffect, useRef, useState } from "react";
import { Mic, MicOff, Radio, Phone, PhoneOff, Copy, Check } from "lucide-react";
import Link from "next/link";

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
}

export default function MonitoredCallPage() {
  const [callId] = useState(`call_${Date.now()}`);
  const [isActive, setIsActive] = useState(false);
  const [isSetup, setIsSetup] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptTurn[]>([]);
  const [nudges, setNudges] = useState<Nudge[]>([]);
  const [copiedCallId, setCopiedCallId] = useState(false);

  // User info (with localStorage persistence)
  const [agentName, setAgentName] = useState(
    typeof window !== "undefined" ? localStorage.getItem("agentName") || "" : ""
  );
  const [customerName, setCustomerName] = useState(
    typeof window !== "undefined" ? localStorage.getItem("customerName") || "" : ""
  );
  const [role, setRole] = useState<"agent" | "customer">(
    (typeof window !== "undefined" ? localStorage.getItem("role") as "agent" | "customer" : null) || "agent"
  );

  const wsRef = useRef<WebSocket | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  const handleCopyCallId = async () => {
    try {
      await navigator.clipboard.writeText(callId);
      setCopiedCallId(true);
      setTimeout(() => setCopiedCallId(false), 2000);
    } catch (err) {
      console.error("Copy failed:", err);
    }
  };

  const startCall = async () => {
    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
      });
      mediaStreamRef.current = stream;

      // Setup audio processing
      const audioContext = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      // Connect to supervisor WebSocket
      const supervisorUrl = process.env.NEXT_PUBLIC_SUPERVISOR_URL || "http://localhost:8001";
      const wsUrl = supervisorUrl.replace(/^http/, "ws");

      const ws = new WebSocket(`${wsUrl}/ws/supervisor/monitored/${callId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[MonitoredCall] Connected");
        setIsActive(true);

        // Send audio chunks to supervisor
        processor.onaudioprocess = (e) => {
          if (ws.readyState === WebSocket.OPEN && !isMuted) {
            const inputData = e.inputBuffer.getChannelData(0);
            const pcm = new Int16Array(inputData.length);

            // Convert float32 to int16
            for (let i = 0; i < inputData.length; i++) {
              const s = Math.max(-1, Math.min(1, inputData[i]));
              pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
            }

            ws.send(pcm.buffer);
          }
        };

        source.connect(processor);
        processor.connect(audioContext.destination);
      };

      ws.onmessage = (e) => {
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
            setNudges((prev) => [msg, ...prev].slice(0, 10));
          }
        } catch (err) {
          console.error("[MonitoredCall] Parse error:", err);
        }
      };

      ws.onerror = () => {
        console.error("[MonitoredCall] WebSocket error");
        stopCall();
      };

      ws.onclose = () => {
        console.log("[MonitoredCall] Disconnected");
        stopCall();
      };

    } catch (err) {
      console.error("[MonitoredCall] Mic access error:", err);
      alert("Microphone access required");
    }
  };

  const stopCall = () => {
    // Stop audio processing
    processorRef.current?.disconnect();
    audioContextRef.current?.close();

    // Stop mic stream
    mediaStreamRef.current?.getTracks().forEach(track => track.stop());

    // Close WebSocket
    wsRef.current?.close();

    setIsActive(false);
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  // Save to localStorage when changed
  useEffect(() => {
    if (agentName) localStorage.setItem("agentName", agentName);
  }, [agentName]);

  useEffect(() => {
    if (customerName) localStorage.setItem("customerName", customerName);
  }, [customerName]);

  useEffect(() => {
    localStorage.setItem("role", role);
  }, [role]);

  useEffect(() => {
    return () => {
      stopCall();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800">
      <div className="container mx-auto p-6 max-w-7xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard/supervisor"
              className="p-3 hover:bg-white/10 rounded-xl transition border border-white/10"
            >
              <Radio className="w-5 h-5 text-white" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-white">Monitored Call</h1>
              <p className="text-sm text-slate-400 mt-1">
                Real-time transcription with AI nudges
              </p>
            </div>
          </div>

          {isActive && (
            <div className="flex items-center gap-3">
              <button
                onClick={toggleMute}
                className={`p-3 rounded-xl transition ${
                  isMuted
                    ? "bg-red-500/20 border border-red-500"
                    : "bg-white/5 border border-white/10 hover:bg-white/10"
                }`}
              >
                {isMuted ? (
                  <MicOff className="w-5 h-5 text-red-400" />
                ) : (
                  <Mic className="w-5 h-5 text-white" />
                )}
              </button>
              <button
                onClick={stopCall}
                className="px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl font-semibold transition flex items-center gap-2"
              >
                <PhoneOff className="w-5 h-5" />
                End Call
              </button>
            </div>
          )}
        </div>

        {/* Call ID Display */}
        {isActive && (
          <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-blue-400 font-semibold uppercase tracking-wide mb-1">
                  Call ID
                </p>
                <p className="text-white font-mono text-sm">{callId}</p>
              </div>
              <button
                onClick={handleCopyCallId}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition flex items-center gap-2"
              >
                {copiedCallId ? (
                  <>
                    <Check className="w-4 h-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {!isSetup ? (
          /* Setup Screen */
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="max-w-md w-full bg-slate-900/50 backdrop-blur border border-slate-700 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-6 text-center">
                Call Setup
              </h2>

              <div className="space-y-4">
                {/* Role Selection */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    You are:
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => setRole("agent")}
                      className={`p-3 rounded-lg font-medium transition ${
                        role === "agent"
                          ? "bg-blue-600 text-white"
                          : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                      }`}
                    >
                      🎙️ Agent
                    </button>
                    <button
                      onClick={() => setRole("customer")}
                      className={`p-3 rounded-lg font-medium transition ${
                        role === "customer"
                          ? "bg-green-600 text-white"
                          : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                      }`}
                    >
                      👤 Customer
                    </button>
                  </div>
                </div>

                {/* Agent Name */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Agent Name
                  </label>
                  <input
                    type="text"
                    value={agentName}
                    onChange={(e) => setAgentName(e.target.value)}
                    placeholder="Enter agent name"
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Customer Name */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Customer Name
                  </label>
                  <input
                    type="text"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    placeholder="Enter customer name"
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <button
                  onClick={() => {
                    if (agentName.trim() && customerName.trim()) {
                      setIsSetup(true);
                    }
                  }}
                  disabled={!agentName.trim() || !customerName.trim()}
                  className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition"
                >
                  Continue to Call
                </button>
              </div>
            </div>
          </div>
        ) : !isActive ? (
          /* Start Screen */
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="text-center">
              <div className="w-32 h-32 mx-auto mb-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center shadow-2xl">
                <Phone className="w-16 h-16 text-white" />
              </div>
              <div className="mb-6">
                <p className="text-slate-400 text-sm mb-2">Calling as:</p>
                <p className="text-2xl font-bold text-white">
                  {role === "agent" ? `🎙️ ${agentName}` : `👤 ${customerName}`}
                </p>
              </div>
              <h2 className="text-2xl font-bold text-white mb-3">
                Ready to Start Monitored Call
              </h2>
              <p className="text-slate-400 mb-8 max-w-md mx-auto">
                Your conversation will be transcribed in real-time with speaker separation
                and AI-powered contextual nudges
              </p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={() => setIsSetup(false)}
                  className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-semibold transition"
                >
                  Back
                </button>
                <button
                  onClick={startCall}
                  className="px-8 py-4 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white rounded-xl font-bold shadow-2xl transition transform hover:scale-105"
                >
                  Start Call
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Active Call UI */
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Left: Transcript */}
            <div className="border border-slate-700 rounded-xl bg-slate-900/50 backdrop-blur flex flex-col h-[calc(100vh-16rem)]">
              <div className="px-6 py-4 border-b border-slate-700 bg-slate-800/50">
                <h2 className="text-lg font-semibold text-white">Live Transcript</h2>
                <p className="text-xs text-slate-400 mt-1">
                  Speaker-separated • Azure Speech Services
                </p>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-3">
                {transcript.length === 0 ? (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-slate-500 text-sm">Start speaking...</p>
                  </div>
                ) : (
                  transcript.map((turn, i) => (
                    <div
                      key={i}
                      className={`p-4 rounded-lg border-l-4 ${
                        turn.speaker === "agent"
                          ? "bg-blue-500/10 border-blue-500"
                          : "bg-green-500/10 border-green-500"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-semibold uppercase text-slate-400">
                          {turn.speaker === "agent" ? `🎙️ ${agentName}` : `👤 ${customerName}`}
                        </span>
                        <span className="text-xs text-slate-500">
                          {new Date(turn.timestamp * 1000).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm text-white leading-relaxed">{turn.text}</p>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Right: Nudges */}
            <div className="border border-amber-700 rounded-xl bg-amber-950/30 backdrop-blur flex flex-col h-[calc(100vh-16rem)]">
              <div className="px-6 py-4 border-b border-amber-700 bg-amber-900/30">
                <h2 className="text-lg font-semibold text-amber-100">AI Nudges</h2>
                <p className="text-xs text-amber-300 mt-1">
                  Contextual suggestions in real-time
                </p>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {nudges.length === 0 ? (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-amber-400/50 text-sm">No nudges yet...</p>
                  </div>
                ) : (
                  nudges.map((nudge, i) => (
                    <div
                      key={i}
                      className={`p-4 rounded-lg border-l-4 shadow-lg ${
                        nudge.priority === 1
                          ? "bg-red-500/20 border-red-500"
                          : nudge.priority === 2
                            ? "bg-amber-500/20 border-amber-500"
                            : "bg-blue-500/20 border-blue-500"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-bold uppercase bg-black/30 px-2 py-1 rounded text-white">
                          {nudge.route.replace(/_/g, " ")}
                        </span>
                        <span className="text-xs text-slate-300">
                          {(nudge.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <h3 className="font-semibold text-white mb-2">{nudge.title}</h3>
                      <p className="text-sm text-slate-200 leading-relaxed">
                        {nudge.suggestion}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
