import os
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.utils.db import get_db_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Try to load local FinBERT, with VaderSentiment as fallback
FINBERT_MODEL = "yiyanghkust/finbert-tone"
nlp_pipeline = None

try:
    from transformers import pipeline
    logger.info(f"Loading local FinBERT model '{FINBERT_MODEL}'...")
    # Initialize pipeline
    nlp_pipeline = pipeline("sentiment-analysis", model=FINBERT_MODEL, tokenizer=FINBERT_MODEL, device=-1) # -1 runs on CPU
    logger.info("FinBERT model loaded successfully.")
except Exception as e:
    logger.warning(f"Failed to load FinBERT model locally: {e}. Falling back to VaderSentiment/Rule-based analyzer.")
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        vader_analyzer = SentimentIntensityAnalyzer()
        logger.info("VaderSentiment initialized as fallback.")
    except Exception as ve:
        logger.error(f"VaderSentiment import failed: {ve}. Will use basic dictionary analyzer.")
        vader_analyzer = None

class NewsEventStore:
    """
    Handles news ingestion, local FinBERT sentiment analysis, article deduplication,
    event consolidation (Event Store), source-based weighting, and time decay calculations.
    """
    
    # Source Weights
    SOURCE_WEIGHTS = {
        "reuters": 1.0,
        "bloomberg": 0.95,
        "cnbc": 0.90,
        "yfinance": 0.80,
        "yahoo": 0.80,
        "marketwatch": 0.80,
        "investing": 0.75
    }

    # Category Keywords
    CATEGORY_KEYWORDS = {
        "War": ["war", "attack", "military", "geopolitics", "strike", "missile", "iran", "russia", "tensions"],
        "Central Bank": ["fed", "federal reserve", "interest rate", "powell", "rate cut", "rate hike", "fomc", "rbi"],
        "Inflation": ["cpi", "ppi", "inflation", "deflation", "cpi/ppi", "prices rise"],
        "Oil": ["crude", "oil", "opec", "energy", "barrel"],
        "ETF Flow": ["etf", "inflow", "outflow", "goldbees", "gold bees", "holdings", "gld"]
    }

    @staticmethod
    def get_source_weight(source: str) -> float:
        source_lower = source.lower()
        for key, val in NewsEventStore.SOURCE_WEIGHTS.items():
            if key in source_lower:
                return val
        return 0.20 # Unknown Blog / general website

    @staticmethod
    def classify_event_category(headline: str) -> str:
        headline_lower = headline.lower()
        for cat, keywords in NewsEventStore.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in headline_lower:
                    return cat
        return "General Macro"

    @staticmethod
    def analyze_sentiment(text: str) -> tuple:
        """
        Determines deterministic sentiment score (-1 to +1) and confidence score (0 to 1).
        """
        if nlp_pipeline is not None:
            try:
                res = nlp_pipeline(text)[0]
                label = res['label'].upper() # 'POSITIVE', 'NEGATIVE', 'NEUTRAL'
                score = res['score']
                
                if label == 'POSITIVE':
                    sentiment = score
                elif label == 'NEGATIVE':
                    sentiment = -score
                else:
                    sentiment = 0.0
                return round(sentiment, 4), round(score, 4)
            except Exception as e:
                logger.warning(f"FinBERT inference error: {e}")
                
        # Vader Sentiment Fallback
        global vader_analyzer
        if vader_analyzer is not None:
            scores = vader_analyzer.polarity_scores(text)
            compound = scores['compound']
            return round(compound, 4), 0.90 # high fallback confidence
            
        # Basic Dictionary Fallback
        positive_words = {"rate cut", "easing", "bullish", "inflow", "buying", "support", "rally", "rise", "stimulus", "tension", "war"}
        negative_words = {"rate hike", "hawkish", "bearish", "outflow", "selling", "dump", "fall", "stabilize", "strong dollar"}
        
        words = text.lower().split()
        pos_count = sum(1 for w in words if w in positive_words)
        neg_count = sum(1 for w in words if w in negative_words)
        
        diff = pos_count - neg_count
        tot = pos_count + neg_count
        if tot == 0:
            return 0.0, 0.5
        return round(diff / tot, 4), 0.70

    @staticmethod
    def calculate_event_signature(headline: str) -> str:
        """Generates a unique hash based on normalized headline for deduplication."""
        # Simple normalization: keep alphanumeric characters and lowercase
        normalized = "".join(c for c in headline.lower() if c.isalnum())
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    @classmethod
    def ingest_rss_feeds(cls):
        """Fetches live financial headlines from key RSS feeds, analyzes, and groups them in Event Store."""
        logger.info("Ingesting news from financial RSS sources...")
        
        feeds = {
            "CNBC Macro": "https://search.cnbc.com/rs/search/all/view.xml?partnerId=2000&keywords=gold",
            "Yahoo Finance Gold": "https://finance.yahoo.com/news/rss",
            "MarketWatch Commodities": "https://www.marketwatch.com/rss/commentary"
        }
        
        conn = get_db_connection()
        c = conn.cursor()
        
        inserted_articles = 0
        
        for feed_name, url in feeds.items():
            try:
                # Basic request
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    xml_data = response.read()
                
                root = ET.fromstring(xml_data)
                for item in root.findall('.//item'):
                    headline = item.find('title').text
                    link = item.find('link').text
                    pub_date_str = item.find('pubDate').text
                    
                    if not headline or not link:
                        continue
                        
                    # Parse timestamp
                    try:
                        # Standard RSS format: 'Thu, 09 Jul 2026 12:00:00 GMT'
                        published_at = pd.to_datetime(pub_date_str).tz_localize(None)
                    except Exception:
                        published_at = datetime.utcnow()
                        
                    sig = cls.calculate_event_signature(headline)
                    sentiment, confidence = cls.analyze_sentiment(headline)
                    category = cls.classify_event_category(headline)
                    weight = cls.get_source_weight(feed_name)
                    
                    # 1. Store or update event inside the Event Store
                    c.execute("""
                        INSERT INTO market_events (event_time, event_type, importance, affected_assets, country, summary, sentiment, source_count, event_signature)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_signature) DO UPDATE SET
                            source_count = market_events.source_count + 1,
                            importance = LEAST(1.0, market_events.importance + 0.05)
                        RETURNING event_id
                    """, (
                        published_at, 
                        category, 
                        confidence * weight, 
                        ['Gold', 'GoldBEES'], 
                        'US/Global', 
                        headline, 
                        sentiment, 
                        1, 
                        sig
                    ))
                    
                    event_id = c.fetchone()[0]
                    
                    # 2. Store the specific article linked to this event
                    try:
                        c.execute("""
                            INSERT INTO news_articles (published_at, source, headline, url, sentiment_score, confidence, event_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (published_at, feed_name, headline, link, sentiment, confidence, event_id))
                        inserted_articles += 1
                    except Exception:
                        # Article url already exists, ignore
                        pass
                        
            except Exception as e:
                logger.warning(f"Failed to fetch/parse news from {feed_name}: {e}")
                try:
                    conn.rollback()
                except Exception:
                    pass
                
        try:
            conn.commit()
        except Exception:
            pass
        conn.close()
        logger.info(f"Ingested {inserted_articles} new articles.")

    @staticmethod
    def get_decayed_sentiment_features(target_date: datetime, lookback_days: int = 10, decay_lambda: float = 0.5) -> dict:
        """
        Aggregates daily news sentiments applying exponential decay:
        S_decayed = sum( S(t - d) * exp(-lambda * d) )
        """
        conn = get_db_connection()
        df = pd.read_sql_query("""
            SELECT event_time::date as date, event_type, sentiment, importance
            FROM market_events
            WHERE event_time <= %s AND event_time >= %s
        """, conn, params=(target_date, target_date - timedelta(days=lookback_days)))
        conn.close()
        
        features = {
            "News_Sentiment_Decayed": 0.0,
            "War_Score_Decayed": 0.0,
            "Fed_Score_Decayed": 0.0,
            "Inflation_Score_Decayed": 0.0,
            "ETF_Score_Decayed": 0.0
        }
        
        if df.empty:
            return features
            
        df['date'] = pd.to_datetime(df['date'])
        target_ts = pd.Timestamp(target_date.date())
        
        # Calculate days difference from target
        df['days_diff'] = (target_ts - df['date']).dt.days
        df['decay_weight'] = np.exp(-decay_lambda * df['days_diff'])
        
        # Calculate weighted scores
        df['weighted_sentiment'] = df['sentiment'] * df['importance'] * df['decay_weight']
        
        features["News_Sentiment_Decayed"] = float(df['weighted_sentiment'].sum())
        
        # Category specific decayed scores
        for category, feat_name in [("War", "War_Score_Decayed"), 
                                    ("Central Bank", "Fed_Score_Decayed"), 
                                    ("Inflation", "Inflation_Score_Decayed"),
                                    ("ETF Flow", "ETF_Score_Decayed")]:
            cat_df = df[df['event_type'] == category]
            if not cat_df.empty:
                features[feat_name] = float(cat_df['weighted_sentiment'].sum())
                
        return features

if __name__ == "__main__":
    NewsEventStore.ingest_rss_feeds()
