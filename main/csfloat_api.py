import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from utils.logging_config import setup_logging

logger = setup_logging()

load_dotenv()
CSFLOAT_API_KEY = os.getenv("CSFLOAT_API_KEY")
CSFLOAT_API_URL = os.getenv("CSFLOAT_API_URL", "https://csfloat.com/api/v1")

def get_request_headers() -> dict:
    if not CSFLOAT_API_KEY:
        raise RuntimeError("CSFLOAT_API_KEY is not set in environment")
    return {"Authorization": CSFLOAT_API_KEY}

def get_listing_params(limit: int = 50, 
                       sort_by: str = "most_recent", 
                       min_price: int = 5000, 
                       type: str = "buy_now") -> dict:
    return f'/listings?limit={limit}&sort_by={sort_by}&min_price={min_price}&type={type}'

def make_listing_request() -> pd.DataFrame | None:
    try:
        response = requests.get(CSFLOAT_API_URL, headers=get_request_headers(), params=(get_listing_params()))
        response.raise_for_status()
        logger.info(f"Successfully retrieved listing data at {datetime.now()}")
        data = response.json().get("data", [])
        return pd.DataFrame(data)
    except requests.RequestException as e:
        logger.error(f"An error occurred in making request: {e}")
        raise
