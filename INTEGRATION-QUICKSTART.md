# 🚀 Integration Quick-Start Guide

**Goal:** Connect all built features in the next 2-3 hours

---

## ⚡ 5-Minute Wins (Do These First!)

### 1. Enable Real Voice (2 minutes)

```bash
# Edit .env file
# Change line 26 from:
TTS_PROVIDER=mock
# To:
TTS_PROVIDER=elevenlabs

# Restart API
make api
```

**Test:** Start a call - agent should now SPEAK!

---

### 2. Ingest Knowledge Base (3 minutes)

```bash
# Make sure Qdrant is running
make up

# Run ingestion script
python -m rag.ingest

# Verify (should see ~10 documents)
curl http://localhost:6333/collections/saarthi_knowledge
```

**Test:** Knowledge base now has product info ready for retrieval!

---

## 🔧 30-Minute Integration (Core Features)

### 3. Connect RAG to Dialog Nodes

**File:** `packages/dialog/dialog/personal_loan/nodes_enhanced.py`

This file already exists! We need to USE it instead of `nodes.py`.

**Edit:** `packages/dialog/dialog/personal_loan/graph.py`

Find the import:
```python
from .nodes import opener, identity_confirm, qualify, ...
```

Change to:
```python
from .nodes_enhanced import opener, identity_confirm, qualify, ...
```

**Or create a wrapper node that uses RAG:**

```python
# Add to packages/dialog/dialog/personal_loan/nodes.py

from rag.retriever import retrieve_context

async def qualify_with_rag(
    state: DialogState,
    llm_fn: LLMCallable,
    rag_fn: RAGCallable | None = None,
) -> DialogState:
    """Qualify node enhanced with RAG for answering questions."""
    
    # Check if customer is asking a question
    asr_text = state.asr_text.lower()
    
    question_keywords = [
        "what", "how", "kya", "kaise", "kitna",
        "interest", "rate", "documents", "eligibility",
        "benefit", "feature", "charges"
    ]
    
    is_question = any(kw in asr_text for kw in question_keywords)
    
    if is_question and rag_fn:
        # Retrieve context from knowledge base
        context = await rag_fn(
            query=state.asr_text,
            product=state.product,
            top_k=3
        )
        
        # Add context to prompt
        messages = await _build_messages(state, "qualify")
        messages.append({
            "role": "system",
            "content": f"Relevant product information:\n{context}"
        })
        
        # Get LLM response with context
        response = await llm_fn(messages, "qualify", state.asr_text)
        
        # ... rest of node logic
    else:
        # Normal qualify flow
        return await qualify(state, llm_fn)
```

---

### 4. Enable Compliance Guardrail

**File:** `apps/api/pipeline.py`

Add after line 150:

```python
# Compliance Guardrail
from guardrail.compliance import check_compliance

class ComplianceProcessor(FrameProcessor):
    """Check agent responses for compliance before TTS."""
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, TextFrame):
            # Check compliance
            result = await check_compliance(
                text=frame.text,
                product=initial_state.product
            )
            
            if not result["compliant"]:
                logger.warning(f"Compliance violation: {result['violations']}")
                # Block this response
                return
        
        await self.push_frame(frame, direction)

# Add to pipeline (after LangGraph, before TTS)
pipeline = Pipeline([
    vad_processor,
    asr_processor,
    langgraph_processor,
    ComplianceProcessor(),  # ← ADD THIS
    tts_processor,
])
```

---

### 5. Add Objection Handling

**File:** `packages/dialog/dialog/personal_loan/nodes.py`

Add at top:
```python
from ..objection_predictor import ObjectionPredictor

_objection_predictor = ObjectionPredictor()
```

Modify qualify node:
```python
async def qualify(state: DialogState, llm_fn: LLMCallable) -> DialogState:
    # ... existing code ...
    
    # Check for objections
    is_objection, obj_type, response_text = _objection_predictor.handle_reactive_objection(
        customer_text=state.asr_text
    )
    
    if is_objection:
        logger.info(f"Detected objection: {obj_type}")
        
        # Return objection response instead of normal qualify
        return state.model_copy(update={
            "history": state.history + [
                TurnRecord(speaker="customer", text=state.asr_text, node="qualify"),
                TurnRecord(speaker="agent", text=response_text, node="qualify_objection"),
            ],
            "turn_index": state.turn_index + 1,
        })
    
    # Get preemptive objection text to add
    preemptive = await _objection_predictor.get_preemptive_script_addition(
        current_stage="qualify",
        customer_profile={},
        current_slots=state.slots.model_dump(),
    )
    
    # ... continue with normal LLM call ...
    
    # Add preemptive text to agent response
    agent_text = response.agent_text + preemptive
    
    # ... rest of node
```

---

## 🎯 Advanced Integration (1 hour)

### 6. Switch to Multi-Agent Architecture

**File:** `apps/api/pipeline.py`

Change line 114:
```python
# OLD:
dialog_module = __import__(f"dialog.{product}.graph", fromlist=["build_graph"])

# NEW:
dialog_module = __import__(f"dialog.{product}.multi_agent", fromlist=["build_graph"])
```

**Test:**
- Agent should now route to specialist agents
- Check logs for "Supervisor routing to: qualifier_agent"

---

### 7. Run Persona Gym Evaluation

```bash
# Run 50 test conversations for personal loan
python -m persona_gym.eval_runner \
    --product personal_loan \
    --n 50 \
    --output evals/persona_runs/run_$(date +%Y%m%d_%H%M%S).json

# Check results
cat evals/persona_runs/*.json | jq '.success_rate'
```

**Expected output:**
```json
{
  "total_conversations": 50,
  "successful": 38,
  "success_rate": 0.76,
  "avg_duration_s": 156.3,
  "avg_turns": 12.4
}
```

---

## 🧪 Testing the Integrations

### Test 1: RAG Knowledge Retrieval

**Start a call, ask:**
```
User: "What is the interest rate for personal loan?"
```

**Expected (WITHOUT RAG):**
```
Agent: "Great. Aapki monthly income approximately kitni hai?"
(ignores question, follows script)
```

**Expected (WITH RAG):**
```
Agent: "The interest rate for personal loan is 10.5% to 18% per annum, depending on your credit profile. Now, aapki monthly income kitni hai?"
(answers question, then continues)
```

---

### Test 2: Objection Handling

**User says:**
```
User: "Bahut expensive lagta hai"
```

**Expected (WITHOUT objection handler):**
```
Agent: "Great. Aur loan ka purpose kya hai?"
(ignores objection)
```

**Expected (WITH objection handler):**
```
Agent: "I understand your concern. Let me show you our most affordable options. EMI starts at just ₹2,000 per month — very manageable."
(handles objection)
```

---

### Test 3: Compliance Guardrail

**If agent tries to say:**
```
"Can you share your PAN card number?"
```

**Guardrail should:**
- ❌ BLOCK this response
- ⚠️ LOG: "Compliance violation: Requesting PII directly"
- ✅ REPLACE with: "I'll need some basic documents. Our team will guide you on that."

---

### Test 4: Voice Output

**Before (mock TTS):**
- ❌ Text appears in transcript
- ❌ No audio in browser
- ❌ Silent call

**After (ElevenLabs):**
- ✅ Text appears in transcript
- ✅ Audio plays in real-time
- ✅ Natural voice conversation

---

## 📊 Integration Checklist

Run through this after each integration:

### Phase 1: Voice & Knowledge (30 min)
- [ ] Changed `TTS_PROVIDER=elevenlabs` in `.env`
- [ ] Ran `python -m rag.ingest` successfully
- [ ] Qdrant collection has 10+ documents
- [ ] Agent speaks (audio output works)
- [ ] Agent can answer "What's the interest rate?"

### Phase 2: Safety & Objections (45 min)
- [ ] Compliance guardrail processor added to pipeline
- [ ] ObjectionPredictor imported in nodes
- [ ] Agent handles "Too expensive" objection
- [ ] Agent doesn't ask for PAN/Aadhaar directly
- [ ] Dashboard logs compliance interventions

### Phase 3: Multi-Agent & Testing (1 hour)
- [ ] Multi-agent graph loaded instead of single-agent
- [ ] Supervisor routing works (check logs)
- [ ] Persona gym runs without errors
- [ ] Success rate > 70% on test personas
- [ ] All 10 products have knowledge base docs

---

## 🐛 Troubleshooting

### Issue: "Qdrant connection refused"
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# If not, start it
make up

# Wait 30 seconds, then retry
```

### Issue: "No module named 'rag'"
```bash
# Install packages
uv sync --all-packages

# Or just RAG
cd packages/rag && uv pip install -e .
```

### Issue: "ElevenLabs API quota exceeded"
```bash
# Switch to XTTS (free)
# Edit .env:
TTS_PROVIDER=hf_space
HF_SPACE_XTTS_URL=https://YOUR_SPACE_URL/generate

# Or back to mock for testing
TTS_PROVIDER=mock
```

### Issue: "Agent still following script rigidly"
- Check that you're using `nodes_enhanced.py` not `nodes.py`
- Verify RAG function is passed to build_graph
- Check logs for "Retrieved context: ..." messages

### Issue: "Compliance guardrail not blocking"
- Verify ComplianceProcessor is in pipeline
- Check processor order (must be BEFORE TTS)
- Test with explicit PII: "Give me your credit card number"

---

## 📈 Before vs After Metrics

### Current System (Basic Scripts)
| Metric | Value |
|--------|-------|
| Can answer product questions | ❌ 0% |
| Handles objections | ❌ 0% |
| Voice output | ❌ No (mock) |
| Compliance violations caught | ❌ 0 |
| Success rate on test personas | ⚠️ Unknown |

### After Integration (Full SAARTHI)
| Metric | Target |
|--------|--------|
| Can answer product questions | ✅ 95%+ |
| Handles objections | ✅ 85%+ |
| Voice output | ✅ Yes (ElevenLabs) |
| Compliance violations caught | ✅ 100% |
| Success rate on test personas | ✅ 75%+ |

---

## 🎯 Success Criteria

You'll know integration is successful when:

1. ✅ **Voice:** Agent speaks naturally (not silent)
2. ✅ **Knowledge:** Agent answers "What's the interest rate?" correctly from KB
3. ✅ **Objections:** Agent handles "Too expensive" with reassurance
4. ✅ **Safety:** Agent never asks for PAN/Aadhaar/CC directly
5. ✅ **Testing:** Persona gym runs with 75%+ success rate
6. ✅ **All Products:** All 10 products have knowledge base entries

---

## 📞 Need Help?

Check these files for working examples:
- **RAG Usage:** `packages/rag/tests/test_retriever.py`
- **Objection Handling:** `packages/dialog/dialog/objection_predictor.py` (line 230)
- **Compliance:** `packages/guardrail/tests/test_compliance.py`
- **Multi-Agent:** `packages/dialog/dialog/personal_loan/multi_agent.py`

---

**Ready to integrate? Start with the 5-Minute Wins! 🚀**
