import torch
import torch.nn as nn
import math

class TimeSeriesLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, output_dim, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x, return_embeds=False):
        # x shape: (batch, seq_len, input_dim)
        out, _ = self.lstm(x)
        # We only care about the output at the last time step
        embedding = out[:, -1, :]
        pred = self.fc(embedding)
        if return_embeds:
            return pred, embedding
        return pred

class TimeSeriesGRU(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, output_dim, dropout=0.2):
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        out, _ = self.gru(x)
        out = self.fc(out[:, -1, :])
        return out

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)

    def forward(self, x):
        # x: (batch, seq_len, d_model)
        x = x + self.pe[:x.size(1), :].unsqueeze(0)
        return x

class TimeSeriesTransformer(nn.Module):
    def __init__(self, input_dim, d_model, num_heads, num_layers, output_dim, dropout=0.1, max_seq_len=100):
        super().__init__()
        self.input_projection = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len=max_seq_len)
        
        encoder_layers = nn.TransformerEncoderLayer(d_model, num_heads, d_model*4, dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)
        self.fc = nn.Linear(d_model, output_dim)

    def forward(self, x):
        x = self.input_projection(x)
        x = self.pos_encoder(x)
        out = self.transformer_encoder(x)
        # Take the output of the last sequence step
        out = self.fc(out[:, -1, :])
        return out

class PatchTST(nn.Module):
    def __init__(self, input_dim, seq_len=60, patch_size=12, stride=12, d_model=64, num_heads=4, num_layers=2, output_dim=1, dropout=0.2):
        super().__init__()
        self.patch_size = patch_size
        self.stride = stride
        
        # Calculate number of patches
        self.num_patches = (seq_len - patch_size) // stride + 1
        
        # Linear projection of patches
        self.patch_proj = nn.Linear(input_dim * patch_size, d_model)
        
        # Positional embedding for patches
        self.pos_embedding = nn.Parameter(torch.randn(1, self.num_patches, d_model))
        
        # Transformer
        encoder_layers = nn.TransformerEncoderLayer(d_model, num_heads, d_model * 2, dropout, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layers, num_layers)
        
        # Head separated for embedding extraction
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(self.num_patches * d_model, 64)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(64, output_dim)
        
    def forward(self, x, return_embeds=False):
        # x: (batch, seq_len, features)
        batch_size = x.size(0)
        
        # Extract patches
        patches = []
        for i in range(self.num_patches):
            start = i * self.stride
            end = start + self.patch_size
            # Patch shape: (batch, patch_size, features)
            patch = x[:, start:end, :]
            # Flatten patch for projection: (batch, patch_size * features)
            patches.append(patch.reshape(batch_size, -1))
            
        # Stack patches: (batch, num_patches, patch_size * features)
        patches = torch.stack(patches, dim=1)
        
        # Project patches
        x = self.patch_proj(patches) # (batch, num_patches, d_model)
        
        # Add positional embedding
        x = x + self.pos_embedding
        
        # Transformer
        x = self.transformer(x) # (batch, num_patches, d_model)
        
        # Head
        x = self.flatten(x)
        embedding = self.dropout(self.relu(self.fc1(x)))
        pred = self.fc2(embedding)
        if return_embeds:
            return pred, embedding
        return pred
