import { useCallback, useEffect, useRef, useState } from "react";

export type CallStatus = "idle" | "connecting" | "active" | "ended" | "error";

export interface TranscriptItem {
  type: "asr_partial" | "asr_final" | "agent_text";
  text: string;
  sequence?: number;
  node_name?: string;
  turn_index?: number;
}

export interface CallMetrics {
  turn_count: number;
  duration_s: number;
  last_latency?: {
    asr_ms?: number;
    llm_ms?: number;
    tts_first_byte_ms?: number;
    e2e_ms?: number;
  };
}

export interface VoiceCallConfig {
  apiBaseUrl: string;
  callId: string;
  customerId: string;
  product: string;
  agentName: string;
  lenderName: string;
  customerName: string;
  onAudioFrame?: (pcm: ArrayBuffer) => void;
}

export function useVoiceCall(config: VoiceCallConfig) {
  const [status, setStatus] = useState<CallStatus>("idle");
  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  const [metrics, setMetrics] = useState<CallMetrics>({
    turn_count: 0,
    duration_s: 0,
  });
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = config.apiBaseUrl.replace(/^http/, "ws");
    const ws = new WebSocket(`${wsUrl}/ws/call/${config.callId}`);
    wsRef.current = ws;

    ws.binaryType = "arraybuffer";
    setStatus("connecting");
    setError(null);

    ws.onopen = () => {
      startTimeRef.current = Date.now();
      const startMsg = {
        type: "start_call",
        call_id: config.callId,
        customer_id: config.customerId,
        product: config.product,
        agent_name: config.agentName,
        lender_name: config.lenderName,
        customer_name: config.customerName,
      };
      ws.send(JSON.stringify(startMsg));

      // Ping keepalive every 15s
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 15000);
    };

    ws.onmessage = (event) => {
      if (typeof event.data === "string") {
        const msg = JSON.parse(event.data);

        switch (msg.type) {
          case "call_accepted":
            setStatus("active");
            break;

          case "asr_partial":
            setTranscript((prev) => {
              const filtered = prev.filter((t) => t.type !== "asr_partial");
              return [
                ...filtered,
                { type: "asr_partial", text: msg.text, sequence: msg.sequence },
              ];
            });
            break;

          case "asr_final":
            setTranscript((prev) => {
              const filtered = prev.filter((t) => t.type !== "asr_partial");
              return [
                ...filtered,
                { type: "asr_final", text: msg.text, sequence: msg.sequence },
              ];
            });
            break;

          case "agent_text":
            setTranscript((prev) => [
              ...prev,
              {
                type: "agent_text",
                text: msg.text,
                node_name: msg.node_name,
                turn_index: msg.turn_index,
              },
            ]);
            break;

          case "turn_end":
            setMetrics((prev) => ({
              ...prev,
              turn_count: msg.turn_index + 1,
              last_latency: msg.latency,
            }));
            break;

          case "call_ended":
            console.log("[useVoiceCall] call_ended received:", msg);
            setStatus("ended");
            setMetrics((prev) => ({
              ...prev,
              turn_count: msg.turn_count || prev.turn_count,
              duration_s: msg.duration_s || prev.duration_s,
            }));
            if (pingIntervalRef.current) {
              clearInterval(pingIntervalRef.current);
              pingIntervalRef.current = null;
            }
            break;

          case "error":
            setError(`${msg.code}: ${msg.message}`);
            setStatus("error");
            break;

          case "pong":
            // Keepalive response, no action needed
            break;

          default:
            console.warn("Unknown message type:", msg.type);
        }
      } else {
        // Binary frame: TTS audio with 0x01 prefix
        const buffer = event.data as ArrayBuffer;
        if (buffer.byteLength > 0) {
          const view = new Uint8Array(buffer);
          if (view[0] === 0x01) {
            // Strip prefix and forward PCM
            const pcm = buffer.slice(1);
            config.onAudioFrame?.(pcm);
          }
        }
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection error");
      setStatus("error");
    };

    ws.onclose = () => {
      if (status === "active") {
        setStatus("ended");
        const elapsed = (Date.now() - startTimeRef.current) / 1000;
        setMetrics((prev) => ({ ...prev, duration_s: elapsed }));
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
    };
  }, [config, status]);

  const sendAudio = useCallback((pcm: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(pcm);
    }
  }, []);

  const endCall = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "end_call",
          call_id: config.callId,
          reason: "user_hangup",
        })
      );
      wsRef.current.close();
    }
    setStatus("ended");
  }, [config.callId]);

  useEffect(() => {
    return () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
    };
  }, []);

  return {
    status,
    transcript,
    metrics,
    error,
    connect,
    sendAudio,
    endCall,
  };
}
