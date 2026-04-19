import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useVoiceCall } from "./useVoiceCall";

// Mock WebSocket
class MockWebSocket {
  public readyState: number = WebSocket.CONNECTING;
  public onopen: (() => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: (() => void) | null = null;
  public onclose: (() => void) | null = null;
  public binaryType: BinaryType = "arraybuffer";
  public sentMessages: (string | ArrayBuffer)[] = [];

  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.onopen?.();
    }, 0);
  }

  send(data: string | ArrayBuffer) {
    this.sentMessages.push(data);
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.();
  }

  // Helper to simulate server messages
  simulateMessage(data: string | ArrayBuffer) {
    const event = new MessageEvent("message", { data });
    this.onmessage?.(event);
  }
}

describe("useVoiceCall", () => {
  let mockWs: MockWebSocket;

  beforeEach(() => {
    vi.stubGlobal("WebSocket", vi.fn((url: string) => {
      mockWs = new MockWebSocket(url);
      return mockWs;
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllTimers();
  });

  it("transitions from idle → connecting → active on connect", async () => {
    const { result } = renderHook(() =>
      useVoiceCall({
        apiBaseUrl: "http://localhost:8000",
        callId: "test_call",
        customerId: "test_customer",
        product: "personal_loan",
        agentName: "Agent",
        lenderName: "Bank",
        customerName: "Customer",
      })
    );

    expect(result.current.status).toBe("idle");

    act(() => {
      result.current.connect();
    });

    await waitFor(() => {
      expect(result.current.status).toBe("connecting");
    });

    // Simulate call_accepted from server
    act(() => {
      mockWs.simulateMessage(JSON.stringify({ type: "call_accepted", call_id: "test_call" }));
    });

    await waitFor(() => {
      expect(result.current.status).toBe("active");
    });
  });

  it("accumulates transcript items correctly", async () => {
    const { result } = renderHook(() =>
      useVoiceCall({
        apiBaseUrl: "http://localhost:8000",
        callId: "test_call",
        customerId: "test_customer",
        product: "personal_loan",
        agentName: "Agent",
        lenderName: "Bank",
        customerName: "Customer",
      })
    );

    act(() => {
      result.current.connect();
    });

    await waitFor(() => {
      expect(result.current.status).toBe("connecting");
    });

    act(() => {
      mockWs.simulateMessage(JSON.stringify({ type: "call_accepted" }));
    });

    // ASR partial
    act(() => {
      mockWs.simulateMessage(
        JSON.stringify({ type: "asr_partial", text: "Hello", sequence: 1 })
      );
    });

    expect(result.current.transcript).toHaveLength(1);
    expect(result.current.transcript[0].type).toBe("asr_partial");
    expect(result.current.transcript[0].text).toBe("Hello");

    // ASR final replaces partial
    act(() => {
      mockWs.simulateMessage(
        JSON.stringify({ type: "asr_final", text: "Hello there", sequence: 1 })
      );
    });

    expect(result.current.transcript).toHaveLength(1);
    expect(result.current.transcript[0].type).toBe("asr_final");
    expect(result.current.transcript[0].text).toBe("Hello there");

    // Agent response
    act(() => {
      mockWs.simulateMessage(
        JSON.stringify({
          type: "agent_text",
          text: "Hi, how can I help?",
          node_name: "opener",
          turn_index: 0,
        })
      );
    });

    expect(result.current.transcript).toHaveLength(2);
    expect(result.current.transcript[1].type).toBe("agent_text");
  });

  it("updates metrics on turn_end and call_ended", async () => {
    const { result } = renderHook(() =>
      useVoiceCall({
        apiBaseUrl: "http://localhost:8000",
        callId: "test_call",
        customerId: "test_customer",
        product: "personal_loan",
        agentName: "Agent",
        lenderName: "Bank",
        customerName: "Customer",
      })
    );

    act(() => {
      result.current.connect();
    });

    await waitFor(() => expect(mockWs.readyState).toBe(WebSocket.OPEN));

    act(() => {
      mockWs.simulateMessage(JSON.stringify({ type: "call_accepted" }));
    });

    act(() => {
      mockWs.simulateMessage(
        JSON.stringify({
          type: "turn_end",
          turn_index: 2,
          latency: { asr_ms: 50, llm_ms: 120, tts_first_byte_ms: 60, e2e_ms: 230 },
        })
      );
    });

    expect(result.current.metrics.turn_count).toBe(3);
    expect(result.current.metrics.last_latency?.e2e_ms).toBe(230);

    act(() => {
      mockWs.simulateMessage(
        JSON.stringify({ type: "call_ended", turn_count: 5, duration_s: 42.3 })
      );
    });

    expect(result.current.status).toBe("ended");
    expect(result.current.metrics.duration_s).toBe(42.3);
  });

  it("handles binary TTS audio frames", async () => {
    const onAudioFrame = vi.fn();

    const { result } = renderHook(() =>
      useVoiceCall({
        apiBaseUrl: "http://localhost:8000",
        callId: "test_call",
        customerId: "test_customer",
        product: "personal_loan",
        agentName: "Agent",
        lenderName: "Bank",
        customerName: "Customer",
        onAudioFrame,
      })
    );

    act(() => {
      result.current.connect();
    });

    await waitFor(() => expect(mockWs.readyState).toBe(WebSocket.OPEN));

    // Simulate binary frame with 0x01 prefix
    const audioData = new Uint8Array([0x01, 0x10, 0x20, 0x30, 0x40]);
    act(() => {
      mockWs.simulateMessage(audioData.buffer);
    });

    expect(onAudioFrame).toHaveBeenCalledTimes(1);
    const receivedBuffer = onAudioFrame.mock.calls[0][0] as ArrayBuffer;
    const receivedView = new Uint8Array(receivedBuffer);

    // Should have stripped the 0x01 prefix
    expect(receivedView).toHaveLength(4);
    expect(receivedView[0]).toBe(0x10);
  });

  it("sets error status on error message", async () => {
    const { result } = renderHook(() =>
      useVoiceCall({
        apiBaseUrl: "http://localhost:8000",
        callId: "test_call",
        customerId: "test_customer",
        product: "personal_loan",
        agentName: "Agent",
        lenderName: "Bank",
        customerName: "Customer",
      })
    );

    act(() => {
      result.current.connect();
    });

    await waitFor(() => expect(mockWs.readyState).toBe(WebSocket.OPEN));

    act(() => {
      mockWs.simulateMessage(
        JSON.stringify({
          type: "error",
          code: "ASR_TIMEOUT",
          message: "Groq Whisper did not respond",
        })
      );
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error).toBe("ASR_TIMEOUT: Groq Whisper did not respond");
  });
});
