import json

main_py_addition = '''
class PortfolioPayload(BaseModel):
    invested_amount: float
    units_held: float

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "portfolios.json")

def load_portfolios():
    if not os.path.exists(PORTFOLIO_FILE):
        return {}
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_portfolios(data):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.get("/portfolio/{user_id}", response_model=ResponseModel)
def get_portfolio(user_id: str):
    try:
        portfolios = load_portfolios()
        user_portfolio = portfolios.get(user_id, {"invested_amount": 0, "units_held": 0})
        return {"status": "success", "message": "Portfolio retrieved", "data": user_portfolio}
    except Exception as e:
        logger.error(f"Portfolio get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/{user_id}", response_model=ResponseModel)
def update_portfolio(user_id: str, payload: PortfolioPayload):
    try:
        portfolios = load_portfolios()
        portfolios[user_id] = {
            "invested_amount": payload.invested_amount,
            "units_held": payload.units_held
        }
        save_portfolios(portfolios)
        return {"status": "success", "message": "Portfolio updated", "data": portfolios[user_id]}
    except Exception as e:
        logger.error(f"Portfolio update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
'''

with open('d:/Goldbees/api/main.py', 'a', encoding='utf-8') as f:
    f.write(main_py_addition)
