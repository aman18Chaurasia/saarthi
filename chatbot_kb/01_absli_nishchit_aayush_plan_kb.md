---
kb_id: absli_sherpa_trainer_absli_nishchit_aayush_plan
product_name: "ABSLI Nishchit Aayush Plan"
product_category: "Savings Plans"
product_type: "Non-linked, non-participating individual savings life insurance plan"
use_case: "ABSLI Sherpa Trainer"
intended_for: "RAG ingestion, trainer evaluation, RM-meeting nudges, customer-question handling"
source_primary: "https://lifeinsurance.adityabirlacapital.com/uploads/Nishchit_Aayush_Plan_V14_Brochure_9_2_26_4e4dcf4a43.pdf"
source_secondary: "Uploaded ABSLI product-benefit matrix and life-insurance golden response dataset"
last_compiled: "2026-05-09"
retrieval_tags: ["ABSLI", "Sherpa Trainer", "Savings Plans", "ABSLI Nishchit Aayush Plan", "life insurance", "trainer coaching"]
---
# ABSLI Nishchit Aayush Plan - Product Knowledge Base for ABSLI Sherpa Trainer

## 1. Purpose of this KB file
This product-wise knowledge base is designed for Sherpa Trainer RAG. It should help the model evaluate whether a trainer is explaining the product correctly, using customer-friendly language, avoiding overcommitment, and moving the discussion toward a Relationship Manager meeting where detailed suitability and documentation can be handled.

## 2. Source scope and reliability

| Source Type | Details | Reliability Use |
| --- | --- | --- |
| Official brochure / supplied URL | https://lifeinsurance.adityabirlacapital.com/uploads/Nishchit_Aayush_Plan_V14_Brochure_9_2_26_4e4dcf4a43.pdf | Use for product facts, eligibility, benefit mechanics, exclusions, charges and policy conditions. |
| Uploaded product-benefit matrix | Contains benefits, give-premium example, get-benefit example and recommended premium. | Use for Sherpa demo talk tracks and quick trainer evaluation. |
| Uploaded golden response dataset | Customer-centric Q&A responses that gently move toward RM meetings. | Use for objection handling, generic insurance concepts and safe answer style. |

**Important RAG rule:** If an answer requires exact premium, personalized suitability, tax treatment, underwriting, claim admissibility or current regulatory interpretation, the model should route to RM/advisor review instead of giving a final recommendation.

## 3. Product classification

| Field | Value |
| --- | --- |
| Product Name | ABSLI Nishchit Aayush Plan |
| Product Category | Savings Plans |
| Product Type | Non-linked, non-participating individual savings life insurance plan |
| High-level Positioning | Guaranteed regular income plus life cover and lump sum benefits, suitable for goal-based long-term planning conversations. |
| Trainer Focus | Trainer must explain that this is not a market-linked ULIP; the core story is predictable income, goal security, life cover, and disciplined long-term planning. |
| Customer-friendly One-liner | This plan is useful when the customer wants a planned stream of income for future goals, while also keeping life cover for family protection. |

## 4. Benefits from uploaded product matrix

| Benefit Field | Value |
| --- | --- |
| benefit_1 | Guaranteed regular income for 10, 15, 20, 25, 30,35 or 40 years |
| benefit_2 | Get lumpsum Benefit at maturity |
| benefit_3 | PPT-6,8,10 and 12 |
| benefit_4 | Life cover throughout the policy |
| benefit_5 | Multiple premium payment modes available |


## 5. Give-get example from uploaded matrix

| Field | Value |
| --- | --- |
| Give / Premium Example | Male |Age-35| Standard Life | Salaried | Premium 1L p.a. | PT-40yrs |PPT -10Yrs| Level Income with Enhanced Lumpsum Benefit |
| Get / Benefit Example | Income: INR 32,750 yearly for 40 years (total: INR 13,10,000), starting from first policy anniversary <br>Maturity: INR 20,00,000 lump sum after 40 years <br>Coverage: INR 10,00,000 life cover for 40 years |
| Recommended Premium | 1L |

## 6. Official brochure extraction - structured product facts

| # | Product Fact / Policy Mechanic |
| --- | --- |
| 1 | Provides life insurance cover with guaranteed regular income and lump sum benefits. |
| 2 | Benefit option choices include Long Term Income and Whole Life Income. |
| 3 | Income variants include Level Income with Lump Sum Benefit, Level Income with Enhanced Lump Sum Benefit, Increasing Income with Lump Sum Benefit, Level Income with Return of Premium Benefit, and Income Only Benefit. |
| 4 | Income payout frequency can be annual in advance, annual in arrears, semi-annual, quarterly, or monthly, subject to product rules. |
| 5 | Premium payment terms include 6 pay, 8 pay, 10 pay, and 12 pay, with policy terms varying by benefit option and variant. |
| 6 | Death benefit is generally defined with reference to Sum Assured on Death, surrender benefit, and at least 105% of total premiums paid where applicable. |
| 7 | Nominee may have a staggered death benefit option over 5 years in annual or monthly instalments, subject to policy terms. |
| 8 | Free-look period is 30 days from receipt of policy document as per brochure terms. |


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
| 1 | Do not describe it as a high-return market product. |
| 2 | Do not promise universal tax benefits; say tax treatment depends on prevailing laws. |
| 3 | Do not quote benefits without linking them to chosen premium, PPT, policy term, deferment, and variant. |


## 9. Suggested customer Q&A for retrieval
These responses are aligned to the uploaded golden dataset style. They are intentionally customer-friendly and should lead to RM assistance rather than a hard product recommendation.

| Category | Customer Question / Objection | Safe Response Style |
| --- | --- | --- |
| PRODUCT BASICS | What are guaranteed / savings components? | Some plans offer predictable benefits based on policy terms. A Relationship Manager can help you understand which options suit you. |
| BENEFITS & RETURNS | What maturity benefits will I get? | Maturity benefits depend on the policy type, term, and conditions. A Relationship Manager can explain this clearly. |
| BENEFITS & RETURNS | Do you have monthly income / pension plans? | Yes, there are plans designed for regular income after a certain period. A Relationship Manager can explain how they work. |
| BENEFITS & RETURNS | Is the payout guaranteed? | Only specific plans offer guaranteed payouts as per policy terms. A Relationship Manager can clarify which ones do. |
| POLICY TERM & CONTINUATION | How long should I pay premium? | Premium duration depends on the policy chosen. A Relationship Manager can help you decide based on comfort. |
| POLICY TERM & CONTINUATION | Can I surrender the policy anytime? | Surrender is allowed as per policy terms, usually after a certain period. A Relationship Manager can explain the details. |
| POLICY TERM & CONTINUATION | What happens if I stop paying premium? | The policy may lapse or provide reduced benefits. A Relationship Manager can explain your options. |
| POLICY TERM & CONTINUATION | Surrender charges & lock-in period | Charges and lock-in vary by plan. A Relationship Manager can clarify this clearly. |
| TAXATION | Tax on maturity / surrender | Tax treatment depends on policy type and prevailing laws. A Relationship Manager can explain how this applies to you. |


## 10. Suggested RAG chunking strategy

| Chunk Type | Suggested Metadata | Retrieval Use |
| --- | --- | --- |
| Product overview | product_name, category, plan_type, use_case | Top-level product identification and routing. |
| Benefit mechanics | product_name, benefit_name, option_name, condition | Trainer scoring and fact-checking. |
| Give-get example | product_name, premium_example, illustration_flag | Demo responses and example-based explanations. |
| Objection handling | objection_type, category, rm_meeting_intent | Handling customer resistance and RM conversion. |
| Guardrails | product_name, compliance_rule, hallucination_risk | Safe answer generation and trainer correction. |

## 11. Recommended system prompt instruction for this product
When answering about ABSLI Nishchit Aayush Plan, first identify the product type as **Non-linked, non-participating individual savings life insurance plan**. Explain benefits only with conditions. Use customer-friendly language. Do not provide final suitability, tax, return or claim decisions. If the customer asks for exact numbers or a recommendation, ask to schedule an RM meeting or use the official benefit illustration.

## 12. Product-wise retrieval examples

| User / Trainer Query | Expected Retrieval Focus |
| --- | --- |
| Explain this plan to a customer in simple words | Sections 3, 4, 5 and 9 |
| What should trainer say if customer asks about returns? | Sections 6, 8 and 9 |
| Is this guaranteed? | Product category + guardrails + golden response dataset |
| How should trainee move to RM meeting? | Golden response style + trainer scoring rubric |

