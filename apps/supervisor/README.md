# Supervisor Service - Real-time Transcription & Nudges

Standalone service for live call monitoring with speaker diarization and contextual nudge generation.

## Architecture

```
Call Audio → Diarization → Transcript Stream → Nudge Pipeline → Supervisor UI
                              ↓
                         Redis Pub/Sub
                              ↓
                    Async Worker (nudge gen)
```

## Components

- **WebSocket Ingress** (`websocket.py`): Receives audio, diarizes, transcribes
- **Context Manager** (`services/context_manager.py`): Stores conversation history
- **Nudge Sidecar Pipeline** (`services/nudge_sidecar/`):
  - Router: Classifies intent (objection/product_question/compliance_risk)
  - Generator: Creates nudge suggestions
  - Policy: Dedupe, rate limit, confidence gate
  - Publisher: Emits to UI stream
- **Worker** (`worker.py`): Async processor consuming transcript chunks

## Setup

### 1. Install Dependencies

```bash
cd saarthi

# Python dependencies
uv add pyannote.audio pydub httpx redis

# System dependencies (for audio processing)
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html
```

### 2. Configure Environment

Add to `.env`:

```bash
# HuggingFace token for pyannote.audio
# Get from: https://huggingface.co/settings/tokens
# Accept user agreement: https://huggingface.co/pyannote/speaker-diarization-3.1
HF_TOKEN=hf_xxxxx

# Supervisor service URL
NEXT_PUBLIC_SUPERVISOR_URL=http://localhost:8001

# Redis (already configured)
REDIS_URL=redis://localhost:6379/0
```

### 3. Accept PyAnnote Model License

Visit https://huggingface.co/pyannote/speaker-diarization-3.1 and accept the user agreement.

## Running

### Terminal 1: Main API (existing)
```bash
cd saarthi/apps/api
uv run uvicorn main:app --port 8000
```

### Terminal 2: Supervisor API (NEW)
```bash
cd saarthi/apps/supervisor
uv run uvicorn main:app --port 8001
```

### Terminal 3: Nudge Worker (NEW)
```bash
cd saarthi/apps/supervisor
uv run python worker.py
```

### Terminal 4: Frontend
```bash
cd saarthi/apps/web
pnpm dev
```

## Usage

1. **Start monitoring**: Navigate to Dashboard → Supervisor → Live Monitor tab
2. **Enter call ID**: Input the call_id to monitor (e.g., `call_1234567890`)
3. **Click "Start Monitoring"**: WebSocket connects to supervisor feed
4. **View real-time**:
   - Left panel: Speaker-separated transcript
   - Right panel: Contextual nudges for agent

## API Endpoints

### WebSocket: `/ws/supervisor/feed/{call_id}`
Subscribe to transcript and nudge stream for a call.

**Messages sent to client:**
```json
// Transcript turn
{
  "type": "transcript",
  "speaker": "agent" | "customer",
  "text": "...",
  "timestamp": 1234567890.123
}

// Nudge suggestion
{
  "type": "nudge",
  "route": "OBJECTION" | "PRODUCT_QUESTION" | "COMPLIANCE_RISK",
  "title": "Brief title",
  "suggestion": "Action suggestion",
  "priority": 1-3,
  "confidence": 0.85,
  "transcript": "Customer context"
}
```

### WebSocket: `/ws/supervisor/ingress/{call_id}`
Send audio chunks for diarization and transcription.

**Audio format**: PCM int16 mono 16kHz

## Configuration

### Nudge Policy (in `services/nudge_sidecar/policy.py`)

```python
NudgePolicy(
    min_confidence=0.7,      # Min confidence to emit
    cooldown_sec=30,         # Min seconds between nudges
    dedupe_window_sec=300,   # Dedupe window (5 min)
)
```

### Routes (in `services/nudge_sidecar/router.py`)

- `OBJECTION`: Customer hesitant/refusing
- `PRODUCT_QUESTION`: Customer asks about loan details
- `COMPLIANCE_RISK`: Agent violating regulations
- `NONE`: Normal flow

## Testing

### Send Test Audio
```python
import websockets
import asyncio

async def test():
    uri = "ws://localhost:8001/ws/supervisor/ingress/call_test123"
    async with websockets.connect(uri) as ws:
        # Send PCM audio chunks
        with open("test_audio.pcm", "rb") as f:
            while chunk := f.read(4096):
                await ws.send(chunk)
                await asyncio.sleep(0.1)

asyncio.run(test())
```

### Monitor Feed
```python
async def monitor():
    uri = "ws://localhost:8001/ws/supervisor/feed/call_test123"
    async with websockets.connect(uri) as ws:
        while True:
            msg = await ws.recv()
            print(msg)

asyncio.run(monitor())
```

## Troubleshooting

### Diarization fails
- Verify HF_TOKEN set correctly
- Accept model license at https://huggingface.co/pyannote/speaker-diarization-3.1
- Check ffmpeg installed: `ffmpeg -version`

### No nudges generated
- Check Redis connection: `redis-cli ping`
- Verify worker running: Check worker.py logs
- Check confidence threshold in policy.py

### WebSocket connection fails
- Verify supervisor service running on port 8001
- Check CORS settings in main.py
- Verify NEXT_PUBLIC_SUPERVISOR_URL in .env

## Development

### Add New Nudge Route
1. Update `router.py`: Add route to SYSTEM_PROMPT
2. Update `generator.py`: Add generation method
3. Update frontend: Add route badge styling

### Tune Policy
Edit `services/nudge_sidecar/policy.py`:
- Adjust `min_confidence` (lower = more nudges)
- Adjust `cooldown_sec` (lower = more frequent)
- Adjust `dedupe_window_sec` (longer = stricter dedupe)

## Production Notes

- Use `wss://` (secure WebSocket) in production
- Add authentication to WebSocket endpoints
- Scale worker horizontally (multiple instances)
- Persist decisions to database for analytics
- Monitor Redis memory usage (context + markers)
