-- Part IV: Reverse ETL
-- Objective: Sync processed/scored data back to operational tools (CRM)

-- 1. Create the CRM target table
CREATE TABLE IF NOT EXISTS crm_customer_scores (
    customer_id INT PRIMARY KEY REFERENCES customers(customer_id),
    spend_score DECIMAL(10,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2 & 3. Calculate spend_score and Push (Upsert)
INSERT INTO crm_customer_scores (customer_id, spend_score, updated_at)
SELECT 
    customer_id, 
    SUM(revenue) AS total_spend, 
    CURRENT_TIMESTAMP
FROM mart.fact_sales
GROUP BY customer_id
ON CONFLICT (customer_id) 
DO UPDATE SET 
    spend_score = EXCLUDED.spend_score,
    updated_at = EXCLUDED.updated_at;

-- Verify the results for screenshot
SELECT * FROM crm_customer_scores ORDER BY spend_score DESC;
