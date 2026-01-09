# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import datetime as dt
from typing import Any, Dict, List, Optional, Tuple, Union
import re
import requests

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


def _parse_date(date_str: str) -> dt.date:
    return dt.date.fromisoformat(date_str)


def _get_nested(d: Dict[str, Any], *path: str) -> Any:
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


def _get_overall_rating(prop: Dict[str, Any]) -> Optional[float]:
    val = prop.get("overall_rating")
    if isinstance(val, (int, float)):
        return float(val)
    return None


def _get_hotel_class(prop: Dict[str, Any]) -> Optional[int]:
    """
    SerpApi (Google Hotels) costuma trazer:
      - hotel_class: "5-star hotel" (string)
      - extracted_hotel_class: 5 (int)  ✅ melhor fonte
    :contentReference[oaicite:1]{index=1}
    """
    v = prop.get("extracted_hotel_class")
    if isinstance(v, (int, float)):
        iv = int(round(float(v)))
        if 1 <= iv <= 5:
            return iv

    # fallback: extrair do texto "5-star hotel"
    s = prop.get("hotel_class")
    if isinstance(s, str):
        m = re.search(r"(\d)\s*-\s*star|\b(\d)\s*star", s.lower())
        if m:
            digit = m.group(1) or m.group(2)
            iv = int(digit)
            if 1 <= iv <= 5:
                return iv

    # fallback extra (caso alguma variação apareça)
    for key in ("stars", "star_rating"):
        v2 = prop.get(key)
        if isinstance(v2, (int, float)):
            iv = int(round(float(v2)))
            if 1 <= iv <= 5:
                return iv

    return None



def _get_total_stay(prop: Dict[str, Any], nights: int) -> Optional[float]:
    """
    Preferência:
      1) total_rate.extracted_lowest  (se existir)
      2) rate_per_night.extracted_lowest * nights
    """
    total = _get_nested(prop, "total_rate", "extracted_lowest")
    if isinstance(total, (int, float)):
        return float(total)

    per_night = _get_nested(prop, "rate_per_night", "extracted_lowest")
    if isinstance(per_night, (int, float)):
        return float(per_night) * float(nights)

    return None


def get_top10_best_rated_total_and_stars(
    destino: str,
    data_entrada: str,          # "YYYY-MM-DD"
    dias_estadia: int,          # nº de noites
    min_estrelas: int = 1,
    max_estrelas: int = 5,
    num_hospedes: int = 2,
    *,
    api_key: Optional[str] = None,
    currency: str = "USD",
    hl: str = "en",
    gl: str = "us",
    timeout_sec: int = 60,
    return_debug: bool = False,
) -> Union[Tuple[List[float], List[Optional[int]]], Tuple[List[float], List[Optional[int]], List[dict]]]:
    """
    Retorna:
      - totais_estadia_top10: 10 melhores avaliados (sort_by=8) filtrados por estrelas
      - estrelas_top10: hotel_class de cada um (pode ser None se não vier no JSON)

    Observações:
      - Filtro por estrelas é aplicado em dois lugares:
        (a) no request via hotel_class=min..max (quando possível)
        (b) validação local (se vier hotel_class no retorno)
      - Total da estadia: usa total_rate.extracted_lowest, senão calcula por noite * noites.
    """
    api_key = api_key or os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SERPAPI_API_KEY não encontrada. Carregue o .env ou passe api_key=...")

    if dias_estadia <= 0:
        raise ValueError("dias_estadia deve ser >= 1")

    if min_estrelas < 1 or max_estrelas > 5 or min_estrelas > max_estrelas:
        raise ValueError("Filtro de estrelas inválido. Use 1..5 e min<=max.")

    ci = _parse_date(data_entrada)
    co = ci + dt.timedelta(days=int(dias_estadia))

    params: Dict[str, Any] = {
        "api_key": api_key,
        "engine": "google_hotels",
        "q": destino,
        "check_in_date": ci.isoformat(),
        "check_out_date": co.isoformat(),
        "adults": int(num_hospedes),
        "currency": currency,
        "hl": hl,
        "gl": gl,
        "sort_by": 8,  # Highest rating (melhores avaliados)
        # filtro por estrelas no request (quando respeitado):
        "hotel_class": ",".join(str(x) for x in range(min_estrelas, max_estrelas + 1)),
    }

    r = requests.get(SERPAPI_ENDPOINT, params=params, timeout=timeout_sec)
    r.raise_for_status()
    data = r.json()

    props = data.get("properties") or []

    totals: List[float] = []
    stars_vec: List[Optional[int]] = []
    debug_rows: List[dict] = []

    for prop in props:
        hotel_class = _get_hotel_class(prop)

        # Validação local do filtro (se tivermos o hotel_class)
        if hotel_class is not None:
            if hotel_class < min_estrelas or hotel_class > max_estrelas:
                continue

        total_stay = _get_total_stay(prop, nights=int(dias_estadia))
        if total_stay is None:
            continue

        totals.append(float(total_stay))
        stars_vec.append(hotel_class)

        debug_rows.append({
            "name": prop.get("name"),
            "overall_rating": _get_overall_rating(prop),
            "reviews": prop.get("reviews"),
            "hotel_class": hotel_class,
            "total_stay": float(total_stay),
            "rate_per_night": _get_nested(prop, "rate_per_night", "extracted_lowest"),
            "total_rate": _get_nested(prop, "total_rate", "extracted_lowest"),
        })

        if len(totals) >= 10:
            break

    if return_debug:
        return totals, stars_vec, debug_rows

    return totals, stars_vec
