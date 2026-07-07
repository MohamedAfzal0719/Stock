import pandas as pd
from typing import Dict, Any

class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def analyze(self, current_data: pd.Series) -> Dict[str, Any]:
        raise NotImplementedError

class TechnicalAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__("Technical Analyst")

    def analyze(self, current_data: pd.Series) -> Dict[str, Any]:
        rsi = current_data.get('RSI', 50)
        macd = current_data.get('MACD', 0)
        macd_signal = current_data.get('MACD_Signal', 0)
        
        score = 0
        reasons = []

        if rsi < 30:
            score += 2
            reasons.append("RSI shows heavily oversold.")
        elif rsi < 45:
            score += 1
            reasons.append("RSI leans oversold.")
        elif rsi > 70:
            score -= 2
            reasons.append("RSI shows heavily overbought.")
        elif rsi > 55:
            score -= 1
            reasons.append("RSI leans overbought.")

        if macd > macd_signal and macd > 0:
            score += 2
            reasons.append("MACD Bullish Crossover.")
        elif macd < macd_signal and macd < 0:
            score -= 2
            reasons.append("MACD Bearish Crossover.")

        if score >= 2:
            signal = "BUY"
            confidence = min(100, 50 + score * 15)
        elif score <= -2:
            signal = "SELL"
            confidence = min(100, 50 + abs(score) * 15)
        else:
            signal = "HOLD"
            confidence = 60

        return {
            "agent": self.name,
            "signal": signal,
            "confidence": confidence,
            "reason": reasons[0] if reasons else "Neutral technicals."
        }

class MacroEconomistAgent(BaseAgent):
    def __init__(self):
        super().__init__("Macro Economist")

    def analyze(self, current_data: pd.Series) -> Dict[str, Any]:
        usd_inr = current_data.get('USD_INR', 83.0)
        gold_spot = current_data.get('Gold_Spot', 2000.0)
        
        # Simplified logic: High gold is good for GoldBeES, weak INR (high USD_INR) is good for GoldBeES
        # We need historical averages to know if it's "high" or "low", but we'll use a mock baseline for the agent
        score = 0
        if usd_inr > 83.5:
            score += 1
        elif usd_inr < 82.5:
            score -= 1
            
        if gold_spot > 2300:
            score += 2
        elif gold_spot < 2000:
            score -= 2
            
        if score > 0:
            signal = "BUY"
        elif score < 0:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "agent": self.name,
            "signal": signal,
            "confidence": 75 if signal != "HOLD" else 50,
            "reason": f"Gold spot at {round(gold_spot, 2)}, USD/INR at {round(usd_inr, 2)}."
        }

class RiskManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Risk Manager")

    def analyze(self, current_data: pd.Series) -> Dict[str, Any]:
        volatility = current_data.get('Volatility_20', 0.01)
        
        if volatility > 0.02:
            return {
                "agent": self.name,
                "signal": "SELL",
                "confidence": 80,
                "reason": f"High market volatility ({round(volatility*100, 2)}%). Reduce exposure."
            }
        elif volatility < 0.01:
            return {
                "agent": self.name,
                "signal": "BUY",
                "confidence": 70,
                "reason": "Stable low-volatility environment."
            }
        else:
            return {
                "agent": self.name,
                "signal": "HOLD",
                "confidence": 60,
                "reason": "Normal volatility levels."
            }

class ChiefInvestmentAI(BaseAgent):
    def __init__(self):
        super().__init__("Chief Investment AI")
        self.agents = [
            TechnicalAnalystAgent(),
            MacroEconomistAgent(),
            RiskManagerAgent()
        ]

    def analyze(self, current_data: pd.Series) -> Dict[str, Any]:
        reports = [agent.analyze(current_data) for agent in self.agents]
        
        buy_score = sum([r['confidence'] for r in reports if r['signal'] == 'BUY'])
        sell_score = sum([r['confidence'] for r in reports if r['signal'] == 'SELL'])
        
        if buy_score > sell_score and buy_score > 60:
            final_signal = "BUY"
            confidence = min(99, int((buy_score / (buy_score + sell_score + 1e-9)) * 100))
        elif sell_score > buy_score and sell_score > 60:
            final_signal = "SELL"
            confidence = min(99, int((sell_score / (buy_score + sell_score + 1e-9)) * 100))
        else:
            final_signal = "HOLD"
            confidence = 65

        return {
            "agent": self.name,
            "final_signal": final_signal,
            "confidence": confidence,
            "sub_agents": reports
        }
