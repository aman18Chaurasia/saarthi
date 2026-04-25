# Configuration Examples

Quick reference for switching between TTS and ASR providers in SAARTHI.

## Example 1: Azure for Both TTS and STT (Recommended)

Update your `.env` file:

```bash
# TTS
TTS_PROVIDER=azure
AZURE_SPEECH_KEY=your-azure-key-here
AZURE_SPEECH_REGION=eastus
AZURE_SPEECH_VOICE=en-IN-NeerjaNeural

# ASR
ASR_PROVIDER=azure
```

**Pros:**
- Single Azure subscription handles both audio tasks
- Consistent quality
- India-optimized voices available

**Cons:**
- Additional API call for STT
- Slightly higher latency for ASR compared to Groq

## Example 2: Azure TTS + Groq ASR (Cost Optimized)

Update your `.env` file:

```bash
# TTS
TTS_PROVIDER=azure
AZURE_SPEECH_KEY=your-azure-key-here
AZURE_SPEECH_REGION=eastus
AZURE_SPEECH_VOICE=en-IN-NeerjaNeural

# ASR - Keep Groq (faster, free tier available)
ASR_PROVIDER=groq
GROQ_API_KEY=your-groq-key-here
GROQ_WHISPER_MODEL=whisper-large-v3
```

**Pros:**
- Groq has very fast ASR
- Balance between quality and cost
- Both free tiers available

**Cons:**
- Need both API keys

## Example 3: ElevenLabs TTS + Groq ASR (Current Default)

```bash
# TTS
TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=your-elevenlabs-key-here
ELEVENLABS_VOICE_ID=Rachel

# ASR
ASR_PROVIDER=groq
GROQ_API_KEY=your-groq-key-here
GROQ_WHISPER_MODEL=whisper-large-v3
```

**Pros:**
- No changes needed - already configured
- ElevenLabs has natural voices
- Groq has very fast ASR

**Cons:**
- Different APIs to manage
- Higher per-character cost for TTS

## Example 4: Development/Testing (Mock TTS)

```bash
# TTS - Silent for testing
TTS_PROVIDER=mock

# ASR - Groq Whisper
ASR_PROVIDER=groq
GROQ_API_KEY=your-groq-key-here
```

**Pros:**
- No TTS API calls = faster testing
- Saves API costs during development
- Focuses on dialog logic testing

## Testing Each Configuration

### Via Web UI

1. Update `.env` file
2. Restart API server: `cd apps/api && python -m uvicorn main:app --reload`
3. Open http://localhost:3000/call in browser
4. Speak into microphone and listen for response

### Via cURL (Twilio)

```bash
# Make outbound call
curl -X POST http://localhost:8000/call/outbound \
  -H "Content-Type: application/json" \
  -d '{
    "customer_phone": "+919876543210",
    "product": "personal_loan",
    "agent_name": "Priya",
    "lender_name": "Demo Bank",
    "customer_name": "Rahul"
  }'
```

### Verify Configuration

Check which providers are active:

```bash
# Check logs
tail -f logs/*.log | grep -i "provider\|azure\|groq\|elevenlabs"

# Check environment variables
grep "TTS_PROVIDER\|ASR_PROVIDER" .env
```

## Performance Comparison

| Configuration | STT Latency | TTS Latency | Total Latency | Monthly Cost (Moderate Use) |
|---|---|---|---|---|
| Azure + Azure | 300ms | 500ms | 800ms | $0 (free tier) |
| Groq + Azure | 100ms | 500ms | 600ms | $0 (free tiers) |
| Groq + ElevenLabs | 100ms | 300ms | 400ms | $5-20 |
| Groq + XTTS | 100ms | 1000ms+ | 1100ms+ | $0 (self-hosted) |

**Note:** Latencies are approximate and depend on network conditions.

## Switching Providers at Runtime

The provider selection happens at **import time**, so you must:

1. Stop the server
2. Update `.env`
3. Restart the server

```bash
# Kill current server
# Ctrl+C in the terminal

# Update .env
nano .env

# Restart server
python -m uvicorn main:app --reload
```

No code changes needed - just environment variables!

## Troubleshooting Provider Issues

### "Unknown TTS_PROVIDER" Error

**Error Message:**
```
ValueError: Unknown TTS_PROVIDER='xyz'. Valid values: elevenlabs, hf_space, azure
```

**Fix:**
- Check spelling in `.env`: `TTS_PROVIDER=azure` (not `Azure` or `AZURE`)
- Valid values are lowercase

### "Missing AZURE_SPEECH_KEY" Error

**Error Message:**
```
KeyError: 'AZURE_SPEECH_KEY'
```

**Fix:**
- Set `TTS_PROVIDER=elevenlabs` if using ElevenLabs instead
- Or add Azure key to `.env`: `AZURE_SPEECH_KEY=xxx`

### "Invalid subscription key" Error

**Error Message:**
```
TTSAPIError: Azure Speech API error 401
```

**Fix:**
- Verify API key is correct (copy-paste carefully)
- Check region matches where key was created
- Try creating a new key in Azure portal

## Environment Variable Reference

### TTS Configuration

| Variable | Provider | Required | Example |
|---|---|---|---|
| `TTS_PROVIDER` | All | Yes | `azure`, `elevenlabs`, `hf_space`, `mock` |
| `AZURE_SPEECH_KEY` | Azure | If TTS_PROVIDER=azure | `abc123...` |
| `AZURE_SPEECH_REGION` | Azure | If TTS_PROVIDER=azure | `eastus`, `westus`, `southcentralus` |
| `AZURE_SPEECH_VOICE` | Azure | No (default: en-IN-NeerjaNeural) | `en-IN-NeerjaNeural`, `en-US-AriaNeural` |
| `ELEVENLABS_API_KEY` | ElevenLabs | If TTS_PROVIDER=elevenlabs | `sk_...` |
| `ELEVENLABS_VOICE_ID` | ElevenLabs | If TTS_PROVIDER=elevenlabs | `Rachel`, `7qBNUtXRGP0jPi0H4r8k` |
| `HF_SPACE_XTTS_URL` | XTTS | If TTS_PROVIDER=hf_space | `https://huggingface.co/spaces/...` |

### ASR Configuration

| Variable | Provider | Required | Example |
|---|---|---|---|
| `ASR_PROVIDER` | All | No (default: groq) | `groq`, `azure` |
| `AZURE_SPEECH_KEY` | Azure | If ASR_PROVIDER=azure | `abc123...` |
| `AZURE_SPEECH_REGION` | Azure | If ASR_PROVIDER=azure | `eastus`, `westus` |
| `GROQ_API_KEY` | Groq | If ASR_PROVIDER=groq | `gsk_...` |
| `GROQ_WHISPER_MODEL` | Groq | No (default: whisper-large-v3) | `whisper-large-v3`, `whisper-large` |

## Quick Start

1. **Default (ElevenLabs + Groq):**
   - Just set API keys in `.env`
   - No TTS_PROVIDER or ASR_PROVIDER needed

2. **Switch to Azure:**
   ```bash
   TTS_PROVIDER=azure
   ASR_PROVIDER=azure
   AZURE_SPEECH_KEY=your-key
   AZURE_SPEECH_REGION=eastus
   ```

3. **Restart and test:**
   ```bash
   # Kill and restart server
   python -m uvicorn main:app --reload
   
   # Test in browser
   http://localhost:3000/call
   ```

Done! Audio will now use Azure for both TTS and STT.
