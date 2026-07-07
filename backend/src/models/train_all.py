import os
import pandas as pd
from src.utils.logger import get_logger
from src.models.trainer import MLTrainer
from src.models.deep_trainer import DeepTrainer
from src.models.evaluator import ModelEvaluator

logger = get_logger(__name__)

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_path = os.path.join(base_dir, "data", "processed", "goldbees_features.csv")
    models_dir = os.path.join(base_dir, "models")
    
    if not os.path.exists(data_path):
        logger.error(f"Data not found at {data_path}. Run Phase 1 first.")
        return

    # Train Traditional ML Models
    ml_trainer = MLTrainer(data_path=data_path, models_dir=models_dir)
    ml_models = ["LinearRegression", "RandomForest", "XGBoost", "LightGBM", "CatBoost", "SVR"]
    
    results = []
    
    for model_name in ml_models:
        try:
            res = ml_trainer.optimize_and_train(model_name, n_trials=5) # 5 trials for speed
            results.append(res)
        except Exception as e:
            logger.error(f"Failed to train {model_name}: {e}")

    # Train Deep Learning Models
    try:
        deep_trainer = DeepTrainer(data_path=data_path, models_dir=models_dir, seq_len=10)
        deep_models = ["LSTM", "GRU", "Transformer"]
        
        for model_name in deep_models:
            res = deep_trainer.train_model(model_name, epochs=5) # 5 epochs for speed
            results.append(res)
    except Exception as e:
        logger.error(f"Failed to train Deep Learning models: {e}")

    # Generate Leaderboard
    if results:
        leaderboard = ModelEvaluator.generate_leaderboard(results)
        leaderboard_path = os.path.join(models_dir, "leaderboard.csv")
        leaderboard.to_csv(leaderboard_path, index=False)
        
        logger.info("\n--- MODEL LEADERBOARD ---")
        logger.info("\n" + leaderboard[["Model", "RMSE", "Directional_Accuracy", "Training_Time_sec"]].to_string())
        logger.info(f"\nLeaderboard saved to {leaderboard_path}")
        
        best_model = leaderboard.iloc[0]['Model']
        logger.info(f"🏆 Best Model: {best_model} 🏆")
    else:
        logger.warning("No models successfully trained.")

if __name__ == "__main__":
    main()
