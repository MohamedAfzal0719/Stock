import pandas as pd
import numpy as np
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataValidator:
    """
    Validation and quality control layer for quantitative market data.
    Ensures input consistency, timezone alignment, outlier controls, and holiday filling.
    """
    
    @staticmethod
    def validate_and_clean_market_data(df: pd.DataFrame, is_intraday: bool = False) -> pd.DataFrame:
        """
        Runs comprehensive data quality validation:
        1. Corrects and normalizes timezone (converts to timezone-naive UTC).
        2. Drops duplicate dates/timestamps, keeping first.
        3. Identifies and fills missing value gaps (e.g., market holidays).
        4. Identifies and caps statistical outliers (e.g., > 4 standard deviation returns).
        """
        if df.empty:
            logger.warning("Empty dataframe passed for validation.")
            return df
            
        df = df.copy()
        
        # 1. Date Index & Timezone Normalization
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        elif 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
        # Ensure index is datetime type
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
            
        # Normalize timezone (strip offset to keep timezone-naive)
        if df.index.tz is not None:
            df.index = df.index.tz_convert('UTC').tz_localize(None)
            
        # 2. Handle duplicates
        dupes = df.index.duplicated().sum()
        if dupes > 0:
            logger.warning(f"Validation alert: Found {dupes} duplicate index entries. Removing duplicates...")
            df = df[~df.index.duplicated(keep='first')]
            
        # Sort index chronologically
        df.sort_index(inplace=True)
        
        # 3. Numeric conversions & Outlier capping
        # We skip capping on columns that are non-numeric
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Apply rolling outlier control for continuous price series (e.g. Close, Open, High, Low)
            if col in ['Close', 'Open', 'High', 'Low', 'goldbees_close', 'goldbees_open', 'goldbees_high', 'goldbees_low']:
                # Compute rolling median and deviation to handle price drifts
                rolling_median = df[col].rolling(window=30, min_periods=5).median()
                rolling_std = df[col].rolling(window=30, min_periods=5).std()
                
                # Z-score metric
                z_scores = (df[col] - rolling_median) / (rolling_std + 1e-8)
                
                # Outlier threshold (z > 4.5)
                outliers = abs(z_scores) > 4.5
                outliers_count = outliers.sum()
                if outliers_count > 0:
                    logger.warning(f"Validation outlier detection: Capping {outliers_count} anomalous points in column '{col}' using rolling limits.")
                    # Cap outliers to rolling median +/- 4 * std
                    lower_limit = rolling_median - 4 * rolling_std
                    upper_limit = rolling_median + 4 * rolling_std
                    df.loc[outliers & (z_scores < 0), col] = lower_limit
                    df.loc[outliers & (z_scores > 0), col] = upper_limit
                    
        # 4. Handle gaps / Holidays
        # If it is daily close, forward-fill missing values to account for weekends/market holidays
        if not is_intraday:
            # We construct a complete business day range
            start_date = df.index.min()
            end_date = df.index.max()
            if pd.notnull(start_date) and pd.notnull(end_date):
                full_range = pd.date_range(start=start_date, end=end_date, freq='B')
                # Reindex with business day range
                df = df.reindex(full_range)
                df.index.name = 'Date'
                
                # Forward-fill gaps (market values don't change over holidays/weekends)
                # Backward fill if start has missing columns
                missing_before = df.isnull().sum().sum()
                df.ffill(inplace=True)
                df.bfill(inplace=True)
                filled_count = missing_before - df.isnull().sum().sum()
                if filled_count > 0:
                    logger.info(f"Validation gap-filling: Forward-filled {filled_count} missing holiday/weekend slots.")
        else:
            # For intraday data, simple forward fill is sufficient
            df.ffill(inplace=True)
            df.bfill(inplace=True)
            
        return df
