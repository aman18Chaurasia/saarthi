---
kb_id: absli_sherpa_trainer_absli_vision_retirement_solution
product_name: "ABSLI Vision Retirement Solution"
product_category: "Retirement Solution"
product_type: "Combination retirement solution based on uploaded matrix: ABSLI Guaranteed Annuity Plus + ABSLI Wealth Infinia"
use_case: "ABSLI Sherpa Trainer"
intended_for: "RAG ingestion, trainer evaluation, RM-meeting nudges, customer-question handling"
source_primary: "Uploaded product-benefit matrix only. No official brochure PDF URL was provided in the current input."
source_secondary: "Uploaded ABSLI product-benefit matrix and life-insurance golden response dataset"
last_compiled: "2026-05-09"
retrieval_tags: ["ABSLI", "Sherpa Trainer", "Retirement Solution", "ABSLI Vision Retirement Solution", "life insurance", "trainer coaching"]
---
# ABSLI Vision Retirement Solution - Product Knowledge Base for ABSLI Sherpa Trainer

## 1. Purpose of this KB file
This product-wise knowledge base is designed for Sherpa Trainer RAG. It should help the model evaluate whether a trainer is explaining the product correctly, using customer-friendly language, avoiding overcommitment, and moving the discussion toward a Relationship Manager meeting where detailed suitability and documentation can be handled.

## 2. Source scope and reliability

| Source Type | Details | Reliability Use |
| --- | --- | --- |
| Official brochure / supplied URL | Uploaded product-benefit matrix only. No official brochure PDF URL was provided in the current input. | Use for product facts, eligibility, benefit mechanics, exclusions, charges and policy conditions. |
| Uploaded product-benefit matrix | Contains benefits, give-premium example, get-benefit example and recommended premium. | Use for Sherpa demo talk tracks and quick trainer evaluation. |
| Uploaded golden response dataset | Customer-centric Q&A responses that gently move toward RM meetings. | Use for objection handling, generic insurance concepts and safe answer style. |

**Important RAG rule:** If an answer requires exact premium, personalized suitability, tax treatment, underwriting, claim admissibility or current regulatory interpretation, the model should route to RM/advisor review instead of giving a final recommendation.

## 3. Product classification

| Field | Value |
| --- | --- |
| Product Name | ABSLI Vision Retirement Solution |
| Product Category | Retirement Solution |
| Product Type | Combination retirement solution based on uploaded matrix: ABSLI Guaranteed Annuity Plus + ABSLI Wealth Infinia |
| High-level Positioning | Retirement income solution combining guaranteed annuity and equity-linked systematic withdrawal payouts, as described in the uploaded product matrix. |
| Trainer Focus | Trainer must mark this as a retirement-oriented combination solution and must not treat the matrix illustration as a guaranteed universal result without official product brochures. |
| Customer-friendly One-liner | This solution is for retirement planning where the customer wants a regular income structure and some equity-linked growth potential. |

## 4. Benefits from uploaded product matrix

| Benefit Field | Value |
| --- | --- |
| benefit_1 | ABSLI Vision Retirement Solution is a combination of ABSLI Guaranteed Annuity Plus and ABSLI Wealth Infinia which is a new<br>age retirement solution to beat inflation through guaranteed annuity along with equity linked payouts through Systematic<br>Withdrawal Facility available under ABSLI Wealth Infinia. |
| benefit_2 | Retirement income till age 100 years for secured retirement. |
| benefit_3 | Double Death Benefit |
| benefit_5 | Different types of fund option to choose from in order to |


## 5. Give-get example from uploaded matrix

| Field | Value |
| --- | --- |
| Give / Premium Example | Male |Age-40| Standard Life | Salaried | Premium 5L p.a. | PT-60yrs |PPT -10Yrs| 60 % GAP and 40% WI |
| Get / Benefit Example | Life Long Guaranteed Annuity of Rs 3,90,432(Annuity- 2,15,938 p.a, Systematic Withdrawl @ 5%-Rs 1,74,494)<br><br>Fund Value at Maturity Rs 1,06,41,741 @ 8% |
| Recommended Premium | 2L |

## 6. Official brochure extraction - structured product facts

| # | Product Fact / Policy Mechanic |
| --- | --- |
| 1 | Uploaded matrix describes it as a combination of ABSLI Guaranteed Annuity Plus and ABSLI Wealth Infinia. |
| 2 | Purpose is to beat inflation through guaranteed annuity along with equity-linked payouts through Systematic Withdrawal Facility available under ABSLI Wealth Infinia. |
| 3 | Highlighted benefit: retirement income till age 100 years for secured retirement. |
| 4 | Highlighted benefit: Double Death Benefit. |
| 5 | Example case in matrix: Male, age 40, salaried, premium INR 5 lakh p.a., PT 60 years, PPT 10 years, 60% GAP and 40% WI. |
| 6 | Example outcome in matrix: lifelong guaranteed annuity of INR 3,90,432, comprising annuity INR 2,15,938 p.a. and systematic withdrawal at 5% of INR 1,74,494; fund value at maturity INR 1,06,41,741 at 8% illustration. |


## 7. Trainer scoring rubric for this product

| Evaluation Area | What Sherpa Trainer should check | Good Trainer Explanation | Red Flag / Deduction |
| --- | --- | --- | --- |
| Product category clarity | Whether trainer correctly identifies plan type | Clearly says whether this is term, savings, ULIP or retirement solution. | Mixes term insurance with investment return or calls ULIP returns guaranteed. |
| Benefit mechanics | Whether benefits are explained according to chosen option | Links benefits to plan option, premium, PPT, policy term, sum assured and payout mode. | Quotes benefits as universal without conditions. |
| Customer language | Whether trainer explains in simple customer language | Uses protection, income, fund value, guaranteed income or retirement language appropriately. | Uses dense brochure jargon without explanation. |
| Compliance guardrails | Whether trainer avoids final advice without suitability | Routes to RM for suitability, illustration, taxes, documentation and final recommendation. | Gives tax, return or claim guarantee as a final answer. |
| RM meeting movement | Whether trainer gently moves conversation forward | Suggests RM meeting/callback to show illustration and suitability. | Ends with only generic information and no next step. |

## 8. Product-specific guardrails

| # | Guardrail |
| --- | --- |
| 1 | Validate against official brochures before regulated responses. |
| 2 | Do not present uploaded matrix illustration as universal guaranteed outcome. |
| 3 | Clearly separate guaranteed annuity language from market-linked withdrawal language. |


## 9. Suggested customer Q&A for retrieval
These responses are aligned to the uploaded golden dataset style. They are intentionally customer-friendly and should lead to RM assistance rather than a hard product recommendation.

| Category | Customer Question / Objection | Safe Response Style |
| --- | --- | --- |
| BENEFITS & RETURNS | Do you have monthly income / pension plans? | Yes, there are plans designed for regular income after a certain period. A Relationship Manager can explain how they work. |
| BENEFITS & RETURNS | Is the payout guaranteed? | Only specific plans offer guaranteed payouts as per policy terms. A Relationship Manager can clarify which ones do. |
| POLICY TERM & CONTINUATION | How long should I pay premium? | Premium duration depends on the policy chosen. A Relationship Manager can help you decide based on comfort. |
| TAXATION | Tax on maturity / surrender | Tax treatment depends on policy type and prevailing laws. A Relationship Manager can explain how this applies to you. |
| GOAL-BASED PLANNING | Long-term savings + protection | Insurance helps combine protection with disciplined saving. A Relationship Manager can explain how. |
| GOAL-BASED PLANNING | Pension / annuity plans | These plans help create regular income after retirement. A Relationship Manager can explain options. |
| GOAL-BASED PLANNING | Guaranteed income / annuity | Some plans offer predictable income based on terms. A Relationship Manager can explain this. |


## 10. Suggested RAG chunking strategy

| Chunk Type | Suggested Metadata | Retrieval Use |
| --- | --- | --- |
| Product overview | product_name, category, plan_type, use_case | Top-level product identification and routing. |
| Benefit mechanics | product_name, benefit_name, option_name, condition | Trainer scoring and fact-checking. |
| Give-get example | product_name, premium_example, illustration_flag | Demo responses and example-based explanations. |
| Objection handling | objection_type, category, rm_meeting_intent | Handling customer resistance and RM conversion. |
| Guardrails | product_name, compliance_rule, hallucination_risk | Safe answer generation and trainer correction. |

## 11. Recommended system prompt instruction for this product
When answering about ABSLI Vision Retirement Solution, first identify the product type as **Combination retirement solution based on uploaded matrix: ABSLI Guaranteed Annuity Plus + ABSLI Wealth Infinia**. Explain benefits only with conditions. Use customer-friendly language. Do not provide final suitability, tax, return or claim decisions. If the customer asks for exact numbers or a recommendation, ask to schedule an RM meeting or use the official benefit illustration.

## 12. Product-wise retrieval examples

| User / Trainer Query | Expected Retrieval Focus |
| --- | --- |
| Explain this plan to a customer in simple words | Sections 3, 4, 5 and 9 |
| What should trainer say if customer asks about returns? | Sections 6, 8 and 9 |
| Is this guaranteed? | Product category + guardrails + golden response dataset |
| How should trainee move to RM meeting? | Golden response style + trainer scoring rubric |

