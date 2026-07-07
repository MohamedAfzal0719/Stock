import os
import yfinance as yf
import pandas as pd
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataDownloader:
    """
    Service to download financial data from Yahoo Finance.
    """
    def __init__(self, ticker: str = "GOLDBEES.NS"):
        self.ticker = ticker
        self.raw_data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "raw"
        )
        os.makedirs(self.raw_data_dir, exist_ok=True)
        self.filepath = os.path.join(self.raw_data_dir, "goldbees.csv")

    def download_data(self) -> Optional[pd.DataFrame]:
        """
        Downloads maximum available historical data for the ticker.
        Saves it to data/raw/goldbees.csv.
        """
        logger.info(f"Starting data download for {self.ticker}...")
        
        try:
            # Download max historical data
            df = yf.download(self.ticker, period="max", progress=False)
            
            if df.empty:
                logger.error(f"No data found for {self.ticker}.")
                return None
            
            # Reset index to make Date a column instead of index, useful for saving cleanly
            df.reset_index(inplace=True)
            
            # Flatten multi-level columns if any (yfinance sometimes returns multi-index columns)
            if isinstance(df.columns, pd.MultiIndex):
                # Flatten the MultiIndex to single string (e.g., ('Close', 'GOLDBEES.NS') -> 'Close')
                df.columns = [col[0] for col in df.columns]

            # Save to CSV
            df.to_csv(self.filepath, index=False)
            logger.info(f"Data successfully downloaded and saved to {self.filepath}")
            logger.info(f"Shape of downloaded data: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error during data download: {str(e)}")
            return None

if __name__ == "__main__":
    downloader = DataDownloader()
    downloader.download_data()
