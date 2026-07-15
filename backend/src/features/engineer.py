import os
import json
import ta
import pandas as pd
import numpy as np
from datetime import datetime
from src.utils.db import get_db_connection, get_engine
from src.services.news_nlp import NewsEventStore
from src.services.economic_calendar import EconomicCalendarService
from src.utils.logger import get_logger

logger = get_logger(__name__)

class FeatureStoreManager:
    """
    Manages loading and saving features to the Feature Store database table.
    """
    
    @staticmethod
    def save_features(df: pd.DataFrame, version: str = "v1"):
        """Saves a dataframe of features to the database as JSONB records in bulk."""
        logger.info(f"Saving features (version: {version}) to Feature Store...")
        from psycopg2.extras import execute_values
        conn = get_db_connection()
        c = conn.cursor()
        
        # Reset index to extract dates
        df_reset = df.reset_index()
        date_col = 'date' if 'date' in df_reset.columns else 'Date'
        
        data_tuples = []
        for _, row in df_reset.iterrows():
            dt = row[date_col]
            row_dict = row.drop(date_col).to_dict()
            
            clean_dict = {}
            for k, v in row_dict.items():
                if pd.isnull(v):
                    clean_dict[k] = None
                elif isinstance(v, (np.integer, np.int64, int)):
                    clean_dict[k] = int(v)
                elif isinstance(v, (np.floating, np.float64, float)):
                    clean_dict[k] = float(v)
                elif isinstance(v, datetime):
                    clean_dict[k] = v.isoformat()
                else:
                    clean_dict[k] = v
            
            data_tuples.append((dt, version, json.dumps(clean_dict)))
            
        execute_values(c, """
            INSERT INTO feature_store (date, feature_version, features)
            VALUES %s
            ON CONFLICT (date) DO UPDATE SET
                feature_version = EXCLUDED.feature_version,
                features = EXCLUDED.features
        """, data_tuples)
            
        conn.commit()
        conn.close()
        logger.info("Features successfully stored in DB.")

    @staticmethod
    def load_features(version: str = "v1") -> pd.DataFrame:
        """Loads features from the Feature Store database table."""
        engine = get_engine()
        df = pd.read_sql_query("""
            SELECT date, features FROM feature_store
            WHERE feature_version = %s
            ORDER BY date ASC
        """, engine, params=(version,))
        
        if df.empty:
            return pd.DataFrame()
            
        # Parse JSONB into columns
        features_list = []
        for idx, row in df.iterrows():
            feat_dict = row['features']
            feat_dict['Date'] = row['date']
            features_list.append(feat_dict)
            
        res_df = pd.DataFrame(features_list)
        res_df.set_index('Date', inplace=True)
        return res_df

class FeatureEngineer:
    """
    Computes technical indicators, rolling correlations, intraday stats,
    macro surprises, decayed news sentiments, market regimes, and future targets.
    """
    def __init__(self):
        pass

    def load_market_data(self) -> pd.DataFrame:
        engine = get_engine()
        df = pd.read_sql_query("""
            SELECT * FROM market_prices 
            ORDER BY date ASC
        """, engine, index_col='date')
        
        if df.empty:
            raise ValueError("No market data found in database. Run downloader first.")
            
        df.sort_index(inplace=True)
        return df

    def get_intraday_features(self) -> pd.DataFrame:
        """Computes daily summaries from intraday candles."""
        engine = get_engine()
        df_intra = pd.read_sql_query("""
            SELECT timestamp::date as date, goldbees_price, goldbees_volume
            FROM market_prices_intraday
            ORDER BY timestamp ASC
        """, engine)
        
        if df_intra.empty:
            return pd.DataFrame()
            
        # Calculate daily indicators
        grouped = df_intra.groupby('date')
        
        intra_features = {}
        for date, group in grouped:
            prices = group['goldbees_price'].values
            volumes = group['goldbees_volume'].values
            
            # Morning Momentum: return from first candle to third (roughly first hour)
            if len(prices) >= 3:
                morn_momentum = (prices[2] / prices[0]) - 1.0
            else:
                morn_momentum = 0.0
                
            # Intraday High-Low spread
            hl_spread = (np.max(prices) - np.min(prices)) / (np.min(prices) + 1e-8)
            
            # Intraday Volume Spikes count
            mean_vol = np.mean(volumes)
            std_vol = np.std(volumes)
            spikes = np.sum(volumes > (mean_vol + 2 * std_vol)) if std_vol > 0 else 0
            
            intra_features[date] = {
                "Intraday_Morning_Momentum": float(morn_momentum),
                "Intraday_HL_Spread": float(hl_spread),
                "Intraday_Vol_Spikes": int(spikes)
            }
            
        df_res = pd.DataFrame.from_dict(intra_features, orient='index')
        df_res.index = pd.to_datetime(df_res.index)
        return df_res

    def detect_market_regime(self, rsi: pd.Series, close: pd.Series, volatility: pd.Series) -> pd.Series:
        """Classifies the market regime: Bull (1), Bear (2), Sideways (3), Volatile/Geopolitical (4)."""
        regimes = []
        vol_threshold = volatility.quantile(0.75)
        
        # Simple crossover trend
        sma20 = close.rolling(20).mean()
        sma50 = close.rolling(50).mean()
        
        for idx in range(len(close)):
            vol = volatility.iloc[idx]
            r = rsi.iloc[idx]
            c = close.iloc[idx]
            s20 = sma20.iloc[idx]
            s50 = sma50.iloc[idx]
            
            if pd.isnull(s20) or pd.isnull(s50):
                regimes.append(3) # Sideways fallback
                continue
                
            if vol > vol_threshold:
                regimes.append(4) # High Volatility environment
            elif s20 > s50 and r > 55:
                regimes.append(1) # Bull Market
            elif s20 < s50 and r < 45:
                regimes.append(2) # Bear Market
            else:
                regimes.append(3) # Sideways / Consolidation
                
        return pd.Series(regimes, index=close.index)

    def generate_all_features(self):
        logger.info("Executing comprehensive Feature Engineering...")
        
        df = self.load_market_data()
        
        # 1. Technical Indicators using Close (GoldBEES Close)
        close = df['goldbees_close']
        high = df['goldbees_high']
        low = df['goldbees_low']
        volume = df['goldbees_volume']
        
        df['RSI'] = ta.momentum.rsi(close, window=14)
        df['MACD'] = ta.trend.macd(close)
        df['MACD_Signal'] = ta.trend.macd_signal(close)
        df['EMA_20'] = ta.trend.ema_indicator(close, window=20)
        df['SMA_20'] = ta.trend.sma_indicator(close, window=20)
        df['SMA_50'] = ta.trend.sma_indicator(close, window=50)
        df['ATR'] = ta.volatility.average_true_range(high, low, close, window=14)
        df['BB_High'] = ta.volatility.bollinger_hband(close, window=20)
        df['BB_Low'] = ta.volatility.bollinger_lband(close, window=20)
        df['ADX'] = ta.trend.adx(high, low, close)
        df['CCI'] = ta.trend.cci(high, low, close)
        df['ROC'] = ta.momentum.roc(close, window=10)
        df['OBV'] = ta.volume.on_balance_volume(close, volume)
        
        # Daily Returns & Rolling Volatility
        df['Daily_Return'] = close.pct_change()
        # Winsorize to remove massive data anomalies (e.g. stock splits)
        df['Daily_Return'] = df['Daily_Return'].clip(lower=-0.1, upper=0.1)
        df['Volatility_20'] = df['Daily_Return'].rolling(window=20).std()
        
        # 2. Rolling Correlations
        logger.info("Calculating asset rolling correlations...")
        for col in ['dxy', 'vix', 'silver', 'crude_oil', 'usd_inr', 'gold_futures']:
            df[f'Corr_GoldBEES_{col.upper()}'] = df['goldbees_close'].rolling(20).corr(df[col])
            
        # 3. Merge Intraday summaries
        logger.info("Merging intraday summaries...")
        df_intra = self.get_intraday_features()
        if not df_intra.empty:
            df = df.merge(df_intra, left_index=True, right_index=True, how='left')
        else:
            df['Intraday_Morning_Momentum'] = 0.0
            df['Intraday_HL_Spread'] = 0.0
            df['Intraday_Vol_Spikes'] = 0
            
        # Fill missing intraday data (which might only exist for last 60 days)
        df['Intraday_Morning_Momentum'].fillna(0.0, inplace=True)
        df['Intraday_HL_Spread'].fillna(df['Daily_Return'].abs() * 0.5, inplace=True)
        df['Intraday_Vol_Spikes'].fillna(0, inplace=True)

        # 4. Integrate Decayed Sentiment & Calendar Surprises
        logger.info("Adding macro calendar and decayed news sentiment features...")
        news_sentiment = []
        war_scores = []
        fed_scores = []
        inflation_scores = []
        etf_scores = []
        
        fed_surprises = []
        inflation_surprises = []
        employment_surprises = []
        gdp_surprises = []
        
        # Ensure seed calendar exists
        EconomicCalendarService.populate_seed_calendar()
        
        # Load all events into memory to avoid nested database queries in the loop
        engine = get_engine()
        df_events = pd.read_sql_query("SELECT event_time, event_type, sentiment, importance FROM market_events", engine)
        df_macro = pd.read_sql_query("SELECT event_date, event_name, surprise FROM economic_events", engine)
        
        if not df_events.empty:
            df_events['event_time'] = pd.to_datetime(df_events['event_time'])
        if not df_macro.empty:
            df_macro['event_date'] = pd.to_datetime(df_macro['event_date'])
            
        for idx in df.index:
            # 1. Aggregating news sentiment locally
            ns, ws, fs, infs, es = 0.0, 0.0, 0.0, 0.0, 0.0
            if not df_events.empty:
                t_start = idx - pd.Timedelta(days=10)
                sub_events = df_events[(df_events['event_time'] <= idx) & (df_events['event_time'] >= t_start)]
                if not sub_events.empty:
                    # Calculate time decay
                    days_diff = (idx - sub_events['event_time']).dt.days
                    decay_weight = np.exp(-0.5 * days_diff)
                    weighted_sentiment = sub_events['sentiment'] * sub_events['importance'] * decay_weight
                    
                    ns = float(weighted_sentiment.sum())
                    ws = float(weighted_sentiment[sub_events['event_type'] == 'War'].sum())
                    fs = float(weighted_sentiment[sub_events['event_type'] == 'Central Bank'].sum())
                    infs = float(weighted_sentiment[sub_events['event_type'] == 'Inflation'].sum())
                    es = float(weighted_sentiment[sub_events['event_type'] == 'ETF Flow'].sum())
            
            news_sentiment.append(ns)
            war_scores.append(ws)
            fed_scores.append(fs)
            inflation_scores.append(infs)
            etf_scores.append(es)
            
            # 2. Aggregating Economic surprises locally
            f_sur, inf_sur, emp_sur, gdp_sur = 0.0, 0.0, 0.0, 0.0
            if not df_macro.empty:
                t_start_macro = idx - pd.Timedelta(days=5)
                sub_macro = df_macro[(df_macro['event_date'] <= idx) & (df_macro['event_date'] >= t_start_macro)]
                if not sub_macro.empty:
                    for _, row in sub_macro.iterrows():
                        name = row['event_name'].lower()
                        val = row['surprise']
                        if 'fed' in name or 'interest rate' in name or 'fomc' in name:
                            f_sur += val
                        elif 'cpi' in name or 'ppi' in name or 'inflation' in name:
                            inf_sur += val
                        elif 'payroll' in name or 'nfp' in name or 'employment' in name:
                            emp_sur += val
                        elif 'gdp' in name:
                            gdp_sur += val
                            
            fed_surprises.append(f_sur)
            inflation_surprises.append(inf_sur)
            employment_surprises.append(emp_sur)
            gdp_surprises.append(gdp_sur)
            
        df['News_Sentiment'] = news_sentiment
        df['News_War_Score'] = war_scores
        df['News_Fed_Score'] = fed_scores
        df['News_Inflation_Score'] = inflation_scores
        df['News_ETF_Score'] = etf_scores
        
        df['Fed_Surprise'] = fed_surprises
        df['Inflation_Surprise'] = inflation_surprises
        df['Employment_Surprise'] = employment_surprises
        df['GDP_Surprise'] = gdp_surprises

        # 5. Market Regime Detection
        logger.info("Classifying market regimes...")
        df['Market_Regime'] = self.detect_market_regime(df['RSI'].fillna(50), close, df['Volatility_20'].fillna(0.015))

        # 6. Future Prediction Targets
        logger.info("Generating multi-horizon target labels...")
        df['Target_Return_t1'] = ((close.shift(-1) - close) / close).clip(lower=-0.1, upper=0.1)
        df['Target_Return_t3'] = ((close.shift(-3) - close) / close).clip(lower=-0.2, upper=0.2)
        df['Target_Return_t7'] = ((close.shift(-7) - close) / close).clip(lower=-0.3, upper=0.3)
        df['Target_Return_t30'] = ((close.shift(-30) - close) / close).clip(lower=-0.5, upper=0.5)
        
        # Volatility target: next day realized volatility (rolling 5-day std of daily returns shifted by -1)
        df['Target_Volatility'] = df['Daily_Return'].rolling(5).std().shift(-1)
        
        # Calendar context variables
        df['Month'] = df.index.month
        df['Quarter'] = df.index.quarter
        df['Weekday'] = df.index.weekday
        
        # 7. Drop lookback NaN rows (about first 50 rows)
        df.dropna(subset=['SMA_50', 'Volatility_20'], inplace=True)
        
        # Save to Feature Store
        FeatureStoreManager.save_features(df)
        logger.info("Feature engineering complete!")

if __name__ == "__main__":
    engineer = FeatureEngineer()
    engineer.generate_all_features()
