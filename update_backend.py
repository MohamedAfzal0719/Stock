import json

# 1. Update main.py
main_py_addition = '''
from pydantic import BaseModel
from typing import List

class Rule(BaseModel):
    indicator: str
    operator: str
    value: float

class StrategyPayload(BaseModel):
    rules: List[Rule]

@app.post("/backtest_strategy", response_model=ResponseModel)
def backtest_custom_strategy(payload: StrategyPayload):
    try:
        from src.services.backtest import BacktestEngine
        engine = BacktestEngine()
        results = engine.evaluate_custom_strategy(payload.rules)
        return {"status": "success", "message": "Backtest complete", "data": results}
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
'''
with open('d:/Goldbees/api/main.py', 'a', encoding='utf-8') as f:
    f.write(main_py_addition)

# 2. Update backtest.py
backtest_py_addition = '''
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
'''
with open('d:/Goldbees/src/services/backtest.py', 'a', encoding='utf-8') as f:
    f.write(backtest_py_addition)
