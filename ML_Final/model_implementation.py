import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import silhouette_score, mean_squared_error, mean_absolute_error, r2_score

# ==========================================
# 1. LOAD AND PREPARE DATA
# ==========================================
# Pointing to the specific Kaggle dataset provided
df = pd.read_csv('dataset/Students Performance Dataset.csv')

# Drop unnecessary identifiers
df = df.drop(columns=['Student_ID', 'First_Name', 'Last_Name', 'Email'], errors='ignore')

# We can also drop "Grade" and "Total_Score" as they are directly derived from Final_Score
df = df.drop(columns=['Grade', 'Total_Score'], errors='ignore')


# Define target and features
target_col = 'Final_Score'
X = df.drop(columns=[target_col])
y = df[target_col]

# Define Feature Groups
behavioral_cols = ['Attendance (%)', 'Study_Hours_per_Week', 'Participation_Score', 
                   'Assignments_Avg', 'Quizzes_Avg', 'Sleep_Hours_per_Night', 'Stress_Level (1-10)']

academic_categorical_cols = ['Department', 'Gender', 'Parent_Education_Level', 'Extracurricular_Activities']
academic_numerical_cols = ['Age', 'Midterm_Score', 'Projects_Score'] # Replace with your actual numerical features

# ==========================================
# 2. DATA SPLITTING (80% Train, 10% Val, 10% Test)
# ==========================================
# First split: 80% Train, 20% Temp (which will become Val and Test)
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.20, random_state=42)

# Second split: Divide the 20% Temp into 10% Val and 10% Test
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.50, random_state=42)

print(f"Train size: {X_train.shape[0]}, Validation size: {X_val.shape[0]}, Test size: {X_test.shape[0]}")

# ==========================================
# 3. STAGE 1: UNSUPERVISED CLUSTERING (K-MEANS)
# ==========================================
print("\n--- STAGE 1: K-Means Clustering ---")

# Step A: Scale only the behavioral features
scaler_behavior = StandardScaler()

# Fit the scaler ONLY on the training data to prevent data leakage, then transform all
X_train_beh = scaler_behavior.fit_transform(X_train[behavioral_cols])
X_val_beh = scaler_behavior.transform(X_val[behavioral_cols])
X_test_beh = scaler_behavior.transform(X_test[behavioral_cols])

# Step B: Train K-Means (Assuming 3 clusters based on Elbow method)
# Note: You can run an elbow method loop here if needed
k = 3 
kmeans = KMeans(n_clusters=k, random_state=42)
train_clusters = kmeans.fit_predict(X_train_beh)

# Step C: Evaluate Clustering
sil_score = silhouette_score(X_train_beh, train_clusters)
print(f"Silhouette Score (Train): {sil_score:.3f}")

# Step D: Apply clusters to Validation and Test sets
val_clusters = kmeans.predict(X_val_beh)
test_clusters = kmeans.predict(X_test_beh)

# Step E: Add the new "Cluster_ID" feature back to the main datasets
X_train = X_train.copy()
X_val = X_val.copy()
X_test = X_test.copy()

X_train['Cluster_ID'] = train_clusters
X_val['Cluster_ID'] = val_clusters
X_test['Cluster_ID'] = test_clusters

# Treat Cluster_ID as a categorical variable for Stage 2
academic_categorical_cols.append('Cluster_ID')

# ==========================================
# 4. STAGE 2: SUPERVISED PREDICTION (RANDOM FOREST)
# ==========================================
print("\n--- STAGE 2: Random Forest Prediction ---")

# Step A: Preprocess the "Academic" features (and the new Cluster_ID)
# We One-Hot Encode categorical columns and Scale numerical ones
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), academic_numerical_cols + behavioral_cols), # Keeping behavioral just in case, or drop them if you only want clusters
        ('cat', OneHotEncoder(handle_unknown='ignore'), academic_categorical_cols)
    ])

# Fit on training data
X_train_processed = preprocessor.fit_transform(X_train)
X_val_processed = preprocessor.transform(X_val)
X_test_processed = preprocessor.transform(X_test)

# Step B: Train the Random Forest Regressor
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train_processed, y_train)

# Step C: Validate the model (Fine-tuning phase)
val_predictions = rf_model.predict(X_val_processed)
val_rmse = np.sqrt(mean_squared_error(y_val, val_predictions))
print(f"Validation RMSE: {val_rmse:.2f}")

# Step D: Final Evaluation on the Unseen Test Set
test_predictions = rf_model.predict(X_test_processed)

test_rmse = np.sqrt(mean_squared_error(y_test, test_predictions))
test_mae = mean_absolute_error(y_test, test_predictions)
test_r2 = r2_score(y_test, test_predictions)

print("\n--- FINAL METRICS (TEST SET) ---")
print(f"RMSE: {test_rmse:.2f} (Average points of error)")
print(f"MAE:  {test_mae:.2f} (Absolute average error)")
print(f"R^2:  {test_r2:.3f} (Accuracy/Explained Variance)")
