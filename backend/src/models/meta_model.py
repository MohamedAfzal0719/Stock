import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import Ridge, LinearRegression
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from src.models.deep_wrapper import DeepModelWrapper
from src.utils.db import get_db_connection
from src.features.engineer import FeatureStoreManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

class StackingEnsemble:
    """
    Implements a Stacking Meta-Model with Conformal Prediction Intervals
    and Tomorrow Volatility Forecasting.
    """
    def __init__(self, feature_version: str = "v1"):
        self.feature_version = feature_version
        self.models_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "models"
        )
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Load features from Feature Store
        df = FeatureStoreManager.load_features(version=feature_version)
        if df.empty:
            raise ValueError("Feature store is empty. Run FeatureEngineer first.")
            
        self.df = df
        self._prepare_datasets()

    def _prepare_datasets(self):
        # We drop target horizons we aren't predicting in base models
        # Target tomorrow is 'Target_Return_t1'
        self.target_col = 'Target_Return_t1'
        self.vol_target_col = 'Target_Volatility'
        
        # Select predictor features
        non_feature_cols = [
            'Target_Return_t1', 'Target_Return_t3', 'Target_Return_t7', 'Target_Return_t30',
            'Target_Volatility', 'goldbees_close', 'Daily_Return'
        ]
        self.feature_cols = [col for col in self.df.columns if col not in non_feature_cols]
        
        # Drop rows missing target (the last row because it doesn't have a t+1 Close yet)
        df_clean = self.df.dropna(subset=[self.target_col, self.vol_target_col])
        
        self.X = df_clean[self.feature_cols]
        self.y = df_clean[self.target_col]
        self.y_vol = df_clean[self.vol_target_col]
        
        # Chronological train-test split (80% train, 20% test/val)
        split_idx = int(len(df_clean) * 0.8)
        self.X_train, self.X_test = self.X.iloc[:split_idx], self.X.iloc[split_idx:]
        self.y_train, self.y_test = self.y.iloc[:split_idx], self.y.iloc[split_idx:]
        self.y_train_vol, self.y_test_vol = self.y_vol.iloc[:split_idx], self.y_vol.iloc[split_idx:]

    def train_models(self) -> dict:
        """Trains base models, stacking meta-model, conformal interval, and volatility model."""
        logger.info("Training Base Models (XGBoost, LightGBM, CatBoost)...")
        
        # 1. Base Models
        xgb = XGBRegressor(n_estimators=100, learning_rate=0.03, max_depth=5, random_state=42)
        lgb = LGBMRegressor(n_estimators=100, learning_rate=0.03, num_leaves=31, random_state=42, verbose=-1)
        cat = CatBoostRegressor(iterations=100, learning_rate=0.03, depth=6, verbose=0, random_state=42)
        
        # Train-Calibration Split using Walk-Forward TimeSeries Validation
        # This replaces random/standard splitting with robust OOF generation
        tscv = TimeSeriesSplit(n_splits=5)
        
        oof_xgb = np.zeros(len(self.X_train))
        oof_lgb = np.zeros(len(self.X_train))
        oof_dfs = []
        
        for train_index, val_index in tscv.split(self.X_train):
            X_tr, X_v = self.X_train.iloc[train_index], self.X_train.iloc[val_index]
            y_tr, y_v = self.y_train.iloc[train_index], self.y_train.iloc[val_index]
            
            xgb.fit(X_tr, y_tr)
            lgb.fit(X_tr, y_tr)
            cat.fit(X_tr, y_tr)
            
            lstm = DeepModelWrapper(model_type="LSTM", seq_len=60, epochs=30, batch_size=32, patience=5)
            lstm.fit(X_tr, y_tr, X_val=X_v, y_val=y_v)
            
            patchtst = DeepModelWrapper(model_type="PatchTST", seq_len=60, epochs=30, batch_size=32, patience=5)
            patchtst.fit(X_tr, y_tr, X_val=X_v, y_val=y_v)
            
            lstm_res = lstm.predict_advanced(X_v)
            patch_res = patchtst.predict_advanced(X_v)
            
            fold_df = pd.DataFrame({
                'xgb': xgb.predict(X_v),
                'lgb': lgb.predict(X_v),
                'cat': cat.predict(X_v),
                'lstm': lstm_res['pred'],
                'lstm_std': lstm_res['std'],
                'patchtst': patch_res['pred'],
                'patchtst_std': patch_res['std']
            }, index=X_v.index)
            
            for i in range(lstm_res['embed'].shape[1]):
                fold_df[f'lstm_emb_{i}'] = lstm_res['embed'][:, i]
            for i in range(patch_res['embed'].shape[1]):
                fold_df[f'patchtst_emb_{i}'] = patch_res['embed'][:, i]
                
            oof_dfs.append(fold_df)
            
        X_meta_calib = pd.concat(oof_dfs)
        y_calib = self.y_train.loc[X_meta_calib.index]
        
        # 2. Train Meta Stacking Model (Ridge Regression)
        logger.info("Training Stacking Meta-Model (Ridge)...")
        meta_model = Ridge(alpha=1.0)
        meta_model.fit(X_meta_calib, y_calib)
        
        # 3. Calibrate Conformal Prediction Interval (95% coverage)
        # Errors on OOF calibration set
        meta_preds_calib = meta_model.predict(X_meta_calib)
        calib_errors = np.abs(y_calib.values - meta_preds_calib)
        
        # Find the 95th percentile error bound Q
        alpha = 0.05
        q_index = int(np.ceil((1 - alpha) * (len(calib_errors) + 1))) - 1
        q_index = min(max(0, q_index), len(calib_errors) - 1)
        sorted_errors = np.sort(calib_errors)
        self.conformal_Q = float(sorted_errors[q_index])
        logger.info(f"Conformal Calibration error bound (Q) calculated: {round(self.conformal_Q, 4)}")
        
        # Fit base models on full training set for production inference
        logger.info("Refitting base models on full training set...")
        xgb.fit(self.X_train, self.y_train)
        lgb.fit(self.X_train, self.y_train)
        cat.fit(self.X_train, self.y_train)
        
        final_lstm = DeepModelWrapper(model_type="LSTM", seq_len=60, epochs=30, batch_size=32, patience=5)
        # No explicit val set here to force using the last 15% implicitly or train on full if we want.
        final_lstm.fit(self.X_train, self.y_train)
        
        final_patchtst = DeepModelWrapper(model_type="PatchTST", seq_len=60, epochs=30, batch_size=32, patience=5)
        final_patchtst.fit(self.X_train, self.y_train)
        
        lstm_res_full = final_lstm.predict_advanced(self.X_train)
        patch_res_full = final_patchtst.predict_advanced(self.X_train)
        
        X_meta_full = pd.DataFrame({
            'xgb': xgb.predict(self.X_train),
            'lgb': lgb.predict(self.X_train),
            'cat': cat.predict(self.X_train),
            'lstm': lstm_res_full['pred'],
            'lstm_std': lstm_res_full['std'],
            'patchtst': patch_res_full['pred'],
            'patchtst_std': patch_res_full['std']
        }, index=self.X_train.index)
        
        for i in range(lstm_res_full['embed'].shape[1]):
            X_meta_full[f'lstm_emb_{i}'] = lstm_res_full['embed'][:, i]
        for i in range(patch_res_full['embed'].shape[1]):
            X_meta_full[f'patchtst_emb_{i}'] = patch_res_full['embed'][:, i]
            
        meta_model.fit(X_meta_full, self.y_train)
        
        # 4. Train Tomorrow's Volatility Forecaster (LightGBM)
        logger.info("Training 1-Day Volatility Forecaster...")
        vol_model = LGBMRegressor(n_estimators=100, learning_rate=0.03, random_state=42, verbose=-1)
        vol_model.fit(self.X_train, self.y_train_vol)
        
        # Save all models
        logger.info("Saving models to disk...")
        joblib.dump(xgb, os.path.join(self.models_dir, "base_model_xgb.pkl"))
        joblib.dump(lgb, os.path.join(self.models_dir, "base_model_lgb.pkl"))
        joblib.dump(cat, os.path.join(self.models_dir, "base_model_cat.pkl"))
        final_lstm.save(self.models_dir)
        final_patchtst.save(self.models_dir)
        joblib.dump(meta_model, os.path.join(self.models_dir, "meta_stacking_model.pkl"))
        joblib.dump(vol_model, os.path.join(self.models_dir, "volatility_model.pkl"))
        joblib.dump({"Q": self.conformal_Q, "features": self.feature_cols}, os.path.join(self.models_dir, "metadata.pkl"))
        
        # Evaluate on Test Set
        lstm_res_test = final_lstm.predict_advanced(self.X_test)
        patch_res_test = final_patchtst.predict_advanced(self.X_test)
        
        X_meta_test = pd.DataFrame({
            'xgb': xgb.predict(self.X_test),
            'lgb': lgb.predict(self.X_test),
            'cat': cat.predict(self.X_test),
            'lstm': lstm_res_test['pred'],
            'lstm_std': lstm_res_test['std'],
            'patchtst': patch_res_test['pred'],
            'patchtst_std': patch_res_test['std']
        }, index=self.X_test.index)
        
        for i in range(lstm_res_test['embed'].shape[1]):
            X_meta_test[f'lstm_emb_{i}'] = lstm_res_test['embed'][:, i]
        for i in range(patch_res_test['embed'].shape[1]):
            X_meta_test[f'patchtst_emb_{i}'] = patch_res_test['embed'][:, i]
        
        test_preds = meta_model.predict(X_meta_test)
        rmse = np.sqrt(np.mean((self.y_test.values - test_preds) ** 2))
        mae = np.mean(np.abs(self.y_test.values - test_preds))
        
        # Directional Accuracy (predict positive return and actual return is positive, or vice versa)
        sign_pred = np.sign(test_preds - self.X_test['goldbees_open'])
        sign_actual = np.sign(self.y_test.values - self.X_test['goldbees_open'])
        dir_acc = float(np.mean(sign_pred == sign_actual) * 100)
        
        # Save metrics to PostgreSQL
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO model_metrics (trained_at, model_version, model_name, rmse, mae, directional_accuracy, data_drift_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (trained_at) DO NOTHING
        """, (datetime.utcnow(), "v1.0.0", "StackingRegressor", float(rmse), float(mae), float(dir_acc), 0.0))
        conn.commit()
        conn.close()
        
        metrics = {
            "RMSE": rmse,
            "MAE": mae,
            "Directional_Accuracy": dir_acc
        }
        logger.info(f"Model Training completed! RMSE: {round(rmse,4)}, MAE: {round(mae,4)}, Directional Accuracy: {round(dir_acc, 2)}%")
        return metrics

if __name__ == "__main__":
    stack = StackingEnsemble()
    stack.train_models()
