/**
 * Queues and plays TTS audio frames (PCM int16, 16kHz, mono) with gapless playback.
 */

export class AudioPlayback {
  private audioContext: AudioContext | null = null;
  private queue: ArrayBuffer[] = [];
  private isPlaying = false;
  private nextStartTime = 0;

  async start(): Promise<void> {
    if (this.audioContext) return;
    this.audioContext = new AudioContext({ sampleRate: 16000 });
    this.nextStartTime = this.audioContext.currentTime;
  }

  enqueue(pcm: ArrayBuffer): void {
    if (!this.audioContext) {
      console.warn("AudioPlayback not started");
      return;
    }

    this.queue.push(pcm);

    if (!this.isPlaying) {
      this.isPlaying = true;
      this.processQueue();
    }
  }

  private processQueue(): void {
    if (!this.audioContext || this.queue.length === 0) {
      this.isPlaying = false;
      return;
    }

    const pcm = this.queue.shift()!;
    const samples = pcm.byteLength / 2;
    const audioBuffer = this.audioContext.createBuffer(1, samples, 16000);
    const channelData = audioBuffer.getChannelData(0);

    // Convert int16 to float32
    const view = new DataView(pcm);
    for (let i = 0; i < samples; i++) {
      const int16 = view.getInt16(i * 2, true); // little-endian
      channelData[i] = int16 / (int16 < 0 ? 0x8000 : 0x7fff);
    }

    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext.destination);

    // Schedule for gapless playback
    const now = this.audioContext.currentTime;
    const startTime = Math.max(now, this.nextStartTime);
    source.start(startTime);
    this.nextStartTime = startTime + audioBuffer.duration;

    source.onended = () => {
      this.processQueue();
    };
  }

  stop(): void {
    this.queue = [];
    this.isPlaying = false;
    this.audioContext?.close();
    this.audioContext = null;
    this.nextStartTime = 0;
  }
}
