import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
from src.utils.logger import get_logger

logger = get_logger(__name__)

def train_model():
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, "data", "processed", "goldbees_features.csv")
    model_path = os.path.join(base_dir, "models", "rf_model.pkl")

    # 1. Load Data
    logger.info("Loading engineered features...")
    if not os.path.exists(data_path):
        logger.error(f"Data not found at {data_path}. Please run src/features/engineer.py first.")
        return

    df = pd.read_csv(data_path)
    
    # 2. Define Features and Target
    # For example, let's try to predict the 'Close' price or 'Daily_Return'
    # We will predict 'Close' using shifted features to avoid data leakage
    # Ensure 'Date' is not in features
    if 'Date' in df.columns:
        df.set_index('Date', inplace=True)
    
    # Target: The Close price
    target_col = 'Close'
    
    # Features: Everything except the target and some non-predictive columns
    # In a real setup, make sure you don't use current day's price to predict current day's price!
    features = [col for col in df.columns if col not in [target_col, 'Daily_Return', 'Log_Return']]
    
    X = df[features]
    y = df[target_col]

    # 3. Train-Test Split (Chronological split is better for time series)
    logger.info("Splitting data into train and test sets...")
    # 80% train, 20% test, without shuffling to keep chronological order
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # 4. Initialize and Train Model
    logger.info("Initializing RandomForestRegressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    
    logger.info("Training model...")
    model.fit(X_train, y_train)

    # 5. Evaluate Model
    logger.info("Evaluating model on test set...")
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    
    logger.info(f"Test MSE: {mse:.4f}")
    logger.info(f"Test MAE: {mae:.4f}")

    # 6. Save Model
    logger.info(f"Saving model to {model_path}...")
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)
    logger.info("Model saved successfully. Training complete!")

if __name__ == "__main__":
    train_model()
