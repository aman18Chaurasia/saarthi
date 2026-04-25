# Azure Speech Service Integration Guide

This guide explains how to set up and use Azure Cognitive Services Speech for both Text-to-Speech (TTS) and Speech-to-Text (STT) in SAARTHI.

## Prerequisites

- Azure subscription (free tier available at https://azure.microsoft.com)
- Azure Cognitive Services Speech API key and region

## Setup Steps

### 1. Create Azure Speech Resource

1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new resource: "Speech"
3. Select your region (e.g., "East US")
4. Choose pricing tier (free tier includes 5,000 API calls/month for TTS)
5. After creation, go to "Keys and Endpoint" to get your API key and region

### 2. Update Environment Variables

Add these to your `.env` file:

```bash
# TTS Configuration
TTS_PROVIDER=azure
AZURE_SPEECH_KEY=<your-api-key>
AZURE_SPEECH_REGION=eastus  # Replace with your region
AZURE_SPEECH_VOICE=en-IN-NeerjaNeural  # Or any other supported voice

# ASR Configuration (optional - defaults to Groq)
ASR_PROVIDER=azure
# AZURE_SPEECH_KEY and AZURE_SPEECH_REGION are reused
```

### 3. Available Voices

Azure offers multiple voices. Here are some popular ones:

**Indian English (Recommended for SAARTHI):**
- `en-IN-NeerjaNeural` - Female (default)
- `en-IN-AmitNeural` - Male

**Other English variants:**
- `en-US-AriaNeural` - US English, female
- `en-GB-LibbyNeural` - British English, female
- `en-AU-NatashaNeural` - Australian English, female

For a full list of supported voices, see: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts

### 4. Test the Integration

#### Test UI Calls (WebSocket)

```bash
# Terminal 1: Start the API server
cd apps/api
python -m uvicorn main:app --reload

# Terminal 2: Open browser and navigate to
http://localhost:3000/call?product=personal_loan
```

#### Test Twilio Calls

```bash
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

## Architecture

### Text-to-Speech (TTS) Flow

```
Dialog LLM generates text
         ↓
    TTSProcessor (Pipecat)
         ↓
    AzureTTSProvider.stream()
         ↓
    Azure Speech Service API (REST)
         ↓
    PCM 16kHz audio chunks
         ↓
    UI: sent via WebSocket with prefix byte
    Twilio: converted to 8kHz mulaw, sent in media message
```

### Speech-to-Text (STT) Flow

```
Customer speaks (microphone input)
         ↓
    UI: captured as PCM 16kHz (AudioCapture)
    Twilio: received as 8kHz mulaw, converted to 16kHz PCM
         ↓
    VADProcessor (Voice Activity Detection)
         ↓
    ASRProcessor
         ↓
    AzureSTTProvider.transcribe() OR GroqProvider.transcribe()
         ↓
    Azure Speech Service API (REST) OR Groq API
         ↓
    Transcribed text
         ↓
    Dialog state machine
```

## Configuration Options

### TTS Providers

| Provider | TTS_PROVIDER Value | Cost | Notes |
|----------|-------------------|------|-------|
| ElevenLabs | `elevenlabs` (default) | 10k chars/month free | High quality, API key required |
| Azure | `azure` | $16/1M characters (free tier: 1M/month) | Fast, reliable, SSML support |
| XTTS v2 | `hf_space` | Free | Requires HuggingFace Space URL |
| Mock | `mock` | Free | Silent audio for testing |

### ASR Providers

| Provider | ASR_PROVIDER Value | Cost | Notes |
|----------|-------------------|------|-------|
| Groq | `groq` (default) | Free with API key | Fast Whisper API |
| Azure | `azure` | $1/hour audio (free tier: 5K calls/month) | Reliable, multilingual |

## Switching Providers

### Switch to Azure for TTS and Groq for ASR

```bash
TTS_PROVIDER=azure
ASR_PROVIDER=groq
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=eastus
GROQ_API_KEY=...
```

### Switch to Azure for Both TTS and ASR

```bash
TTS_PROVIDER=azure
ASR_PROVIDER=azure
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=eastus
```

### Fallback to ElevenLabs

```bash
TTS_PROVIDER=elevenlabs
ASR_PROVIDER=groq
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
GROQ_API_KEY=...
```

## Troubleshooting

### Azure API Errors

**Error: "Invalid subscription key or wrong API endpoint"**
- Verify `AZURE_SPEECH_KEY` is correct
- Check `AZURE_SPEECH_REGION` matches your resource region

**Error: "Service returned: 429 (Too Many Requests)"**
- Hitting rate limits
- Azure free tier: 300 requests/minute for TTS
- Upgrade to paid tier or implement caching

**Error: "Invalid voice name"**
- Check voice name spelling
- Verify voice is available in your region
- Use voice names from: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts

### Audio Quality Issues

**Latency Too High**
- Azure TTS first-byte latency: typically 200-500ms
- Check network connectivity
- Consider caching responses for common phrases

**Audio Cutting Out in Twilio**
- Ensure proper audio conversion (16kHz PCM → 8kHz mulaw)
- Twilio media stream requires continuous audio
- Avoid long pauses between audio chunks

## Monitoring and Metrics

The system records latency metrics for each component:

- **ASR latency** (`asr_ms`): Time to transcribe customer speech
- **LLM latency** (`llm_ms`): Time for dialog decision
- **TTS latency** (`tts_first_byte_ms`): Time for first audio byte
- **E2E latency** (`e2e_ms`): Total turn latency

View metrics at: `http://localhost:8000/metrics`

## Cost Estimation

### Azure Speech Services (Free Tier)
- TTS: 1M characters/month (first 12 months)
- STT: 5K audio minutes/month (first 12 months)
- Speech Translation: 1M characters/month

### After Free Tier
- TTS: $16 per 1M characters
- STT: $1 per hour of audio
- Typically: **₹0-500/month** for moderate usage

## Advanced Configuration

### Custom SSML

Azure supports SSML for more control over TTS output:

```xml
<speak version='1.0' xml:lang='en-IN'>
    <voice name='en-IN-NeerjaNeural'>
        <prosody rate='0.95' pitch='10%'>
            This is a sample sentence.
        </prosody>
    </voice>
</speak>
```

The provider automatically generates SSML with the configured voice and language.

### Language Support

For STT in languages other than English:

```bash
ASR_PROVIDER=azure
AZURE_SPEECH_LANGUAGE=hi-IN  # For Hindi
```

Supported languages:
- `hi-IN` - Hindi
- `ta-IN` - Tamil
- `te-IN` - Telugu
- `mr-IN` - Marathi
- `bn-IN` - Bengali
- `gu-IN` - Gujarati
- `kn-IN` - Kannada
- `ml-IN` - Malayalam
- `pa-IN` - Punjabi

## References

- [Azure Speech Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/)
- [Supported Languages and Voices](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts)
- [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/)
