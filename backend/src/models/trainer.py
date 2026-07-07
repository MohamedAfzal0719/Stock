import time
import os
import joblib
import pandas as pd
import numpy as np
import optuna
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from sklearn.model_selection import TimeSeriesSplit
from src.utils.logger import get_logger
from src.models.evaluator import ModelEvaluator

logger = get_logger(__name__)

class MLTrainer:
    def __init__(self, data_path: str, models_dir: str):
        self.data_path = data_path
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.df = self._load_data()
        self.X_train, self.X_test, self.y_train, self.y_test = self._prepare_data()

    def _load_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.data_path)
        if 'Date' in df.columns:
            df.set_index('Date', inplace=True)
        return df

    def _prepare_data(self):
        # We will predict next day's close
        target_col = 'Close'
        # Drop columns that leak the target (e.g., current day's returns, if any, or next day's)
        # Assuming current 'Close' is the target. We must shift features to predict tomorrow.
        # Alternatively, the engineer.py already created lag features. We can use only lag features to predict current Close.
        
        # Select features: all columns containing 'Lag', plus some rolling/calendar if they are historically aligned
        # For a truly safe prediction of 'Close(t)', we can use 'Close_Lag_1', etc.
        features = [col for col in self.df.columns if col not in [target_col, 'Daily_Return', 'Log_Return']]
        
        X = self.df[features]
        y = self.df[target_col]
        
        # Time series split: 80% train, 20% test
        split_idx = int(len(self.df) * 0.8)
        return X.iloc[:split_idx], X.iloc[split_idx:], y.iloc[:split_idx], y.iloc[split_idx:]

    def optimize_and_train(self, model_name: str, n_trials: int = 10) -> dict:
        logger.info(f"Starting optimization for {model_name}...")
        start_time = time.time()
        
        def objective(trial):
            model = self._get_model(model_name, trial)
            # Use TimeSeriesSplit for CV
            tscv = TimeSeriesSplit(n_splits=3)
            cv_scores = []
            
            for train_idx, val_idx in tscv.split(self.X_train):
                X_tr, X_val = self.X_train.iloc[train_idx], self.X_train.iloc[val_idx]
                y_tr, y_val = self.y_train.iloc[train_idx], self.y_train.iloc[val_idx]
                
                model.fit(X_tr, y_tr)
                preds = model.predict(X_val)
                cv_scores.append(np.sqrt(np.mean((y_val - preds)**2)))
            
            return np.mean(cv_scores)

        study = optuna.create_study(direction="minimize")
        study.optimize(objective, n_trials=n_trials)
        
        logger.info(f"Best params for {model_name}: {study.best_params}")
        
        # Train final model on full train set
        best_model = self._get_model(model_name, optuna.trial.FixedTrial(study.best_params))
        
        train_start = time.time()
        best_model.fit(self.X_train, self.y_train)
        train_time = time.time() - train_start
        
        # Evaluate
        inf_start = time.time()
        preds = best_model.predict(self.X_test)
        inf_time = time.time() - inf_start
        
        metrics = ModelEvaluator.compute_regression_metrics(self.y_test.values, preds)
        
        # Save model
        model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
        joblib.dump(best_model, model_path)
        
        result = {
            "Model": model_name,
            **metrics,
            "Training_Time_sec": train_time,
            "Inference_Time_sec": inf_time,
            "Best_Params": study.best_params
        }
        total_time = time.time() - start_time
        logger.info(f"Finished {model_name} in {total_time:.2f}s. RMSE: {metrics['RMSE']:.4f}")
        return result

    def _get_model(self, model_name: str, trial):
        if model_name == "LinearRegression":
            return LinearRegression()
        elif model_name == "RandomForest":
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 200),
                "max_depth": trial.suggest_int("max_depth", 3, 15),
                "random_state": 42
            }
            return RandomForestRegressor(**params)
        elif model_name == "XGBoost":
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 200),
                "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.1, log=True),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "random_state": 42
            }
            return XGBRegressor(**params)
        elif model_name == "LightGBM":
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 200),
                "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.1, log=True),
                "num_leaves": trial.suggest_int("num_leaves", 10, 50),
                "random_state": 42,
                "verbose": -1
            }
            return LGBMRegressor(**params)
        elif model_name == "CatBoost":
            params = {
                "iterations": trial.suggest_int("iterations", 50, 200),
                "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.1, log=True),
                "depth": trial.suggest_int("depth", 3, 10),
                "verbose": 0,
                "random_state": 42
            }
            return CatBoostRegressor(**params)
        elif model_name == "SVR":
            params = {
                "C": trial.suggest_float("C", 0.1, 10.0, log=True),
                "gamma": trial.suggest_categorical("gamma", ["scale", "auto"])
            }
            return SVR(**params)
        else:
            raise ValueError(f"Unknown model: {model_name}")
