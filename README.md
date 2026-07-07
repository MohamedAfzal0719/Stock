# AI Powered GoldBeES Prediction Platform 🚀

An institutional-grade, end-to-end Machine Learning ecosystem for forecasting and trading the NSE:GOLDBEES Exchange Traded Fund. Built from scratch with Python, FastAPI, and Next.js.

## 🌟 Key Features
- **Automated Data Pipelines**: Robust fetching and cleaning of historical market data via `yfinance`.
- **Advanced Feature Engineering**: 40+ engineered features using the `ta` library (MACD, RSI, Bollinger Bands, Lags, etc).
- **Model Zoo & Optuna HPO**: Automatically trains, optimizes, and ranks 9 different AI architectures (Linear Regression, Random Forest, XGBoost, LightGBM, CatBoost, SVR, LSTM, GRU, Transformer).
- **Vectorized Backtesting Engine**: Tests the AI's predictions against a "Buy & Hold" benchmark with professional risk metrics (Sharpe Ratio, Maximum Drawdown, CAGR).
- **Explainable AI**: SHAP-powered visualizations to understand why the AI is making its decisions.
- **Next.js Dashboard**: A beautiful, real-time glassmorphism React dashboard using Tailwind CSS and Chart.js.

## 🏗️ Architecture

```
Goldbees/
├── api/                  # FastAPI Backend Routes
├── data/                 # Raw, Processed, and EDA outputs
├── frontend/             # Next.js React Dashboard
├── models/               # Serialized ML models and Leaderboard
├── src/                  # Core Python Packages
│   ├── data/             # Downloader, Cleaner, EDA modules
│   ├── features/         # Feature Engineering (engineer.py)
│   ├── models/           # Training (trainer.py, deep_models.py)
│   ├── services/         # Inference, Signals, and Backtesting engines
│   └── utils/            # Logging
├── docker-compose.yml    # Orchestration
├── requirements.txt      # Python dependencies
└── run_api.py            # API Server Entrypoint
```

## 🚀 Quick Start (Local)

### 1. Backend (FastAPI)
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the complete pipeline (Download -> Clean -> Engineer -> Train)
python -m src.data.downloader
python -m src.data.cleaner
python -m src.features.engineer
python -m src.models.train_all

# Start API Server
python run_api.py
```

### 2. Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:3000` to view the Dashboard.

## 🐳 Docker Deployment
You can deploy the entire stack instantly using Docker Compose:
```bash
docker-compose up --build -d
```

## 📊 Evaluation & Metrics
The `src.models.evaluator` calculates:
- **RMSE & MAPE**: For absolute price precision.
- **Directional Accuracy**: For trading signal viability.
- **Value at Risk (95%)**: To quantify downside exposure.

---
*Built with ❤️ for Quantitative Research.*
