import os
import json
import pandas as pd
from typing import Dict, Any

from src.utils.logger import get_logger
logger = get_logger(__name__)

# Initialize Groq client
try:
    from dotenv import load_dotenv
    load_dotenv()
    from groq import Groq
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except ImportError:
    groq_client = None

def get_llm_decision(system_prompt: str, data_context: str) -> Dict[str, Any]:
    """Helper function to call Groq LLM with JSON mode."""
    if not groq_client:
        raise ValueError("Groq client not initialized")
        
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": data_context}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    return json.loads(content)

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
        
        try:
            system_prompt = """You are a Technical Analyst AI for the GoldBeES ETF. 
Analyze the provided technical indicators and output a strict JSON object with these exact keys:
"signal": either "BUY", "SELL", or "HOLD".
"confidence": an integer between 0 and 100 representing your confidence.
"reason": A concise 1-sentence technical explanation for your decision."""
            
            data_context = f"Current Indicators - RSI: {rsi:.2f}, MACD: {macd:.4f}, MACD Signal: {macd_signal:.4f}."
            
            result = get_llm_decision(system_prompt, data_context)
            return {
                "agent": self.name,
                "signal": result.get("signal", "HOLD"),
                "confidence": int(result.get("confidence", 60)),
                "reason": result.get("reason", "No reason provided.")
            }
        except Exception as e:
            logger.warning(f"{self.name} LLM call failed: {e}. Using fallback logic.")
            # Fallback deterministic logic
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
        usd_inr = current_data.get('USD_INR', 95.50)
        gold_spot = current_data.get('Gold_Spot', 2000.0)
        
        try:
            system_prompt = """You are a Macro Economist AI for the Indian GoldBeES ETF. 
GoldBeES tracks domestic physical gold, which is highly influenced by Global Gold Spot prices and the USD/INR exchange rate.
A higher Global Gold Spot price is bullish. A higher USD/INR (weaker Rupee) is bullish for domestic gold.
Output a strict JSON object with these exact keys:
"signal": either "BUY", "SELL", or "HOLD".
"confidence": an integer between 0 and 100 representing your confidence.
"reason": A concise 1-sentence macro explanation for your decision."""
            
            data_context = f"Global Gold Spot Price: ${gold_spot:.2f}, USD/INR Exchange Rate: ₹{usd_inr:.2f}."
            
            result = get_llm_decision(system_prompt, data_context)
            return {
                "agent": self.name,
                "signal": result.get("signal", "HOLD"),
                "confidence": int(result.get("confidence", 60)),
                "reason": result.get("reason", "No reason provided.")
            }
        except Exception as e:
            logger.warning(f"{self.name} LLM call failed: {e}. Using fallback logic.")
            # Fallback deterministic logic
            score = 0
            if usd_inr > 95.5:
                score += 1
            elif usd_inr < 94.5:
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
        
        try:
            system_prompt = """You are a Risk Manager AI for an investment portfolio focusing on ETFs.
Analyze the 20-day historical volatility. High volatility (>2%) suggests reducing exposure (SELL), low volatility (<1%) suggests stable environments (BUY or HOLD).
Output a strict JSON object with these exact keys:
"signal": either "BUY", "SELL", or "HOLD".
"confidence": an integer between 0 and 100 representing your confidence.
"reason": A concise 1-sentence risk explanation for your decision."""
            
            data_context = f"20-Day Rolling Volatility: {volatility*100:.2f}%."
            
            result = get_llm_decision(system_prompt, data_context)
            return {
                "agent": self.name,
                "signal": result.get("signal", "HOLD"),
                "confidence": int(result.get("confidence", 60)),
                "reason": result.get("reason", "No reason provided.")
            }
        except Exception as e:
            logger.warning(f"{self.name} LLM call failed: {e}. Using fallback logic.")
            # Fallback deterministic logic
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
        
        try:
            # Let LLM aggregate the reports
            system_prompt = """You are the Chief Investment AI. You oversee a team of specialized AI agents.
You will be provided with the JSON reports from your Technical Analyst, Macro Economist, and Risk Manager.
You must aggregate their views and make a final executive decision. 
Output a strict JSON object with these exact keys:
"final_signal": either "BUY", "SELL", or "HOLD".
"confidence": an integer between 0 and 100.
"reason": A short 1-sentence summary of your final consensus decision."""
            
            data_context = json.dumps(reports, indent=2)
            result = get_llm_decision(system_prompt, data_context)
            
            return {
                "agent": self.name,
                "final_signal": result.get("final_signal", "HOLD"),
                "confidence": int(result.get("confidence", 65)),
                "sub_agents": reports
            }
        except Exception as e:
            logger.warning(f"{self.name} LLM call failed: {e}. Using fallback aggregation.")
            # Fallback deterministic aggregation
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
