import os
from src.utils.logger import get_logger
from src.models.meta_model import StackingEnsemble

logger = get_logger(__name__)

def main():
    logger.info("Starting Stacking Ensemble model training...")
    try:
        ensemble = StackingEnsemble()
        metrics = ensemble.train_models()
        logger.info(f"Stacking Ensemble model training complete! Metrics: {metrics}")
    except Exception as e:
        logger.error(f"Failed to train Stacking Ensemble model: {e}")

if __name__ == "__main__":
    main()
