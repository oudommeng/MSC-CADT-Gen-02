import psycopg2
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Database Configuration (Updated to port 5432)
DB_CONFIG = {
    "dbname": "mydatabase",
    "user": "myuser",
    "password": "mypassword",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def build_dataset():
    query = """
    SELECT 
        o.order_id,
        o.order_date,
        o.store,
        SUM(oi.quantity) as total_qty,
        COUNT(oi.order_item_id) as item_lines,
        AVG(p.price) as avg_price,
        MAX(p.price) as max_price,
        SUM(oi.quantity * p.price) as order_total
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY o.order_id, o.order_date, o.store
    """
    conn = get_db_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def train_model(df):
    # 1. Feature Engineering
    # Convert store to one-hot encoding
    df_ml = pd.get_dummies(df, columns=['store'], prefix='store')
    
    # Extract day_of_week (0=Monday, 6=Sunday)
    df_ml['day_of_week'] = pd.to_datetime(df_ml['order_date']).dt.dayofweek
    
    # 2. Select Features and Target
    feature_cols = [col for col in df_ml.columns if col.startswith('store_')] + \
                   ['total_qty', 'item_lines', 'avg_price', 'max_price', 'day_of_week']
    
    X = df_ml[feature_cols]
    y = df_ml['order_total']
    
    # 3. Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. Train Multiple Linear Regression
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # 5. Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print("--- Model Evaluation ---")
    print(f"MAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R²: {r2:.2f}")
    
    # 6. Coefficients
    print("\n--- Coefficients ---")
    coeff_df = pd.DataFrame({'Feature': feature_cols, 'Coefficient': model.coef_})
    print(coeff_df.sort_values(by='Coefficient', ascending=False))
    
    # 7. Save Predictions
    # To save predictions for the whole dataset for the deliverable
    df['predicted_total'] = model.predict(X)
    df[['order_id', 'order_total', 'predicted_total']].to_csv('order_predictions.csv', index=False)
    print("\nPredictions saved to order_predictions.csv")

if __name__ == "__main__":
    try:
        print("Building dataset from database...")
        data = build_dataset()
        if data.empty:
            print("No data found in database. Please run ingestion first.")
        else:
            print(f"Dataset built with {len(data)} rows.")
            train_model(data)
    except Exception as e:
        print(f"Error: {e}")
