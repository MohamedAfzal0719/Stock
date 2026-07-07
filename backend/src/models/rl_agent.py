import pandas as pd
import numpy as np
from typing import Dict, Any

class ReinforcementLearningAgent:
    def __init__(self):
        self.model_name = "PPO_Trading_Agent_v1"
        self.episodes_trained = 10000
        self.learning_rate = 0.0003
        self.discount_factor = 0.99

    def get_status(self, current_data: pd.Series) -> Dict[str, Any]:
        """
        Simulates the output of a PPO RL Agent that has learned to trade.
        Uses recent price action to determine the simulated RL state.
        """
        rsi = current_data.get('RSI', 50)
        macd = current_data.get('MACD', 0)
        macd_signal = current_data.get('MACD_Signal', 0)
        
        # Simulated cumulative reward based on a realistic learning curve
        base_reward = 15420.50 
        daily_fluctuation = np.random.normal(0, 50)
        cumulative_reward = base_reward + daily_fluctuation

        # RL Action Logic
        # PPO tends to be aggressive when momentum aligns
        if rsi < 40 and macd > macd_signal:
            action = "BUY"
            confidence = np.random.randint(75, 95)
            policy_loss = round(np.random.uniform(0.01, 0.05), 4)
            value_loss = round(np.random.uniform(0.1, 0.3), 4)
        elif rsi > 60 and macd < macd_signal:
            action = "SELL"
            confidence = np.random.randint(75, 95)
            policy_loss = round(np.random.uniform(0.01, 0.05), 4)
            value_loss = round(np.random.uniform(0.1, 0.3), 4)
        else:
            action = "HOLD"
            confidence = np.random.randint(50, 70)
            policy_loss = round(np.random.uniform(0.05, 0.1), 4)
            value_loss = round(np.random.uniform(0.3, 0.6), 4)

        return {
            "model": self.model_name,
            "episodes_trained": self.episodes_trained,
            "cumulative_reward": round(cumulative_reward, 2),
            "current_action": action,
            "action_confidence": confidence,
            "metrics": {
                "policy_loss": policy_loss,
                "value_loss": value_loss,
                "learning_rate": self.learning_rate,
                "gamma": self.discount_factor
            }
        }
