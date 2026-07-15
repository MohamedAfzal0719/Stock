import os
from datetime import datetime
import pandas as pd
import numpy as np
from src.utils.db import get_db_connection, get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)

class EconomicCalendarService:
    """
    Manages global economic events and calculates Standardized Economic Surprise Index:
    Surprise Score = (Actual - Expected) / Historical Std Dev
    """
    
    # Historical Standard Deviations of Surprises (representing standard surprise sizes)
    HISTORICAL_STDS = {
        "Fed Interest Rate Decision": 0.25,      # in percentage points
        "US CPI YoY": 0.15,                      # in percentage points
        "US PPI YoY": 0.20,
        "US Non-Farm Payrolls": 75.0,            # in thousands
        "US GDP Growth Rate": 0.40,
        "RBI Interest Rate Decision": 0.25
    }

    @classmethod
    def get_surprise_std(cls, event_name: str) -> float:
        for key, val in cls.HISTORICAL_STDS.items():
            if key in event_name:
                return val
        return 1.0  # Default fallback if standard deviation is unknown

    @classmethod
    def save_event(cls, event_date: datetime, event_name: str, actual: float, expected: float, previous: float):
        """Saves economic event and computes surprise index."""
        std = cls.get_surprise_std(event_name)
        surprise = 0.0
        if actual is not None and expected is not None:
            surprise = (actual - expected) / std
            
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO economic_events (event_date, event_name, actual, expected, previous, surprise)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (event_date, event_name, actual, expected, previous, surprise))
        conn.commit()
        conn.close()
        logger.info(f"Saved economic event: {event_name}. Surprise Index: {round(surprise, 4)}")

    @classmethod
    def get_macro_surprise_features(cls, target_date: datetime) -> dict:
        """
        Gets aggregated surprise index scores for the last 5 days.
        """
        engine = get_engine()
        df = pd.read_sql_query("""
            SELECT event_name, surprise, event_date
            FROM economic_events
            WHERE event_date <= %s AND event_date >= %s::timestamp - interval '5 days'
        """, engine, params=(target_date, target_date))
        
        features = {
            "Fed_Surprise_Score": 0.0,
            "Inflation_Surprise_Score": 0.0,
            "Employment_Surprise_Score": 0.0,
            "GDP_Surprise_Score": 0.0
        }
        
        if df.empty:
            return features
            
        for _, row in df.iterrows():
            name = row['event_name'].lower()
            val = row['surprise']
            
            if 'fed' in name or 'interest rate' in name or 'fomc' in name:
                features["Fed_Surprise_Score"] += val
            elif 'cpi' in name or 'ppi' in name or 'inflation' in name:
                features["Inflation_Surprise_Score"] += val
            elif 'payroll' in name or 'nfp' in name or 'employment' in name:
                features["Employment_Surprise_Score"] += val
            elif 'gdp' in name:
                features["GDP_Surprise_Score"] += val
                
        return features

    @classmethod
    def populate_seed_calendar(cls):
        """Populates seed data for economic events for backtesting or fallback purposes."""
        logger.info("Seeding economic events...")
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM economic_events")
        if c.fetchone()[0] > 0:
            conn.close()
            logger.info("Economic calendar already has events. Skipping seed.")
            return

        # Seed data over the last year
        seed_events = [
            (datetime(2026, 6, 12), "Fed Interest Rate Decision", 5.25, 5.25, 5.50),
            (datetime(2026, 6, 15), "US CPI YoY", 3.2, 3.1, 3.4),
            (datetime(2026, 6, 18), "US PPI YoY", 2.1, 2.3, 2.2),
            (datetime(2026, 7, 3), "US Non-Farm Payrolls", 185.0, 170.0, 210.0),
            (datetime(2026, 7, 8), "RBI Interest Rate Decision", 6.50, 6.50, 6.50),
        ]
        conn.close()

        for dt, name, act, exp, prev in seed_events:
            cls.save_event(dt, name, act, exp, prev)
            
        logger.info("Economic calendar seeding completed.")

if __name__ == "__main__":
    EconomicCalendarService.populate_seed_calendar()
