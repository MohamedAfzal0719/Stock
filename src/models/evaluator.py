import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    mean_absolute_percentage_error
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ModelEvaluator:
    """
    Computes comprehensive evaluation metrics for financial time series models.
    """
    @staticmethod
    def compute_regression_metrics(y_true, y_pred) -> dict:
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mape = mean_absolute_percentage_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        # Directional Accuracy (Did the model predict the correct direction of the move?)
        # Since these are prices, we check if diff(true) and diff(pred) have same sign
        y_true_diff = np.diff(y_true)
        y_pred_diff = np.diff(y_pred)
        
        if len(y_true_diff) > 0:
            dir_correct = (np.sign(y_true_diff) == np.sign(y_pred_diff)).sum()
            dir_acc = dir_correct / len(y_true_diff)
        else:
            dir_acc = 0.0

        return {
            "MAE": mae,
            "MSE": mse,
            "RMSE": rmse,
            "MAPE": mape,
            "R2": r2,
            "Directional_Accuracy": dir_acc
        }

    @staticmethod
    def compute_classification_metrics(y_true_dir, y_pred_dir) -> dict:
        """
        Assumes y_true_dir and y_pred_dir are binary or categorical (-1, 0, 1)
        """
        precision = precision_score(y_true_dir, y_pred_dir, average='macro', zero_division=0)
        recall = recall_score(y_true_dir, y_pred_dir, average='macro', zero_division=0)
        f1 = f1_score(y_true_dir, y_pred_dir, average='macro', zero_division=0)
        conf_matrix = confusion_matrix(y_true_dir, y_pred_dir).tolist()

        return {
            "Precision": precision,
            "Recall": recall,
            "F1": f1,
            "Confusion_Matrix": conf_matrix
        }

    @staticmethod
    def generate_leaderboard(results_list: list) -> pd.DataFrame:
        """
        Takes a list of dictionaries with model results and returns a sorted leaderboard.
        """
        if not results_list:
            return pd.DataFrame()
            
        df = pd.DataFrame(results_list)
        # Rank primarily by RMSE (lower is better), then Directional Accuracy (higher is better)
        df.sort_values(by=["RMSE", "Directional_Accuracy"], ascending=[True, False], inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
