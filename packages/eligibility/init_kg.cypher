// SAARTHI Eligibility Knowledge Graph Initialization
// Populates Neo4j with 10 products and their eligibility rules
// Run: docker-compose exec neo4j cypher-shell < packages/eligibility/init_kg.cypher

// Clear existing data
MATCH (n) DETACH DELETE n;

// ============================================================================
// PERSONAL LOAN
// ============================================================================
CREATE (p1:Product {
  id: "personal_loan",
  name: "Personal Loan",
  category: "unsecured",
  max_amount_inr: 1000000,
  tenure_months_max: 60
});

CREATE (r1_1:Rule {
  rule_id: "personal_loan_income_min",
  rule_type: "income_threshold",
  threshold_value: 15000,
  operator: "gte",
  error_message: "Minimum monthly income ₹15,000 required for personal loan"
});

CREATE (r1_2:Rule {
  rule_id: "personal_loan_income_max",
  rule_type: "income_threshold",
  threshold_value: 500000,
  operator: "lte",
  error_message: "Maximum monthly income ₹5,00,000 for personal loan category"
});

CREATE (r1_3:Rule {
  rule_id: "personal_loan_age_min",
  rule_type: "age_threshold",
  threshold_value: 21,
  operator: "gte",
  error_message: "Minimum age 21 years required"
});

MATCH (p:Product {id: "personal_loan"}), (r1:Rule {rule_id: "personal_loan_income_min"})
CREATE (p)-[:HAS_RULE]->(r1);

MATCH (p:Product {id: "personal_loan"}), (r2:Rule {rule_id: "personal_loan_income_max"})
CREATE (p)-[:HAS_RULE]->(r2);

MATCH (p:Product {id: "personal_loan"}), (r3:Rule {rule_id: "personal_loan_age_min"})
CREATE (p)-[:HAS_RULE]->(r3);

// ============================================================================
// HOME LOAN
// ============================================================================
CREATE (p2:Product {
  id: "home_loan",
  name: "Home Loan",
  category: "secured",
  max_amount_inr: 10000000,
  tenure_months_max: 240
});

CREATE (r2_1:Rule {
  rule_id: "home_loan_income_min",
  rule_type: "income_threshold",
  threshold_value: 25000,
  operator: "gte",
  error_message: "Minimum monthly income ₹25,000 required for home loan"
});

CREATE (r2_2:Rule {
  rule_id: "home_loan_age_min",
  rule_type: "age_threshold",
  threshold_value: 21,
  operator: "gte",
  error_message: "Minimum age 21 years required"
});

CREATE (r2_3:Rule {
  rule_id: "home_loan_age_max",
  rule_type: "age_threshold",
  threshold_value: 65,
  operator: "lte",
  error_message: "Maximum age at loan maturity: 65 years"
});

MATCH (p:Product {id: "home_loan"}), (r:Rule {rule_id: "home_loan_income_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "home_loan"}), (r:Rule {rule_id: "home_loan_age_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "home_loan"}), (r:Rule {rule_id: "home_loan_age_max"})
CREATE (p)-[:HAS_RULE]->(r);

// ============================================================================
// EDUCATION LOAN
// ============================================================================
CREATE (p3:Product {
  id: "education_loan",
  name: "Education Loan",
  category: "secured",
  max_amount_inr: 5000000,
  tenure_months_max: 180
});

CREATE (r3_1:Rule {
  rule_id: "education_loan_income_min",
  rule_type: "income_threshold",
  threshold_value: 20000,
  operator: "gte",
  error_message: "Minimum family monthly income ₹20,000 required"
});

CREATE (r3_2:Rule {
  rule_id: "education_loan_age_min",
  rule_type: "age_threshold",
  threshold_value: 18,
  operator: "gte",
  error_message: "Minimum age 18 years required"
});

CREATE (r3_3:Rule {
  rule_id: "education_loan_age_max",
  rule_type: "age_threshold",
  threshold_value: 35,
  operator: "lte",
  error_message: "Maximum age 35 years for education loan"
});

MATCH (p:Product {id: "education_loan"}), (r:Rule {rule_id: "education_loan_income_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "education_loan"}), (r:Rule {rule_id: "education_loan_age_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "education_loan"}), (r:Rule {rule_id: "education_loan_age_max"})
CREATE (p)-[:HAS_RULE]->(r);

// ============================================================================
// GOLD LOAN
// ============================================================================
CREATE (p4:Product {
  id: "gold_loan",
  name: "Gold Loan",
  category: "secured",
  max_amount_inr: 2000000,
  tenure_months_max: 36
});

CREATE (r4_1:Rule {
  rule_id: "gold_loan_income_min",
  rule_type: "income_threshold",
  threshold_value: 10000,
  operator: "gte",
  error_message: "Minimum monthly income ₹10,000 required"
});

CREATE (r4_2:Rule {
  rule_id: "gold_loan_age_min",
  rule_type: "age_threshold",
  threshold_value: 21,
  operator: "gte",
  error_message: "Minimum age 21 years required"
});

CREATE (r4_3:Rule {
  rule_id: "gold_loan_purity_min",
  rule_type: "gold_purity_threshold",
  threshold_value: 18,
  operator: "gte",
  error_message: "Minimum gold purity 18 karats required"
});

MATCH (p:Product {id: "gold_loan"}), (r:Rule {rule_id: "gold_loan_income_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "gold_loan"}), (r:Rule {rule_id: "gold_loan_age_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "gold_loan"}), (r:Rule {rule_id: "gold_loan_purity_min"})
CREATE (p)-[:HAS_RULE]->(r);

// ============================================================================
// CREDIT CARD
// ============================================================================
CREATE (p5:Product {
  id: "credit_card",
  name: "Credit Card",
  category: "unsecured",
  max_limit_inr: 500000,
  tenure_months_max: 0
});

CREATE (r5_1:Rule {
  rule_id: "credit_card_income_min",
  rule_type: "income_threshold",
  threshold_value: 20000,
  operator: "gte",
  error_message: "Minimum monthly income ₹20,000 required for credit card"
});

CREATE (r5_2:Rule {
  rule_id: "credit_card_age_min",
  rule_type: "age_threshold",
  threshold_value: 21,
  operator: "gte",
  error_message: "Minimum age 21 years required"
});

CREATE (r5_3:Rule {
  rule_id: "credit_card_age_max",
  rule_type: "age_threshold",
  threshold_value: 60,
  operator: "lte",
  error_message: "Maximum age 60 years for credit card"
});

MATCH (p:Product {id: "credit_card"}), (r:Rule {rule_id: "credit_card_income_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "credit_card"}), (r:Rule {rule_id: "credit_card_age_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "credit_card"}), (r:Rule {rule_id: "credit_card_age_max"})
CREATE (p)-[:HAS_RULE]->(r);

// ============================================================================
// UNSECURED LOAN
// ============================================================================
CREATE (p6:Product {
  id: "unsecured_loan",
  name: "Unsecured Loan",
  category: "unsecured",
  max_amount_inr: 1500000,
  tenure_months_max: 60
});

CREATE (r6_1:Rule {
  rule_id: "unsecured_loan_income_min",
  rule_type: "income_threshold",
  threshold_value: 15000,
  operator: "gte",
  error_message: "Minimum monthly income ₹15,000 required"
});

CREATE (r6_2:Rule {
  rule_id: "unsecured_loan_age_min",
  rule_type: "age_threshold",
  threshold_value: 23,
  operator: "gte",
  error_message: "Minimum age 23 years required for unsecured loan"
});

CREATE (r6_3:Rule {
  rule_id: "unsecured_loan_age_max",
  rule_type: "age_threshold",
  threshold_value: 58,
  operator: "lte",
  error_message: "Maximum age 58 years for unsecured loan"
});

MATCH (p:Product {id: "unsecured_loan"}), (r:Rule {rule_id: "unsecured_loan_income_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "unsecured_loan"}), (r:Rule {rule_id: "unsecured_loan_age_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "unsecured_loan"}), (r:Rule {rule_id: "unsecured_loan_age_max"})
CREATE (p)-[:HAS_RULE]->(r);

// ============================================================================
// LOAN AGAINST PROPERTY (LAP)
// ============================================================================
CREATE (p7:Product {
  id: "lap_secured",
  name: "Loan Against Property",
  category: "secured",
  max_amount_inr: 20000000,
  tenure_months_max: 180
});

CREATE (r7_1:Rule {
  rule_id: "lap_income_min",
  rule_type: "income_threshold",
  threshold_value: 30000,
  operator: "gte",
  error_message: "Minimum monthly income ₹30,000 required for LAP"
});

CREATE (r7_2:Rule {
  rule_id: "lap_age_min",
  rule_type: "age_threshold",
  threshold_value: 25,
  operator: "gte",
  error_message: "Minimum age 25 years required"
});

CREATE (r7_3:Rule {
  rule_id: "lap_age_max",
  rule_type: "age_threshold",
  threshold_value: 65,
  operator: "lte",
  error_message: "Maximum age at loan maturity: 65 years"
});

MATCH (p:Product {id: "lap_secured"}), (r:Rule {rule_id: "lap_income_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "lap_secured"}), (r:Rule {rule_id: "lap_age_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "lap_secured"}), (r:Rule {rule_id: "lap_age_max"})
CREATE (p)-[:HAS_RULE]->(r);

// ============================================================================
// COMMERCIAL VEHICLE LOAN
// ============================================================================
CREATE (p8:Product {
  id: "commercial_vehicle",
  name: "Commercial Vehicle Loan",
  category: "secured",
  max_amount_inr: 5000000,
  tenure_months_max: 84
});

CREATE (r8_1:Rule {
  rule_id: "commercial_vehicle_income_min",
  rule_type: "income_threshold",
  threshold_value: 25000,
  operator: "gte",
  error_message: "Minimum monthly income ₹25,000 required"
});

CREATE (r8_2:Rule {
  rule_id: "commercial_vehicle_age_min",
  rule_type: "age_threshold",
  threshold_value: 21,
  operator: "gte",
  error_message: "Minimum age 21 years required"
});

CREATE (r8_3:Rule {
  rule_id: "commercial_vehicle_age_max",
  rule_type: "age_threshold",
  threshold_value: 65,
  operator: "lte",
  error_message: "Maximum age 65 years for commercial vehicle loan"
});

MATCH (p:Product {id: "commercial_vehicle"}), (r:Rule {rule_id: "commercial_vehicle_income_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "commercial_vehicle"}), (r:Rule {rule_id: "commercial_vehicle_age_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "commercial_vehicle"}), (r:Rule {rule_id: "commercial_vehicle_age_max"})
CREATE (p)-[:HAS_RULE]->(r);

// ============================================================================
// FOUR-WHEELER LOAN
// ============================================================================
CREATE (p9:Product {
  id: "four_wheeler",
  name: "Four-Wheeler Loan",
  category: "secured",
  max_amount_inr: 3000000,
  tenure_months_max: 84
});

CREATE (r9_1:Rule {
  rule_id: "four_wheeler_income_min",
  rule_type: "income_threshold",
  threshold_value: 20000,
  operator: "gte",
  error_message: "Minimum monthly income ₹20,000 required for car loan"
});

CREATE (r9_2:Rule {
  rule_id: "four_wheeler_age_min",
  rule_type: "age_threshold",
  threshold_value: 21,
  operator: "gte",
  error_message: "Minimum age 21 years required"
});

CREATE (r9_3:Rule {
  rule_id: "four_wheeler_age_max",
  rule_type: "age_threshold",
  threshold_value: 60,
  operator: "lte",
  error_message: "Maximum age 60 years for car loan"
});

MATCH (p:Product {id: "four_wheeler"}), (r:Rule {rule_id: "four_wheeler_income_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "four_wheeler"}), (r:Rule {rule_id: "four_wheeler_age_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "four_wheeler"}), (r:Rule {rule_id: "four_wheeler_age_max"})
CREATE (p)-[:HAS_RULE]->(r);

// ============================================================================
// MSME BUSINESS LOAN
// ============================================================================
CREATE (p10:Product {
  id: "msme_business",
  name: "MSME Business Loan",
  category: "secured",
  max_amount_inr: 10000000,
  tenure_months_max: 120
});

CREATE (r10_1:Rule {
  rule_id: "msme_revenue_min",
  rule_type: "revenue_threshold",
  threshold_value: 50000,
  operator: "gte",
  error_message: "Minimum monthly business revenue ₹50,000 required"
});

CREATE (r10_2:Rule {
  rule_id: "msme_age_min",
  rule_type: "age_threshold",
  threshold_value: 25,
  operator: "gte",
  error_message: "Minimum age 25 years required for business loan"
});

CREATE (r10_3:Rule {
  rule_id: "msme_business_vintage_min",
  rule_type: "business_vintage_threshold",
  threshold_value: 12,
  operator: "gte",
  error_message: "Minimum 12 months business vintage required"
});

MATCH (p:Product {id: "msme_business"}), (r:Rule {rule_id: "msme_revenue_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "msme_business"}), (r:Rule {rule_id: "msme_age_min"})
CREATE (p)-[:HAS_RULE]->(r);

MATCH (p:Product {id: "msme_business"}), (r:Rule {rule_id: "msme_business_vintage_min"})
CREATE (p)-[:HAS_RULE]->(r);

// Verification query
MATCH (p:Product)-[:HAS_RULE]->(r:Rule)
RETURN p.name AS product, COUNT(r) AS rule_count
ORDER BY p.name;
