import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from src.utils.logger import get_logger

# Load environment variables from backend/.env or root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

logger = get_logger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

from sqlalchemy import create_engine

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set!")
    return psycopg2.connect(DATABASE_URL)

def get_engine():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set!")
    # SQLAlchemy requires postgresql:// instead of postgres:// in newer versions, 
    # but let's just pass it as is or fix it if needed.
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url)

def init_db():
    """Initializes the database schema for the GoldBEES system."""
    logger.info("Initializing database tables...")
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Market prices table
    c.execute("""
        CREATE TABLE IF NOT EXISTS market_prices (
            date TIMESTAMP PRIMARY KEY,
            goldbees_open REAL,
            goldbees_high REAL,
            goldbees_low REAL,
            goldbees_close REAL,
            goldbees_volume REAL,
            gold_futures REAL,
            usd_inr REAL,
            dxy REAL,
            treasury_10y REAL,
            vix REAL,
            crude_oil REAL,
            silver REAL,
            gld_etf_volume REAL
        )
    """)
    
    # 2. Intraday market prices table
    c.execute("""
        CREATE TABLE IF NOT EXISTS market_prices_intraday (
            timestamp TIMESTAMP PRIMARY KEY,
            goldbees_price REAL,
            goldbees_volume REAL,
            gold_futures_price REAL
        )
    """)

    # 3. Market Events Table (Event Store)
    c.execute("""
        CREATE TABLE IF NOT EXISTS market_events (
            event_id SERIAL PRIMARY KEY,
            event_time TIMESTAMP,
            event_type VARCHAR(100),
            importance REAL,
            affected_assets TEXT[],
            country VARCHAR(100),
            summary TEXT,
            sentiment REAL,
            source_count INT DEFAULT 1,
            event_signature TEXT UNIQUE
        )
    """)

    # 4. News Articles Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            id SERIAL PRIMARY KEY,
            published_at TIMESTAMP,
            source VARCHAR(100),
            headline TEXT,
            url TEXT UNIQUE,
            sentiment_score REAL,
            confidence REAL,
            event_id INT REFERENCES market_events(event_id) ON DELETE SET NULL
        )
    """)

    # 5. Economic Calendar
    c.execute("""
        CREATE TABLE IF NOT EXISTS economic_events (
            id SERIAL PRIMARY KEY,
            event_date TIMESTAMP,
            event_name VARCHAR(150),
            actual REAL,
            expected REAL,
            previous REAL,
            surprise REAL
        )
    """)

    # 6. Feature Store
    c.execute("""
        CREATE TABLE IF NOT EXISTS feature_store (
            date TIMESTAMP PRIMARY KEY,
            feature_version VARCHAR(20),
            features JSONB NOT NULL
        )
    """)

    # 7. Predictions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_date TIMESTAMP PRIMARY KEY,
            model_version VARCHAR(20),
            predicted_close REAL,
            predicted_volatility REAL,
            prob_move_1pct REAL,
            prob_move_2pct REAL,
            actual_close REAL,
            actual_volatility REAL,
            ci_lower REAL,
            ci_upper REAL,
            error REAL,
            mape REAL,
            shap_contributions JSONB,
            confidence_score REAL,
            market_regime VARCHAR(50)
        )
    """)

    # 8. Model Metrics table
    c.execute("""
        CREATE TABLE IF NOT EXISTS model_metrics (
            trained_at TIMESTAMP PRIMARY KEY,
            model_version VARCHAR(20),
            model_name VARCHAR(50),
            rmse REAL,
            mae REAL,
            directional_accuracy REAL,
            data_drift_score REAL
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database tables initialized successfully.")

if __name__ == "__main__":
    init_db()
