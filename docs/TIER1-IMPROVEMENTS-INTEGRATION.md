# Tier 1 Improvements Integration Guide

**Status:** ✅ Modules Created  
**Next:** Integration into existing pipeline

---

## What Was Built

### 1. **ConversationMemory** (`packages/dialog/dialog/memory_manager.py`)
- Full conversation history with embeddings
- Semantic retrieval of relevant past turns
- Automatic key fact extraction (objections, interests, preferences)
- Context-aware question detection

### 2. **SentimentAnalyzer** (`packages/voice/sentiment_analyzer.py`)
- Text + audio sentiment analysis
- Emotion classification (frustrated, confused, interested, etc.)
- Adaptive response guidance
- TTS parameter adjustments based on emotion

### 3. **Smart Retry Logic** (`packages/dialog/dialog/personal_loan/prompts.py`)
- Dynamic rephrasing (3 variants per node)
- Retry-aware system prompts
- No more asking same question 3 times!

### 4. **SmartVAD** (`apps/api/frame_processors/smart_vad.py`)
- Filler detection ("um", "uh" → ignore)
- Backchannel detection ("haan", "okay" → acknowledge but continue)
- Real interruption detection

---

## Integration Steps

### Step 1: Update DialogState to Include Memory

```python
# packages/dialog/dialog/personal_loan/state.py

from dialog.memory_manager import ConversationMemory

class DialogState(BaseModel):
    # ... existing fields ...
    
    # NEW: Add memory manager (not persisted, runtime only)
    conversation_memory: ConversationMemory = Field(
        default_factory=ConversationMemory,
        exclude=True  # Don't serialize
    )
    
    # NEW: Current sentiment
    current_sentiment: dict[str, float] | None = None
```

### Step 2: Update Nodes to Use Memory & Sentiment

```python
# packages/dialog/dialog/personal_loan/nodes.py

from voice.sentiment_analyzer import SentimentAnalyzer

# Initialize sentiment analyzer (do this once at module level)
_sentiment_analyzer = SentimentAnalyzer()

async def _build_messages(state: DialogState, node_name: str) -> list[dict[str, str]]:
    """Updated to use memory and sentiment."""
    
    # Analyze sentiment from customer's last utterance
    sentiment = None
    if state.asr_text:
        sentiment = await _sentiment_analyzer.analyze(state.asr_text)
        sentiment_guidance = await _sentiment_analyzer.get_adaptive_response_guidance(sentiment)
    else:
        sentiment_guidance = ""
    
    # Retrieve relevant context from long-term memory
    memory_context = ""
    if state.conversation_memory:
        memory_context = await state.conversation_memory.retrieve_relevant_context(
            query=state.asr_text,
            max_turns=3
        )
        
        # Add key facts summary
        facts = state.conversation_memory.get_key_facts_summary()
        if facts:
            memory_context += "\n\n" + facts
    
    # Build messages with enhanced context
    return build_messages(
        agent_name=state.agent_name,
        lender_name=state.lender_name,
        customer_name=state.customer_name,
        node_name=node_name,
        asr_text=state.asr_text,
        history=state.history,
        retry_count=state.retry_count,
        sentiment_guidance=sentiment_guidance,
        memory_context=memory_context,
    )


async def identity_confirm_node(state: DialogState, llm_fn: LLMCallable) -> DialogState:
    """Updated node with memory tracking."""
    
    # Add customer turn to memory BEFORE LLM call
    if state.asr_text and state.conversation_memory:
        await state.conversation_memory.add_turn(
            speaker="customer",
            text=state.asr_text,
            node_name="identity_confirm",
            turn_index=state.turn_index,
        )
    
    # Call LLM (now with memory context)
    resp = await _call_llm(llm_fn, state, "identity_confirm")
    
    # ... rest of existing logic ...
    
    # Add agent turn to memory
    if state.conversation_memory:
        await state.conversation_memory.add_turn(
            speaker="agent",
            text=resp.agent_turn_text,
            node_name="identity_confirm",
            turn_index=ti,
        )
    
    # Save sentiment to state
    if state.asr_text:
        sentiment = await _sentiment_analyzer.analyze(state.asr_text)
        new_slots = new_slots.model_copy(update={
            "current_sentiment": sentiment.model_dump()
        })
    
    return state.model_copy(update={
        "current_node": "identity_confirm",
        "history": history,
        "slots": new_slots,
        "retry_count": 0 if useful else state.retry_count + 1,
        "turn_index": ti,
    })
```

**Repeat for all node functions:**
- `qualify_node`
- `qualify_followup_node`
- `consent_node`
- `next_step_node`
- `close_node`

### Step 3: Integrate SmartVAD into Pipeline

```python
# apps/api/pipeline.py

from .frame_processors.smart_vad import SmartVAD
from .frame_processors.vad_processor import VADProcessor  # existing

def build_pipeline(...):
    # ... existing setup ...
    
    # Create quick transcribe function for SmartVAD
    async def quick_transcribe(audio_bytes: bytes) -> str:
        """Fast transcription for filler detection."""
        # Use Groq Whisper with shorter timeout
        # or local faster-whisper model
        result = await groq_client.audio.transcriptions.create(
            file=("audio.wav", _pcm_to_wav(audio_bytes)),
            model="whisper-large-v3-turbo",  # faster variant
        )
        return result.text
    
    # Replace VADProcessor with SmartVAD wrapper
    base_vad = VADProcessor()
    smart_vad = SmartVAD(
        transcribe_fn=quick_transcribe,
        base_vad=base_vad
    )
    
    # Build pipeline with smart_vad instead of base_vad
    pipeline = Pipeline([
        smart_vad,  # ← NEW
        ASRProcessor(...),
        LangGraphProcessor(...),
        TTSProcessor(...),
    ])
```

### Step 4: Add Sentiment-Adaptive TTS

```python
# apps/api/frame_processors/tts_processor.py

from voice.sentiment_analyzer import SentimentAnalyzer

class TTSProcessor(FrameProcessor):
    def __init__(self, tts_provider, sentiment_analyzer: SentimentAnalyzer | None = None):
        super().__init__()
        self.tts_provider = tts_provider
        self.sentiment_analyzer = sentiment_analyzer
    
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        # ... existing code ...
        
        if isinstance(frame, TextFrame):
            text = frame.text
            
            # Get sentiment from frame metadata (set by LangGraphProcessor)
            sentiment_dict = frame.metadata.get("sentiment")
            
            # Get TTS adjustments based on sentiment
            adjustments = {"rate": 1.0, "pitch_shift": 0, "energy": 1.0}
            if sentiment_dict and self.sentiment_analyzer:
                from voice.sentiment_analyzer import Sentiment
                sentiment = Sentiment(**sentiment_dict)
                adjustments = self.sentiment_analyzer.get_tts_adjustments(sentiment)
            
            # Stream TTS with adjustments
            async for audio_chunk in self.tts_provider.stream(
                text,
                rate=adjustments["rate"],
                pitch_shift=adjustments["pitch_shift"],
                energy=adjustments["energy"],
            ):
                await self.push_frame(
                    TTSAudioRawFrame(...),
                    direction
                )
```

### Step 5: Pass Sentiment in TextFrame Metadata

```python
# apps/api/frame_processors/langgraph_processor.py

async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
    # ... existing code ...
    
    if isinstance(frame, TranscriptionFrame):
        # ... existing ainvoke ...
        
        agent_text = _extract_agent_text(result)
        if agent_text:
            text_frame = TextFrame(text=agent_text)
            text_frame.metadata["node_name"] = result.get("current_node", "unknown")
            text_frame.metadata["turn_index"] = result.get("turn_index", 0)
            
            # NEW: Add sentiment to metadata
            sentiment_dict = result.get("current_sentiment")
            if sentiment_dict:
                text_frame.metadata["sentiment"] = sentiment_dict
            
            await self.push_frame(text_frame, direction)
```

---

## Testing the Improvements

### Test 1: Filler Detection
```python
# Terminal 1: Start API
make api

# Terminal 2: Test call
# Say: "um... uh... yes, I'm interested"
# Expected: Agent doesn't stop for "um" and "uh"
```

### Test 2: Emotion Adaptation
```python
# Say: "This is too expensive! I can't afford it!"
# Expected: 
# - Agent detects frustration
# - Responds with empathy
# - TTS slows down, lower pitch (calming)
```

### Test 3: Smart Retry
```python
# Agent: "Aapki monthly income kitni hai?"
# You: "What?" (unclear)
# Agent: "Boliye, aap mahine mein roughly kitna kamate hain?" (different phrasing!)
```

### Test 4: Memory Recall
```python
# Turn 5: "I need loan for travel"
# Turn 15: Agent: "You mentioned travel earlier - we have special rates for that!"
# (Agent remembers from 10 turns ago)
```

---

## Performance Considerations

### Latency Impact

| Feature | Added Latency | Mitigation |
|---------|--------------|------------|
| Sentiment Analysis | ~50ms | Heuristic-based, no LLM call |
| Memory Retrieval | ~30ms | Cache embeddings, limit to 3 turns |
| SmartVAD Transcription | ~200ms | Use faster-whisper or turbo model |
| **Total** | ~280ms | Still well under 600ms target |

### Memory Usage

- ConversationMemory: ~1KB per turn, ~50KB for 50-turn conversation
- Embeddings (if used): ~3KB per turn (768-dim float32)
- **Total for 50 turns:** ~200KB (negligible)

---

## Rollout Plan

### Week 1: Core Integration
- [ ] Add ConversationMemory to DialogState
- [ ] Update all node functions to track memory
- [ ] Test memory retrieval in isolation

### Week 2: Sentiment Integration
- [ ] Integrate SentimentAnalyzer into nodes
- [ ] Add sentiment-adaptive TTS
- [ ] Test emotion detection accuracy

### Week 3: SmartVAD
- [ ] Replace VADProcessor with SmartVAD
- [ ] Test filler detection
- [ ] Tune backchannel thresholds

### Week 4: Polish & Evaluate
- [ ] Run 100 test calls with personas
- [ ] Measure accuracy improvement
- [ ] Document results

---

## Expected Results

### Before (Baseline)
- Memory: 4 turns
- Retry: Same question 3x
- Interruption: Every sound stops agent
- Emotion: None
- **Qualification Rate:** 85%

### After (Tier 1)
- Memory: Full conversation + semantic search
- Retry: 3 different phrasings
- Interruption: Ignores fillers, detects intent
- Emotion: Real-time adaptation
- **Qualification Rate Target:** 90%+

---

## Next Steps (Tier 2)

Once Tier 1 is integrated and tested:

1. **Per-Customer Learning** - Save profiles to database
2. **Online DPO** - Update model after each call
3. **Proactive Objection Handling** - Predict and preempt
4. **Chain-of-Thought Planning** - LLM plans next moves

**Timeline:** 2-3 weeks for Tier 1 integration, then Tier 2 in parallel

---

## Questions? Issues?

See full documentation:
- `docs/MAKING-IT-WORLD-CLASS.md` - Complete roadmap
- `docs/PRODUCT-SCRIPTS-GUIDE.md` - Product scripts
- `docs/PRODUCTS-QUICK-REFERENCE.md` - Quick reference

**Status:** Ready for integration! 🚀
