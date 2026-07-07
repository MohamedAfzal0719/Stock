import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import mplfinance as mpf
from statsmodels.tsa.seasonal import seasonal_decompose
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataExplorer:
    """
    Service to perform Exploratory Data Analysis (EDA) on cleaned data.
    """
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.processed_filepath = os.path.join(self.base_dir, "data", "processed", "goldbees_cleaned.csv")
        self.eda_dir = os.path.join(self.base_dir, "data", "eda")
        os.makedirs(self.eda_dir, exist_ok=True)
        
        # Set visualization style
        sns.set_theme(style="darkgrid")
        plt.rcParams['figure.figsize'] = (12, 6)

    def load_data(self) -> pd.DataFrame:
        if not os.path.exists(self.processed_filepath):
            raise FileNotFoundError(f"Cleaned data not found at {self.processed_filepath}. Run cleaner first.")
        df = pd.read_csv(self.processed_filepath)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        return df

    def run_eda(self):
        logger.info("Starting Exploratory Data Analysis...")
        try:
            df = self.load_data()
            
            self._plot_price_history(df)
            self._plot_volume_distribution(df)
            self._plot_returns(df)
            self._plot_moving_averages(df)
            self._plot_rolling_volatility(df)
            self._plot_correlation_matrix(df)
            self._plot_candlestick(df)
            self._plot_trend_decomposition(df)
            self._plot_seasonality_heatmap(df)
            
            logger.info(f"EDA successfully completed. All graphs saved to {self.eda_dir}")
            
        except Exception as e:
            logger.error(f"Error during EDA: {str(e)}")

    def _plot_price_history(self, df: pd.DataFrame):
        plt.figure()
        sns.histplot(df['Close'], bins=50, kde=True, color='gold')
        plt.title('Price Distribution')
        plt.xlabel('Price (INR)')
        plt.tight_layout()
        plt.savefig(os.path.join(self.eda_dir, 'price_distribution.png'))
        plt.close()

    def _plot_volume_distribution(self, df: pd.DataFrame):
        plt.figure()
        sns.histplot(df['Volume'], bins=50, kde=True, color='teal')
        plt.title('Volume Distribution')
        plt.xlabel('Volume')
        plt.tight_layout()
        plt.savefig(os.path.join(self.eda_dir, 'volume_distribution.png'))
        plt.close()

    def _plot_returns(self, df: pd.DataFrame):
        df['Daily_Return'] = df['Close'].pct_change()
        
        # Daily Returns
        plt.figure()
        sns.histplot(df['Daily_Return'].dropna(), bins=100, kde=True, color='purple')
        plt.title('Daily Returns Distribution')
        plt.xlabel('Daily Return')
        plt.tight_layout()
        plt.savefig(os.path.join(self.eda_dir, 'daily_returns.png'))
        plt.close()
        
        # Weekly Returns
        weekly = df['Close'].resample('W').last().pct_change()
        plt.figure()
        sns.histplot(weekly.dropna(), bins=50, kde=True, color='blue')
        plt.title('Weekly Returns Distribution')
        plt.xlabel('Weekly Return')
        plt.tight_layout()
        plt.savefig(os.path.join(self.eda_dir, 'weekly_returns.png'))
        plt.close()
        
        # Monthly Returns
        monthly = df['Close'].resample('ME').last().pct_change()
        plt.figure()
        sns.histplot(monthly.dropna(), bins=30, kde=True, color='green')
        plt.title('Monthly Returns Distribution')
        plt.xlabel('Monthly Return')
        plt.tight_layout()
        plt.savefig(os.path.join(self.eda_dir, 'monthly_returns.png'))
        plt.close()
        
        # Yearly trend
        yearly = df['Close'].resample('YE').mean()
        plt.figure()
        yearly.plot(kind='bar', color='orange')
        plt.title('Yearly Average Price Trend')
        plt.xlabel('Year')
        plt.ylabel('Average Price')
        plt.xticks(range(len(yearly)), yearly.index.year, rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.eda_dir, 'yearly_trend.png'))
        plt.close()

    def _plot_moving_averages(self, df: pd.DataFrame):
        plt.figure()
        plt.plot(df.index, df['Close'], label='Close', alpha=0.5)
        plt.plot(df.index, df['Close'].rolling(window=50).mean(), label='50-Day SMA')
        plt.plot(df.index, df['Close'].rolling(window=200).mean(), label='200-Day SMA')
        plt.title('Price with Moving Averages')
        plt.xlabel('Date')
        plt.ylabel('Price (INR)')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(self.eda_dir, 'moving_averages.png'))
        plt.close()

    def _plot_rolling_volatility(self, df: pd.DataFrame):
        if 'Daily_Return' not in df.columns:
            df['Daily_Return'] = df['Close'].pct_change()
            
        rolling_vol = df['Daily_Return'].rolling(window=30).std() * np.sqrt(252) # Annualized
        plt.figure()
        plt.plot(df.index, rolling_vol, color='red')
        plt.title('30-Day Rolling Annualized Volatility')
        plt.xlabel('Date')
        plt.ylabel('Volatility')
        plt.tight_layout()
        plt.savefig(os.path.join(self.eda_dir, 'rolling_volatility.png'))
        plt.close()

    def _plot_correlation_matrix(self, df: pd.DataFrame):
        plt.figure(figsize=(8, 6))
        numeric_df = df.select_dtypes(include=[np.number])
        corr = numeric_df.corr()
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title('Feature Correlation Matrix')
        plt.tight_layout()
        plt.savefig(os.path.join(self.eda_dir, 'correlation_matrix.png'))
        plt.close()
        
    def _plot_candlestick(self, df: pd.DataFrame):
        # Plot last 6 months for clarity
        recent_df = df.last('6ME')
        # mpf requires index to be DatetimeIndex and columns Open, High, Low, Close, Volume
        if all(col in recent_df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
            save_path = os.path.join(self.eda_dir, 'candlestick_6m.png')
            mpf.plot(recent_df, type='candle', volume=True, style='charles', 
                     title='Candlestick Chart (Last 6 Months)', savefig=save_path)

    def _plot_trend_decomposition(self, df: pd.DataFrame):
        # Decompose using statsmodels, resampling to monthly to smooth it out
        monthly_close = df['Close'].resample('ME').mean().dropna()
        if len(monthly_close) > 24: # need at least 2 years for good decomposition
            decomposition = seasonal_decompose(monthly_close, model='multiplicative', period=12)
            fig = decomposition.plot()
            fig.set_size_inches(12, 8)
            plt.tight_layout()
            plt.savefig(os.path.join(self.eda_dir, 'trend_decomposition.png'))
            plt.close()
            
    def _plot_seasonality_heatmap(self, df: pd.DataFrame):
        # Monthly returns heatmap by year
        monthly = df['Close'].resample('ME').last().pct_change().dropna()
        monthly_df = monthly.to_frame(name='Return')
        monthly_df['Year'] = monthly_df.index.year
        monthly_df['Month'] = monthly_df.index.month
        
        pivot = monthly_df.pivot(index='Year', columns='Month', values='Return')
        plt.figure(figsize=(12, 8))
        sns.heatmap(pivot, annot=True, cmap='RdYlGn', fmt=".2%", center=0)
        plt.title('Monthly Seasonality Heatmap (Returns)')
        plt.tight_layout()
        plt.savefig(os.path.join(self.eda_dir, 'seasonality_heatmap.png'))
        plt.close()

if __name__ == "__main__":
    explorer = DataExplorer()
    explorer.run_eda()
