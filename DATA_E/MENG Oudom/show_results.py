import psycopg2

DB_CONFIG = {
    "dbname": "de-week3",
    "user": "postgres",
    "password": "oudom123",
    "host": "localhost",
    "port": "5432"
}

def show_results():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Ensure mart schema and views exist
        with open('01_data_mart.sql', 'r') as f:
            cur.execute(f.read())
            
        # Run Reverse ETL logic
        with open('04_reverse_etl.sql', 'r') as f:
            cur.execute(f.read())
            
        # Fetch results
        cur.execute("SELECT * FROM crm_customer_scores LIMIT 10;")
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        
        print("\n--- CRM Customer Scores (Reverse ETL Result) ---")
        # Simple table formatting
        header = " | ".join(colnames)
        print(header)
        print("-" * len(header))
        for row in rows:
            print(" | ".join(map(str, row)))
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_results()
