# -*- coding: utf-8 -*-
"""
hotels_serpapi.py
=================
Consulta hotéis via SerpApi (engine=google_hotels) e retorna vetores alinhados
com os 10 melhores avaliados (rating desc, reviews desc, total asc) que atendem
os filtros de entrada.

Saída principal:
- totais_usd: lista[float] com o TOTAL da estadia (preço/noite * dias) em USD
- estrelas:  lista[int|None] com o número de estrelas (hotel_class) quando disponível
- nomes:     lista[str] com o nome dos hotéis

Bônus:
- tenta resolver estrelas via regex em campos textuais
- opcional: fallback via chamada de detalhes usando property_token

Requisitos:
- requests
- variável de ambiente SERPAPI_API_KEY
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from typing import Any

import requests

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


# -----------------------------
# Helpers
# -----------------------------
def _to_float_price(value: Any) -> float | None:
    """Converte diferentes formatos de preço em float (USD) quando possível."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    s = (
        s.replace("US$", "")
        .replace("$", "")
        .replace("R$", "")
        .replace(",", "")
        .strip()
    )
    try:
        return float(s)
    except ValueError:
        return None


def _extract_price_per_night(hotel: dict) -> float | None:
    """Extrai preço/noite em USD (float) de diferentes formatos possíveis do payload."""
    rpn = hotel.get("rate_per_night")
    if isinstance(rpn, dict):
        candidate = (
            rpn.get("extracted_lowest")
            or rpn.get("lowest")
            or rpn.get("extracted")
            or rpn.get("price")
        )
        v = _to_float_price(candidate)
        if v is not None:
            return v

    for key in ("price", "price_per_night", "lowest_rate", "rate"):
        v = _to_float_price(hotel.get(key))
        if v is not None:
            return v

    tr = hotel.get("total_rate")
    if isinstance(tr, dict):
        v = _to_float_price(tr.get("extracted") or tr.get("price") or tr.get("lowest"))
        if v is not None:
            return v

    return None


def _try_parse_star_from_any_text(*texts: Any) -> int | None:
    """
    Tenta extrair estrelas a partir de textos como:
    - "3-star hotel", "4 star hotel", "5-star"
    - "3 estrelas", "4 estrelas"
    - "★★★" (3)
    """
    joined = " | ".join([str(t) for t in texts if t is not None]).strip()
    if not joined:
        return None

    s = joined.lower()

    # Caso: "3-star", "3 star"
    m = re.search(r"\b([1-5])\s*[- ]?\s*star\b", s)
    if m:
        return int(m.group(1))

    # Caso: "3 estrelas"
    m = re.search(r"\b([1-5])\s*estrel", s)
    if m:
        return int(m.group(1))

    # Caso: "★★★"
    stars_count = s.count("★")
    if 1 <= stars_count <= 5:
        return int(stars_count)

    return None


def _parse_star_rating(hotel: dict) -> int | None:
    """
    Normaliza estrelas para int quando possível.
    Estratégia:
      1) tenta chaves numéricas diretas (hotel_class, stars, etc.)
      2) tenta extrair de texto (type, description, etc.)
    """
    # 1) chaves diretas
    for key in ("hotel_class", "stars", "star_rating", "class"):
        if key in hotel and hotel[key] is not None:
            try:
                return int(float(hotel[key]))
            except Exception:
                pass

    # 2) tentar por texto (muito comum vir em "type": "3-star hotel")
    return _try_parse_star_from_any_text(
        hotel.get("type"),
        hotel.get("description"),
        hotel.get("hotel_class"),
        hotel.get("title"),
        hotel.get("name"),
    )


def _fetch_star_from_property_token(property_token: str, api_key: str) -> int | None:
    """
    Busca detalhes do hotel via property_token para tentar obter estrelas.
    (Isso faz uma chamada extra na SerpApi por hotel — usar com parcimônia.)
    """
    if not property_token:
        return None

    params = {
        "engine": "google_hotels",
        "property_token": property_token,
        "api_key": api_key,
    }

    r = requests.get(SERPAPI_ENDPOINT, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    # Dependendo da resposta, os detalhes podem aparecer em chaves diferentes.
    # Tentamos algumas prováveis.
    details = data.get("property") or data.get("hotel") or data.get("about") or data

    if not isinstance(details, dict):
        return None

    # Tenta novamente pelo mesmo parser (chaves + texto)
    return _parse_star_rating(details)


# -----------------------------
# Função principal
# -----------------------------
def get_top10_best_rated_total_stars_names(
    destino: str,
    data_entrada: str,
    dias_estadia: int,
    min_estrelas: int = 1,
    max_estrelas: int = 5,
    num_hospedes: int = 2,
    currency: str = "USD",
    hl: str = "en",
    gl: str = "us",
    api_key: str | None = None,
    fetch_missing_stars: bool = True,   # <- ativa fallback via property_token
) -> tuple[list[float], list[int | None], list[str]]:
    """
    Retorna 3 vetores alinhados (mesmo índice):
    - totais_usd: total da estadia (diárias * preço/noite) em USD
    - estrelas: classificação do hotel (int) quando disponível
    - nomes: nome do hotel

    Critério de "melhores avaliados":
      1) overall_rating desc
      2) reviews desc
      3) total_usd asc

    Filtro de estrelas:
      - Se estrelas vierem (int), aplica [min, max]
      - Se vier None, mantém o hotel (flexível)
        (se você quiser EXCLUIR None, eu te digo onde mudar)
    """
    api_key = api_key or os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SERPAPI_API_KEY não encontrada (env/.env não carregado?)")

    if not destino or not destino.strip():
        raise ValueError("destino é obrigatório")

    if int(dias_estadia) < 1:
        raise ValueError("dias_estadia deve ser >= 1")

    dt_in = datetime.fromisoformat(data_entrada).date()
    dt_out = dt_in + timedelta(days=int(dias_estadia))

    params = {
        "engine": "google_hotels",
        "q": destino,
        "check_in_date": dt_in.isoformat(),
        "check_out_date": dt_out.isoformat(),
        "adults": int(num_hospedes),
        "currency": currency,
        "hl": hl,
        "gl": gl,
        "sort_by": 8,  # tentativa de "best rated", mas reordenamos localmente
        "api_key": api_key,
    }

    r = requests.get(SERPAPI_ENDPOINT, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    properties = data.get("properties") or data.get("hotels") or []
    if not isinstance(properties, list):
        properties = []

    candidatos: list[dict[str, Any]] = []

    for h in properties:
        if not isinstance(h, dict):
            continue

        nome = (h.get("name") or h.get("title") or "").strip()
        if not nome:
            continue

        estrelas = _parse_star_rating(h)

        # rating e reviews
        overall = h.get("overall_rating") or h.get("rating") or 0
        reviews = h.get("reviews") or h.get("reviews_count") or 0

        try:
            overall_f = float(overall)
        except Exception:
            overall_f = 0.0

        try:
            reviews_i = int(reviews)
        except Exception:
            reviews_i = 0

        price_night = _extract_price_per_night(h)
        if price_night is None:
            continue

        total = float(price_night) * int(dias_estadia)

        candidatos.append({
            "name": nome,
            "stars": estrelas,
            "total": total,
            "overall": overall_f,
            "reviews": reviews_i,
            "property_token": h.get("property_token") or h.get("propertyToken") or None,
            "raw": h,
        })

    # Ordena pelos critérios definidos
    candidatos.sort(key=lambda x: (-x["overall"], -x["reviews"], x["total"]))
    top10 = candidatos[:10]

    # Fallback: tentar buscar estrelas via property_token para os que ficaram None
    if fetch_missing_stars:
        for item in top10:
            if item["stars"] is None and item.get("property_token"):
                try:
                    item["stars"] = _fetch_star_from_property_token(item["property_token"], api_key)
                except Exception:
                    # se falhar, mantém None
                    pass

    # Agora aplica filtro de estrelas (somente quando existe estrela)
    filtrados = []
    for item in top10:
        s = item["stars"]
        if s is not None:
            if s < int(min_estrelas) or s > int(max_estrelas):
                continue
        filtrados.append(item)

    # Se após filtrar ficou menos de 10, tenta completar com próximos da lista
    if len(filtrados) < 10:
        for item in candidatos[10:]:
            if len(filtrados) >= 10:
                break
            s = item["stars"]
            if s is not None:
                if s < int(min_estrelas) or s > int(max_estrelas):
                    continue
            filtrados.append(item)

        # e tenta preencher estrelas via token também nos novos
        if fetch_missing_stars:
            for item in filtrados:
                if item["stars"] is None and item.get("property_token"):
                    try:
                        item["stars"] = _fetch_star_from_property_token(item["property_token"], api_key)
                    except Exception:
                        pass

    top_final = filtrados[:10]

    totais_usd = [float(x["total"]) for x in top_final]
    estrelas_out = [x["stars"] for x in top_final]
    nomes_out = [x["name"] for x in top_final]

    return totais_usd, estrelas_out, nomes_out


# ---------------------------------------------------------
# Compatibilidade com imports antigos
# ---------------------------------------------------------
# Se você tinha código chamando get_top10_best_rated_total_and_stars,
# deixamos um alias para não quebrar:
def get_top10_best_rated_total_and_stars(*args, **kwargs):
    totais, estrelas, _nomes = get_top10_best_rated_total_stars_names(*args, **kwargs)
    return totais, estrelas


# Função nova (nome preferido)
get_top10_best_rated_total_stars_names_v1 = get_top10_best_rated_total_stars_names


if __name__ == "__main__":
    totals, stars, names = get_top10_best_rated_total_stars_names(
        destino="Seattle WA",
        data_entrada="2026-01-15",
        dias_estadia=3,
        min_estrelas=3,
        max_estrelas=5,
        num_hospedes=2,
        fetch_missing_stars=True,
    )
    print("Totais:", totals)
    print("Estrelas:", stars)
    print("Nomes:", names)
