# SAARTHI Product Scripts Guide

## Overview

SAARTHI uses YAML-based scripts to define conversation flows for 10 different BFSI products. Each script defines the agent's dialogue at each stage of the call.

## Available Products

All scripts located in: `packages/scripts/products/`

| Product | Script File | Key Qualifying Questions |
|---------|-------------|-------------------------|
| **Personal Loan** | `personal_loan.yaml` | Monthly income, Loan purpose |
| **Home Loan** | `home_loan.yaml` | Monthly income, Property value & location |
| **Education Loan** | `education_loan.yaml` | Monthly income, Course & institution |
| **Gold Loan** | `gold_loan.yaml` | Monthly income, Gold weight |
| **Credit Card** | `credit_card.yaml` | Monthly income, Monthly spending, Existing cards |
| **Unsecured Loan** | `unsecured_loan.yaml` | Monthly income, Loan purpose |
| **LAP (Secured)** | `lap_secured.yaml` | Monthly income, Property value |
| **Commercial Vehicle** | `commercial_vehicle.yaml` | Monthly income, Vehicle type |
| **Four Wheeler** | `four_wheeler.yaml` | Monthly income, Car model preference |
| **MSME Business** | `msme_business.yaml` | Monthly revenue, Business type |

## Script Structure

### YAML Template

```yaml
# Product call script
product: <product_id>
version: "0.1"

nodes:
  opener:
    agent: |
      Namaste! Main {agent_name} bol raha hoon, {lender_name} se.
      Kya aap {customer_name} ji bol rahe hain? <pause:wait_user/>

  identity_confirm:
    agent: |
      Thank you. Main aapko ek <PRODUCT> offer ke baare mein baat karna chahta tha —
      kya abhi aapke paas 2 minute hain? <pause:wait_user/>

  qualify:
    agent: |
      Great. Aapki monthly income approximately kitni hai? <pause:wait_user/>
    follow_up:
      agent: |
        <PRODUCT-SPECIFIC QUALIFYING QUESTIONS> <pause:wait_user/>

  consent:
    agent: |
      Main aapko ek tailored offer bhejne ke liye aapki basic details record karna chahta hoon.
      Kya aap consent dete hain? <pause:wait_user/>

  next_step:
    agent: |
      Perfect. Aapko 24 ghante mein ek detailed offer SMS aur email par milega.
      Koi bhi sawaal ho toh hum available hain. <pause:wait_user/>

  close:
    agent: |
      Bahut bahut shukriya aapka samay dene ke liye. Have a great day! <pause:end/>
```

### Node Stages

1. **opener** - Initial greeting, identity confirmation
2. **identity_confirm** - Confirm availability, introduce product
3. **qualify** - Collect primary qualifying info (usually income)
4. **qualify_followup** (from qualify.follow_up) - Collect product-specific details
5. **consent** - Request permission to record details
6. **next_step** - Confirm next steps
7. **close** - Farewell

### Variable Placeholders

- `{agent_name}` - Agent's name
- `{lender_name}` - Financial institution name
- `{customer_name}` - Customer's name

### Pause Markers

- `<pause:wait_user/>` - Wait for customer response
- `<pause:end/>` - End of call

### Script Guidelines

✅ **DO:**
- Keep agent turns ≤25 words average
- Use conversational Hinglish (Hindi + English)
- Ask one question at a time
- Be respectful and professional

❌ **DON'T:**
- Use overly formal language
- Ask multiple complex questions in one turn
- Exceed 35 words per response

## Creating a New Product Script

1. **Copy template:**
   ```bash
   cp packages/scripts/products/_TEMPLATE.yaml packages/scripts/products/new_product.yaml
   ```

2. **Update fields:**
   - `product:` - Unique product ID (snake_case)
   - Replace `{{PRODUCT_DESCRIPTION}}` in identity_confirm
   - Replace `{{QUALIFY_QUESTION}}` in qualify
   - Replace `{{FOLLOWUP_QUESTION}}` in follow_up

3. **Create dialog package:**
   ```bash
   mkdir -p packages/dialog/dialog/new_product
   # Copy structure from personal_loan
   ```

4. **Define slots in schema:**
   - Create `schema.py` with product-specific `StructuredAgentResponse`
   - Update `state.py` with required slots

## Few-Shot Prompt Engineering

### Current Approach: **Structured Few-Shot Prompts**

The system uses **few-shot learning** in slot extraction guidance. Each node includes 5-10 examples showing:

**Example from `prompts.py`:**

```python
"qualify": (
    "Extract: monthly_income_inr (integer).\n\n"
    "EXAMPLES:\n"
    "Customer: 'Fifty thousand' → {\"monthly_income_inr\": 50000}, intent: provide_value\n"
    "Customer: '50,000 rupees' → {\"monthly_income_inr\": 50000}, intent: provide_value\n"
    "Customer: 'Rs. 3000' → {\"monthly_income_inr\": 3000}, intent: provide_value\n"
    "Customer: '45k per month' → {\"monthly_income_inr\": 45000}, intent: provide_value\n"
    "Customer: 'Around thirty thousand' → {\"monthly_income_inr\": 30000}, intent: provide_value\n"
    "Customer: 'I make 25 thousand' → {\"monthly_income_inr\": 25000}, intent: provide_value\n"
    "Customer: 'Thank you' → {}, intent: unclear\n\n"
    "CRITICAL: If you see ANY number in the response, extract it as monthly_income_inr. Be aggressive - any number = income."
),
```

### Shot Count by Node

| Node | Example Count | Coverage |
|------|---------------|----------|
| **opener** | 0 | No extraction needed |
| **identity_confirm** | 6 | Affirmative, negative, product interest, unclear |
| **qualify** | 7 | Number formats (digits, words, abbreviated, Hindi/English) |
| **qualify_followup** | 9 | Product-specific purposes (varies by product) |
| **consent** | 5 | Yes/no variations |
| **next_step** | 0 | Confirmation only |
| **close** | 0 | No extraction needed |

### Why Few-Shot?

1. **Language Diversity** - Hindi, English, Hinglish mixing requires examples
2. **Number Formats** - "50000", "50k", "fifty thousand", "पचास हज़ार"
3. **Intent Ambiguity** - "Thank you" vs "Yes, I need a loan"
4. **Edge Cases** - Product confusion, incomplete answers

### Recent Improvements (April 2026)

**Added:**
- ✅ Conversation history (last 4 turns) for context
- ✅ Cross-product handling ("I want home loan" when calling for personal loan)
- ✅ Hindi/Hinglish phrase examples
- ✅ Natural language understanding rules

**Before:**
```
"strictly follow the script, max 30 words"
```

**After:**
```
"adapt naturally, don't repeat verbatim"
+ Conversation history
+ Acknowledge and redirect
+ Don't ask same question twice
```

## Testing Scripts

### Unit Test Example

```python
# packages/dialog/tests/test_nodes.py
async def test_qualify_extracts_income():
    state = DialogState(...)
    state.asr_text = "My income is fifty thousand"
    
    result = await qualify_node(state, mock_llm_fn)
    
    assert result.slots.monthly_income_inr == 50000
    assert "income" in result.history[-1].text.lower()
```

### Integration Test

```bash
# Run full conversation scenario
uv run pytest packages/dialog/tests/test_graph.py::test_personal_loan_happy_path -v
```

### Manual Testing

1. Start servers:
   ```bash
   make api  # Terminal 1
   make web  # Terminal 2
   ```

2. Navigate to http://localhost:3000

3. Start call with desired product

4. Check transcript quality and slot extraction

## Switching Between Products

### At Runtime (Dashboard)

The dashboard allows selecting product when starting a call. The `product` field determines which YAML script loads.

### In Code

```python
from dialog.home_loan.graph import build_graph as build_home_loan_graph

# Instead of personal_loan
app = build_home_loan_graph(llm_fn)
```

## Advanced: Multi-Product Handling

For scenarios where customers mention different products:

**Current Strategy:**
- Acknowledge the different product interest
- Gently redirect to the call's primary product
- Example: "I understand you're interested in home loan. Let me also share our personal loan offer which might be helpful."

**Future Enhancement (Phase 3):**
- Dynamic product switching mid-call
- Multi-product comparison agent

## Documentation

- **ADRs**: `docs/adr/` - Architecture decisions
- **Project Plan**: `docs/SAARTHI-Project-Plan.md`
- **Phase completion**: `docs/PHASE1-COMPLETE.md`, `docs/PHASE2-COMPLETE.md`
- **Deployment**: `docs/DEPLOYMENT.md`

## Common Issues

### Issue: Agent repeats same question

**Cause:** Slot not extracted, retry_count incrementing

**Fix:** Check few-shot examples cover the response format

### Issue: Wrong product script loaded

**Cause:** Product ID mismatch

**Fix:** Verify `product` field in YAML matches directory name

### Issue: Hindi text not understood

**Cause:** Missing Unicode examples in few-shot

**Fix:** Add Hindi/Hinglish examples to slot guidance

## Contributing New Products

1. Create YAML script following template
2. Define dialog state machine in `packages/dialog/dialog/<product>/`
3. Add Neo4j eligibility rules (Phase 2)
4. Create 3 demo recordings (success, failure, edge case)
5. Add to product selector in dashboard
6. Update documentation

---

**Last Updated:** April 20, 2026  
**Version:** 1.1 (Post Few-Shot Enhancement)
