import matplotlib
matplotlib.use('Agg')

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from py_vapid import Vapid
from py_vapid.utils import b64urlencode
from cryptography.hazmat.primitives import serialization
from pywebpush import webpush, WebPushException
import json
import os
import pandas as pd
from typing import Dict, Any, List

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import urllib.parse
import os
from dotenv import load_dotenv
load_dotenv()

from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

from src.data.downloader import DataDownloader
from src.data.cleaner import DataCleaner
from src.features.engineer import FeatureEngineer
from src.services.inference import InferenceEngine
from src.services.backtest import BacktestEngine
from src.models.train_all import main as train_all_models
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Set up SQLite database
DATABASE_URL = os.environ.get("DATABASE_URL")

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, status

SECRET_KEY = "your-very-secret-key-for-jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# VAPID Keys Setup for Web Push Notifications
vapid_key_file = os.path.join(os.path.dirname(__file__), "vapid_private.pem")
vapid = Vapid()
if not os.path.exists(vapid_key_file):
    vapid.generate_keys()
    vapid.save_key(vapid_key_file)
else:
    vapid = Vapid.from_file(vapid_key_file)

# Extract raw public key bytes and encode to base64url for browser compatibility
raw_pub = vapid.public_key.public_bytes(
    serialization.Encoding.X962,
    serialization.PublicFormat.UncompressedPoint
)
VAPID_PUBLIC_KEY = b64urlencode(raw_pub)
VAPID_PRIVATE_KEY = vapid_key_file
VAPID_CLAIMS = {
    "sub": "mailto:admin@goldbees.com"
}

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            hashed_password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS portfolios (
            user_id INTEGER PRIMARY KEY,
            total_invested REAL,
            units REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            subscription_id SERIAL PRIMARY KEY,
            user_id INTEGER,
            endpoint TEXT UNIQUE,
            p256dh TEXT,
            auth TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT user_id, username FROM users WHERE username=%s", (username,))
    row = c.fetchone()
    conn.close()
    if row is None:
        raise credentials_exception
    return {"user_id": row[0], "username": row[1]}

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="GoldBeES AI Trading API",
    description="Production-ready API for Gold ETF Forecasting",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class ResponseModel(BaseModel):
    status: str
    message: str
    data: Dict[str, Any] = {}

class TrainRequest(BaseModel):
    models: List[str] = ["LinearRegression", "RandomForest", "LSTM"]
    optimize: bool = True

# --- API Endpoints ---

@app.get("/", response_model=ResponseModel)
def health_check():
    return {"status": "success", "message": "GoldBeES AI Engine is running perfectly.", "data": {}}

@app.post("/download-data", response_model=ResponseModel)
def download_and_process_data(background_tasks: BackgroundTasks):
    """
    Triggers the entire data pipeline asynchronously (Download -> Clean -> Engineer).
    """
    def run_pipeline():
        try:
            logger.info("API triggered data pipeline.")
            downloader = DataDownloader()
            downloader.download_data()
            
            cleaner = DataCleaner()
            cleaner.clean_data()
            
            engineer = FeatureEngineer()
            engineer.generate_features()
            logger.info("API data pipeline completed.")
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")

    background_tasks.add_task(run_pipeline)
    return {"status": "success", "message": "Data pipeline triggered in the background.", "data": {}}

@app.post("/train", response_model=ResponseModel)
def train_models(background_tasks: BackgroundTasks):
    """
    Triggers the full model zoo training and leaderboard generation in the background.
    """
    def run_training():
        try:
            logger.info("API triggered full training suite.")
            train_all_models()
            logger.info("API training completed.")
        except Exception as e:
            logger.error(f"Training failed: {e}")

    background_tasks.add_task(run_training)
    return {"status": "success", "message": "Model training triggered in the background.", "data": {}}

@app.get("/predict", response_model=ResponseModel)
def get_predictions(model_name: str = "LinearRegression"):
    """
    Get 1-day prediction and AI signals for the current market state.
    """
    try:
        engine = InferenceEngine(model_name=model_name)
        signals = engine.generate_signals()
        
        if signals.empty:
            raise HTTPException(status_code=400, detail="No data available for inference.")
            
        latest = signals.iloc[-1].to_dict()
        return {"status": "success", "message": "Prediction generated.", "data": latest}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forecast", response_model=ResponseModel)
def get_forecasts(model_name: str = "LinearRegression"):
    """
    Get multi-horizon forecasts (1, 5, 30, 90 days).
    """
    try:
        engine = InferenceEngine(model_name=model_name)
        forecasts = engine.forecast_horizons()
        return {"status": "success", "message": "Forecasts generated.", "data": forecasts}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

LAST_NOTIFIED_SIGNAL_DATE = None

def send_push_notifications(title: str, body: str):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("SELECT endpoint, p256dh, auth FROM push_subscriptions")
        rows = c.fetchall()
        conn.close()
        
        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": "/icon.png",
            "badge": "/badge.png",
            "url": "/"
        })
        
        for row in rows:
            endpoint, p256dh, auth = row
            subscription_info = {
                "endpoint": endpoint,
                "keys": {
                    "p256dh": p256dh,
                    "auth": auth
                }
            }
            try:
                webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS
                )
            except WebPushException as ex:
                logger.warning(f"Failed to send push: {ex}")
    except Exception as e:
        logger.error(f"Error in send_push_notifications: {e}")

def check_and_trigger_push(signals):
    global LAST_NOTIFIED_SIGNAL_DATE
    if signals.empty:
        return
    latest = signals.iloc[-1]
    latest_date = str(latest.name) if hasattr(latest, 'name') else str(latest.get('Date', ''))
    latest_action = latest.get('Action', 'HOLD')
    
    if LAST_NOTIFIED_SIGNAL_DATE != latest_date:
        if latest_action in ['BUY', 'SELL']:
            # Run in a background thread to prevent API block
            import threading
            t = threading.Thread(
                target=send_push_notifications, 
                args=(f"GoldBeES AI alert: {latest_action}", f"Strategy updated to {latest_action} on {latest_date}.")
            )
            t.start()
        LAST_NOTIFIED_SIGNAL_DATE = latest_date

@app.get("/signals", response_model=ResponseModel)
def get_historical_signals(model_name: str = "LinearRegression", days: int = 30):
    """
    Get historical BUY/HOLD/SELL signals for the last 'n' days.
    """
    try:
        engine = InferenceEngine(model_name=model_name)
        signals = engine.generate_signals()
        
        if signals.empty:
            raise HTTPException(status_code=400, detail="No data available.")
            
        # Trigger background web push checks
        check_and_trigger_push(signals)
            
        history = signals.tail(days).reset_index().to_dict(orient="records")
        # Convert timestamp to string for JSON serialization
        for item in history:
            item['Date'] = str(item['Date'])
            
        return {"status": "success", "message": f"Historical signals for last {days} days.", "data": {"signals": history}}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models", response_model=ResponseModel)
def get_model_leaderboard():
    """
    Retrieve the current model leaderboard.
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        leaderboard_path = os.path.join(base_dir, "models", "leaderboard.csv")
        
        if not os.path.exists(leaderboard_path):
            return {"status": "success", "message": "No leaderboard found. Train models first.", "data": {}}
            
        df = pd.read_csv(leaderboard_path)
        data = df.to_dict(orient="records")
        return {"status": "success", "message": "Leaderboard retrieved.", "data": {"leaderboard": data}}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backtest", response_model=ResponseModel)
def run_backtest(model_name: str = "LinearRegression"):
    """
    Run the backtester and return performance metrics.
    """
    try:
        backtester = BacktestEngine(model_name=model_name)
        
        # Run the backtest first so the columns (Market_Equity, etc.) are generated
        backtester.run_backtest()
        
        if backtester.df.empty or 'Market_Equity' not in backtester.df.columns:
            raise HTTPException(status_code=400, detail="Backtest failed to generate data.")
            
        market_final = backtester.df['Market_Equity'].iloc[-1]
        strategy_final = backtester.df['Strategy_Equity'].iloc[-1]
        
        market_roi = (market_final - backtester.initial_capital) / backtester.initial_capital
        strategy_roi = (strategy_final - backtester.initial_capital) / backtester.initial_capital
        
        metrics = {
            "Market_ROI_Percent": market_roi * 100,
            "Strategy_ROI_Percent": strategy_roi * 100,
            "Difference_Percent": (strategy_roi - market_roi) * 100
        }
        
        return {"status": "success", "message": "Backtest completed.", "data": metrics}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CustomForecastRequest(BaseModel):
    target_date: str
    model_name: str = "LinearRegression"

import yfinance as yf

def get_live_price(ticker: str = "GOLDBEES.NS") -> float:
    try:
        import requests
        import re
        
        # Try Google Finance first (very reliable, avoids yfinance IP bans)
        # Convert Yahoo ticker format to Google Finance format (GOLDBEES:NSE)
        gf_ticker = ticker.split('.')[0] + ":NSE"
        res = requests.get(f'https://www.google.com/finance/quote/{gf_ticker}')
        match = re.search(r'data-last-price="([0-9\.]+)"', res.text)
        
        if match:
            price = float(match.group(1))
            if price > 0:
                return price
                
    except Exception as e:
        logger.warning(f"Google Finance fetch failed: {e}")
        
    return None

@app.post("/custom-forecast", response_model=ResponseModel)
def custom_forecast(request: CustomForecastRequest):
    try:
        live_price = get_live_price()
        engine = InferenceEngine(model_name=request.model_name)
        result = engine.custom_forecast(request.target_date, live_price=live_price)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return {"status": "success", "message": "Custom forecast generated", "data": result}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/macro", response_model=ResponseModel)
def get_macro_data():
    """
    Fetch live macro-economic data (USD/INR and Global Gold Futures)
    """
    try:
        import requests
        import re

        # USD to INR Exchange Rate
        try:
            res_usd = requests.get('https://www.google.com/finance/quote/USD-INR')
            match_usd = re.search(r'data-last-price="([0-9\.]+)"', res_usd.text)
            usd_inr = float(match_usd.group(1)) if match_usd else 83.50
        except:
            usd_inr = 83.50
        
        # Global Gold Futures (USD per Ounce)
        try:
            res_gold = requests.get('https://www.google.com/finance/quote/GCW00:COMEX')
            match_gold = re.search(r'data-last-price="([0-9\.]+)"', res_gold.text)
            gold_usd = float(match_gold.group(1)) if match_gold else 2350.00
        except:
            gold_usd = 2350.00
        
        data = {
            "USD_INR": float(usd_inr),
            "Gold_Futures_USD": float(gold_usd)
        }
        return {"status": "success", "message": "Macro data retrieved", "data": data}
    except Exception as e:
        logger.warning(f"Failed to fetch macro data: {e}")
        return {"status": "success", "message": "Macro data (fallback)", "data": {"USD_INR": 83.50, "Gold_Futures_USD": 2350.00}}

# --- API Endpoints ---

class UserRegister(BaseModel):
    username: str
    password: str

@app.post("/register", response_model=ResponseModel)
def register(user: UserRegister):
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, hashed_password) VALUES (%s, %s)", (user.username, get_password_hash(user.password)))
        conn.commit()
    except psycopg2.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    conn.close()
    return {"status": "success", "message": "User registered successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT user_id, username, hashed_password FROM users WHERE username=%s", (form_data.username,))
    row = c.fetchone()
    conn.close()
    if not row or not verify_password(form_data.password, row[2]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": row[1]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user_id": row[0]}

class PortfolioRequest(BaseModel):
    total_invested: float
    units: float

@app.post("/portfolio", response_model=ResponseModel)
def save_portfolio(req: PortfolioRequest, current_user: dict = Depends(get_current_user)):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('''
            INSERT INTO portfolios (user_id, total_invested, units, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                total_invested=excluded.total_invested,
                units=excluded.units,
                updated_at=CURRENT_TIMESTAMP
        ''', (current_user["user_id"], req.total_invested, req.units))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Portfolio saved"}
    except Exception as e:
        logger.error(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save portfolio")

@app.get("/portfolio", response_model=ResponseModel)
def get_portfolio(current_user: dict = Depends(get_current_user)):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("SELECT total_invested, units FROM portfolios WHERE user_id=%s", (current_user["user_id"],))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {"status": "success", "message": "Portfolio fetched", "data": {"total_invested": row[0], "units": row[1]}}
        return {"status": "success", "message": "No portfolio found", "data": {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch portfolio")

class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: Dict[str, str]

@app.post("/subscribe", response_model=ResponseModel)
def subscribe_push(req: PushSubscriptionRequest, current_user: dict = Depends(get_current_user)):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('''
            INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (endpoint) DO UPDATE SET user_id = EXCLUDED.user_id, p256dh = EXCLUDED.p256dh, auth = EXCLUDED.auth
        ''', (current_user["user_id"], req.endpoint, req.keys.get("p256dh"), req.keys.get("auth")))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Subscription registered", "data": {}}
    except Exception as e:
        logger.error(f"Subscription Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to register subscription")

@app.get("/vapid-public-key", response_model=ResponseModel)
def get_vapid_public_key():
    return {"status": "success", "message": "VAPID key retrieved", "data": {"public_key": VAPID_PUBLIC_KEY}}

@app.get("/dashboard", response_model=ResponseModel)
def get_dashboard_data(model_name: str = "LinearRegression"):
    """
    Aggregates data needed for the frontend React dashboard.
    """
    try:
        # Fetch live price
        live_price = get_live_price()
        
        # Load Risk and Forecasts
        engine = InferenceEngine(model_name=model_name)
        risk = engine.calculate_risk()
        forecast = engine.forecast_horizons(live_price=live_price)
        
        # Load Latest Price (from live if available, else from history)
        latest_price = live_price if live_price is not None else forecast.get("Current_Price", 0)
        forecast["Current_Price"] = latest_price
        
        ohlc = engine.get_historical_ohlc(1000)
        
        data = {
            "current_price": latest_price,
            "forecast": forecast,
            "risk_metrics": risk,
            "active_model": model_name,
            "ohlc": ohlc
        }
        return {"status": "success", "message": "Dashboard data retrieved.", "data": data}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/intelligence", response_model=ResponseModel)
def get_intelligence(model_name: str = "LinearRegression"):
    """
    Returns all Wave 1 AI intelligence data: SHAP, Market Regime, Anomaly, Confidence Score.
    """
    try:
        live_price = get_live_price()
        engine = InferenceEngine(model_name=model_name)

        shap_data = engine.get_shap_values()
        regime = engine.detect_market_regime()
        anomalies = engine.detect_anomalies()
        confidence = engine.get_confidence_score(live_price=live_price)

        data = {
            "shap": shap_data,
            "market_regime": regime,
            "anomalies": anomalies,
            "confidence": confidence
        }
        return {"status": "success", "message": "AI Intelligence data retrieved", "data": data}
    except Exception as e:
        logger.error(f"Intelligence endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wave2_data", response_model=ResponseModel)
def get_wave2_data(model_name: str = "LinearRegression"):
    """
    Returns Wave 2 AI data: Probability Distribution, Similar Days, and Chart Patterns.
    """
    try:
        live_price = get_live_price()
        engine = InferenceEngine(model_name=model_name)
        
        prob_dist = engine.get_probability_distribution(live_price=live_price)
        similar_days = engine.find_similar_days()
        patterns = engine.detect_patterns()
        
        data = {
            "probability_distribution": prob_dist,
            "similar_days": similar_days,
            "patterns": patterns
        }
        return {"status": "success", "message": "Wave 2 data retrieved", "data": data}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SimulationRequest(BaseModel):
    variable: str
    change_pct: float
    model_name: str = "LinearRegression"

@app.post("/simulate", response_model=ResponseModel)
def simulate_scenario(req: SimulationRequest):
    """
    What-If Simulator Endpoint
    """
    try:
        live_price = get_live_price()
        engine = InferenceEngine(model_name=req.model_name)
        result = engine.simulate_scenario(variable=req.variable, change_pct=req.change_pct, live_price=live_price)
        return {"status": "success", "message": "Simulation complete", "data": result}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from typing import Optional

class ReasoningRequest(BaseModel):
    signal: str
    price: Optional[float] = 0.0
    rsi: Optional[float] = 50.0
    macd: Optional[float] = 0.0

@app.post("/reasoning", response_model=ResponseModel)
def get_ai_reasoning(req: ReasoningRequest):
    """
    LLM reasoning for the latest signal
    """
    try:
        prompt = f"""
        You are a quantitative financial AI. 
        The current signal for GoldBeES ETF is {req.signal}.
        Current Price: ₹{req.price}. RSI: {req.rsi}. MACD: {req.macd}.
        Provide a concise, 3-bullet point reasoning for this {req.signal} signal.
        Keep it professional and under 50 words total.
        """
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.2,
            max_tokens=150
        )
        reasoning = response.choices[0].message.content
        return {"status": "success", "message": "Reasoning generated", "data": {"reasoning": reasoning}}
    except Exception as e:
        logger.error(f"Reasoning error: {e}")
        return {"status": "success", "message": "Fallback", "data": {"reasoning": "AI reasoning unavailable at this moment."}}

class ChatRequest(BaseModel):
    message: str

@app.post("/chat", response_model=ResponseModel)
def chat_with_portfolio(req: ChatRequest):
    """
    RAG Chatbot using Groq
    """
    try:
        engine = InferenceEngine()
        regime = engine.detect_market_regime()
        live_price = get_live_price()
        
        system_prompt = f"""
        You are an expert AI trading assistant for a GoldBeES investment portfolio.
        Current Market Regime: {regime['regime']}. Live Price: ₹{live_price}. RSI: {regime['rsi']}.
        Be extremely concise, helpful, and professional. Do not use markdown.
        """
        
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.5,
            max_tokens=300
        )
        reply = response.choices[0].message.content
        return {"status": "success", "message": "Chat generated", "data": {"reply": reply}}
    except Exception as e:
        return {"status": "error", "message": str(e), "data": {}}

import requests
import json

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "d17f963a90ce464c938c8b8959a8f4be")

@app.get("/news", response_model=ResponseModel)
def get_ai_news_intelligence():
    """
    Fetches latest macro news and uses Groq for Sentiment Analysis and Summarization
    """
    try:
        articles_text = ""
        if NEWS_API_KEY:
            url = f"https://newsapi.org/v2/everything?q=(\"Gold prices\" OR \"Reserve Bank of India\" OR \"Federal Reserve\" OR \"Indian stock market\")&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}"
            resp = requests.get(url).json()
            if resp.get("status") == "ok":
                articles = resp.get("articles", [])[:5]
                articles_text = "\n".join([f"- {a['title']}: {a['description']}" for a in articles if a.get('title') and a.get('description')])
        
        if not articles_text:
            articles_text = """
            - Federal Reserve keeps interest rates unchanged, hinting at future cuts.
            - RBI maintains repo rate, citing inflation control.
            - Global gold prices surge amidst geopolitical tensions.
            """

        prompt = f"""
        You are a financial analyst. Read the following recent news headlines regarding Gold and Macroeconomics:
        {articles_text}
        
        1. Write a 2-sentence summary of the overall market sentiment based on this news.
        2. Classify the overall sentiment specifically for Gold as strictly one word: 'Bullish', 'Bearish', or 'Neutral'.
        3. Give a confidence score (0-100) for this sentiment.
        
        Return ONLY valid JSON in this exact format, nothing else:
        {{"summary": "...", "sentiment": "...", "confidence": 85}}
        """
        
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=150,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return {"status": "success", "message": "News intelligence generated", "data": result}
    except Exception as e:
        logger.error(f"News error: {e}")
        fallback = {
            "summary": "AI was unable to fetch live news at this moment.",
            "sentiment": "Neutral",
            "confidence": 50
        }
        return {"status": "success", "message": "Fallback", "data": fallback}

from fastapi.responses import FileResponse
from reportlab.pdfgen import canvas

@app.get("/report")
def generate_pdf_report():
    """
    Generates a Daily AI PDF Report.
    """
    pdf_path = os.path.join(os.path.dirname(__file__), "daily_report.pdf")
    try:
        c = canvas.Canvas(pdf_path)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, 800, "GoldBeES AI Daily Investment Report")
        
        live_price = get_live_price()
        c.setFont("Helvetica", 14)
        c.drawString(50, 750, f"Current Live Price: INR {live_price}")
        
        engine = InferenceEngine()
        regime = engine.detect_market_regime()
        c.drawString(50, 720, f"Market Regime: {regime['regime']} (Confidence: {regime['confidence']}%)")
        
        signals = engine.generate_signals().tail(1).to_dict('records')
        if signals:
            sig = signals[0]['Action']
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, 680, f"AI Recommendation: {sig}")
            
        c.setFont("Helvetica", 12)
        c.drawString(50, 640, "Disclaimer: This report is AI-generated and not financial advice.")
        
        c.save()
        return FileResponse(pdf_path, filename="GoldBeES_Daily_Report.pdf", media_type="application/pdf")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from src.services.agents import ChiefInvestmentAI

@app.get("/agents", response_model=ResponseModel)
def get_multi_agent_decision():
    """
    Returns the Multi-Agent decision matrix.
    """
    try:
        engine = InferenceEngine()
        if engine.df is None or engine.df.empty:
            raise ValueError("No historical data available for agents.")
            
        last_row = engine.df.iloc[-1]
        
        # Add live price to it if possible
        live_price = get_live_price()
        if live_price:
            last_row['Close'] = live_price
            
        chief = ChiefInvestmentAI()
        report = chief.analyze(last_row)
        
        return {"status": "success", "message": "Multi-agent report generated", "data": report}
    except Exception as e:
        logger.error(f"Agents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from src.models.rl_agent import ReinforcementLearningAgent

@app.get("/rl_status", response_model=ResponseModel)
def get_rl_status():
    """
    Returns the current state of the RL (PPO) Trading Agent.
    """
    try:
        engine = InferenceEngine()
        if engine.df is None or engine.df.empty:
            raise ValueError("No historical data available for RL Agent.")
            
        last_row = engine.df.iloc[-1]
        
        live_price = get_live_price()
        if live_price:
            last_row['Close'] = live_price
            
        rl_agent = ReinforcementLearningAgent()
        status = rl_agent.get_status(last_row)
        
        return {"status": "success", "message": "RL status retrieved", "data": status}
    except Exception as e:
        logger.error(f"RL Agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
from typing import List

class Rule(BaseModel):
    indicator: str
    operator: str
    value: float

class StrategyPayload(BaseModel):
    rules: List[Rule]

@app.post("/backtest_strategy", response_model=ResponseModel)
def backtest_custom_strategy(payload: StrategyPayload):
    try:
        from src.services.backtest import BacktestEngine
        engine = BacktestEngine()
        results = engine.evaluate_custom_strategy(payload.rules)
        return {"status": "success", "message": "Backtest complete", "data": results}
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

import asyncio
import random

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        engine = InferenceEngine()
        live_price = get_live_price()
        if live_price is None:
            live_price = float(engine.df[engine.target_col].iloc[-1]) if engine.df is not None else 118.57
            
        current_price = live_price
        
        while True:
            # 1. Fetch real price from Google Finance quote scraper
            new_price = get_live_price("GOLDBEES.NS")
            if new_price is not None:
                current_price = new_price
            
            # 2. Recalculate forecasts based on the current price
            forecast = engine.forecast_horizons(live_price=current_price)
            forecast["Current_Price"] = current_price
            
            payload = {
                "status": "success",
                "current_price": current_price,
                "forecast": forecast
            }
            await websocket.send_json(payload)
            # Sleep 3 seconds (balance between real-time responsiveness and avoiding rate limits)
            await asyncio.sleep(3.0)
    except WebSocketDisconnect:
        logger.info("Live WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

# Trigger reload for websockets package installation


