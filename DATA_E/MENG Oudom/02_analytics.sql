-- Part II: Serve for Analytics using File Exchange

-- 1. SQL Query for CSV-style result
-- This query aggregates data from the fact_sales view created in Part I
SELECT
    TO_CHAR(order_date, 'YYYY-MM') AS month,
    store,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(revenue) AS total_revenue
FROM
    mart.fact_sales
GROUP BY
    1, 2
ORDER BY
    1, 2;

/*
-- Answers to Questions:

-- Q: When is file exchange a good idea?
-- A: File exchange is a good idea when:
--    1. Low Frequency: Data is shared occasionally (daily/weekly) rather than in real-time.
--    2. Simplicity: The consumer doesn't have direct access to the database or an API (e.g., non-technical users, external partners).
--    3. Tool Compatibility: The consumer uses tools like Excel, Google Sheets, or specialized software that easily imports CSV/Excel files.
--    4. Decoupling: You want to provide a snapshot of data without giving the consumer any direct connection to your operational or warehouse systems.

-- Q: What is the biggest limitation if you email Excel files?
-- A: The biggest limitation is "Single Source of Truth" and "Data Freshness" issues.
--    Once an Excel file is emailed, it becomes a static, disconnected copy. If the source data changes, 
--    the emailed file is immediately outdated. Furthermore, multiple versions of the "same" report 
--    can circulate (e.g., "Report_v1.xls", "Report_v2_FINAL.xls"), leading to confusion and 
--    conflicting numbers across teams.
*/
