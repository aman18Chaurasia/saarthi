"use client";

import { useEffect, useRef, useState } from "react";
import { Transcript } from "./transcript";
import { useVoiceCall } from "@/lib/useVoiceCall";
import { AudioCapture } from "@/lib/audio-capture";
import { AudioPlayback } from "@/lib/audio-playback";

export default function CallPage() {
  const [isInitialized, setIsInitialized] = useState(false);
  const audioCaptureRef = useRef<AudioCapture | null>(null);
  const audioPlaybackRef = useRef<AudioPlayback | null>(null);

  const callId = `call_${Date.now()}`;

  const voiceCall = useVoiceCall({
    apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    callId,
    customerId: "demo_customer",
    product: "personal_loan",
    agentName: "Priya",
    lenderName: "Demo Bank",
    customerName: "Rahul",
    onAudioFrame: (pcm) => {
      audioPlaybackRef.current?.enqueue(pcm);
    },
  });

  useEffect(() => {
    if (voiceCall.status === "active" && !isInitialized) {
      setIsInitialized(true);

      // Start mic capture (playback already started in handleStartCall)
      audioCaptureRef.current = new AudioCapture((pcm) => {
        voiceCall.sendAudio(pcm);
      });
      audioCaptureRef.current.start().catch(console.error);
    }

    if (voiceCall.status === "ended" && isInitialized) {
      audioCaptureRef.current?.stop();
      audioPlaybackRef.current?.stop();
      setIsInitialized(false);
    }
  }, [voiceCall.status, voiceCall.sendAudio, isInitialized]);

  useEffect(() => {
    return () => {
      audioCaptureRef.current?.stop();
      audioPlaybackRef.current?.stop();
    };
  }, []);

  const handleStartCall = async () => {
    // Start audio playback BEFORE connecting (user interaction required for AudioContext)
    audioPlaybackRef.current = new AudioPlayback();
    await audioPlaybackRef.current.start();

    voiceCall.connect();
  };

  const handleEndCall = () => {
    voiceCall.endCall();
  };

  return (
    <main className="container mx-auto p-6 max-w-4xl">
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Voice Call Demo</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Personal Loan Qualification - Phase 1 MVP
            </p>
          </div>

          <div className="flex gap-3">
            {voiceCall.status === "idle" && (
              <button
                type="button"
                onClick={handleStartCall}
                className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 font-medium"
              >
                Start Call
              </button>
            )}

            {voiceCall.status === "connecting" && (
              <button
                type="button"
                disabled
                className="px-6 py-2 bg-muted text-muted-foreground rounded-md cursor-not-allowed font-medium"
              >
                Connecting...
              </button>
            )}

            {voiceCall.status === "active" && (
              <button
                type="button"
                onClick={handleEndCall}
                className="px-6 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 font-medium"
              >
                End Call
              </button>
            )}
          </div>
        </div>

        {voiceCall.error && (
          <div className="p-4 bg-destructive/10 border border-destructive rounded-md">
            <p className="text-sm text-destructive font-medium">Error: {voiceCall.error}</p>
          </div>
        )}

        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Live Transcript</h2>
            {voiceCall.status === "active" && (
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm text-muted-foreground">Recording</span>
              </div>
            )}
          </div>

          <Transcript items={voiceCall.transcript} />
        </div>

        {voiceCall.status === "ended" && (
          <div className="p-6 bg-card border rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Call Ended</h2>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Total Turns</p>
                <p className="text-2xl font-bold">{voiceCall.metrics.turn_count}</p>
              </div>

              <div>
                <p className="text-muted-foreground">Duration</p>
                <p className="text-2xl font-bold">
                  {voiceCall.metrics.duration_s.toFixed(1)}s
                </p>
              </div>

              {voiceCall.metrics.last_latency && (
                <>
                  <div>
                    <p className="text-muted-foreground">ASR Latency</p>
                    <p className="text-lg font-semibold">
                      {voiceCall.metrics.last_latency.asr_ms?.toFixed(0) || "N/A"}ms
                    </p>
                  </div>

                  <div>
                    <p className="text-muted-foreground">LLM Latency</p>
                    <p className="text-lg font-semibold">
                      {voiceCall.metrics.last_latency.llm_ms?.toFixed(0) || "N/A"}ms
                    </p>
                  </div>

                  <div>
                    <p className="text-muted-foreground">TTS First Byte</p>
                    <p className="text-lg font-semibold">
                      {voiceCall.metrics.last_latency.tts_first_byte_ms?.toFixed(0) || "N/A"}ms
                    </p>
                  </div>

                  <div>
                    <p className="text-muted-foreground">End-to-End</p>
                    <p className="text-lg font-semibold">
                      {voiceCall.metrics.last_latency.e2e_ms?.toFixed(0) || "N/A"}ms
                    </p>
                  </div>
                </>
              )}
            </div>

            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-6 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 font-medium w-full"
            >
              Start New Call
            </button>
          </div>
        )}

        {voiceCall.status === "active" && (
          <div className="p-4 bg-muted/50 rounded-md">
            <p className="text-xs text-muted-foreground">
              Call ID: {callId} • Product: Personal Loan • Customer: Rahul • Agent: Priya
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
