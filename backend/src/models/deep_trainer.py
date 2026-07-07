import os
import time
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from src.utils.logger import get_logger
from src.models.deep_models import TimeSeriesLSTM, TimeSeriesGRU, TimeSeriesTransformer
from src.models.evaluator import ModelEvaluator

logger = get_logger(__name__)

class TimeSeriesDataset(Dataset):
    def __init__(self, X, y, seq_len=10):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
        self.seq_len = seq_len
        
    def __len__(self):
        return len(self.X) - self.seq_len
        
    def __getitem__(self, idx):
        return self.X[idx:idx+self.seq_len], self.y[idx+self.seq_len-1]

class DeepTrainer:
    def __init__(self, data_path: str, models_dir: str, seq_len: int = 10):
        self.data_path = data_path
        self.models_dir = models_dir
        self.seq_len = seq_len
        os.makedirs(self.models_dir, exist_ok=True)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        df = pd.read_csv(self.data_path)
        if 'Date' in df.columns:
            df.set_index('Date', inplace=True)
            
        target_col = 'Close'
        features = [col for col in df.columns if col not in [target_col, 'Daily_Return', 'Log_Return']]
        
        # Scaling is critical for Deep Learning
        self.X = df[features].values
        self.y = df[target_col].values
        
        # Simple standardization
        self.X_mean = np.mean(self.X, axis=0)
        self.X_std = np.std(self.X, axis=0) + 1e-8
        self.X = (self.X - self.X_mean) / self.X_std
        
        split_idx = int(len(self.X) * 0.8)
        self.train_dataset = TimeSeriesDataset(self.X[:split_idx], self.y[:split_idx], seq_len)
        self.test_dataset = TimeSeriesDataset(self.X[split_idx:], self.y[split_idx:], seq_len)
        
        self.train_loader = DataLoader(self.train_dataset, batch_size=32, shuffle=False)
        self.test_loader = DataLoader(self.test_dataset, batch_size=32, shuffle=False)
        self.input_dim = self.X.shape[1]

    def train_model(self, model_name: str, epochs: int = 10) -> dict:
        logger.info(f"Starting training for {model_name} on {self.device}...")
        start_time = time.time()
        
        if model_name == "LSTM":
            model = TimeSeriesLSTM(self.input_dim, hidden_dim=64, num_layers=2, output_dim=1).to(self.device)
        elif model_name == "GRU":
            model = TimeSeriesGRU(self.input_dim, hidden_dim=64, num_layers=2, output_dim=1).to(self.device)
        elif model_name == "Transformer":
            model = TimeSeriesTransformer(self.input_dim, d_model=64, num_heads=4, num_layers=2, output_dim=1, max_seq_len=self.seq_len).to(self.device)
        else:
            raise ValueError("Unknown deep model")

        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        
        train_start = time.time()
        for epoch in range(epochs):
            model.train()
            epoch_loss = 0
            for batch_X, batch_y in self.train_loader:
                batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                
                optimizer.zero_grad()
                out = model(batch_X).squeeze(-1)
                loss = criterion(out, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
        train_time = time.time() - train_start
        
        # Inference / Evaluation
        inf_start = time.time()
        model.eval()
        preds, trues = [], []
        with torch.no_grad():
            for batch_X, batch_y in self.test_loader:
                batch_X = batch_X.to(self.device)
                out = model(batch_X).squeeze(-1)
                preds.extend(out.cpu().numpy())
                trues.extend(batch_y.numpy())
        inf_time = time.time() - inf_start
        
        preds = np.array(preds)
        trues = np.array(trues)
        
        metrics = ModelEvaluator.compute_regression_metrics(trues, preds)
        
        model_path = os.path.join(self.models_dir, f"{model_name}.pth")
        torch.save(model.state_dict(), model_path)
        
        result = {
            "Model": model_name,
            **metrics,
            "Training_Time_sec": train_time,
            "Inference_Time_sec": inf_time,
            "Best_Params": {"epochs": epochs, "seq_len": self.seq_len}
        }
        
        logger.info(f"Finished {model_name}. RMSE: {metrics['RMSE']:.4f}")
        return result
