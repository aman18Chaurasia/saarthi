# 🔍 SAARTHI Missing Integrations Audit

**Date:** 2026-04-20  
**Status:** Many features built but NOT connected to the pipeline

---

## 📋 Executive Summary

Your SAARTHI system has **8 major features** that are **fully built but NOT integrated** into the actual call flow. The agent currently just follows basic scripts instead of using these advanced capabilities.

---

## 🚨 Critical Missing Integrations

### 1. ❌ **RAG Knowledge Base** (EXISTS but NOT USED)
**Location:** `packages/rag/`

**What it does:**
- Retrieves answers from product brochures and RBI FAQs
- Answers customer questions like:
  - "What's the interest rate?"
  - "What documents do I need?"
  - "What are the benefits?"
  - "Can I prepay without charges?"

**Status:** 
- ✅ Built: `retriever.py`, `embedder.py`, `chunker.py`
- ✅ Data exists: Product brochures in `fixtures/documents/brochures/`
- ❌ **NOT integrated** into dialog nodes
- ❌ Documents NOT ingested into Qdrant yet

**How to verify:**
```bash
# Check if knowledge base is populated
grep -r "retrieve_context" apps/api --include="*.py"
# Result: NO usage found!
```

**Impact:** Agent can't answer product-specific questions!

---

### 2. ✅ **Compliance Guardrail** (INTEGRATED)
**Location:** `apps/api/frame_processors/langgraph_processor.py`

**What it does:**
- Scans agent output for PII (PAN, Aadhaar, Credit Card patterns).
- Blocks non-compliant agent responses before TTS and replaces them with a safe fallback.

**Status:**
- ✅ Built: Full Python re-pattern and rules integration.
- ✅ **Fully running** in the pipeline as a pre-TTS interceptor.

---

### 3. ❌ **Objection Handling** (EXISTS but NOT USED)
**Location:** `packages/dialog/dialog/objection_predictor.py`

**What it does:**
- **Proactive:** Predicts objections (affordability, interest rate, trust, documents)
- **Reactive:** Detects when customer raises objection and handles it
- Adds preemptive reassurance to agent responses

**Example:**
```python
# If customer has low income (< ₹25,000):
# Add: "The best part? EMI starts at just ₹2,000/month — very affordable."
```

**Status:**
- ✅ Built: Full predictor with templates and LLM integration
- ✅ Pattern matching for Hindi/Hinglish objections
- ❌ **NOT wired** into dialog graph

**How to check:**
```bash
grep -r "ObjectionPredictor" apps/api --include="*.py"
# Result: NO usage!
```

**Impact:** Agent can't handle customer concerns naturally!

---

### 4. ✅ **Multi-Agent Conversational Core** (INTEGRATED)
**Location:** `packages/dialog/dialog/_shared/nodes_base.py` & `live_supervisor.py`

**What it does:**
- **LiveConversationSupervisor:** Wraps all products to provide memory, RAG, and sentiment.
- **Shared Enriched Nodes:** All 10 products use a conversational-first logic base.

**Status:**
- ✅ Built: Complete async conversational core implementation
- ✅ **Fully loaded** in pipeline - all products route through `LiveConversationSupervisor`.

---

### 5. ❌ **TTS is MOCKED** (Real TTS exists but disabled)
**Location:** `.env` line 26

**Current setting:**
```env
TTS_PROVIDER=mock
```

**What's available:**
- ✅ ElevenLabs API key configured (line 29)
- ✅ Voice ID set (line 30)
- ✅ TTS processor built (`apps/api/frame_processors/tts_processor.py`)
- ❌ **Set to mock mode** - NO VOICE OUTPUT

**Impact:** Agent shows text but DOESN'T SPEAK!

---

### 6. ❌ **Eligibility Engine** (PARTIALLY integrated)
**Location:** `packages/eligibility/`

**What it does:**
- Neo4j knowledge graph with product rules
- Real-time eligibility checking during call
- Returns detailed reasons for qualification/rejection

**Status:**
- ✅ Built: Full Neo4j integration with fallback rules
- ⚠️ **PARTIALLY integrated:** Loaded in pipeline but not all products use it
- ❌ Neo4j might not be populated with rules

**How to verify:**
```bash
# Check if Neo4j has rules
docker exec -it infra-neo4j-1 cypher-shell -u neo4j -p saarthi_neo4j
MATCH (n:ProductRule) RETURN count(n);
```

**Impact:** Eligibility checks might use fallback only!

---

### 7. ❌ **Persona Gym** (Built but not run)
**Location:** `packages/persona_gym/` + `evals/personas/`

**What it does:**
- Generates 500+ synthetic customer personas
- Automated testing across all products
- Collects conversation logs for RLAIF training
- Measures success rates

**What's in `evals/personas/`:**
- Pre-generated test personas (YAML files)
- Each has: income, personality, expected outcome
- Used for evaluating agent performance

**Example persona (`personal_loan_0000.yaml`):**
```yaml
persona_id: personal_loan_0000
monthly_income_inr: 8000
income_level: low
personality_type: cooperative
expected_outcome: not_qualified
loan_purpose: debt_consolidation
```

**Status:**
- ✅ Built: Generator, eval runner, DPO trainer
- ✅ Personas generated: ~50 per product
- ❌ **NOT running** automated evals
- ❌ No preference collection for RLAIF

**How to run:**
```bash
python -m persona_gym.eval_runner --product personal_loan --n 50
```

**Impact:** No systematic testing or self-improvement!

---

### 8. ❌ **Hinglish Code-Switching** (EXISTS but basic)
**Location:** `packages/guardrail/guardrail/hinglish.py`

**What it does:**
- Sentiment-adaptive prosody (SSML rate/pitch)
- Hinglish mixing based on customer language
- `<lang:hi>` tags in transcript

**Status:**
- ✅ Built: Hinglish formatter and prosody adjuster
- ⚠️ **PARTIALLY working:** Scripts have Hinglish but no dynamic switching
- ❌ Sentiment analyzer not connected

**Impact:** Agent uses fixed Hinglish, doesn't adapt!

---

## 📊 Integration Matrix

| Feature | Built? | Tested? | Integrated? | Impact |
|---------|--------|---------|-------------|--------|
| RAG Knowledge Base | ✅ | ✅ | ✅ | **RESOLVED** - RAG Context injected by Supervisor |
| Compliance Guardrail | ✅ | ✅ | ✅ | **RESOLVED** - Running pre-TTS in pipeline |
| Multi-Agent Routing | ✅ | ✅ | ✅ | **RESOLVED** - Supervisor loaded in pipeline |
| Objection Handling | ✅ | ✅ | ❌ | **HIGH** - Poor customer experience |
| Real TTS (Voice) | ✅ | ✅ | ❌ | **CRITICAL** - Silent agent! |
| Eligibility Engine | ✅ | ✅ | ⚠️ | **MEDIUM** - Using fallback |
| Persona Gym Testing | ✅ | ⚠️ | ❌ | **MEDIUM** - No automated QA |
| Hinglish Adaptation | ✅ | ⚠️ | ⚠️ | **LOW** - Works but basic |

---

## 🎯 Why This Happened

Looking at `CLAUDE.md` Phase breakdown:

### ✅ Phase 1 - MVP (DONE)
- Basic ASR → LangGraph → TTS pipeline
- Script-based dialog
- Dashboard

### ⚠️ Phase 3 - Differentiators (PARTIALLY DONE)
- Code written but NOT wired up
- Multi-agent: Built but not loaded
- Guardrail: Built but not running
- Hinglish: Basic implementation

### ❌ Phase 4 - RLAIF (NOT STARTED)
- Persona gym evaluation not run
- No preference collection
- No DPO training

**Conclusion:** Development jumped ahead to build features without integrating earlier phases!

---

## 🔧 What Needs to Happen

### Step 1: Enable Voice (5 min)
```bash
# Edit .env
TTS_PROVIDER=elevenlabs  # Change from mock

# Restart API
make api
```

### Step 2: Ingest Knowledge Base (10 min)
```bash
# Start Qdrant
make up

# Ingest documents
python -m rag.ingest

# Verify
curl http://localhost:6333/collections/saarthi_knowledge
```

### Step 3: Wire RAG into Dialog (30 min)
- Modify dialog nodes to call `retrieve_context()`
- Add context to LLM prompts
- Handle follow-up questions

### Step 4: Enable Compliance Guardrail (20 min)
- Add compliance check in pipeline before TTS
- Block non-compliant responses
- Log interventions

### Step 5: Enable Objection Handling (15 min)
- Import `ObjectionPredictor` in nodes
- Add preemptive text to responses
- Route detected objections

### Step 6: Switch to Multi-Agent (45 min)
- Load `multi_agent.py` instead of `graph.py`
- Test supervisor routing
- Verify state sharing

### Step 7: Run Persona Evals (30 min)
```bash
python -m persona_gym.eval_runner --product personal_loan --n 50
# Review results in evals/persona_runs/
```

---

## 📁 Key Files to Modify

### Priority 1 (Critical - Enable Voice & RAG)
1. `.env` - Change `TTS_PROVIDER=elevenlabs`
2. `apps/api/pipeline.py` - Import and inject RAG function
3. `packages/dialog/dialog/personal_loan/nodes.py` - Call `retrieve_context()`

### Priority 2 (High - Safety & Quality)
4. `apps/api/pipeline.py` - Add guardrail processor
5. `packages/dialog/dialog/personal_loan/nodes.py` - Add objection predictor

### Priority 3 (Medium - Advanced Features)
6. `apps/api/pipeline.py` - Load multi_agent graph
7. Run `python -m rag.ingest` to populate Qdrant

---

## 🎓 What is evals/personas?

**Purpose:** Synthetic customer profiles for automated testing

**Structure:**
```
evals/personas/
├── personal_loan/
│   ├── personal_loan_0000.yaml  # Low income, cooperative
│   ├── personal_loan_0001.yaml  # Medium income, hesitant
│   └── ... (50 personas)
├── home_loan/
├── education_loan/
└── ... (all 10 products)
```

**How it works:**
1. **Generator** creates personas with varied:
   - Income levels (determines eligibility)
   - Personality types (cooperative, objection-prone, rushed, etc.)
   - Loan purposes
   - Expected outcomes (qualified/not_qualified)

2. **Eval Runner** simulates calls:
   ```bash
   python -m persona_gym.eval_runner --product personal_loan --n 50
   ```
   - Runs 50 test conversations
   - Compares actual vs expected outcomes
   - Logs transcripts
   - Measures success rate

3. **Preference Collector** (for RLAIF):
   - Takes successful + failed conversations
   - Generates preference pairs
   - Feeds into DPO training

**Current Status:**
- ✅ 500+ personas generated
- ❌ NOT being run in CI/CD
- ❌ Results not tracked over time
- ❌ No RLAIF training yet

---

## 📈 Expected Performance After Integration

### Current (Basic Scripts)
- ❌ Can't answer product questions
- ❌ No objection handling
- ❌ No voice output (mock TTS)
- ❌ Compliance risk
- ✅ Follows script linearly

### After Integration (Full SAARTHI)
- ✅ Answers "What's the interest rate?" from knowledge base
- ✅ Handles "Too expensive!" with reassurance
- ✅ Speaks naturally with ElevenLabs voice
- ✅ Blocks PII collection in real-time
- ✅ Routes complex cases to specialist agents
- ✅ Adapts to customer sentiment
- ✅ Tested against 500+ personas

---

## 🚀 Next Steps

**Immediate (Today):**
1. Enable real TTS: Change `.env` → `TTS_PROVIDER=elevenlabs`
2. Ingest knowledge base: `python -m rag.ingest`

**Short-term (This Week):**
3. Integrate RAG into dialog nodes
4. Add compliance guardrail to pipeline
5. Enable objection handling

**Medium-term (Next Week):**
6. Switch to multi-agent architecture
7. Run persona gym evaluations
8. Document results

**Long-term (Phase 4):**
9. Collect preference pairs
10. Train DPO model
11. Compare baseline vs RLAIF performance

---

## 📞 Testing Checklist

After integration, verify:

- [ ] Agent SPEAKS (not just text)
- [ ] Agent answers "What's the interest rate?" correctly
- [ ] Agent handles "Too expensive" objection
- [ ] Agent doesn't ask for PAN/Aadhaar directly
- [ ] Dashboard shows compliance interventions
- [ ] Persona gym runs successfully
- [ ] Knowledge base has 10+ documents indexed

---

**Bottom Line:** You have a Lamborghini engine sitting in the garage. Let's put it in the car! 🏎️
