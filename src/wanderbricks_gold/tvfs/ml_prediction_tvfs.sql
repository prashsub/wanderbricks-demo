-- =============================================================================
-- ML Model Prediction TVFs for Genie Space Integration
-- =============================================================================
-- These TVFs provide natural language access to ML model predictions
-- Reference: https://docs.databricks.com/aws/en/genie/trusted-assets#tips-for-writing-functions

-- =============================================================================
-- 1. DEMAND PREDICTIONS TVF
-- =============================================================================
-- Purpose: Get predicted booking demand for properties
-- Sample questions:
--   "What are the demand predictions for properties in Miami?"
--   "Show me high-demand properties for next month"
--   "Which properties have the highest predicted bookings?"

CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_demand_predictions(
    p_destination_id BIGINT DEFAULT NULL,
    p_min_predicted_bookings DECIMAL(10,2) DEFAULT 0
)
RETURNS TABLE (
    property_id BIGINT,
    predicted_bookings DECIMAL(10,2),
    scoring_date DATE,
    model_name STRING
)
LANGUAGE SQL
COMMENT 'Returns predicted booking demand for properties. Use: "What properties have high predicted demand?" or "Show demand predictions for destination X"'
RETURN
    SELECT 
        property_id,
        predicted_bookings,
        scoring_date,
        model_name
    FROM ${catalog}.${ml_schema}.demand_predictions
    WHERE (p_destination_id IS NULL OR destination_id = p_destination_id)
      AND predicted_bookings >= p_min_predicted_bookings
    ORDER BY predicted_bookings DESC
    LIMIT 1000;


-- =============================================================================
-- 2. CONVERSION PREDICTIONS TVF
-- =============================================================================
-- Purpose: Get predicted conversion probability for property engagements
-- Sample questions:
--   "Which properties have high conversion likelihood?"
--   "Show me properties with conversion probability above 70%"
--   "What's the conversion prediction for property X?"

CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_conversion_predictions(
    p_min_probability DECIMAL(5,4) DEFAULT 0.5,
    p_property_id BIGINT DEFAULT NULL
)
RETURNS TABLE (
    property_id BIGINT,
    conversion_probability DECIMAL(5,4),
    predicted_conversion INT,
    scoring_date DATE,
    model_name STRING
)
LANGUAGE SQL
COMMENT 'Returns predicted booking conversion probability for properties. Use: "Which properties have high conversion likelihood?" or "Show properties likely to convert"'
RETURN
    SELECT 
        property_id,
        conversion_probability,
        predicted_conversion,
        scoring_date,
        model_name
    FROM ${catalog}.${ml_schema}.conversion_predictions
    WHERE conversion_probability >= p_min_probability
      AND (p_property_id IS NULL OR property_id = p_property_id)
    ORDER BY conversion_probability DESC
    LIMIT 1000;


-- =============================================================================
-- 3. PRICING RECOMMENDATIONS TVF
-- =============================================================================
-- Purpose: Get optimal pricing recommendations for properties
-- Sample questions:
--   "What prices should we set for Miami properties?"
--   "Show pricing recommendations for property X"
--   "Which properties need price adjustments?"

CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_pricing_recommendations(
    p_destination_id BIGINT DEFAULT NULL,
    p_property_id BIGINT DEFAULT NULL
)
RETURNS TABLE (
    property_id BIGINT,
    recommended_price DECIMAL(18,2),
    scoring_date DATE,
    model_name STRING
)
LANGUAGE SQL
COMMENT 'Returns ML-optimized pricing recommendations for properties. Use: "What are the pricing recommendations?" or "Show optimal prices for destination X"'
RETURN
    SELECT 
        property_id,
        recommended_price,
        scoring_date,
        model_name
    FROM ${catalog}.${ml_schema}.pricing_recommendations
    WHERE (p_destination_id IS NULL OR destination_id = p_destination_id)
      AND (p_property_id IS NULL OR property_id = p_property_id)
    ORDER BY property_id
    LIMIT 1000;


-- =============================================================================
-- 4. CUSTOMER LTV PREDICTIONS TVF
-- =============================================================================
-- Purpose: Get predicted lifetime value for customers
-- Sample questions:
--   "Who are our VIP customers?"
--   "Show high-value customers"
--   "What's the predicted LTV for customer X?"

CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_customer_ltv_predictions(
    p_ltv_segment STRING DEFAULT NULL,
    p_min_ltv DECIMAL(18,2) DEFAULT 0,
    p_user_id BIGINT DEFAULT NULL
)
RETURNS TABLE (
    user_id BIGINT,
    predicted_ltv_12m DECIMAL(18,2),
    ltv_segment STRING,
    scoring_date DATE,
    model_name STRING
)
LANGUAGE SQL
COMMENT 'Returns predicted 12-month lifetime value for customers. LTV segments: VIP (>$2500), High ($1000-2500), Medium ($500-1000), Low (<$500). Use: "Show VIP customers" or "Who are our highest value users?"'
RETURN
    SELECT 
        user_id,
        predicted_ltv_12m,
        ltv_segment,
        scoring_date,
        model_name
    FROM ${catalog}.${ml_schema}.customer_ltv_predictions
    WHERE (p_ltv_segment IS NULL OR ltv_segment = p_ltv_segment)
      AND predicted_ltv_12m >= p_min_ltv
      AND (p_user_id IS NULL OR user_id = p_user_id)
    ORDER BY predicted_ltv_12m DESC
    LIMIT 1000;


-- =============================================================================
-- 5. VIP CUSTOMERS SHORTCUT TVF
-- =============================================================================
-- Purpose: Quick access to VIP customers
-- Sample questions:
--   "Show me VIP customers"
--   "Who are our top customers?"

CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_vip_customers()
RETURNS TABLE (
    user_id BIGINT,
    predicted_ltv_12m DECIMAL(18,2),
    ltv_segment STRING,
    scoring_date DATE
)
LANGUAGE SQL
COMMENT 'Returns VIP customers (predicted LTV > $2500). Use: "Show me VIP customers" or "Who are our top customers?"'
RETURN
    SELECT 
        user_id,
        predicted_ltv_12m,
        ltv_segment,
        scoring_date
    FROM ${catalog}.${ml_schema}.customer_ltv_predictions
    WHERE ltv_segment = 'VIP'
    ORDER BY predicted_ltv_12m DESC
    LIMIT 500;


-- =============================================================================
-- 6. HIGH DEMAND PROPERTIES SHORTCUT TVF
-- =============================================================================
-- Purpose: Quick access to high-demand properties
-- Sample questions:
--   "Which properties have high demand?"
--   "Show popular properties"

CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_high_demand_properties(
    p_top_n INT DEFAULT 100
)
RETURNS TABLE (
    property_id BIGINT,
    predicted_bookings DECIMAL(10,2),
    scoring_date DATE
)
LANGUAGE SQL
COMMENT 'Returns properties with highest predicted booking demand. Use: "Which properties have high demand?" or "Show popular properties"'
RETURN
    SELECT 
        property_id,
        predicted_bookings,
        scoring_date
    FROM ${catalog}.${ml_schema}.demand_predictions
    ORDER BY predicted_bookings DESC
    LIMIT p_top_n;


-- =============================================================================
-- 7. ML MODEL PERFORMANCE SUMMARY TVF
-- =============================================================================
-- Purpose: Get summary of all ML predictions
-- Sample questions:
--   "Show me ML model summary"
--   "What predictions are available?"

CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_ml_predictions_summary()
RETURNS TABLE (
    model_name STRING,
    prediction_count BIGINT,
    latest_scoring_date DATE,
    description STRING
)
LANGUAGE SQL
COMMENT 'Returns summary of all ML model predictions available. Use: "Show ML predictions summary" or "What ML models are available?"'
RETURN
    SELECT 
        'demand_predictor' as model_name,
        COUNT(*) as prediction_count,
        MAX(scoring_date) as latest_scoring_date,
        'Predicts booking demand by property' as description
    FROM ${catalog}.${ml_schema}.demand_predictions
    
    UNION ALL
    
    SELECT 
        'conversion_predictor' as model_name,
        COUNT(*) as prediction_count,
        MAX(scoring_date) as latest_scoring_date,
        'Predicts booking conversion probability' as description
    FROM ${catalog}.${ml_schema}.conversion_predictions
    
    UNION ALL
    
    SELECT 
        'pricing_optimizer' as model_name,
        COUNT(*) as prediction_count,
        MAX(scoring_date) as latest_scoring_date,
        'Recommends optimal property prices' as description
    FROM ${catalog}.${ml_schema}.pricing_recommendations
    
    UNION ALL
    
    SELECT 
        'customer_ltv_predictor' as model_name,
        COUNT(*) as prediction_count,
        MAX(scoring_date) as latest_scoring_date,
        'Predicts customer 12-month lifetime value' as description
    FROM ${catalog}.${ml_schema}.customer_ltv_predictions;

