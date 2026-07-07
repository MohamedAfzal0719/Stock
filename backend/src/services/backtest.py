import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.utils.logger import get_logger
from src.services.inference import InferenceEngine

logger = get_logger(__name__)

class BacktestEngine:
    """
    Vectorized Backtesting Engine to simulate trading strategies against Buy & Hold.
    """
    def __init__(self, initial_capital: float = 100000.0, model_name: str = "LinearRegression"):
        self.initial_capital = initial_capital
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        self.inference = InferenceEngine(model_name=model_name)
        signals_df = self.inference.generate_signals()
        self.df = self.inference.df.copy()
        if 'Action' in signals_df.columns:
            self.df['Action'] = signals_df['Action']
        
        if self.df.empty:
            logger.error("Failed to generate signals for backtesting.")

    def run_backtest(self):
        logger.info("Running vectorized backtest...")
        if self.df.empty:
            return
            
        # Strategy: 
        # BUY signal -> Hold 1 unit (100% exposure)
        # SELL signal -> Hold 0 units (0% exposure, flat)
        # HOLD -> Keep previous position
        
        # Convert Action to Position Target (1 for Buy, 0 for Sell, NaN for Hold)
        self.df['Target_Position'] = np.nan
        self.df.loc[self.df['Action'] == 'BUY', 'Target_Position'] = 1.0
        self.df.loc[self.df['Action'] == 'SELL', 'Target_Position'] = 0.0
        
        # Forward fill to maintain HOLD states
        self.df['Position'] = self.df['Target_Position'].ffill().fillna(0.0) # Start flat
        
        # Shift position by 1 because we trade at the CLOSE of the signal day, 
        # meaning we capture the return of the NEXT day.
        self.df['Position'] = self.df['Position'].shift(1).fillna(0)
        
        # Daily Returns of the asset
        self.df['Market_Return'] = self.df['Close'].pct_change()
        
        # Strategy Returns
        self.df['Strategy_Return'] = self.df['Position'] * self.df['Market_Return']
        
        # Cumulative Equity Curves
        self.df['Market_Equity'] = self.initial_capital * (1 + self.df['Market_Return']).cumprod()
        self.df['Strategy_Equity'] = self.initial_capital * (1 + self.df['Strategy_Return']).cumprod()
        
        self._calculate_metrics()
        self._plot_equity_curve()
        
    def _calculate_metrics(self):
        # Time Period in years
        years = len(self.df) / 252.0
        
        # ROI
        market_final = self.df['Market_Equity'].iloc[-1]
        strategy_final = self.df['Strategy_Equity'].iloc[-1]
        
        market_roi = (market_final - self.initial_capital) / self.initial_capital
        strategy_roi = (strategy_final - self.initial_capital) / self.initial_capital
        
        # CAGR
        market_cagr = (market_final / self.initial_capital) ** (1 / years) - 1
        strategy_cagr = (strategy_final / self.initial_capital) ** (1 / years) - 1
        
        # Volatility
        market_vol = self.df['Market_Return'].std() * np.sqrt(252)
        strategy_vol = self.df['Strategy_Return'].std() * np.sqrt(252)
        
        # Sharpe Ratio (assuming risk-free rate = 0 for simplicity)
        market_sharpe = (market_cagr) / market_vol if market_vol != 0 else 0
        strategy_sharpe = (strategy_cagr) / strategy_vol if strategy_vol != 0 else 0
        
        # Max Drawdown
        self.df['Market_Peak'] = self.df['Market_Equity'].cummax()
        self.df['Market_DD'] = (self.df['Market_Equity'] - self.df['Market_Peak']) / self.df['Market_Peak']
        market_mdd = self.df['Market_DD'].min()
        
        self.df['Strategy_Peak'] = self.df['Strategy_Equity'].cummax()
        self.df['Strategy_DD'] = (self.df['Strategy_Equity'] - self.df['Strategy_Peak']) / self.df['Strategy_Peak']
        strategy_mdd = self.df['Strategy_DD'].min()
        
        # Win Rate (percentage of days with positive return when in market)
        active_days = self.df[self.df['Position'] > 0]
        win_rate = (active_days['Strategy_Return'] > 0).sum() / len(active_days) if len(active_days) > 0 else 0
        
        logger.info("\n=== BACKTEST RESULTS ===")
        logger.info(f"{'Metric':<20} | {'Market (Buy&Hold)':<20} | {'Strategy':<20}")
        logger.info("-" * 65)
        logger.info(f"{'Total ROI':<20} | {market_roi:>.2%} | {strategy_roi:>.2%}")
        logger.info(f"{'CAGR':<20} | {market_cagr:>.2%} | {strategy_cagr:>.2%}")
        logger.info(f"{'Sharpe Ratio':<20} | {market_sharpe:>20.2f} | {strategy_sharpe:>20.2f}")
        logger.info(f"{'Max Drawdown':<20} | {market_mdd:>.2%} | {strategy_mdd:>.2%}")
        logger.info(f"{'Win Rate (Active)':<20} | {'N/A':>20} | {win_rate:>.2%}")
        logger.info("========================")

    def _plot_equity_curve(self):
        plt.figure(figsize=(14, 7))
        plt.plot(self.df.index, self.df['Market_Equity'], label='Buy & Hold', alpha=0.7)
        plt.plot(self.df.index, self.df['Strategy_Equity'], label='AI Strategy', color='green', linewidth=2)
        plt.title('Backtest Equity Curve: AI Strategy vs Buy & Hold')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value (INR)')
        plt.legend()
        plt.grid(True)
        
        plot_dir = os.path.join(self.base_dir, "data", "eda", "backtest")
        os.makedirs(plot_dir, exist_ok=True)
        save_path = os.path.join(plot_dir, "equity_curve.png")
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        logger.info(f"Equity curve saved to {save_path}")

    def evaluate_custom_strategy(self, rules: list) -> dict:
        import pandas as pd
        if self.df is None or self.df.empty:
            return {}
            
        buy_condition = pd.Series(True, index=self.df.index)
        
        for rule in rules:
            indicator = rule.indicator
            operator = rule.operator
            value = rule.value
            
            if indicator not in self.df.columns:
                continue
                
            if operator == '>':
                buy_condition = buy_condition & (self.df[indicator] > value)
            elif operator == '<':
                buy_condition = buy_condition & (self.df[indicator] < value)
            elif operator == '>=':
                buy_condition = buy_condition & (self.df[indicator] >= value)
            elif operator == '<=':
                buy_condition = buy_condition & (self.df[indicator] <= value)
            elif operator == '==':
                buy_condition = buy_condition & (self.df[indicator] == value)
                
        self.df['Target_Position'] = 0.0
        self.df.loc[buy_condition, 'Target_Position'] = 1.0
        
        self.df['Position'] = self.df['Target_Position'].shift(1).fillna(0)
        self.df['Market_Return'] = self.df['Close'].pct_change()
        self.df['Strategy_Return'] = self.df['Position'] * self.df['Market_Return']
        
        self.df['Market_Equity'] = self.initial_capital * (1 + self.df['Market_Return']).cumprod()
        self.df['Strategy_Equity'] = self.initial_capital * (1 + self.df['Strategy_Return']).cumprod()
        
        strategy_final = self.df['Strategy_Equity'].iloc[-1]
        strategy_roi = (strategy_final - self.initial_capital) / self.initial_capital * 100
        
        active_days = self.df[self.df['Position'] > 0]
        trades = (self.df['Position'].diff() > 0).sum()
        win_rate = (active_days['Strategy_Return'] > 0).sum() / len(active_days) * 100 if len(active_days) > 0 else 0
        
        return {
            "total_return": round(strategy_roi, 2),
            "win_rate": round(win_rate, 2),
            "total_trades": int(trades),
            "final_equity": round(strategy_final, 2)
        }

if __name__ == "__main__":
    backtester = BacktestEngine(model_name="LinearRegression")
    backtester.run_backtest()

