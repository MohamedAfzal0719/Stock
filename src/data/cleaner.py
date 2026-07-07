import os
import pandas as pd
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataCleaner:
    """
    Service to clean the raw financial data.
    """
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.raw_filepath = os.path.join(self.base_dir, "data", "raw", "goldbees.csv")
        self.processed_dir = os.path.join(self.base_dir, "data", "processed")
        os.makedirs(self.processed_dir, exist_ok=True)
        self.processed_filepath = os.path.join(self.processed_dir, "goldbees_cleaned.csv")

    def clean_data(self) -> Optional[pd.DataFrame]:
        """
        Cleans the raw dataset:
        - Handles missing values
        - Handles duplicates
        - Corrects datatypes
        - Ensures date index is continuous (handling weekends/holidays implicitly by trading days)
        """
        logger.info("Starting data cleaning process...")

        try:
            if not os.path.exists(self.raw_filepath):
                logger.error(f"Raw data file not found at {self.raw_filepath}")
                return None

            df = pd.read_csv(self.raw_filepath)
            initial_shape = df.shape
            logger.info(f"Loaded raw data with shape: {initial_shape}")

            # 1. Correct Datatypes
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.tz_localize(None) # Remove timezone for simplicity
                df.set_index('Date', inplace=True)
                df.sort_index(inplace=True)
            
            # Ensure numeric columns
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 2. Handle duplicates
            duplicates = df.index.duplicated().sum()
            if duplicates > 0:
                logger.warning(f"Found {duplicates} duplicate rows. Removing...")
                df = df[~df.index.duplicated(keep='first')]

            # 3. Handle missing values (forward fill then backward fill for any remaining)
            missing_count = df.isnull().sum().sum()
            if missing_count > 0:
                logger.warning(f"Found {missing_count} missing values. Imputing...")
                df.ffill(inplace=True)
                df.bfill(inplace=True)

            # 4. Handle abnormal zero volumes (if any, replace with rolling median)
            if 'Volume' in df.columns:
                zero_vols = (df['Volume'] == 0).sum()
                if zero_vols > 0:
                    logger.warning(f"Found {zero_vols} rows with zero volume. Replacing with rolling median...")
                    import numpy as np
                    # Replace 0 with NaN temporarily
                    df['Volume'] = df['Volume'].replace(0, np.nan)
                    # Convert to numeric explicitly just in case
                    df['Volume'] = pd.to_numeric(df['Volume'])
                    # Fill with 20-day rolling median
                    df['Volume'] = df['Volume'].fillna(df['Volume'].rolling(20, min_periods=1).median())
                    # Fill any remaining with overall median
                    df['Volume'] = df['Volume'].fillna(df['Volume'].median())

            # Log stock splits if any large jumps exist (basic heuristic, GOLDBEES has had historical splits)
            # YFinance 'Adj Close' handles splits, but we check if we need to use it
            # We will use 'Close' for prediction generally, but 'Adj Close' is safer if splits occurred
            
            # Save cleaned dataset
            df.reset_index(inplace=True)
            df.to_csv(self.processed_filepath, index=False)
            logger.info(f"Cleaned data saved to {self.processed_filepath}")
            logger.info(f"Shape of cleaned data: {df.shape}")
            
            return df

        except Exception as e:
            logger.error(f"Error during data cleaning: {str(e)}")
            return None

if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.clean_data()
