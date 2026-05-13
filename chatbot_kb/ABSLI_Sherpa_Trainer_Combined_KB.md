

---

<!-- FILE: README.md -->

# ABSLI Sherpa Trainer Product-wise Knowledge Base

Compiled on: 2026-05-09

## What is included

1. `00_common_life_insurance_golden_responses.md` - shared customer Q&A and objection handling layer.
2. `00_product_benefits_matrix_preserved.md` - uploaded spreadsheet/product-matrix preserved as markdown table.
3. `00_product_routing_kb.md` - retrieval router for deciding which product KB to fetch.
4. One markdown KB per product:
   - `01_absli_nishchit_aayush_plan_kb.md`
   - `02_absli_super_term_plan_kb.md`
   - `03_absli_salaried_term_plan_kb.md`
   - `04_absli_fortune_wealth_plan_kb.md`
   - `05_absli_platinum_gain_plan_kb.md`
   - `06_absli_vision_retirement_solution_kb.md`
5. `absli_kb_manifest.json` - machine-readable metadata for ingestion.

## Recommended RAG structure

Use a hybrid structure:

- Keep **separate product-wise KB files** for retrieval precision.
- Keep **one common golden-response KB** for generic objections and RM-meeting movement.
- Keep **one product-routing KB** as the first-stage retrieval layer.
- Attach metadata at chunk level: `product_name`, `category`, `plan_type`, `section`, `source_primary`, `risk_level`, `rm_required`.

## Suggested retrieval flow

1. Classify user query into product-specific or generic insurance question.
2. If product is clear, retrieve product-wise KB plus common golden response KB.
3. If product is unclear, retrieve product-routing KB first.
4. For regulated answers, route exact premium, tax, claim and suitability decisions to RM/advisor review.

## Data-loss note

The supplied uploaded spreadsheet text has been preserved in markdown table form. The official PDFs were converted into structured RAG-ready product knowledge using the product URLs supplied in the prompt. For absolute zero-loss PDF table reconstruction, upload the original PDFs and XLSX files directly; then a table-extraction pipeline can preserve every visual table, page reference and row/column relationship exactly.



---

<!-- FILE: 00_product_routing_kb.md -->

---
kb_id: absli_sherpa_trainer_product_routing
use_case: ABSLI Sherpa Trainer
last_compiled: 2026-05-09
retrieval_tags: [ABSLI, product routing, product classification, RAG routing]
---
# ABSLI Sherpa Trainer - Product Routing KB

Use this as the first-stage retrieval layer before retrieving a product-wise KB. It is meant to reduce product confusion between term insurance, savings plans, ULIPs and retirement solutions.

| Product | Category | Plan Type | Positioning | Next KB File |
| --- | --- | --- | --- | --- |
| ABSLI Nishchit Aayush Plan | Savings Plans | Non-linked, non-participating individual savings life insurance plan | Guaranteed regular income plus life cover and lump sum benefits, suitable for goal-based long-term planning conversations. | Use absli_nishchit_aayush_plan_kb.md |
| ABSLI Super Term Plan | Term Insurance | Non-linked, non-participating life individual pure risk premium plan | Comprehensive term protection with multiple payout choices, terminal illness, ACI and disability-related features, and customer-friendly flexibility. | Use absli_super_term_plan_kb.md |
| ABSLI Salaried Term Plan | Term Insurance | Non-linked, non-participating life individual pure risk premium plan for salaried professionals | Protection plan tailored for salaried customers with payout options including life cover, return of premium, fixed income cover and increasing income cover. | Use absli_salaried_term_plan_kb.md |
| ABSLI Fortune Wealth Plan | ULIP Plans | Unit-linked, non-participating individual life insurance savings plan | ULIP for wealth creation with life cover, fund allocation flexibility, 5 investment options and 18 funds, with market-linked fund value. | Use absli_fortune_wealth_plan_kb.md |
| ABSLI Platinum Gain Plan | ULIP Plans | Unit-linked, non-participating individual life insurance savings plan | Premium ULIP with life cover, 18 funds, 5 investment strategies, wealth boosters, loyalty additions and return of mortality/premium allocation charges at maturity subject to terms. | Use absli_platinum_gain_plan_kb.md |
| ABSLI Vision Retirement Solution | Retirement Solution | Combination retirement solution based on uploaded matrix: ABSLI Guaranteed Annuity Plus + ABSLI Wealth Infinia | Retirement income solution combining guaranteed annuity and equity-linked systematic withdrawal payouts, as described in the uploaded product matrix. | Use absli_vision_retirement_solution_kb.md |


## Routing logic

| Query Pattern | Recommended Retrieval |
| --- | --- |
| Customer asks about pure protection, family security, death cover, high sum assured | Retrieve term-insurance files: Super Term Plan or Salaried Term Plan. |
| Customer asks about guaranteed income, long-term fixed income, child education, goal planning | Retrieve Nishchit Aayush Plan. |
| Customer asks about market-linked wealth, fund value, fund switching, ULIP returns | Retrieve Fortune Wealth Plan or Platinum Gain Plan. |
| Customer asks about retirement, annuity, income till old age | Retrieve Vision Retirement Solution, and validate with official source before regulated response. |
| Customer asks generic insurance objection | Retrieve common golden response KB first, then product-wise KB. |



---

<!-- FILE: 00_product_benefits_matrix_preserved.md -->

---
kb_id: absli_sherpa_trainer_product_benefits_matrix
use_case: ABSLI Sherpa Trainer
source: Uploaded product-benefit spreadsheet text
last_compiled: 2026-05-09
retrieval_tags: [ABSLI, product benefits, give get, premium examples, product matrix]
---
# ABSLI Product Benefits Matrix - Preserved Markdown Table

This file preserves the uploaded spreadsheet-style row and column structure in a RAG-friendly markdown table. Use this as a quick product-routing and example-response layer. For regulated product details, retrieve the product-wise KB and official brochure URL.

| Product Name | Benefit 1 | Benefit 2 | Benefit 3 | Benefit 4 | Benefit 5 | Give Premiums | Get Benefits | Recommended Premium |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ABSLI Nishchit Aayush Plan | Guaranteed regular income for 10, 15, 20, 25, 30,35 or 40 years | Get lumpsum Benefit at maturity | PPT-6,8,10 and 12 | Life cover throughout the policy | Multiple premium payment modes available | Male \|Age-35\| Standard Life \| Salaried \| Premium 1L p.a. \| PT-40yrs \|PPT -10Yrs\| Level Income with Enhanced Lumpsum Benefit | Income: INR 32,750 yearly for 40 years (total: INR 13,10,000), starting from first policy anniversary <br>Maturity: INR 20,00,000 lump sum after 40 years <br>Coverage: INR 10,00,000 life cover for 40 years | 1L |
| ABSLI Super Term Plan | 3D Cover -This plan support the family on the Death of the policy holder,also it helps during the difficult time such as Disease & Disablity with the waiver of premium and a lumpsum benefit on Terminal Illness | Healthy living with inbuilt Health Management Services where 2 family members can be added (Spouse & 1 Child) (perceived value up to 74,000 p.a.), to avail this benefit customer should have Min 1Cr Sum Assured | Instant Payment on Claim Intimation* for immediate support to family | Special discounts for Salaried customers and Female Lives<br><br>Male (Salaried)-10% , Online -6%, and Female -upto 25% + 2% | Option to defer premiums by up to 12 months with Cover Continuance Benefit | Male \|Age-35\| Standard Life \| Salaried \| Sum Assured 1 cr. \| Cover till 85 \| Level Cover \| Premium<br><br>Regular Pay -Rs 23,300 p.a.<br>10 Pay - Rs 57,600 p.a. | Coverage:  Get INR 1 crore Term insurance  <br>Benefit: 50% of sum assured advance payment if diagnosed with terminal illness | 50-60K |
| ABSLI Salaried Term Plan | This plan support the family on the Death of the policy holder,also it helps during the difficult time such as Disease with the waiver of premium and a lumpsum benefit on Terminal Illness | Special discounts for Salaried customers and Female Lives<br><br>Male (Salaried)-10% , Online -6%, and Female -upto 25% + 2% | Annual, Semi-annual, Quarterly & Monthly modes available | Life Cover of up to INR 5 crore |  | Male\|Age-35 \| Standard Life \| Salaried \| Sum Assured 1 cr. \| Cover till 75 \| Level Cover \| Premium <br><br>Regular Pay -Rs 19400 p.a.<br>10 Pay - Rs 38,100 p.a. | Coverage:  Get INR 1 crore Term insurance  <br>Benefit: 50% of sum assured advance payment if diagnosed with terminal illness | 50-60K |
| ABSLI Fortune Wealth Plan | Flexibility to choose from 5 investment & 18 fund options | Life coverage of up to 10 times annual premium | Loyalty Additions from 6th policy year onwards | Active portfolio management with systematic transfer & dynamic fund allocation | Flexible premium payment options - Limited Pay / Regular Pay | INR 1,00,000 annually for 10 years (total: INR 10,00,000) in a 20 year policy | Maturity: Fund Value : INR 26,37,455 @8%  and Rs 14,38,870 @ 4%<br>Coverage: Life cover throughout the policy term<br>Other benefits: Potential for even higher returns based on market performance | 1L |
| ABSLI Platinum Gain Plan | Flexibility to choose from 5 investment & 18 fund options | Flexible premium payment options - Limited Pay / Regular Pay | Liquidity through systematic withdrawal benefit | No policy Administration Charge | Return of Premium Allocation and mortality Charge at Maturity. | INR 2,00,000 annually for 10 years (total: INR 20,00,000) in a 20-year policy | Maturity: Fund Value : Rs 57,75,675 @8%  and Rs 32,12,058 @ 4%<br>Coverage: Life cover throughout the policy term<br>Other benefits: Potential for even higher returns based on market performance | 2L |
| ABSLI Vision Retirement Solution | ABSLI Vision Retirement Solution is a combination of ABSLI Guaranteed Annuity Plus and ABSLI Wealth Infinia which is a new<br>age retirement solution to beat inflation through guaranteed annuity along with equity linked payouts through Systematic<br>Withdrawal Facility available under ABSLI Wealth Infinia. | Retirement income till age 100 years for secured retirement. | Double Death Benefit |  | Different types of fund option to choose from in order to | Male \|Age-40\| Standard Life \| Salaried \| Premium 5L p.a. \| PT-60yrs \|PPT -10Yrs\| 60 % GAP and 40% WI | Life Long Guaranteed Annuity of Rs 3,90,432(Annuity- 2,15,938 p.a, Systematic Withdrawl @ 5%-Rs 1,74,494)<br><br>Fund Value at Maturity Rs 1,06,41,741 @ 8% | 2L |




---

<!-- FILE: 00_common_life_insurance_golden_responses.md -->

---
kb_id: absli_sherpa_trainer_common_golden_responses
use_case: ABSLI Sherpa Trainer
source: Uploaded life-insurance customer-centric golden response dataset
last_compiled: 2026-05-09
retrieval_tags: [ABSLI, Sherpa Trainer, golden responses, customer objections, RM meeting]
---
# ABSLI Sherpa Trainer - Common Life Insurance Golden Response KB

## Purpose
This file contains the customer-centric golden response dataset supplied for the ABSLI Sherpa Trainer use case. The response style is deliberately gentle, explanatory and RM-meeting oriented. Use this file as a shared/common KB across all product-wise product files.

## Global response rules

| Rule | Instruction |
| --- | --- |
| Lead to RM | Whenever possible, gently offer a Relationship Manager meeting/callback for detailed explanation. |
| Avoid final recommendation | Do not present a product as suitable without customer need analysis and official illustration. |
| Be clear on plan type | Separate term protection, guaranteed/savings plans, ULIPs and retirement/annuity solutions. |
| Preserve uncertainty | Use "depends on policy terms", "subject to conditions", and "as per prevailing tax laws" where appropriate. |
| Avoid pressure | The trainer should not push aggressively; it should create confidence and a logical next step. |

## Golden Q&A table

| Category | Question / Objection | Golden Response |
| --- | --- | --- |
| PRODUCT BASICS | What is Life Insurance? | Life insurance helps protect your family financially if something unexpected happens to you. Some plans also help with long-term savings. A Relationship Manager can explain how this works based on your needs. |
| PRODUCT BASICS | What is premium payment (monthly/annual)? | Premium is the amount you pay to keep the policy active, either monthly or annually. A Relationship Manager can help you choose a payment option that feels comfortable. |
| PRODUCT BASICS | What is policy fund value / sum assured? | Policy fund value applies to market-linked plans, while sum assured is the coverage amount as per policy terms. A Relationship Manager can explain this clearly with examples. |
| PRODUCT BASICS | What is sum assured? | Sum assured is the amount payable as per policy conditions in case of a covered event. A Relationship Manager can help you understand how much coverage is usually considered. |
| PRODUCT BASICS | What is a new insurance plan / new launch? | New plans are introduced to meet changing customer needs and regulations. A Relationship Manager can share details if you’d like to explore. |
| PRODUCT BASICS | What is the role of the insurer / actuary? | The insurer designs and manages policies, while actuaries calculate risks and benefits. A Relationship Manager can explain how this impacts your policy. |
| PRODUCT BASICS | What is life cover / risk cover? | Life cover provides financial protection to your family in case of an unfortunate event. A Relationship Manager can explain how this fits into your planning. |
| PRODUCT BASICS | What are guaranteed / savings components? | Some plans offer predictable benefits based on policy terms. A Relationship Manager can help you understand which options suit you. |
| SAFETY & RISK | Is life insurance safe? | Life insurance is regulated by IRDAI, ensuring customer protection and transparency. A Relationship Manager can explain this further. |
| SAFETY & RISK | Will I lose my premium if I stop? | That depends on the policy terms. Some policies may lapse or offer reduced benefits. A Relationship Manager can clarify this for your policy. |
| SAFETY & RISK | What is low-risk vs market-linked insurance? | Low-risk plans offer stable benefits, while market-linked plans may fluctuate. A Relationship Manager can help you understand the difference. |
| SAFETY & RISK | Is insurance affected by markets? | Market-linked plans like ULIPs are affected by markets, while traditional plans are less impacted. A Relationship Manager can explain this clearly. |
| SAFETY & RISK | Is ULIP risky right now? | ULIPs have market exposure, so values can move up or down. Risk depends on fund choice and duration. A Relationship Manager can guide you better. |
| SAFETY & RISK | Do you have guaranteed insurance plans? | Yes, there are plans with guaranteed benefits as per terms. A Relationship Manager can explain these options in detail. |
| BENEFITS & RETURNS | What maturity benefits will I get? | Maturity benefits depend on the policy type, term, and conditions. A Relationship Manager can explain this clearly. |
| BENEFITS & RETURNS | Why is maturity value lower than expected? | Benefits depend on policy structure, charges, and duration. A Relationship Manager can help review this with you. |
| BENEFITS & RETURNS | Other insurers give better benefits | Different insurers design plans differently. A Relationship Manager can help compare features meaningfully. |
| BENEFITS & RETURNS | Why ABSLI benefits look lower | Insurance benefits are structured based on long-term protection and stability. A Relationship Manager can explain this in detail. |
| BENEFITS & RETURNS | Paying premiums long-term, benefits not clear | It’s important to understand policy benefits clearly. A Relationship Manager can walk you through them step by step. |
| BENEFITS & RETURNS | Do you have monthly income / pension plans? | Yes, there are plans designed for regular income after a certain period. A Relationship Manager can explain how they work. |
| BENEFITS & RETURNS | Is the payout guaranteed? | Only specific plans offer guaranteed payouts as per policy terms. A Relationship Manager can clarify which ones do. |
| POLICY TERM & CONTINUATION | How long should I pay premium? | Premium duration depends on the policy chosen. A Relationship Manager can help you decide based on comfort. |
| POLICY TERM & CONTINUATION | Policy term & premium paying term | Policy term is coverage duration; premium paying term is how long you pay. A Relationship Manager can explain this with examples. |
| POLICY TERM & CONTINUATION | Can I surrender the policy anytime? | Surrender is allowed as per policy terms, usually after a certain period. A Relationship Manager can explain the details. |
| POLICY TERM & CONTINUATION | What happens if I stop paying premium? | The policy may lapse or provide reduced benefits. A Relationship Manager can explain your options. |
| POLICY TERM & CONTINUATION | Surrender charges & lock-in period | Charges and lock-in vary by plan. A Relationship Manager can clarify this clearly. |
| TAXATION | Tax on maturity / surrender | Tax treatment depends on policy type and prevailing laws. A Relationship Manager can explain how this applies to you. |
| TAXATION | Section 80C insurance benefit | Premiums may be eligible for tax benefits under Section 80C, subject to conditions. A Relationship Manager can explain more. |
| TAXATION | Is maturity amount taxable? | Some maturity amounts may be taxable depending on policy terms. A Relationship Manager can clarify this. |
| TAXATION | Why insurance has lock-in? | Insurance is designed for long-term protection and discipline. A Relationship Manager can explain this reasoning. |
| TAXATION | Tax limits on premium & payout | Tax limits depend on regulations and policy type. A Relationship Manager can explain how this affects you. |
| POLICY STRUCTURE & FEATURES | Agent policy vs online policy | Both offer the same policy benefits; the difference is service support. A Relationship Manager can explain this clearly. |
| POLICY STRUCTURE & FEATURES | Policy charges | Charges vary based on policy type and features. A Relationship Manager can explain them transparently. |
| POLICY STRUCTURE & FEATURES | Fund performance deviation (ULIP) | ULIP fund performance may differ due to market conditions. A Relationship Manager can explain how this works. |
| POLICY STRUCTURE & FEATURES | Declared bonus / benchmark rate | Bonuses depend on insurer performance and policy terms. A Relationship Manager can clarify this. |
| POLICY STRUCTURE & FEATURES | Premium increase / top-up | Some policies allow premium increase or top-ups as per terms. A Relationship Manager can guide you. |
| POLICY STRUCTURE & FEATURES | Single premium + regular premium | Some plans allow one-time and regular payments. A Relationship Manager can explain which suits you. |
| ULIP-SPECIFIC | ULIP fund options | ULIPs offer multiple fund options with different risk levels. A Relationship Manager can explain these. |
| ULIP-SPECIFIC | Fund switching | Fund switching is allowed as per policy terms. A Relationship Manager can guide you. |
| ULIP-SPECIFIC | ULIP fund returns | Returns depend on market performance and fund choice. A Relationship Manager can explain this clearly. |
| ULIP-SPECIFIC | Multiple ULIP fund allocation | Some policies allow allocation across funds. A Relationship Manager can help you understand. |
| ULIP-SPECIFIC | ULIP fund switch | Switching rules vary by policy. A Relationship Manager can explain this. |
| ULIP-SPECIFIC | ULIP market exposure | ULIPs are exposed to markets, so values can fluctuate. A Relationship Manager can explain how to manage this. |
| OPERATIONS & SERVICING | Policy details update | Details can be updated through proper process. A Relationship Manager can assist you. |
| OPERATIONS & SERVICING | Nominee change / assignment | Nominee changes are allowed as per policy rules. A Relationship Manager can help you do this. |
| OPERATIONS & SERVICING | Unclaimed policy payout | Unclaimed payouts can be retrieved after verification. A Relationship Manager can guide you. |
| OPERATIONS & SERVICING | Insurance portal issues | Technical issues can be resolved with support. A Relationship Manager can raise a request. |
| OPERATIONS & SERVICING | Policy benefit illustration | Benefit illustrations show how a policy works. A Relationship Manager can explain them clearly. |
| OPERATIONS & SERVICING | Policy documents required | Documents depend on policy type and regulations. A Relationship Manager can guide you. |
| GOAL-BASED PLANNING | Long-term savings + protection | Insurance helps combine protection with disciplined saving. A Relationship Manager can explain how. |
| GOAL-BASED PLANNING | Child education insurance plan | Such plans help secure education goals even in difficult situations. A Relationship Manager can guide you. |
| GOAL-BASED PLANNING | Pension / annuity plans | These plans help create regular income after retirement. A Relationship Manager can explain options. |
| GOAL-BASED PLANNING | Guaranteed income / annuity | Some plans offer predictable income based on terms. A Relationship Manager can explain this. |
| GOAL-BASED PLANNING | Required sum assured planning | Coverage depends on income, goals, and responsibilities. A Relationship Manager can help assess this. |
| TRUST & OBJECTIONS | How can I trust this policy? | That’s understandable. ABSLI is regulated by IRDAI, and details are fully documented. A Relationship Manager can meet you personally. |
| TRUST & OBJECTIONS | Is this genuine insurance? | Yes, it’s offered by an IRDAI-regulated insurer. A Relationship Manager can share complete details. |
| TRUST & OBJECTIONS | Who regulates insurance (IRDAI)? | IRDAI regulates insurers and protects policyholders. A Relationship Manager can explain this. |
| TRUST & OBJECTIONS | Another insurer better | Different insurers offer different features. A Relationship Manager can help compare fairly. |
| TRUST & OBJECTIONS | Agent suggested surrender | Before taking any decision, it’s good to understand implications. A Relationship Manager can review this with you. |
| TRUST & OBJECTIONS | I already have insurance | That’s good. A review can ensure it still meets your needs. A Relationship Manager can assist. |
| HARD OBJECTIONS | I don’t want insurance right now | I understand. A Relationship Manager can connect later if you feel the need. |
| HARD OBJECTIONS | Had bad experience with insurance | I’m sorry to hear that. A Relationship Manager can help address concerns transparently. |
| HARD OBJECTIONS | Premium feels expensive | That’s a common concern. A Relationship Manager can explore affordable options. |
| HARD OBJECTIONS | Can’t commit to premiums | That’s understandable. A Relationship Manager can explain flexible options. |
| HARD OBJECTIONS | Insurance not for me | I respect your view. A Relationship Manager can clarify only if you wish. |
| HARD OBJECTIONS | I prefer fixed / guaranteed plans | There are plans aligned to that preference. A Relationship Manager can explain. |
| REGULATORY & DISCLOSURES | IRDAI regulation | Insurance is regulated by IRDAI for customer protection. A Relationship Manager can explain more. |
| REGULATORY & DISCLOSURES | Policy brochure | The brochure explains features and terms. A Relationship Manager can walk you through it. |
| REGULATORY & DISCLOSURES | Insurance benefit illustration disclaimer | Illustrations are indicative, not guaranteed. A Relationship Manager can clarify expectations. |
| REGULATORY & DISCLOSURES | Not a policy recommendation | This call is for information only. A Relationship Manager will guide you further. |
| CALL HANDLING | Why did you call? | This is a service call from ABSLI to check if you need assistance. A Relationship Manager can meet you if needed. |
| CALL HANDLING | Are you AI / Bot? | Yes, I’m a virtual assistant. A Relationship Manager will handle detailed discussions. |
| CALL HANDLING | Want to talk to senior | I can arrange a callback or meeting with a senior Relationship Manager. |
| CALL HANDLING | Language preference | I can arrange a Relationship Manager who speaks your preferred language. |
| CALL HANDLING | Call me later | Sure. I’ll arrange a callback through our Relationship Manager. |
| CALL HANDLING | Not interested | Understood. If you wish later, a Relationship Manager can assist. |
| CALL HANDLING | Abusive / gibberish | I’ll disconnect the call now. Thank you. |




---

<!-- FILE: 01_absli_nishchit_aayush_plan_kb.md -->

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




---

<!-- FILE: 02_absli_super_term_plan_kb.md -->

---
kb_id: absli_sherpa_trainer_absli_super_term_plan
product_name: "ABSLI Super Term Plan"
product_category: "Term Insurance"
product_type: "Non-linked, non-participating life individual pure risk premium plan"
use_case: "ABSLI Sherpa Trainer"
intended_for: "RAG ingestion, trainer evaluation, RM-meeting nudges, customer-question handling"
source_primary: "https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Super_Term_Plan_V02_Brochure_Web_Version_ac63b34e77.pdf"
source_secondary: "Uploaded ABSLI product-benefit matrix and life-insurance golden response dataset"
last_compiled: "2026-05-09"
retrieval_tags: ["ABSLI", "Sherpa Trainer", "Term Insurance", "ABSLI Super Term Plan", "life insurance", "trainer coaching"]
---
# ABSLI Super Term Plan - Product Knowledge Base for ABSLI Sherpa Trainer

## 1. Purpose of this KB file
This product-wise knowledge base is designed for Sherpa Trainer RAG. It should help the model evaluate whether a trainer is explaining the product correctly, using customer-friendly language, avoiding overcommitment, and moving the discussion toward a Relationship Manager meeting where detailed suitability and documentation can be handled.

## 2. Source scope and reliability

| Source Type | Details | Reliability Use |
| --- | --- | --- |
| Official brochure / supplied URL | https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Super_Term_Plan_V02_Brochure_Web_Version_ac63b34e77.pdf | Use for product facts, eligibility, benefit mechanics, exclusions, charges and policy conditions. |
| Uploaded product-benefit matrix | Contains benefits, give-premium example, get-benefit example and recommended premium. | Use for Sherpa demo talk tracks and quick trainer evaluation. |
| Uploaded golden response dataset | Customer-centric Q&A responses that gently move toward RM meetings. | Use for objection handling, generic insurance concepts and safe answer style. |

**Important RAG rule:** If an answer requires exact premium, personalized suitability, tax treatment, underwriting, claim admissibility or current regulatory interpretation, the model should route to RM/advisor review instead of giving a final recommendation.

## 3. Product classification

| Field | Value |
| --- | --- |
| Product Name | ABSLI Super Term Plan |
| Product Category | Term Insurance |
| Product Type | Non-linked, non-participating life individual pure risk premium plan |
| High-level Positioning | Comprehensive term protection with multiple payout choices, terminal illness, ACI and disability-related features, and customer-friendly flexibility. |
| Trainer Focus | Trainer must distinguish term protection from savings/ULIP products and teach trainees how to explain payout format, claim support, and protection continuity without overpromising. |
| Customer-friendly One-liner | This is a protection-focused term plan for families who need high life cover and flexibility in how the nominee receives the claim amount. |

## 4. Benefits from uploaded product matrix

| Benefit Field | Value |
| --- | --- |
| benefit_1 | 3D Cover -This plan support the family on the Death of the policy holder,also it helps during the difficult time such as Disease & Disablity with the waiver of premium and a lumpsum benefit on Terminal Illness |
| benefit_2 | Healthy living with inbuilt Health Management Services where 2 family members can be added (Spouse & 1 Child) (perceived value up to 74,000 p.a.), to avail this benefit customer should have Min 1Cr Sum Assured |
| benefit_3 | Instant Payment on Claim Intimation* for immediate support to family |
| benefit_4 | Special discounts for Salaried customers and Female Lives<br><br>Male (Salaried)-10% , Online -6%, and Female -upto 25% + 2% |
| benefit_5 | Option to defer premiums by up to 12 months with Cover Continuance Benefit |


## 5. Give-get example from uploaded matrix

| Field | Value |
| --- | --- |
| Give / Premium Example | Male |Age-35| Standard Life | Salaried | Sum Assured 1 cr. | Cover till 85 | Level Cover | Premium<br><br>Regular Pay -Rs 23,300 p.a.<br>10 Pay - Rs 57,600 p.a. |
| Get / Benefit Example | Coverage:  Get INR 1 crore Term insurance  <br>Benefit: 50% of sum assured advance payment if diagnosed with terminal illness |
| Recommended Premium | 50-60K |

## 6. Official brochure extraction - structured product facts

| # | Product Fact / Policy Mechanic |
| --- | --- |
| 1 | Offers 3 plan options: Level Cover, Increasing Cover, and Level Cover with Return of Premium. |
| 2 | Death benefit payout can be lump sum, monthly income for 10/15/20 years, or a combination of lump sum and monthly income. |
| 3 | Increasing Cover grows Sum Assured by 5% simple per annum at each policy anniversary, capped at 200% of Sum Assured at inception. |
| 4 | Inbuilt Terminal Illness benefit is available for all plan options; terminal illness payout is 50% of Sum Assured on death or INR 1 crore, whichever is lower, as per brochure terms. |
| 5 | Waiver of Premium on Accidental Total and Permanent Disability is inbuilt for eligible policies. |
| 6 | ACI benefit is optional at inception and covers listed critical illnesses subject to waiting period and policy conditions. |
| 7 | Cover Continuance Benefit can allow deferment of base policy premium for up to 12 months while maintaining risk cover, subject to eligibility and conditions. |
| 8 | Instant Payment on Claim can provide accelerated support within 1 working day from claim registration subject to mandatory documents and conditions. |
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
| 1 | Do not position this as an investment return product. |
| 2 | Do not say return of premium applies to all options; it is a specific plan option. |
| 3 | Do not guarantee ACI or instant claim without eligibility, waiting period and document conditions. |


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
When answering about ABSLI Super Term Plan, first identify the product type as **Non-linked, non-participating life individual pure risk premium plan**. Explain benefits only with conditions. Use customer-friendly language. Do not provide final suitability, tax, return or claim decisions. If the customer asks for exact numbers or a recommendation, ask to schedule an RM meeting or use the official benefit illustration.

## 12. Product-wise retrieval examples

| User / Trainer Query | Expected Retrieval Focus |
| --- | --- |
| Explain this plan to a customer in simple words | Sections 3, 4, 5 and 9 |
| What should trainer say if customer asks about returns? | Sections 6, 8 and 9 |
| Is this guaranteed? | Product category + guardrails + golden response dataset |
| How should trainee move to RM meeting? | Golden response style + trainer scoring rubric |




---

<!-- FILE: 03_absli_salaried_term_plan_kb.md -->

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




---

<!-- FILE: 04_absli_fortune_wealth_plan_kb.md -->

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




---

<!-- FILE: 05_absli_platinum_gain_plan_kb.md -->

---
kb_id: absli_sherpa_trainer_absli_platinum_gain_plan
product_name: "ABSLI Platinum Gain Plan"
product_category: "ULIP Plans"
product_type: "Unit-linked, non-participating individual life insurance savings plan"
use_case: "ABSLI Sherpa Trainer"
intended_for: "RAG ingestion, trainer evaluation, RM-meeting nudges, customer-question handling"
source_primary: "https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Platinum_Gain_Plan_V01_Brochure_Web_Version_e9471d7811.pdf"
source_secondary: "Uploaded ABSLI product-benefit matrix and life-insurance golden response dataset"
last_compiled: "2026-05-09"
retrieval_tags: ["ABSLI", "Sherpa Trainer", "ULIP Plans", "ABSLI Platinum Gain Plan", "life insurance", "trainer coaching"]
---
# ABSLI Platinum Gain Plan - Product Knowledge Base for ABSLI Sherpa Trainer

## 1. Purpose of this KB file
This product-wise knowledge base is designed for Sherpa Trainer RAG. It should help the model evaluate whether a trainer is explaining the product correctly, using customer-friendly language, avoiding overcommitment, and moving the discussion toward a Relationship Manager meeting where detailed suitability and documentation can be handled.

## 2. Source scope and reliability

| Source Type | Details | Reliability Use |
| --- | --- | --- |
| Official brochure / supplied URL | https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Platinum_Gain_Plan_V01_Brochure_Web_Version_e9471d7811.pdf | Use for product facts, eligibility, benefit mechanics, exclusions, charges and policy conditions. |
| Uploaded product-benefit matrix | Contains benefits, give-premium example, get-benefit example and recommended premium. | Use for Sherpa demo talk tracks and quick trainer evaluation. |
| Uploaded golden response dataset | Customer-centric Q&A responses that gently move toward RM meetings. | Use for objection handling, generic insurance concepts and safe answer style. |

**Important RAG rule:** If an answer requires exact premium, personalized suitability, tax treatment, underwriting, claim admissibility or current regulatory interpretation, the model should route to RM/advisor review instead of giving a final recommendation.

## 3. Product classification

| Field | Value |
| --- | --- |
| Product Name | ABSLI Platinum Gain Plan |
| Product Category | ULIP Plans |
| Product Type | Unit-linked, non-participating individual life insurance savings plan |
| High-level Positioning | Premium ULIP with life cover, 18 funds, 5 investment strategies, wealth boosters, loyalty additions and return of mortality/premium allocation charges at maturity subject to terms. |
| Trainer Focus | Trainer must explain premium ULIP features with strict market-risk disclosure, while ensuring trainee does not oversell wealth boosters or return of charges as unconditional. |
| Customer-friendly One-liner | This is a market-linked wealth plan with life cover and extra value-enhancement features, suitable only when the customer is comfortable with long-term fund value movement. |

## 4. Benefits from uploaded product matrix

| Benefit Field | Value |
| --- | --- |
| benefit_1 | Flexibility to choose from 5 investment & 18 fund options |
| benefit_2 | Flexible premium payment options - Limited Pay / Regular Pay |
| benefit_3 | Liquidity through systematic withdrawal benefit |
| benefit_4 | No policy Administration Charge |
| benefit_5 | Return of Premium Allocation and mortality Charge at Maturity. |


## 5. Give-get example from uploaded matrix

| Field | Value |
| --- | --- |
| Give / Premium Example | INR 2,00,000 annually for 10 years (total: INR 20,00,000) in a 20-year policy |
| Get / Benefit Example | Maturity: Fund Value : Rs 57,75,675 @8%  and Rs 32,12,058 @ 4%<br>Coverage: Life cover throughout the policy term<br>Other benefits: Potential for even higher returns based on market performance |
| Recommended Premium | 2L |

## 6. Official brochure extraction - structured product facts

| # | Product Fact / Policy Mechanic |
| --- | --- |
| 1 | Provides life cover throughout policy term with 18 fund options and 5 investment strategies. |
| 2 | Choice of Sum Assured multiple: 7X and 10X annualized premium. |
| 3 | Wealth Boosters and Loyalty Additions are added periodically during the policy term to enhance fund value, subject to policy conditions. |
| 4 | No policy administration charge as per brochure key features. |
| 5 | At the end of policy term, fund value may be enhanced by return of total mortality charges and premium allocation charges deducted, subject to all due premiums being paid and policy not being surrendered/discontinued/reduced paid-up. |
| 6 | Minimum entry age is 30 days and maximum entry age is 65 years; maximum maturity age is 85 years as per brochure table. |
| 7 | Limited Pay PPT range is 5 to 12 years and Regular Pay PPT range is 10 to 20 years. |
| 8 | Partial withdrawals are allowed after five complete policy years if policyholder attained age is 18 years or above, subject to withdrawal limits and fund value maintenance. |
| 9 | Settlement option can continue fund management and periodic payouts after maturity for up to 5 years, subject to policy terms. |
| 10 | Maturity illustration in the brochure shows fund value at 4% and 8% for a sample case; these are illustrative, not guaranteed. |


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
| 1 | Do not say returns are guaranteed. |
| 2 | Do not say charge return applies if policy is surrendered/discontinued/reduced paid-up. |
| 3 | Do not ignore five-year lock-in and partial withdrawal conditions. |


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
When answering about ABSLI Platinum Gain Plan, first identify the product type as **Unit-linked, non-participating individual life insurance savings plan**. Explain benefits only with conditions. Use customer-friendly language. Do not provide final suitability, tax, return or claim decisions. If the customer asks for exact numbers or a recommendation, ask to schedule an RM meeting or use the official benefit illustration.

## 12. Product-wise retrieval examples

| User / Trainer Query | Expected Retrieval Focus |
| --- | --- |
| Explain this plan to a customer in simple words | Sections 3, 4, 5 and 9 |
| What should trainer say if customer asks about returns? | Sections 6, 8 and 9 |
| Is this guaranteed? | Product category + guardrails + golden response dataset |
| How should trainee move to RM meeting? | Golden response style + trainer scoring rubric |




---

<!-- FILE: 06_absli_vision_retirement_solution_kb.md -->

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

