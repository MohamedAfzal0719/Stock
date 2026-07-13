import os
import json
import joblib
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from src.utils.logger import get_logger
from src.models.deep_models import TimeSeriesLSTM, TimeSeriesGRU, TimeSeriesTransformer, PatchTST

logger = get_logger(__name__)

class TimeSeriesSequenceDataset(Dataset):
    def __init__(self, X, y, seq_len):
        self.X = torch.tensor(X, dtype=torch.float32)
        if y is not None:
            self.y = torch.tensor(y, dtype=torch.float32)
        else:
            self.y = None
        self.seq_len = seq_len
        
    def __len__(self):
        return len(self.X) - self.seq_len + 1
        
    def __getitem__(self, idx):
        if self.y is not None:
            # We predict y for the final step of the sequence
            return self.X[idx:idx+self.seq_len], self.y[idx+self.seq_len-1]
        else:
            return self.X[idx:idx+self.seq_len], torch.tensor(0.0)

class DeepModelWrapper:
    """
    A unified interface for deep learning sequence models (LSTM, PatchTST, etc.)
    that acts like a Scikit-Learn regressor, managing sequence creation,
    scaling, early stopping, and configuration.
    """
    def __init__(self, model_type="LSTM", seq_len=60, epochs=30, batch_size=32, patience=5, hidden_dim=128):
        self.model_type = model_type
        self.seq_len = seq_len
        self.epochs = epochs
        self.batch_size = batch_size
        self.patience = patience
        self.hidden_dim = hidden_dim
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.scaler = StandardScaler()
        self.model = None
        self.feature_cols = None

    def _build_model(self, input_dim):
        if self.model_type == "LSTM":
            # 2-layer LSTM with dropout as requested by user
            return TimeSeriesLSTM(input_dim, hidden_dim=self.hidden_dim, num_layers=2, output_dim=1, dropout=0.2).to(self.device)
        elif self.model_type == "GRU":
            return TimeSeriesGRU(input_dim, hidden_dim=self.hidden_dim, num_layers=2, output_dim=1, dropout=0.2).to(self.device)
        elif self.model_type == "Transformer":
            return TimeSeriesTransformer(input_dim, d_model=self.hidden_dim, num_heads=4, num_layers=2, output_dim=1, max_seq_len=self.seq_len).to(self.device)
        elif self.model_type == "PatchTST":
            return PatchTST(input_dim, seq_len=self.seq_len, patch_size=12, stride=12, d_model=self.hidden_dim, num_heads=4, num_layers=2, output_dim=1, dropout=0.2).to(self.device)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def fit(self, X: pd.DataFrame, y: pd.Series, X_val=None, y_val=None):
        logger.info(f"Training {self.model_type} on {self.device}...")
        self.feature_cols = list(X.columns)
        
        # Scale
        X_scaled = self.scaler.fit_transform(X.values)
        y_vals = y.values
        
        # Padding: pad the beginning with the first row so len(out) == len(X)
        pad_len = self.seq_len - 1
        X_padded = np.vstack([np.tile(X_scaled[0], (pad_len, 1)), X_scaled])
        y_padded = np.concatenate([np.tile(y_vals[0], pad_len), y_vals])
        
        dataset = TimeSeriesSequenceDataset(X_padded, y_padded, self.seq_len)
        
        # Validation set (Walk-forward / out-of-sample)
        val_loader = None
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val.values)
            y_val_vals = y_val.values
            X_val_padded = np.vstack([np.tile(X_val_scaled[0], (pad_len, 1)), X_val_scaled])
            y_val_padded = np.concatenate([np.tile(y_val_vals[0], pad_len), y_val_vals])
            val_dataset = TimeSeriesSequenceDataset(X_val_padded, y_val_padded, self.seq_len)
            val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)
        else:
            # If no explicit val set, use last 15% of train for early stopping
            split_idx = int(len(dataset) * 0.85)
            train_sub = torch.utils.data.Subset(dataset, range(0, split_idx))
            val_sub = torch.utils.data.Subset(dataset, range(split_idx, len(dataset)))
            dataset = train_sub
            val_loader = DataLoader(val_sub, batch_size=self.batch_size, shuffle=False)
            
        train_loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)
        
        self.model = self._build_model(X_scaled.shape[1])
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        
        best_val_loss = float('inf')
        patience_counter = 0
        best_weights = None
        
        for epoch in range(self.epochs):
            self.model.train()
            train_loss = 0
            for batch_X, batch_y in train_loader:
                batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                optimizer.zero_grad()
                out = self.model(batch_X).squeeze(-1)
                loss = criterion(out, batch_y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
                
            # Validation
            self.model.eval()
            val_loss = 0
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                    out = self.model(batch_X).squeeze(-1)
                    val_loss += criterion(out, batch_y).item()
                    
            train_loss /= len(train_loader)
            val_loss /= len(val_loader)
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_weights = self.model.state_dict()
            else:
                patience_counter += 1
                
            if patience_counter >= self.patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
                
        if best_weights is not None:
            self.model.load_state_dict(best_weights)
            
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        self.model.eval()
        X_scaled = self.scaler.transform(X[self.feature_cols].values)
        
        pad_len = self.seq_len - 1
        X_padded = np.vstack([np.tile(X_scaled[0], (pad_len, 1)), X_scaled])
        
        dataset = TimeSeriesSequenceDataset(X_padded, None, self.seq_len)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)
        
        preds = []
        with torch.no_grad():
            for batch_X, _ in loader:
                batch_X = batch_X.to(self.device)
                out = self.model(batch_X).squeeze(-1)
                preds.extend(out.cpu().numpy())
                
        return np.array(preds)

    def predict_advanced(self, X: pd.DataFrame, n_mc_samples=10) -> dict:
        X_scaled = self.scaler.transform(X[self.feature_cols].values)
        pad_len = self.seq_len - 1
        X_padded = np.vstack([np.tile(X_scaled[0], (pad_len, 1)), X_scaled])
        
        dataset = TimeSeriesSequenceDataset(X_padded, None, self.seq_len)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)
        
        # 1. Deterministic Pass (get clean prediction + embedding)
        self.model.eval()
        clean_preds = []
        embeddings = []
        with torch.no_grad():
            for batch_X, _ in loader:
                batch_X = batch_X.to(self.device)
                pred, embed = self.model(batch_X, return_embeds=True)
                clean_preds.extend(pred.squeeze(-1).cpu().numpy())
                embeddings.extend(embed.cpu().numpy())
                
        # 2. Stochastic Passes (get uncertainty)
        self.model.train() # Enable dropout
        mc_preds = []
        for _ in range(n_mc_samples):
            mc_pass = []
            with torch.no_grad():
                for batch_X, _ in loader:
                    batch_X = batch_X.to(self.device)
                    # We only need prediction here
                    pred = self.model(batch_X).squeeze(-1)
                    mc_pass.extend(pred.cpu().numpy())
            mc_preds.append(mc_pass)
            
        mc_preds = np.array(mc_preds) # shape: (n_mc_samples, len(X))
        std_preds = np.std(mc_preds, axis=0)
        
        return {
            'pred': np.array(clean_preds),
            'std': std_preds,
            'embed': np.array(embeddings)
        }

    def save(self, model_dir: str):
        os.makedirs(model_dir, exist_ok=True)
        # 1. Save PyTorch weights
        torch.save(self.model.state_dict(), os.path.join(model_dir, f"{self.model_type.lower()}_weights.pt"))
        # 2. Save Scaler
        joblib.dump(self.scaler, os.path.join(model_dir, f"{self.model_type.lower()}_scaler.pkl"))
        # 3. Save Config
        config = {
            "model_type": self.model_type,
            "seq_len": self.seq_len,
            "hidden_dim": self.hidden_dim,
            "feature_cols": self.feature_cols
        }
        with open(os.path.join(model_dir, f"{self.model_type.lower()}_config.json"), 'w') as f:
            json.dump(config, f)

    @classmethod
    def load(cls, model_dir: str, model_type: str = "LSTM"):
        config_path = os.path.join(model_dir, f"{model_type.lower()}_config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        instance = cls(
            model_type=config['model_type'], 
            seq_len=config['seq_len'],
            hidden_dim=config.get('hidden_dim', 128)
        )
        instance.feature_cols = config['feature_cols']
        
        # Load Scaler
        instance.scaler = joblib.load(os.path.join(model_dir, f"{model_type.lower()}_scaler.pkl"))
        
        # Load Model
        instance.model = instance._build_model(len(instance.feature_cols))
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        instance.model.load_state_dict(torch.load(os.path.join(model_dir, f"{model_type.lower()}_weights.pt"), map_location=device))
        instance.model.to(device)
        instance.model.eval()
        
        return instance
