---
kb_id: absli_sherpa_trainer_absli_salaried_term_plan
product_name: "ABSLI Salaried Term Plan"
product_category: "Term Insurance"
product_type: "Non-linked, non-participating life individual pure risk premium plan for salaried professionals"
use_case: "ABSLI Sherpa Trainer"
intended_for: "RAG ingestion, trainer evaluation, RM-meeting nudges, customer-question handling"
source_primary: "https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Salaried_Term_Plan_V05_Brochure_Web_Version_9743b6e5d7.pdf"
source_secondary: "Uploaded ABSLI product-benefit matrix and life-insurance golden response dataset"
last_compiled: "2026-05-09"
retrieval_tags: ["ABSLI", "Sherpa Trainer", "Term Insurance", "ABSLI Salaried Term Plan", "life insurance", "trainer coaching"]
---
# ABSLI Salaried Term Plan - Product Knowledge Base for ABSLI Sherpa Trainer

## 1. Purpose of this KB file
This product-wise knowledge base is designed for Sherpa Trainer RAG. It should help the model evaluate whether a trainer is explaining the product correctly, using customer-friendly language, avoiding overcommitment, and moving the discussion toward a Relationship Manager meeting where detailed suitability and documentation can be handled.

## 2. Source scope and reliability

| Source Type | Details | Reliability Use |
| --- | --- | --- |
| Official brochure / supplied URL | https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Salaried_Term_Plan_V05_Brochure_Web_Version_9743b6e5d7.pdf | Use for product facts, eligibility, benefit mechanics, exclusions, charges and policy conditions. |
| Uploaded product-benefit matrix | Contains benefits, give-premium example, get-benefit example and recommended premium. | Use for Sherpa demo talk tracks and quick trainer evaluation. |
| Uploaded golden response dataset | Customer-centric Q&A responses that gently move toward RM meetings. | Use for objection handling, generic insurance concepts and safe answer style. |

**Important RAG rule:** If an answer requires exact premium, personalized suitability, tax treatment, underwriting, claim admissibility or current regulatory interpretation, the model should route to RM/advisor review instead of giving a final recommendation.

## 3. Product classification

| Field | Value |
| --- | --- |
| Product Name | ABSLI Salaried Term Plan |
| Product Category | Term Insurance |
| Product Type | Non-linked, non-participating life individual pure risk premium plan for salaried professionals |
| High-level Positioning | Protection plan tailored for salaried customers with payout options including life cover, return of premium, fixed income cover and increasing income cover. |
| Trainer Focus | Trainer must explain why salaried customers may need income replacement and how lump sum vs monthly income payout changes the family protection story. |
| Customer-friendly One-liner | This plan is built for salaried people who want their family to receive either a lump sum cover or structured monthly income if something happens to them. |

## 4. Benefits from uploaded product matrix

| Benefit Field | Value |
| --- | --- |
| benefit_1 | This plan support the family on the Death of the policy holder,also it helps during the difficult time such as Disease with the waiver of premium and a lumpsum benefit on Terminal Illness |
| benefit_2 | Special discounts for Salaried customers and Female Lives<br><br>Male (Salaried)-10% , Online -6%, and Female -upto 25% + 2% |
| benefit_3 | Annual, Semi-annual, Quarterly & Monthly modes available |
| benefit_4 | Life Cover of up to INR 5 crore |


## 5. Give-get example from uploaded matrix

| Field | Value |
| --- | --- |
| Give / Premium Example | Male|Age-35 | Standard Life | Salaried | Sum Assured 1 cr. | Cover till 75 | Level Cover | Premium <br><br>Regular Pay -Rs 19400 p.a.<br>10 Pay - Rs 38,100 p.a. |
| Get / Benefit Example | Coverage:  Get INR 1 crore Term insurance  <br>Benefit: 50% of sum assured advance payment if diagnosed with terminal illness |
| Recommended Premium | 50-60K |

## 6. Official brochure extraction - structured product facts

| # | Product Fact / Policy Mechanic |
| --- | --- |
| 1 | Designed for salaried individuals looking to secure family financial stability. |
| 2 | Four plan options: Life Cover, Life Cover with Return of Premium, Fixed Income Cover, and Increasing Income Cover. |
| 3 | Fixed Income Cover pays nominee monthly income equal to 1.25% of Sum Assured for chosen income benefit period on death during policy term. |
| 4 | Increasing Income Cover starts at 1.25% of Sum Assured and grows at 5% or 10% simple interest per annum depending on selected escalation rate. |
| 5 | Income benefit period for income variants can be 10, 15, or 20 years and is chosen at inception. |
| 6 | Product eligibility includes minimum entry age 21 years and maximum entry age 55 years; maturity age ranges from minimum 31 years to maximum 75 years as per brochure. |
| 7 | Premium payment modes include annual, semi-annual, quarterly and monthly with modal factors. |
| 8 | No policy loan facility is available in this plan. |
| 9 | Free-look period is 30 days from receipt of policy document as per brochure terms. |


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
| 1 | Do not say all benefits can be changed later; core choices are made at inception. |
| 2 | Do not call the income payout a survival benefit; it is a death benefit payout variant. |
| 3 | Do not promise policy loan because brochure states no loan facility. |


## 9. Suggested customer Q&A for retrieval
These responses are aligned to the uploaded golden dataset style. They are intentionally customer-friendly and should lead to RM assistance rather than a hard product recommendation.

| Category | Customer Question / Objection | Safe Response Style |
| --- | --- | --- |
| PRODUCT BASICS | What is Life Insurance? | Life insurance helps protect your family financially if something unexpected happens to you. Some plans also help with long-term savings. A Relationship Manager can explain how this works based on your needs. |
| PRODUCT BASICS | What is sum assured? | Sum assured is the amount payable as per policy conditions in case of a covered event. A Relationship Manager can help you understand how much coverage is usually considered. |
| PRODUCT BASICS | What is life cover / risk cover? | Life cover provides financial protection to your family in case of an unfortunate event. A Relationship Manager can explain how this fits into your planning. |
| POLICY TERM & CONTINUATION | Policy term & premium paying term | Policy term is coverage duration; premium paying term is how long you pay. A Relationship Manager can explain this with examples. |
| TAXATION | Section 80C insurance benefit | Premiums may be eligible for tax benefits under Section 80C, subject to conditions. A Relationship Manager can explain more. |
| TRUST & OBJECTIONS | How can I trust this policy? | That’s understandable. ABSLI is regulated by IRDAI, and details are fully documented. A Relationship Manager can meet you personally. |
| TRUST & OBJECTIONS | I already have insurance | That’s good. A review can ensure it still meets your needs. A Relationship Manager can assist. |
| HARD OBJECTIONS | Premium feels expensive | That’s a common concern. A Relationship Manager can explore affordable options. |
| HARD OBJECTIONS | Can’t commit to premiums | That’s understandable. A Relationship Manager can explain flexible options. |
| REGULATORY & DISCLOSURES | Not a policy recommendation | This call is for information only. A Relationship Manager will guide you further. |


## 10. Suggested RAG chunking strategy

| Chunk Type | Suggested Metadata | Retrieval Use |
| --- | --- | --- |
| Product overview | product_name, category, plan_type, use_case | Top-level product identification and routing. |
| Benefit mechanics | product_name, benefit_name, option_name, condition | Trainer scoring and fact-checking. |
| Give-get example | product_name, premium_example, illustration_flag | Demo responses and example-based explanations. |
| Objection handling | objection_type, category, rm_meeting_intent | Handling customer resistance and RM conversion. |
| Guardrails | product_name, compliance_rule, hallucination_risk | Safe answer generation and trainer correction. |

## 11. Recommended system prompt instruction for this product
When answering about ABSLI Salaried Term Plan, first identify the product type as **Non-linked, non-participating life individual pure risk premium plan for salaried professionals**. Explain benefits only with conditions. Use customer-friendly language. Do not provide final suitability, tax, return or claim decisions. If the customer asks for exact numbers or a recommendation, ask to schedule an RM meeting or use the official benefit illustration.

## 12. Product-wise retrieval examples

| User / Trainer Query | Expected Retrieval Focus |
| --- | --- |
| Explain this plan to a customer in simple words | Sections 3, 4, 5 and 9 |
| What should trainer say if customer asks about returns? | Sections 6, 8 and 9 |
| Is this guaranteed? | Product category + guardrails + golden response dataset |
| How should trainee move to RM meeting? | Golden response style + trainer scoring rubric |

