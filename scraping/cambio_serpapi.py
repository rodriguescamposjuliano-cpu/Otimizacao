import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

def get_cambio_usd_brl_serpapi(api_key: str | None = None) -> float:
    api_key = api_key or os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SERPAPI_API_KEY não encontrada")

    params = {
        "engine": "google_finance",
        "q": "USD-BRL",
        "api_key": api_key,
    }

    r = requests.get(SERPAPI_ENDPOINT, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    try:
        return float(data["summary"]["price"])
    except (KeyError, TypeError, ValueError):
        raise RuntimeError("Não foi possível extrair o câmbio USD/BRL")
