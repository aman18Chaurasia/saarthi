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
