import requests
import psycopg2
from psycopg2 import sql
import os
from datetime import datetime

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api"
DB_CONFIG = {
    "dbname": "de-week3",
    "user": "postgres",
    "password": "oudom123",
    "host": "localhost",
    "port": "5433"
}
WATERMARK_FILE = "watermark.txt"

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_watermark():
    if os.path.exists(WATERMARK_FILE):
        with open(WATERMARK_FILE, "r") as f:
            return f.read().strip()
    return "2020-01-01T00:00:00Z"

def update_watermark(timestamp):
    with open(WATERMARK_FILE, "w") as f:
        f.write(timestamp)

def fetch_data(endpoint, params=None):
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {endpoint}: {e}")
        return []

def sync_customers(conn):
    customers = fetch_data("customers")
    cur = conn.cursor()
    for cust in customers:
        # Assuming API returns id, name, email. Schema has customer_id, name, phone.
        # Mapping: id->customer_id, name->name, email->phone (placeholder as requested schema has phone)
        cur.execute("""
            INSERT INTO customers (customer_id, name, phone)
            VALUES (%s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE 
            SET name = EXCLUDED.name, phone = EXCLUDED.phone
        """, (cust["id"], cust["name"], cust.get("email", ""))) # Using email for phone slot for now as mock data has email
    conn.commit()
    print(f"Synced {len(customers)} customers.")
    cur.close()

def sync_products(conn):
    products = fetch_data("products")
    cur = conn.cursor()
    for prod in products:
        # Schema: product_id, name, category, price
        # Mock API: id, name, price. Missing category in mock, defaulting to 'General'
        cur.execute("""
            INSERT INTO products (product_id, name, category, price)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (product_id) DO UPDATE 
            SET name = EXCLUDED.name, category = EXCLUDED.category, price = EXCLUDED.price
        """, (prod["id"], prod["name"], "General", prod["price"]))
    conn.commit()
    print(f"Synced {len(products)} products.")
    cur.close()

def process_ingestion():
    conn = get_db_connection()
    
    # 1. Sync Dimensions (Customers, Products) first to satisfy FKs
    sync_customers(conn)
    sync_products(conn)

    # 2. Ingest Orders
    last_watermark = get_watermark()
    print(f"Fetching orders since {last_watermark}...")
    
    orders = fetch_data("orders", params={"since": last_watermark, "page": 1, "limit": 100})
    print(f"Fetched {len(orders)} orders.")

    max_updated_at = last_watermark
    cur = conn.cursor()

    for order in orders:
        order_max_date = order.get("updated_at", "")
        if order_max_date > max_updated_at:
            max_updated_at = order_max_date
            
        # Insert Order
        try:
            cur.execute("""
                INSERT INTO orders (order_id, customer_id, order_date, store, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (order_id) DO UPDATE
                SET customer_id = EXCLUDED.customer_id, 
                    order_date = EXCLUDED.order_date,
                    store = EXCLUDED.store,
                    updated_at = EXCLUDED.updated_at
            """, (order["order_id"], order["customer_id"], order["order_date"], order["store"], order["updated_at"]))

            # Fetch items
            items = fetch_data("order-items", params={"order_id": order["order_id"]})
            
            for item in items:
                # Validation
                if item.get("quantity", 0) <= 0 or item.get("price", 0) < 0:
                    print(f"Skipping invalid item {item}")
                    continue

                # Insert Order Item
                cur.execute("""
                    INSERT INTO order_items (order_item_id, order_id, product_id, quantity)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (order_item_id) DO UPDATE
                    SET order_id = EXCLUDED.order_id,
                        product_id = EXCLUDED.product_id,
                        quantity = EXCLUDED.quantity
                """, (item["order_item_id"], order["order_id"], item["product_id"], item["quantity"]))
            
            conn.commit()
            print(f"Ingested Order {order['order_id']}")

        except Exception as e:
            conn.rollback()
            print(f"Failed to ingest order {order.get('order_id')}: {e}")

    cur.close()
    conn.close()

    if max_updated_at > last_watermark:
        update_watermark(max_updated_at)
        print(f"Updated watermark to {max_updated_at}")
    else:
        print("No new data.")

if __name__ == "__main__":
    process_ingestion()
