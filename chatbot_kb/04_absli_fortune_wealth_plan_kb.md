---
kb_id: absli_sherpa_trainer_absli_fortune_wealth_plan
product_name: "ABSLI Fortune Wealth Plan"
product_category: "ULIP Plans"
product_type: "Unit-linked, non-participating individual life insurance savings plan"
use_case: "ABSLI Sherpa Trainer"
intended_for: "RAG ingestion, trainer evaluation, RM-meeting nudges, customer-question handling"
source_primary: "https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Fortune_Wealth_Plan_V01_Brochure_Web_Version_ead76f3e45.pdf"
source_secondary: "Uploaded ABSLI product-benefit matrix and life-insurance golden response dataset"
last_compiled: "2026-05-09"
retrieval_tags: ["ABSLI", "Sherpa Trainer", "ULIP Plans", "ABSLI Fortune Wealth Plan", "life insurance", "trainer coaching"]
---
# ABSLI Fortune Wealth Plan - Product Knowledge Base for ABSLI Sherpa Trainer

## 1. Purpose of this KB file
This product-wise knowledge base is designed for Sherpa Trainer RAG. It should help the model evaluate whether a trainer is explaining the product correctly, using customer-friendly language, avoiding overcommitment, and moving the discussion toward a Relationship Manager meeting where detailed suitability and documentation can be handled.

## 2. Source scope and reliability

| Source Type | Details | Reliability Use |
| --- | --- | --- |
| Official brochure / supplied URL | https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Fortune_Wealth_Plan_V01_Brochure_Web_Version_ead76f3e45.pdf | Use for product facts, eligibility, benefit mechanics, exclusions, charges and policy conditions. |
| Uploaded product-benefit matrix | Contains benefits, give-premium example, get-benefit example and recommended premium. | Use for Sherpa demo talk tracks and quick trainer evaluation. |
| Uploaded golden response dataset | Customer-centric Q&A responses that gently move toward RM meetings. | Use for objection handling, generic insurance concepts and safe answer style. |

**Important RAG rule:** If an answer requires exact premium, personalized suitability, tax treatment, underwriting, claim admissibility or current regulatory interpretation, the model should route to RM/advisor review instead of giving a final recommendation.

## 3. Product classification

| Field | Value |
| --- | --- |
| Product Name | ABSLI Fortune Wealth Plan |
| Product Category | ULIP Plans |
| Product Type | Unit-linked, non-participating individual life insurance savings plan |
| High-level Positioning | ULIP for wealth creation with life cover, fund allocation flexibility, 5 investment options and 18 funds, with market-linked fund value. |
| Trainer Focus | Trainer must repeatedly clarify that this is market-linked, so fund value can move up or down. Benefit illustration values at 4% and 8% are illustrative and not guaranteed. |
| Customer-friendly One-liner | This plan combines life cover with the possibility of long-term wealth creation through selected market-linked funds, so it works best when the customer understands investment risk and time horizon. |

## 4. Benefits from uploaded product matrix

| Benefit Field | Value |
| --- | --- |
| benefit_1 | Flexibility to choose from 5 investment & 18 fund options |
| benefit_2 | Life coverage of up to 10 times annual premium |
| benefit_3 | Loyalty Additions from 6th policy year onwards |
| benefit_4 | Active portfolio management with systematic transfer & dynamic fund allocation |
| benefit_5 | Flexible premium payment options - Limited Pay / Regular Pay |


## 5. Give-get example from uploaded matrix

| Field | Value |
| --- | --- |
| Give / Premium Example | INR 1,00,000 annually for 10 years (total: INR 10,00,000) in a 20 year policy |
| Get / Benefit Example | Maturity: Fund Value : INR 26,37,455 @8%  and Rs 14,38,870 @ 4%<br>Coverage: Life cover throughout the policy term<br>Other benefits: Potential for even higher returns based on market performance |
| Recommended Premium | 1L |

## 6. Official brochure extraction - structured product facts

| # | Product Fact / Policy Mechanic |
| --- | --- |
| 1 | Offers life insurance plus market-linked wealth accumulation through unit-linked funds. |
| 2 | Customer can choose from 5 investment options and 18 fund options. |
| 3 | Plan options include Classic Option and Assured Option. |
| 4 | Under Classic Option, death benefit is higher of fund value as on death intimation or Sum Assured, with adjustments for partial withdrawals as per terms. |
| 5 | Under Assured Option, death benefit is paid immediately as higher of Sum Assured on death or 105% of annualized premiums paid, and the policy can continue till maturity with future premiums paid by the insurer subject to terms. |
| 6 | Sum Assured is 10 times Annualized Premium under both plan options. |
| 7 | Maturity benefit is Fund Value in lump sum if the life insured survives to policy maturity and conditions are met. |
| 8 | Partial withdrawals are available after five complete policy years subject to policy terms. |
| 9 | Fund management charges and mortality charges apply; mortality charges are based on Sum at Risk and deducted monthly by cancellation of units. |
| 10 | Grace period is 30 days, or 15 days for monthly mode, for unpaid premium as per brochure. |


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
| 1 | Do not guarantee 4% or 8% illustration values. |
| 2 | Do not describe fund value as fixed or assured. |
| 3 | Do not recommend fund switches without suitability and RM review. |


## 9. Suggested customer Q&A for retrieval
These responses are aligned to the uploaded golden dataset style. They are intentionally customer-friendly and should lead to RM assistance rather than a hard product recommendation.

| Category | Customer Question / Objection | Safe Response Style |
| --- | --- | --- |
| PRODUCT BASICS | What is policy fund value / sum assured? | Policy fund value applies to market-linked plans, while sum assured is the coverage amount as per policy terms. A Relationship Manager can explain this clearly with examples. |
| SAFETY & RISK | Is insurance affected by markets? | Market-linked plans like ULIPs are affected by markets, while traditional plans are less impacted. A Relationship Manager can explain this clearly. |
| SAFETY & RISK | Is ULIP risky right now? | ULIPs have market exposure, so values can move up or down. Risk depends on fund choice and duration. A Relationship Manager can guide you better. |
| POLICY STRUCTURE & FEATURES | Policy charges | Charges vary based on policy type and features. A Relationship Manager can explain them transparently. |
| POLICY STRUCTURE & FEATURES | Fund performance deviation (ULIP) | ULIP fund performance may differ due to market conditions. A Relationship Manager can explain how this works. |
| ULIP-SPECIFIC | ULIP fund options | ULIPs offer multiple fund options with different risk levels. A Relationship Manager can explain these. |
| ULIP-SPECIFIC | Fund switching | Fund switching is allowed as per policy terms. A Relationship Manager can guide you. |
| ULIP-SPECIFIC | ULIP fund returns | Returns depend on market performance and fund choice. A Relationship Manager can explain this clearly. |
| ULIP-SPECIFIC | Multiple ULIP fund allocation | Some policies allow allocation across funds. A Relationship Manager can help you understand. |
| OPERATIONS & SERVICING | Policy benefit illustration | Benefit illustrations show how a policy works. A Relationship Manager can explain them clearly. |


## 10. Suggested RAG chunking strategy

| Chunk Type | Suggested Metadata | Retrieval Use |
| --- | --- | --- |
| Product overview | product_name, category, plan_type, use_case | Top-level product identification and routing. |
| Benefit mechanics | product_name, benefit_name, option_name, condition | Trainer scoring and fact-checking. |
| Give-get example | product_name, premium_example, illustration_flag | Demo responses and example-based explanations. |
| Objection handling | objection_type, category, rm_meeting_intent | Handling customer resistance and RM conversion. |
| Guardrails | product_name, compliance_rule, hallucination_risk | Safe answer generation and trainer correction. |

## 11. Recommended system prompt instruction for this product
When answering about ABSLI Fortune Wealth Plan, first identify the product type as **Unit-linked, non-participating individual life insurance savings plan**. Explain benefits only with conditions. Use customer-friendly language. Do not provide final suitability, tax, return or claim decisions. If the customer asks for exact numbers or a recommendation, ask to schedule an RM meeting or use the official benefit illustration.

## 12. Product-wise retrieval examples

| User / Trainer Query | Expected Retrieval Focus |
| --- | --- |
| Explain this plan to a customer in simple words | Sections 3, 4, 5 and 9 |
| What should trainer say if customer asks about returns? | Sections 6, 8 and 9 |
| Is this guaranteed? | Product category + guardrails + golden response dataset |
| How should trainee move to RM meeting? | Golden response style + trainer scoring rubric |

