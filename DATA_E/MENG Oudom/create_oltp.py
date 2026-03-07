import psycopg2
from psycopg2 import sql

# Configuration
DB_CONFIG = {
    "dbname": "mydatabase",
    "user": "myuser",
    "password": "mypassword",
    "host": "localhost",
    "port": "5432"
}

def create_tables():
    commands = [
        """
        DROP TABLE IF EXISTS order_items CASCADE;
        DROP TABLE IF EXISTS orders CASCADE;
        DROP TABLE IF EXISTS products CASCADE;
        DROP TABLE IF EXISTS customers CASCADE;
        """,
        """
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(50)
        )
        """,
        """
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            price DECIMAL(10, 2)
        )
        """,
        """
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(customer_id),
            order_date DATE,
            store VARCHAR(50),
            updated_at TIMESTAMP
        )
        """,
        """
        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER REFERENCES orders(order_id),
            product_id INTEGER REFERENCES products(product_id),
            quantity INTEGER CHECK (quantity > 0)
        )
        """
    ]

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"Connected to PostgreSQL database: {DB_CONFIG['dbname']}")
        
        for command in commands:
            cur.execute(command)
        
        # Commit the changes
        conn.commit()
        
        print("Tables created successfully.")
        
        # Verification: List tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print("Existing tables in public schema:")
        for table in tables:
            print(f"- {table[0]}")

        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_tables()
