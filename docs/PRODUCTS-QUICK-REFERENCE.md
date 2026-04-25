# SAARTHI Products Quick Reference

## All 10 Products Side-by-Side

| # | Product | Key Slot 1 | Key Slot 2 | Key Slot 3 | Target Audience |
|---|---------|------------|------------|------------|-----------------|
| 1 | **Personal Loan** | monthly_income_inr | loan_purpose | - | General consumers, emergency needs |
| 2 | **Home Loan** | monthly_income_inr | property_value | property_location | Home buyers |
| 3 | **Education Loan** | monthly_income_inr | course_name | institution_name | Students, parents |
| 4 | **Gold Loan** | monthly_income_inr | gold_weight_grams | - | Quick liquidity needs |
| 5 | **Credit Card** | monthly_income_inr | monthly_spending | has_existing_card | Regular spenders |
| 6 | **Unsecured Loan** | monthly_income_inr | loan_purpose | - | No collateral borrowers |
| 7 | **LAP (Secured)** | monthly_income_inr | property_value | - | Property owners |
| 8 | **Commercial Vehicle** | monthly_income_inr | vehicle_type | - | Transport businesses |
| 9 | **Four Wheeler** | monthly_income_inr | vehicle_model | - | Car buyers |
| 10 | **MSME Business** | monthly_revenue_inr | business_type | - | Small business owners |

## Follow-Up Questions by Product

### Personal Loan
```
Aur aap is loan ka use kisliye karna chahte hain —
home renovation, travel, ya kuch aur?
```
**Extracts:** loan_purpose (home_renovation | travel | medical | education | business | other)

### Home Loan
```
Aur aap jo property dekhne mein interested hain, uski approximate value kya hai?
Location bhi bataiye.
```
**Extracts:** property_value (integer), property_location (string)

### Education Loan
```
Aur aap kaun sa course aur kaunse institution mein lena chahte hain?
```
**Extracts:** course_name (string), institution_name (string)

### Gold Loan
```
Aur aapke paas approximately kitne gram gold hai jo aap pledge karna chahte hain?
```
**Extracts:** gold_weight_grams (integer)

### Credit Card
```
Aur aapki monthly spending kitni hoti hai?
Kya aapke paas koi existing credit card hai?
```
**Extracts:** monthly_spending (integer), has_existing_card (boolean)

### Unsecured Loan
```
Aur aap is loan ka use kis purpose ke liye karna chahte hain?
```
**Extracts:** loan_purpose (string)

### LAP (Loan Against Property)
```
Aur jo property aap pledge karna chahte hain, uski approximate market value kitni hai?
```
**Extracts:** property_value (integer)

### Commercial Vehicle Loan
```
Aur aap kaun sa type ka commercial vehicle lena chahte hain?
Truck, tempo, ya koi aur?
```
**Extracts:** vehicle_type (truck | tempo | bus | other)

### Four Wheeler Loan
```
Aur aap kaunsi car model mein interested hain?
Approximate budget bhi bataiye.
```
**Extracts:** vehicle_model (string), budget (integer)

### MSME Business Loan
```
Aur aapki business ki monthly revenue approximately kitni hai?
Kis type ka business hai?
```
**Extracts:** monthly_revenue_inr (integer), business_type (string)

## Eligibility Rules (Phase 2 - Neo4j)

Simplified eligibility thresholds:

| Product | Min Income | Min Revenue | Other Requirements |
|---------|------------|-------------|-------------------|
| Personal Loan | ₹15,000/mo | - | Age 21-60 |
| Home Loan | ₹25,000/mo | - | Property < 10 years old |
| Education Loan | ₹20,000/mo | - | Recognized institution |
| Gold Loan | ₹10,000/mo | - | Min 10g gold, 22kt+ |
| Credit Card | ₹25,000/mo | - | Credit score > 650 |
| Unsecured Loan | ₹20,000/mo | - | Age 23-58 |
| LAP | ₹30,000/mo | - | Clear property title |
| Commercial Vehicle | ₹40,000/mo | - | Valid transport license |
| Four Wheeler | ₹30,000/mo | - | Age 21-65 |
| MSME Business | - | ₹1,00,000/mo | GST registered |

## Common Slots Across All Products

Every product includes:

```python
class SlotSet(BaseModel):
    name_confirmed: bool = False
    has_time: Optional[bool] = None
    consent_given: Optional[bool] = None
    outcome: Optional[Literal[
        "qualified", "not_qualified", "no_consent", 
        "callback_requested", "dropped"
    ]] = None
    
    # Product-specific slots added here
    monthly_income_inr: Optional[int] = None
    # ... etc
```

## Language Patterns

All scripts use **Hinglish** (Hindi + English code-switching):

### Structure Pattern
1. **Hindi greeting**: "Namaste! Main Priya bol raha hoon"
2. **English product**: "personal loan offer"
3. **Hindi connector**: "ke baare mein baat karna chahta tha"
4. **Mixed questioning**: "kya aapke paas 2 minute hain?"

### Why Hinglish?
- ✅ Mirrors natural Indian conversation
- ✅ Accessible to broader audience
- ✅ Professional yet familiar tone
- ✅ Financial terms often in English (loan, credit, interest)

## Intent Classification

All products use same 4 intents:

```python
classified_intent: Literal["affirm", "deny", "provide_value", "unclear"]
```

| Intent | Examples |
|--------|----------|
| **affirm** | "Yes", "Haan", "Sure", "Okay", "I'm interested" |
| **deny** | "No", "Nahi", "I'm busy", "Not interested" |
| **provide_value** | "50000", "Home renovation", "Mumbai" |
| **unclear** | "What?", "Huh?", "I don't understand" |

## Response Templates by Outcome

### Qualified
```
Perfect. Aapko 24 ghante mein ek detailed offer SMS aur email par milega.
Koi bhi sawaal ho toh hum available hain.
```

### Not Qualified (Eligibility Failed)
```
Thank you for your interest. Unfortunately, aapki current profile is product ke 
requirements ko match nahi kar rahi. Hum aapko alternate options share karenge.
```

### No Consent
```
Koi baat nahi, main samajh sakta hoon. Agar future mein interest ho toh 
humein zaroor contact karein.
```

### Dropped (No Time / Busy)
```
Bilkul theek hai. Main aapko convenient time par dubara call karunga. 
Have a great day!
```

## Testing Cheat Sheet

### Quick Test Commands

```bash
# Run all dialog tests
uv run pytest packages/dialog/tests/ -v

# Test specific product
uv run pytest packages/dialog/tests/test_personal_loan.py -v

# Test with coverage
uv run pytest packages/dialog/tests/ --cov=dialog --cov-report=html

# Run persona gym scenarios
uv run python -m persona_gym run --product personal_loan --n 10
```

### Test a New Script

1. **Lint YAML:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('packages/scripts/products/new_product.yaml'))"
   ```

2. **Verify placeholders:**
   ```bash
   grep -o '{[^}]*}' packages/scripts/products/new_product.yaml
   # Should only see: {agent_name}, {lender_name}, {customer_name}
   ```

3. **Check word count:**
   ```bash
   # Each agent line should be ≤25 words
   ```

## Migration Between Products

If customer mentions wrong product during call:

### Current Behavior (Phase 1)
```python
# In identity_confirm node
if "home loan" in asr_text and product == "personal_loan":
    response = """
    I understand you're interested in home loan. 
    Let me also share our personal loan offer which might be helpful.
    Kya aapke paas 2 minute hain?
    """
```

### Future Behavior (Phase 3)
- Dynamic product switching
- Multi-product comparison
- Transfer to appropriate agent

---

**See also:**
- Full guide: `docs/PRODUCT-SCRIPTS-GUIDE.md`
- Project plan: `docs/SAARTHI-Project-Plan.md`
- ADR 0002: `docs/adr/0002-phase1-voice-loop.md`
