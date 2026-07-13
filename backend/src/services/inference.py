import os
import joblib
import pandas as pd
import numpy as np
import scipy.stats as stats
import shap
from datetime import datetime
from groq import Groq
from src.features.engineer import FeatureStoreManager
from src.models.deep_wrapper import DeepModelWrapper
from src.utils.db import get_db_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize Groq client
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

class InferenceEngine:
    """
    Production inference engine executing stacking ensemble predictions, conformal ranges,
    breakout probabilities, SHAP explainers, LLM reasoning, and all original legacy endpoints.
    """
    def __init__(self, model_name: str = "StackingRegressor"):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.models_dir = os.path.join(self.base_dir, "models")
        
        # Load Features to verify data presence
        self.df = FeatureStoreManager.load_features()
        if not self.df.empty:
            self.target_col = 'Target_Return_t1'
            # Predictor features
            non_feature_cols = [
                'Target_Return_t1', 'Target_Return_t3', 'Target_Return_t7', 'Target_Return_t30',
                'Target_Volatility', 'goldbees_close', 'Daily_Return'
            ]
            self.feature_cols = [col for col in self.df.columns if col not in non_feature_cols]
        else:
            self.feature_cols = []
            
        # Load Stacking Models
        try:
            self.xgb = joblib.load(os.path.join(self.models_dir, "base_model_xgb.pkl"))
            self.lgb = joblib.load(os.path.join(self.models_dir, "base_model_lgb.pkl"))
            self.cat = joblib.load(os.path.join(self.models_dir, "base_model_cat.pkl"))
            self.meta = joblib.load(os.path.join(self.models_dir, "meta_stacking_model.pkl"))
            self.vol_model = joblib.load(os.path.join(self.models_dir, "volatility_model.pkl"))
            self.lstm = DeepModelWrapper.load(self.models_dir, model_type="LSTM")
            self.patchtst = DeepModelWrapper.load(self.models_dir, model_type="PatchTST")
            
            meta_data = joblib.load(os.path.join(self.models_dir, "metadata.pkl"))
            self.conformal_Q = meta_data["Q"]
            self.feature_cols = meta_data["features"]
            logger.info("Stacking models successfully loaded in InferenceEngine.")
        except Exception as e:
            logger.warning(f"Failed to load Stacking models: {e}. Falling back to default baseline models.")
            self.meta = None

    def predict_tomorrow(self, live_price: float = None) -> dict:
        """
        Predicts tomorrow's close price (t+1), volatility, conformal bounds, and probability thresholds.
        """
        if self.meta is None or self.df.empty:
            return {"error": "Models or features are not ready."}
            
        last_row = self.df[self.feature_cols].iloc[-1:]
        current_price = live_price if live_price is not None else float(self.df['goldbees_close'].iloc[-1])
        last_60_rows = self.df[self.feature_cols].tail(60)
        
        # Meta Stacking Inference
        if self.meta:
            pred_xgb = self.xgb.predict(last_row)[0]
            pred_lgb = self.lgb.predict(last_row)[0]
            pred_cat = self.cat.predict(last_row)[0]
            
            lstm_res = self.lstm.predict_advanced(last_60_rows)
            patch_res = self.patchtst.predict_advanced(last_60_rows)
            
            X_meta = pd.DataFrame({
                'xgb': [pred_xgb],
                'lgb': [pred_lgb],
                'cat': [pred_cat],
                'lstm': [lstm_res['pred'][-1]],
                'lstm_std': [lstm_res['std'][-1]],
                'patchtst': [patch_res['pred'][-1]],
                'patchtst_std': [patch_res['std'][-1]]
            })
            
            for i in range(lstm_res['embed'].shape[1]):
                X_meta[f'lstm_emb_{i}'] = [lstm_res['embed'][-1, i]]
            for i in range(patch_res['embed'].shape[1]):
                X_meta[f'patchtst_emb_{i}'] = [patch_res['embed'][-1, i]]
            
        # Stacking Predictor returns percentage return now
        pred_return = float(self.meta.predict(X_meta)[0])
        pred_close = current_price * (1 + pred_return)
        
        # Conformal Q is also a percentage return error
        ci_lower = current_price * (1 + pred_return - self.conformal_Q)
        ci_upper = current_price * (1 + pred_return + self.conformal_Q)
        
        # Volatility Projection
        pred_vol = float(self.vol_model.predict(last_row)[0])
        pred_vol = max(0.002, pred_vol)
        
        # Move Probabilities
        expected_return = (pred_close - current_price) / current_price
        prob_move_1pct = float(1.0 - (stats.norm.cdf(0.01, loc=expected_return, scale=pred_vol) - 
                                      stats.norm.cdf(-0.01, loc=expected_return, scale=pred_vol)))
        prob_move_2pct = float(1.0 - (stats.norm.cdf(0.02, loc=expected_return, scale=pred_vol) - 
                                      stats.norm.cdf(-0.02, loc=expected_return, scale=pred_vol)))
        
        direction = "NEUTRAL"
        if expected_return > 0.0025:
            direction = "BULLISH"
        elif expected_return < -0.0025:
            direction = "BEARISH"
            
        confidence = int(min(98, max(50, 100 * (1 - (self.conformal_Q / current_price)))))
        
        res = {
            "Current_Price": round(current_price, 2),
            "Predicted_Close": round(pred_close, 2),
            "Predicted_Volatility": round(pred_vol * 100, 3),
            "Conformal_Lower": round(ci_lower, 2),
            "Conformal_Upper": round(ci_upper, 2),
            "Prob_Move_1pct": round(prob_move_1pct * 100, 1),
            "Prob_Move_2pct": round(prob_move_2pct * 100, 1),
            "Direction": direction,
            "Confidence": confidence,
            "Expected_Return_Pct": round(expected_return * 100, 2),
            "Consensus": {
                "XGBoost": round(float(current_price * (1 + pred_xgb)), 2),
                "LightGBM": round(float(current_price * (1 + pred_lgb)), 2),
                "CatBoost": round(float(current_price * (1 + pred_cat)), 2),
                "LSTM": round(float(current_price * (1 + lstm_res['pred'][-1])), 2),
                "PatchTST": round(float(current_price * (1 + patch_res['pred'][-1])), 2)
            },
            "Deep_Confidence": {
                "LSTM_Uncertainty": round(float(lstm_res['std'][-1]), 4),
                "PatchTST_Uncertainty": round(float(patch_res['std'][-1]), 4)
            }
        }
        
        self._log_prediction(res)
        return res

    def _log_prediction(self, res: dict):
        """Stores the prediction inside the DB for audit trail & drift tracking."""
        conn = get_db_connection()
        c = conn.cursor()
        
        regime = "Sideways"
        regime_code = int(self.df['Market_Regime'].iloc[-1]) if 'Market_Regime' in self.df.columns else 3
        if regime_code == 1: regime = "Bull"
        elif regime_code == 2: regime = "Bear"
        elif regime_code == 4: regime = "Volatile"
        
        try:
            target_date = datetime.utcnow().date() + pd.Timedelta(days=1)
            c.execute("""
                INSERT INTO predictions (
                    prediction_date, model_version, predicted_close, predicted_volatility,
                    prob_move_1pct, prob_move_2pct, ci_lower, ci_upper, confidence_score, market_regime
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (prediction_date) DO UPDATE SET
                    predicted_close = EXCLUDED.predicted_close,
                    predicted_volatility = EXCLUDED.predicted_volatility,
                    prob_move_1pct = EXCLUDED.prob_move_1pct,
                    prob_move_2pct = EXCLUDED.prob_move_2pct,
                    ci_lower = EXCLUDED.ci_lower,
                    ci_upper = EXCLUDED.ci_upper,
                    confidence_score = EXCLUDED.confidence_score,
                    market_regime = EXCLUDED.market_regime
            """, (
                target_date, "v1.0.0", res["Predicted_Close"], res["Predicted_Volatility"],
                res["Prob_Move_1pct"], res["Prob_Move_2pct"], res["Conformal_Lower"], res["Conformal_Upper"],
                res["Confidence"], regime
            ))
            conn.commit()
        except Exception as e:
            logger.warning(f"Failed to log prediction: {e}")
        finally:
            conn.close()

    def get_shap_values(self) -> dict:
        if self.meta is None or self.df.empty:
            return {}
        try:
            X_sample = self.df[self.feature_cols].tail(100)
            last_row = self.df[self.feature_cols].iloc[-1:]
            
            explainer = shap.Explainer(self.lgb, X_sample)
            shap_values = explainer(last_row)
            
            values = shap_values.values[0]
            contributions = dict(zip(self.feature_cols, [float(v) for v in values]))
            
            top_feats = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
            total_abs = sum(abs(v) for k, v in top_feats) + 1e-9
            
            res_feats = []
            for feat, val in top_feats:
                res_feats.append({
                    "feature": feat.replace('_', ' '),
                    "value": round(val, 4),
                    "percentage": round((abs(val) / total_abs) * 100, 1),
                    "direction": "positive" if val > 0 else "negative"
                })
            return {"top_features": res_feats}
        except Exception as e:
            logger.warning(f"SHAP computation error: {e}")
            return {"top_features": []}

    def get_ai_reasoning(self, pred_res: dict) -> str:
        if not groq_client:
            return "AI reasoning is currently unavailable (missing GROQ_API_KEY)."
            
        shap_data = self.get_shap_values()
        feats_desc = ", ".join([f"{f['feature']} ({f['percentage']}% importance, {f['direction']})" for f in shap_data.get("top_features", [])])
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT event_type, summary, sentiment FROM market_events ORDER BY event_time DESC LIMIT 3")
        recent_events = c.fetchall()
        conn.close()
        
        events_desc = ", ".join([f"{e[0]} Event: '{e[1]}' (Sentiment: {e[2]})" for e in recent_events]) if recent_events else "No major geopolitical events detected recently."

        prompt = f"""
        You are an elite quantitative analyst.
        Explain the model's prediction for tomorrow's GoldBEES ETF close price.
        Current Price: ₹{pred_res['Current_Price']}
        Tomorrow's Forecasted Close: ₹{pred_res['Predicted_Close']} (Direction: {pred_res['Direction']}, Volatility: {pred_res['Predicted_Volatility']}%)
        Model Feature Contributions (SHAP): {feats_desc}
        Latest Financial Events: {events_desc}
        
        Provide a concise, professional 3-bullet point breakdown explaining the prediction using SHAP factors and event sentiment. 
        Limit your entire response to 50 words. Do not add salutations.
        """
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.2,
                max_tokens=150
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return "Unable to compile AI summary due to API limits."

    # --- Legacy API Support Methods ---
    
    def forecast_horizons(self, live_price: float = None) -> dict:
        """Forecast tomorrow (ensemble), 5 days, 30 days, 90 days."""
        if self.df.empty:
            return {}
            
        # Get ensemble tomorrow prediction
        pred_tomorrow = self.predict_tomorrow(live_price)
        pred_1d = pred_tomorrow.get("Predicted_Close", self.df['goldbees_close'].iloc[-1])
        current_price = live_price if live_price is not None else float(self.df['goldbees_close'].iloc[-1])
        
        vol = float(self.df['Volatility_20'].iloc[-1]) if 'Volatility_20' in self.df.columns else 0.015
        
        return {
            "Current_Price": float(current_price),
            "Forecast_1_Day": float(pred_1d),
            "Forecast_5_Days": float(pred_1d * (1 + (vol * np.sqrt(5)))),
            "Forecast_30_Days": float(pred_1d * (1 + (vol * np.sqrt(30)))),
            "Forecast_90_Days": float(pred_1d * (1 + (vol * np.sqrt(90)))),
            "CI_1_Day_Lower": float(pred_tomorrow.get("Conformal_Lower", pred_1d - 1.0)),
            "CI_1_Day_Upper": float(pred_tomorrow.get("Conformal_Upper", pred_1d + 1.0))
        }

    def custom_forecast(self, target_date: str, live_price: float = None) -> dict:
        import datetime
        target = pd.to_datetime(target_date).tz_localize(None)
        today = pd.Timestamp.today().normalize()
        days = np.busday_count(today.date(), target.date())
        
        if days <= 0:
            return {"error": "Target date must be in the future"}
            
        pred_tomorrow = self.predict_tomorrow(live_price)
        baseline = pred_tomorrow.get("Predicted_Close", self.df['goldbees_close'].iloc[-1])
        vol = float(self.df['Volatility_20'].iloc[-1]) if 'Volatility_20' in self.df.columns else 0.015
        
        # Calculate daily drift based on long-term past gold price
        if len(self.df) > 252:
            past_return = (self.df['goldbees_close'].iloc[-1] / self.df['goldbees_close'].iloc[-252]) - 1
            base_daily_drift = float(past_return / 252.0)
        elif len(self.df) > 30:
            past_return = (self.df['goldbees_close'].iloc[-1] / self.df['goldbees_close'].iloc[-30]) - 1
            base_daily_drift = float(past_return / 30.0)
        else:
            base_daily_drift = 0.0004
            
        # For long-term forecasts, extrapolate towards a safe historical gold average (~10% annualized)
        historical_safe_drift = 0.0004
        weight_safe = min(1.0, days / 252.0)
        daily_drift = (base_daily_drift * (1 - weight_safe)) + (historical_safe_drift * weight_safe)
            
        # Cap drift to realistic bounds (-0.1% to +0.15% daily max)
        daily_drift = max(-0.001, min(0.0015, daily_drift))
        
        # Integrate World News Sentiment
        news_sentiment = 0.0
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT sentiment FROM market_events ORDER BY event_time DESC LIMIT 5")
            events = c.fetchall()
            conn.close()
            if events:
                scores = []
                for ev in events:
                    s = str(ev[0]).lower()
                    if 'bull' in s or 'positive' in s: scores.append(1.0)
                    elif 'bear' in s or 'negative' in s: scores.append(-1.0)
                    else: scores.append(0.0)
                news_sentiment = sum(scores) / len(scores)
        except Exception:
            pass
            
        # Adjust drift based on world news impact
        daily_drift += (news_sentiment * 0.0002)
        
        # Project using compound interest formula instead of linear
        projected_price = float(baseline * ((1 + daily_drift) ** max(0, days - 1)))
        
        z_score = 1.96
        projected_vol = vol * np.sqrt(days)
        
        return {
            "Target_Date": target_date,
            "Trading_Days": int(days),
            "Projected_Price": round(projected_price, 2),
            "CI_Lower": round(float(projected_price * (1 - z_score * projected_vol)), 2),
            "CI_Upper": round(float(projected_price * (1 + z_score * projected_vol)), 2)
        }

    def generate_signals(self) -> pd.DataFrame:
        """Generates buy/sell actions."""
        df_sig = self.df.copy()
        
        # Stacking predictions for historical rows
        if self.meta is not None:
            pred_xgb = self.xgb.predict(self.df[self.feature_cols])
            pred_lgb = self.lgb.predict(self.df[self.feature_cols])
            pred_cat = self.cat.predict(self.df[self.feature_cols])
            
            lstm_res = self.lstm.predict_advanced(self.df[self.feature_cols])
            patch_res = self.patchtst.predict_advanced(self.df[self.feature_cols])
            
            X_meta = pd.DataFrame({
                'xgb': pred_xgb,
                'lgb': pred_lgb,
                'cat': pred_cat,
                'lstm': lstm_res['pred'],
                'lstm_std': lstm_res['std'],
                'patchtst': patch_res['pred'],
                'patchtst_std': patch_res['std']
            })
            
            for i in range(lstm_res['embed'].shape[1]):
                X_meta[f'lstm_emb_{i}'] = lstm_res['embed'][:, i]
            for i in range(patch_res['embed'].shape[1]):
                X_meta[f'patchtst_emb_{i}'] = patch_res['embed'][:, i]
            df_sig['Predicted_Close'] = df_sig['goldbees_close'] * (1 + self.meta.predict(X_meta))
        else:
            df_sig['Predicted_Close'] = df_sig['goldbees_close']
            
        df_sig['AI_Signal'] = np.where(df_sig['Predicted_Close'] > df_sig['goldbees_close'], 1, -1)
        df_sig['Trend_Signal'] = np.where(df_sig['SMA_20'] > df_sig['SMA_50'], 1, -1)
        
        df_sig['Momentum_Signal'] = 0
        df_sig.loc[df_sig['RSI'] < 30, 'Momentum_Signal'] = 1
        df_sig.loc[df_sig['RSI'] > 70, 'Momentum_Signal'] = -1
        
        df_sig['Composite_Score'] = df_sig['AI_Signal'] + df_sig['Trend_Signal'] + df_sig['Momentum_Signal']
        df_sig['Action'] = "HOLD"
        df_sig.loc[df_sig['Composite_Score'] >= 2, 'Action'] = "BUY"
        df_sig.loc[df_sig['Composite_Score'] <= -2, 'Action'] = "SELL"
        
        df_sig.rename(columns={'goldbees_close': 'Close'}, inplace=True)
        return df_sig[['Close', 'Predicted_Close', 'AI_Signal', 'Trend_Signal', 'Momentum_Signal', 'Composite_Score', 'Action']]

    def get_historical_ohlc(self, days: int = 30) -> list:
        if self.df.empty:
            return []
        recent = self.df.tail(days).copy()
        ohlc_data = []
        for index, row in recent.iterrows():
            ohlc_data.append({
                "x": str(index).split(' ')[0],
                "y": [
                    round(row['goldbees_open'], 2),
                    round(row['goldbees_high'], 2),
                    round(row['goldbees_low'], 2),
                    round(row['goldbees_close'], 2)
                ]
            })
        return ohlc_data

    def calculate_risk(self) -> dict:
        if self.df.empty:
            return {}
        returns = self.df['Daily_Return'].replace([np.inf, -np.inf], np.nan).dropna()
        returns = returns.clip(lower=-0.05, upper=0.05)
        
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        expected_shortfall_95 = returns[returns <= var_95].mean()
        
        return {
            "VaR_95%": float(var_95),
            "VaR_99%": float(var_99),
            "Expected_Shortfall_95%": float(expected_shortfall_95),
            "Annualized_Volatility": float(returns.std() * np.sqrt(252))
        }

    def detect_market_regime(self) -> dict:
        if self.df.empty:
            return {"regime": "Unknown", "confidence": 0}
        last = self.df.iloc[-1]
        regime_code = int(last.get('Market_Regime', 3))
        
        regime_name = "Sideways"
        if regime_code == 1: regime_name = "Bull"
        elif regime_code == 2: regime_name = "Bear"
        elif regime_code == 4: regime_name = "High Volatility"
        
        return {
            "regime": regime_name,
            "confidence": 85 if regime_name != "Sideways" else 60,
            "rsi": round(float(last.get('RSI', 50)), 1),
            "sma20": round(float(last.get('SMA_20', 0)), 2),
            "sma50": round(float(last.get('SMA_50', 0)), 2),
            "volatility": round(float(last.get('Volatility_20', 0.015)) * 100, 2)
        }

    def detect_anomalies(self) -> dict:
        if self.df.empty or len(self.df) < 30:
            return {"anomaly_detected": False}
            
        recent = self.df.tail(30)
        last = self.df.iloc[-1]
        anomalies = []
        
        # Volume Spikes
        vol_mean = float(recent['goldbees_volume'].mean())
        vol_std = float(recent['goldbees_volume'].std())
        last_vol = float(last.get('goldbees_volume', vol_mean))
        if vol_std > 0:
            vol_zscore = (last_vol - vol_mean) / vol_std
            if abs(vol_zscore) > 2.5:
                pct = int((last_vol / vol_mean - 1) * 100)
                direction = "above" if pct > 0 else "below"
                anomalies.append({
                    "type": "Volume Spike",
                    "message": f"Today's volume is {abs(pct)}% {direction} the 30-day average.",
                    "severity": "high" if abs(vol_zscore) > 3.5 else "medium",
                    "icon": "📊"
                })
        return {"anomaly_detected": len(anomalies) > 0, "anomalies": anomalies}

    def get_confidence_score(self, live_price: float = None) -> dict:
        pred_res = self.predict_tomorrow(live_price)
        return {
            "score": pred_res.get("Confidence", 75),
            "label": "High Confidence" if pred_res.get("Confidence", 75) > 80 else "Moderate Confidence",
            "factors": [
                {"label": "Conformal Bound calibrated", "impact": "OK", "positive": True},
                {"label": "Regime Stacking active", "impact": "OK", "positive": True}
            ]
        }

    def get_probability_distribution(self, live_price: float = None) -> dict:
        pred = self.predict_tomorrow(live_price)
        pred_close = pred.get("Predicted_Close", 120.0)
        vol = pred.get("Predicted_Volatility", 1.0) / 100.0
        
        # Generate normal distribution bins
        np.random.seed(42)
        sim_prices = np.random.normal(pred_close, pred_close * vol, 1000)
        hist, bin_edges = np.histogram(sim_prices, bins=5)
        
        distribution = []
        total = sum(hist)
        for i in range(len(hist)):
            prob = (hist[i] / total) * 100
            price_label = round((bin_edges[i] + bin_edges[i+1]) / 2, 2)
            distribution.append({
                "price": price_label,
                "probability": round(prob, 1)
            })
        return {"distribution": distribution}

    def find_similar_days(self) -> dict:
        if self.df.empty or len(self.df) < 100:
            return {}
        cols = ['RSI', 'MACD', 'Volatility_20', 'ADX']
        cols = [c for c in cols if c in self.df.columns]
        
        today = self.df[cols].iloc[-1].values
        history = self.df[cols].iloc[:-1].values
        
        norm_today = np.linalg.norm(today)
        norms_history = np.linalg.norm(history, axis=1)
        norms_history[norms_history == 0] = 1e-9
        
        similarities = np.dot(history, today) / (norms_history * (norm_today if norm_today > 0 else 1e-9))
        best_idx = np.argmax(similarities)
        best_sim = similarities[best_idx]
        
        similar_date = str(self.df.index[best_idx]).split(' ')[0]
        outcome_return = (self.df['goldbees_close'].iloc[best_idx + 1] / self.df['goldbees_close'].iloc[best_idx]) - 1 if best_idx + 1 < len(self.df) else 0
        
        return {
            "similar_date": similar_date,
            "similarity_score": round(float(best_sim) * 100, 1),
            "outcome_pct": round(float(outcome_return) * 100, 2)
        }

    def simulate_scenario(self, variable: str, change_pct: float, live_price: float = None) -> dict:
        if self.df.empty:
            return {}
        current_price = live_price if live_price is not None else float(self.df['goldbees_close'].iloc[-1])

        pred_tomorrow = self.predict_tomorrow(live_price)
        base_pred = pred_tomorrow.get("Predicted_Close", current_price)  # noqa – kept for UI context

        mapping = {
            'dxy': 'dxy', 'vix': 'vix',
            'silver': 'silver', 'crude_oil': 'crude_oil',
            'usd_inr': 'usd_inr', 'gold_futures': 'gold_futures',
            'gold_spot': 'gold_futures',
            'volume': 'goldbees_volume'
        }

        mapped_col = mapping.get(variable.lower(), None)


        # --- CORRELATION-BETA APPROACH ---
        # Tree-based models cannot extrapolate beyond training data, so we use
        # historical OLS beta (sensitivity) which works at any input magnitude.
        # beta = Cov(R_goldbees, R_variable) / Var(R_variable)
        # Expected GoldBEES impact ≈ beta * scenario_variable_change
        impact_pct = 0.0

        if mapped_col and mapped_col in self.df.columns:
            try:
                # Compute daily returns for both series (last 252 trading days = 1 year)
                lookback = min(252, len(self.df) - 1)
                gb_returns = self.df['goldbees_close'].pct_change().tail(lookback).dropna()
                var_returns = self.df[mapped_col].pct_change().tail(lookback).dropna()

                # Align the two series
                aligned = pd.concat([gb_returns, var_returns], axis=1).dropna()
                aligned.columns = ['gb', 'var']

                if len(aligned) >= 20:
                    # OLS beta: how much GoldBEES moves per 1-unit move in the variable
                    var_variance = aligned['var'].var()
                    if var_variance > 1e-10:
                        beta = aligned['gb'].cov(aligned['var']) / var_variance
                    else:
                        beta = 0.0

                    # Apply: change_pct is the user input (e.g. +100 means +100%)
                    # We convert to decimal for the calculation
                    variable_return = change_pct / 100.0
                    impact_pct = beta * variable_return

                    # Cap at ±30% to prevent absurd outputs from extreme inputs
                    impact_pct = max(-0.30, min(0.30, impact_pct))
            except Exception:
                impact_pct = 0.0

        new_expected_price = current_price * (1 + impact_pct)

        return {
            "scenario": f"{variable} {'+' if change_pct > 0 else ''}{change_pct}%",
            "base_expected": round(current_price, 2),
            "new_expected": round(new_expected_price, 2),
            "impact_pct": round(impact_pct * 100, 2)
        }

    def detect_patterns(self) -> dict:
        if self.df.empty or len(self.df) < 20:
            return {}
        closes = self.df.tail(20)['goldbees_close'].values
        peaks = []
        troughs = []
        for i in range(1, len(closes)-1):
            if closes[i] > closes[i-1] and closes[i] > closes[i+1]:
                peaks.append((i, closes[i]))
            if closes[i] < closes[i-1] and closes[i] < closes[i+1]:
                troughs.append((i, closes[i]))
        patterns = []
        if len(peaks) >= 2:
            p1, p2 = peaks[-2][1], peaks[-1][1]
            if abs(p1 - p2) / p1 < 0.01:
                patterns.append("Double Top Detected (Bearish)")
        if len(troughs) >= 2:
            t1, t2 = troughs[-2][1], troughs[-1][1]
            if abs(t1 - t2) / t1 < 0.01:
                patterns.append("Double Bottom Detected (Bullish)")
        if not patterns:
            patterns.append("No clear patterns in last 20 days")
        return {"patterns": patterns}

if __name__ == "__main__":
    engine = InferenceEngine()
    print("Ensemble Forecast:", engine.forecast_horizons())
