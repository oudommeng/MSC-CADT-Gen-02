-- Part I: Data Mart (Star-Style)
CREATE SCHEMA IF NOT EXISTS mart;

-- 1. Create the Customer Dimension View
CREATE OR REPLACE VIEW mart.dim_customer AS
SELECT customer_id, name, phone
FROM customers;

-- 2. Create the Product Dimension View
CREATE OR REPLACE VIEW mart.dim_product AS
SELECT product_id, name, category, price
FROM products;

-- 3. Create the Fact Sales View
-- Note: grain is order_item
CREATE OR REPLACE VIEW mart.fact_sales AS
SELECT 
    oi.order_item_id, 
    oi.order_id, 
    o.order_date, 
    o.store, 
    o.customer_id, 
    oi.product_id, 
    oi.quantity, 
    p.price,
    (oi.quantity * p.price) AS revenue 
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE oi.quantity > 0 AND p.price >= 0;
