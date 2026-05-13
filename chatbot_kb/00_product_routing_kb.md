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
