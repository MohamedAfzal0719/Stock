import uvicorn
import os

if __name__ == "__main__":
    # Add project root to path implicitly by running from root
    os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

