/**
 * Captures microphone audio and downsamples to 16kHz mono PCM int16.
 * Emits 20ms chunks (320 samples at 16kHz) as ArrayBuffer.
 */

const CHUNK_SIZE = 320; // 20ms at 16kHz

export class AudioCapture {
  private audioContext: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private processor: ScriptProcessorNode | null = null;
  private isCapturing = false;
  private buffer: number[] = [];

  constructor(private onChunk: (pcm: ArrayBuffer) => void) {}

  async start(): Promise<void> {
    if (this.isCapturing) return;

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: { ideal: 16000 },
        echoCancellation: true,
        noiseSuppression: true,
      },
    });

    this.audioContext = new AudioContext({ sampleRate: 16000 });
    this.source = this.audioContext.createMediaStreamSource(this.stream);

    // ScriptProcessorNode is deprecated but AudioWorklet requires separate file
    // For Phase 1 MVP, ScriptProcessorNode is acceptable
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    this.processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);

      // Convert float32 [-1, 1] to int16 [-32768, 32767]
      for (let i = 0; i < inputData.length; i++) {
        const s = Math.max(-1, Math.min(1, inputData[i]));
        this.buffer.push(s < 0 ? s * 0x8000 : s * 0x7fff);
      }

      // Emit 20ms chunks
      while (this.buffer.length >= CHUNK_SIZE) {
        const chunk = this.buffer.splice(0, CHUNK_SIZE);
        const pcm = new ArrayBuffer(chunk.length * 2);
        const view = new DataView(pcm);

        for (let i = 0; i < chunk.length; i++) {
          view.setInt16(i * 2, chunk[i], true); // little-endian
        }

        this.onChunk(pcm);
      }
    };

    this.source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
    this.isCapturing = true;
  }

  stop(): void {
    if (!this.isCapturing) return;

    this.processor?.disconnect();
    this.source?.disconnect();
    this.audioContext?.close();
    this.stream?.getTracks().forEach((track) => track.stop());

    this.processor = null;
    this.source = null;
    this.audioContext = null;
    this.stream = null;
    this.buffer = [];
    this.isCapturing = false;
  }
}
