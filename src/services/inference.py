import os
import joblib
import pandas as pd
import numpy as np
import shap
from src.utils.logger import get_logger

logger = get_logger(__name__)

class InferenceEngine:
    """
    Handles Multi-Horizon Forecasting, Signal Generation, Risk Analysis, and Explainable AI.
    """
    def __init__(self, model_name: str = "LinearRegression"):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.model_path = os.path.join(self.base_dir, "models", f"{model_name}.pkl")
        self.data_path = os.path.join(self.base_dir, "data", "processed", "goldbees_features.csv")
        
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
        else:
            logger.warning(f"Model {model_name} not found at {self.model_path}. Please train first.")
            self.model = None
            
        if os.path.exists(self.data_path):
            self.df = pd.read_csv(self.data_path)
            if 'Date' in self.df.columns:
                self.df.set_index('Date', inplace=True)
            self.target_col = 'Close'
            self.features = [col for col in self.df.columns if col not in [self.target_col, 'Daily_Return', 'Log_Return']]
        else:
            self.df = None

    def forecast_horizons(self, live_price: float = None) -> dict:
        """
        Predict tomorrow, 5 days, 30 days, 90 days.
        Uses live_price if provided (for real-time dashboard).
        """
        logger.info("Generating multi-horizon forecasts...")
        if self.model is None or self.df is None:
            return {}
            
        last_row = self.df[self.features].iloc[-1:]
        current_price = live_price if live_price is not None else self.df[self.target_col].iloc[-1]
        
        # 1-Day Forecast (anchored to actual features, but if current price deviates wildly, we can adjust.
        # For simplicity, we just use the model prediction and apply volatility drift from the live price)
        pred_1d = self.model.predict(last_row)[0]
        
        # If live price is provided, adjust the baseline
        if live_price is not None:
            baseline = live_price
        else:
            baseline = pred_1d

        # Clean up extreme outliers in daily returns (Yahoo Finance glitches)
        returns = self.df['Daily_Return'].replace([np.inf, -np.inf], np.nan).dropna()
        returns = returns.clip(lower=-0.05, upper=0.05) # Max 5% daily move for Gold ETF
        vol = returns.std()
        
        forecasts = {
            "Current_Price": float(current_price),
            "Forecast_1_Day": float(pred_1d),
            "Forecast_5_Days": float(baseline * (1 + (vol * np.sqrt(5)))),
            "Forecast_30_Days": float(baseline * (1 + (vol * np.sqrt(30)))),
            "Forecast_90_Days": float(baseline * (1 + (vol * np.sqrt(90)))),
        }
        
        # Confidence Intervals (Simple statistical approach)
        z_score = 1.96 # 95% CI
        forecasts["CI_1_Day_Lower"] = float(pred_1d * (1 - z_score * vol))
        forecasts["CI_1_Day_Upper"] = float(pred_1d * (1 + z_score * vol))
        
        return forecasts

    def custom_forecast(self, target_date: str, live_price: float = None) -> dict:
        """
        Forecast price for a specific future date.
        """
        import datetime
        target = pd.to_datetime(target_date).tz_localize(None)
        today = pd.Timestamp.today().normalize()
        
        # Calculate trading days roughly (excluding weekends)
        days = np.busday_count(today.date(), target.date())
        
        if days <= 0:
            return {"error": "Target date must be in the future"}
            
        current_price = live_price if live_price is not None else self.df[self.target_col].iloc[-1]
        
        returns = self.df['Daily_Return'].replace([np.inf, -np.inf], np.nan).dropna()
        returns = returns.clip(lower=-0.05, upper=0.05)
        vol = returns.std()
        
        # Base 1-day prediction
        last_row = self.df[self.features].iloc[-1:]
        pred_1d = self.model.predict(last_row)[0]
        baseline = live_price if live_price is not None else pred_1d
        
        projected_price = float(baseline * (1 + (vol * np.sqrt(days))))
        z_score = 1.96
        projected_vol = vol * np.sqrt(days)
        
        return {
            "Target_Date": target_date,
            "Trading_Days": int(days),
            "Projected_Price": projected_price,
            "CI_Lower": float(projected_price * (1 - z_score * projected_vol)),
            "CI_Upper": float(projected_price * (1 + z_score * projected_vol))
        }

    def generate_signals(self) -> pd.DataFrame:
        """
        Generates BUY/HOLD/SELL signals combining Trend, Momentum, Volatility, and Model Predictions.
        """
        logger.info("Generating trading signals...")
        if self.df is None:
            return pd.DataFrame()
            
        df_sig = self.df.copy()
        
        # 1. AI Prediction Signal (Did the model predict up or down?)
        preds = self.model.predict(df_sig[self.features])
        df_sig['Predicted_Close'] = preds
        df_sig['AI_Signal'] = np.where(df_sig['Predicted_Close'] > df_sig['Close'], 1, -1)
        
        # Trend: SMA20 > SMA50 is Bullish
        df_sig['Trend_Signal'] = np.where(df_sig['SMA_20'] > df_sig['SMA_50'], 1, -1)
        
        # Momentum: RSI < 30 (Oversold -> Buy), RSI > 70 (Overbought -> Sell)
        df_sig['Momentum_Signal'] = 0
        df_sig.loc[df_sig['RSI'] < 30, 'Momentum_Signal'] = 1
        df_sig.loc[df_sig['RSI'] > 70, 'Momentum_Signal'] = -1
        
        # 3. Composite Signal (-3 to +3)
        df_sig['Composite_Score'] = df_sig['AI_Signal'] + df_sig['Trend_Signal'] + df_sig['Momentum_Signal']
        
        # Final Action
        df_sig['Action'] = "HOLD"
        df_sig.loc[df_sig['Composite_Score'] >= 2, 'Action'] = "BUY"
        df_sig.loc[df_sig['Composite_Score'] <= -2, 'Action'] = "SELL"
        
        return df_sig[['Close', 'Predicted_Close', 'AI_Signal', 'Trend_Signal', 'Momentum_Signal', 'Composite_Score', 'Action']]

    def get_historical_ohlc(self, days: int = 30) -> list:
        """
        Extract the last N days of OHLC data for charting.
        Returns a list of dictionaries formatted for ApexCharts candlestick series:
        { x: timestamp, y: [open, high, low, close] }
        """
        if self.df is None or self.df.empty:
            return []
            
        recent = self.df.tail(days).copy()
        
        ohlc_data = []
        for index, row in recent.iterrows():
            ohlc_data.append({
                "x": str(index),
                "y": [
                    round(row['Open'], 2),
                    round(row['High'], 2),
                    round(row['Low'], 2),
                    round(row['Close'], 2)
                ]
            })
            
        return ohlc_data

    def calculate_risk(self) -> dict:
        """
        Calculate Value at Risk (VaR) and Expected Shortfall using historical simulation.
        """
        if self.df is None:
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

    def get_shap_values(self) -> dict:
        """
        Returns SHAP feature importance as a JSON-serializable dict for the dashboard.
        Shows the top features that drove today's prediction.
        """
        logger.info("Generating SHAP feature importance for dashboard...")
        if self.model is None or self.df is None:
            return {}

        try:
            X_sample = self.df[self.features].tail(100)
            last_row = self.df[self.features].iloc[-1:]

            explainer = shap.Explainer(self.model, X_sample)
            shap_values = explainer(last_row)

            # Get values as a flat array
            values = shap_values.values[0]
            feature_names = self.features

            # Create sorted dict of feature -> shap contribution
            contributions = dict(zip(feature_names, [float(v) for v in values]))
            # Sort by absolute importance, take top 8
            top_features = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)[:8]

            total = sum(abs(v) for _, v in top_features)
            result = []
            for feat, val in top_features:
                pct = (abs(val) / total * 100) if total > 0 else 0
                result.append({
                    "feature": feat,
                    "value": round(val, 4),
                    "percentage": round(pct, 1),
                    "direction": "positive" if val > 0 else "negative"
                })

            return {"top_features": result}

        except Exception as e:
            logger.error(f"SHAP computation failed: {e}")
            return {}

    def detect_market_regime(self) -> dict:
        """
        Classifies the current market as Bull, Bear, Sideways, or High Volatility.
        Uses trend (SMA crossover) + volatility to classify.
        """
        if self.df is None or self.df.empty:
            return {"regime": "Unknown", "confidence": 0}

        recent = self.df.tail(20)
        last = self.df.iloc[-1]

        volatility_20 = float(self.df['Volatility_20'].iloc[-1]) if 'Volatility_20' in self.df.columns else 0.01
        sma20 = float(last.get('SMA_20', 0))
        sma50 = float(last.get('SMA_50', 0))
        rsi = float(last.get('RSI', 50))
        close = float(last.get('Close', 0))
        
        high_vol_threshold = self.df['Volatility_20'].quantile(0.8) if 'Volatility_20' in self.df.columns else 0.02

        # Determine regime
        if volatility_20 > high_vol_threshold:
            regime = "High Volatility"
            confidence = min(95, int((volatility_20 / high_vol_threshold) * 70))
        elif sma20 > sma50 and rsi > 55:
            regime = "Bull"
            confidence = min(95, int(((sma20 - sma50) / sma50) * 5000 + 60))
        elif sma20 < sma50 and rsi < 45:
            regime = "Bear"
            confidence = min(95, int(((sma50 - sma20) / sma50) * 5000 + 60))
        else:
            regime = "Sideways"
            confidence = 65

        return {
            "regime": regime,
            "confidence": int(confidence),
            "rsi": round(rsi, 1),
            "sma20": round(sma20, 2),
            "sma50": round(sma50, 2),
            "volatility": round(float(volatility_20) * 100, 2)
        }

    def detect_anomalies(self) -> dict:
        """
        Detects unusual price or volume activity using Z-scores.
        """
        if self.df is None or len(self.df) < 30:
            return {"anomaly_detected": False}

        recent = self.df.tail(30)
        last = self.df.iloc[-1]

        anomalies = []

        # Volume anomaly
        if 'Volume' in self.df.columns:
            vol_mean = float(recent['Volume'].mean())
            vol_std = float(recent['Volume'].std())
            last_vol = float(last.get('Volume', vol_mean))
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

        # Price anomaly
        price_mean = float(recent['Close'].mean())
        price_std = float(recent['Close'].std())
        last_price = float(last.get('Close', price_mean))
        if price_std > 0:
            price_zscore = (last_price - price_mean) / price_std
            if abs(price_zscore) > 2.0:
                pct = round(abs((last_price - price_mean) / price_mean * 100), 1)
                direction = "above" if price_zscore > 0 else "below"
                anomalies.append({
                    "type": "Price Deviation",
                    "message": f"Price is {pct}% {direction} the 30-day average. Possible breakout.",
                    "severity": "medium",
                    "icon": "⚡"
                })

        return {
            "anomaly_detected": len(anomalies) > 0,
            "anomalies": anomalies
        }

    def get_confidence_score(self, live_price: float = None) -> dict:
        """
        Generates an AI confidence score (0-100) based on signal agreement,
        model performance, and market conditions.
        """
        if self.model is None or self.df is None:
            return {"score": 0, "label": "Unknown", "factors": []}

        score = 50  # Base score
        factors = []

        last = self.df.iloc[-1]
        rsi = float(last.get('RSI', 50))
        macd = float(last.get('MACD', 0))
        macd_signal = float(last.get('MACD_Signal', 0))
        adx = float(last.get('ADX', 20))

        # ADX > 25 means strong trend → higher confidence
        if adx > 25:
            score += 15
            factors.append({"label": "Strong Trend (ADX)", "impact": "+15%", "positive": True})
        else:
            score -= 5
            factors.append({"label": "Weak Trend (ADX)", "impact": "-5%", "positive": False})

        # MACD alignment
        if (macd > macd_signal and macd > 0):
            score += 10
            factors.append({"label": "MACD Bullish", "impact": "+10%", "positive": True})
        elif (macd < macd_signal and macd < 0):
            score += 10
            factors.append({"label": "MACD Bearish (clear signal)", "impact": "+10%", "positive": True})
        else:
            factors.append({"label": "MACD Uncertain", "impact": "0%", "positive": False})

        # RSI not in neutral zone
        if rsi < 35 or rsi > 65:
            score += 10
            factors.append({"label": "RSI Non-Neutral", "impact": "+10%", "positive": True})
        else:
            factors.append({"label": "RSI Neutral Zone", "impact": "0%", "positive": False})

        # Volatility check (lower vol = higher confidence in prediction)
        vol = float(self.df['Volatility_20'].iloc[-1]) if 'Volatility_20' in self.df.columns else 0.015
        vol_baseline = float(self.df['Volatility_20'].median()) if 'Volatility_20' in self.df.columns else 0.015
        if vol < vol_baseline:
            score += 10
            factors.append({"label": "Low Volatility", "impact": "+10%", "positive": True})
        else:
            score -= 5
            factors.append({"label": "High Volatility", "impact": "-5%", "positive": False})

        score = max(10, min(98, score))

        if score >= 80:
            label = "High Confidence"
        elif score >= 60:
            label = "Moderate Confidence"
        else:
            label = "Low Confidence"

        return {
            "score": int(score),
            "label": label,
            "factors": factors
        }

    def get_probability_distribution(self, live_price: float = None) -> dict:
        """
        Monte Carlo simulation to generate a probability heatmap for tomorrow's price.
        """
        if self.df is None:
            return {}
            
        current_price = live_price if live_price is not None else float(self.df['Close'].iloc[-1])
        volatility = float(self.df['Volatility_20'].iloc[-1]) if 'Volatility_20' in self.df.columns else 0.015
        
        # Run 10,000 simulations for 1 day
        np.random.seed(42)
        simulated_returns = np.random.normal(0, volatility, 10000)
        simulated_prices = current_price * (1 + simulated_returns)
        
        # Bin the prices
        hist, bin_edges = np.histogram(simulated_prices, bins=5)
        
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
        """
        Finds the most similar historical day based on technical indicators (Cosine Similarity).
        """
        if self.df is None or len(self.df) < 100:
            return {}
            
        # Use key indicators for similarity
        cols = ['RSI', 'MACD', 'Volatility_20', 'ADX']
        cols = [c for c in cols if c in self.df.columns]
        
        if not cols:
            return {}
            
        today = self.df[cols].iloc[-1].values
        history = self.df[cols].iloc[:-1].values
        
        # Compute cosine similarity
        norm_today = np.linalg.norm(today)
        norms_history = np.linalg.norm(history, axis=1)
        
        # Avoid division by zero
        norms_history[norms_history == 0] = 1e-9
        if norm_today == 0: norm_today = 1e-9
            
        similarities = np.dot(history, today) / (norms_history * norm_today)
        
        best_idx = np.argmax(similarities)
        best_sim = similarities[best_idx]
        
        similar_date = self.df.index[best_idx]
        if not isinstance(similar_date, str):
            similar_date = str(similar_date).split(' ')[0]
            
        # Outcome after the similar day (1 day return)
        if best_idx + 1 < len(self.df):
            outcome_return = (self.df['Close'].iloc[best_idx + 1] / self.df['Close'].iloc[best_idx]) - 1
        else:
            outcome_return = 0
            
        return {
            "similar_date": similar_date,
            "similarity_score": round(float(best_sim) * 100, 1),
            "outcome_pct": round(float(outcome_return) * 100, 2)
        }

    def simulate_scenario(self, variable: str, change_pct: float, live_price: float = None) -> dict:
        """
        What-If Simulator: Adjusts a macro variable and predicts the new price.
        """
        if self.model is None or self.df is None:
            return {}
            
        current_price = live_price if live_price is not None else float(self.df['Close'].iloc[-1])
        last_row = self.df[self.features].iloc[-1:].copy()
        
        # Base prediction
        base_pred = self.model.predict(last_row)[0]
        
        # Apply scenario
        scenario_pred = base_pred
        if variable in last_row.columns:
            last_row[variable] = last_row[variable] * (1 + (change_pct / 100.0))
            scenario_pred = self.model.predict(last_row)[0]
        elif variable in ['USD_INR', 'Gold_Spot']:
            # GoldBeES tracks Gold in INR, so it is highly correlated (~0.98 beta) to both variables
            beta = 0.98
            scenario_pred = base_pred * (1 + ((change_pct * beta) / 100.0))
        
        # Scale to live price if needed (simplified)
        impact_pct = (scenario_pred - base_pred) / base_pred
        new_expected_price = current_price * (1 + impact_pct)
        
        return {
            "scenario": f"{variable} {'+' if change_pct > 0 else ''}{change_pct}%",
            "base_expected": round(current_price, 2),
            "new_expected": round(new_expected_price, 2),
            "impact_pct": round(impact_pct * 100, 2)
        }

    def detect_patterns(self) -> dict:
        """
        Algorithmic detection of basic chart patterns (e.g. Double Top, Double Bottom).
        Simplified implementation for the last 20 days.
        """
        if self.df is None or len(self.df) < 20:
            return {}
            
        recent = self.df.tail(20)
        closes = recent['Close'].values
        
        # Very simplified peak/trough detection
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
                
        if len(peaks) >= 2 and peaks[-1][1] > peaks[-2][1] * 1.005:
            patterns.append("Higher Highs (Bullish Trend)")
        elif len(peaks) >= 2 and peaks[-1][1] < peaks[-2][1] * 0.995:
            patterns.append("Lower Highs (Bearish Trend)")
            
        if len(troughs) >= 2 and troughs[-1][1] < troughs[-2][1] * 0.995:
            patterns.append("Lower Lows (Bearish Trend)")
        elif len(troughs) >= 2 and troughs[-1][1] > troughs[-2][1] * 1.005:
            patterns.append("Higher Lows (Bullish Trend)")

        if not patterns:
            patterns.append("No clear patterns in last 20 days")
            
        return {"patterns": patterns}

if __name__ == "__main__":
    engine = InferenceEngine(model_name="LinearRegression")
    
    forecasts = engine.forecast_horizons()
    print("Forecasts:", forecasts)
    
    risk = engine.calculate_risk()
    print("Risk Metrics:", risk)
    
    signals = engine.generate_signals()
    print("Latest Signals:\n", signals.tail())
    
    engine.explain_prediction()
