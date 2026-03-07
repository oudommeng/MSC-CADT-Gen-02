-- RESET AND SETUP SCRIPT (V3 - USING EXTERNAL .DAT DATA)

-- 1. DELETE OLD TABLES (Reset)
DROP TABLE IF EXISTS fact_sales_v2 CASCADE;
DROP TABLE IF EXISTS dim_customer_v2 CASCADE;
DROP TABLE IF EXISTS dim_product_v2 CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS crm_customer_scores CASCADE;

-- 2. CREATE OLTP TABLES (Storage)
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) -- Using this for City from .dat mapping
);

CREATE TABLE products (
    product_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    store VARCHAR(50),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    order_item_id INT PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id),
    product_id INT NOT NULL REFERENCES products(product_id),
    quantity INT NOT NULL CHECK (quantity > 0)
);

-- 3. INSERT DATA FROM .DAT FILES (Parsed and converted to INSERTs)

-- From 3403.dat (Customers)
INSERT INTO customers (customer_id, name, phone) VALUES 
(1, 'Sok Dara', 'Phnom Penh'),
(2, 'Kim Sreymom', 'Battambang'),
(3, 'Chanthy', 'Siem Reap');

-- From 3404.dat (Products)
INSERT INTO products (product_id, name, category, price) VALUES 
(10, 'Banana', 'Fresh fruit', 0.50),
(11, 'Apple', 'Fresh fruit', 0.80),
(12, 'Candy', 'Candy', 0.30),
(13, 'Milk', 'Dairy', 1.20);

-- From 3405.dat (Orders)
INSERT INTO orders (order_id, customer_id, order_date, store) VALUES 
(1001, 1, '2026-01-02', 'Store_A'),
(1002, 1, '2026-01-03', 'Store_A'),
(1003, 2, '2026-01-03', 'Store_B'),
(1004, 3, '2026-01-04', 'Store_A');

-- From 3406.dat (Order Items)
INSERT INTO order_items (order_item_id, order_id, product_id, quantity) VALUES 
(1, 1001, 10, 10),
(2, 1001, 12, 5),
(3, 1002, 11, 3),
(4, 1003, 10, 20),
(5, 1003, 13, 2),
(6, 1004, 12, 10);
