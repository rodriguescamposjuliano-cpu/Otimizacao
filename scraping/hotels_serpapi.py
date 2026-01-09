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

Requisitos:
- requests
- variável de ambiente SERPAPI_API_KEY (ex.: via .env carregado no app)
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

import requests

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


def _to_float_price(value: Any) -> float | None:
    """Converte diferentes formatos de preço em float (USD) quando possível."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    # exemplos: "$170", "US$ 170", "170", "170.50"
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


def _parse_star_rating(hotel: dict) -> int | None:
    """
    Normaliza estrelas para int quando possível.
    Em geral, SerpApi google_hotels usa 'hotel_class' (3,4,5).
    """
    for key in ("hotel_class", "stars", "star_rating", "class"):
        if key in hotel and hotel[key] is not None:
            try:
                return int(float(hotel[key]))
            except Exception:
                pass
    return None


def _extract_price_per_night(hotel: dict) -> float | None:
    """
    Extrai preço/noite em USD (float) de diferentes formatos possíveis do payload.
    """
    # Formato comum: rate_per_night = {"lowest": "$170", "extracted_lowest": 170, ...}
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

    # Outros formatos possíveis
    for key in ("price", "price_per_night", "lowest_rate", "rate"):
        v = _to_float_price(hotel.get(key))
        if v is not None:
            return v

    # Alguns payloads podem ter preço dentro de "total_rate" ou semelhantes
    tr = hotel.get("total_rate")
    if isinstance(tr, dict):
        v = _to_float_price(tr.get("extracted") or tr.get("price") or tr.get("lowest"))
        if v is not None:
            return v

    return None


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
) -> tuple[list[float], list[int | None], list[str]]:
    """
    Retorna 3 vetores alinhados (mesmo índice):
    - totais_usd: total da estadia (diárias * preço/noite) em USD
    - estrelas: classificação do hotel (int) quando disponível
    - nomes: nome do hotel

    Critério de "melhores avaliados":
      1) overall_rating desc
      2) reviews desc
      3) total_usd asc (desempate para escolher o mais barato entre equivalentes)

    Observação sobre filtro de estrelas:
      - Se o payload trouxer estrelas (hotel_class), aplica filtro [min, max]
      - Se NÃO trouxer estrelas (None), mantém o hotel (não exclui)
        (se você quiser excluir, troque a lógica no trecho do filtro)
    """
    api_key = api_key or os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SERPAPI_API_KEY não encontrada (env/.env não carregado?)")

    if not destino or not destino.strip():
        raise ValueError("destino é obrigatório")

    if int(dias_estadia) < 1:
        raise ValueError("dias_estadia deve ser >= 1")

    # check-out = entrada + dias
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
        # sort_by=8 costuma retornar "highest rating" em muitos cenários.
        # Mesmo assim, reordenamos localmente para garantir o critério.
        "sort_by": 8,
        "api_key": api_key,
    }

    r = requests.get(SERPAPI_ENDPOINT, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    # A SerpApi geralmente retorna em data["properties"]
    # (fallbacks por segurança)
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

        # Filtro de estrelas:
        # se veio estrela, filtra; se não veio (None), mantém (flexível)
        if estrelas is not None:
            if estrelas < int(min_estrelas) or estrelas > int(max_estrelas):
                continue

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
        })

    # Ordena pelos critérios definidos
    candidatos.sort(key=lambda x: (-x["overall"], -x["reviews"], x["total"]))

    top10 = candidatos[:10]

    totais_usd = [float(x["total"]) for x in top10]
    estrelas_out = [x["stars"] for x in top10]
    nomes_out = [x["name"] for x in top10]

    return totais_usd, estrelas_out, nomes_out


# Alias para compatibilidade (se você já importava a função antiga por engano)
# Você pode remover se não precisar.
get_top10_best_rated_total_stars_names_v1 = get_top10_best_rated_total_stars_names


if __name__ == "__main__":
    # Teste rápido manual (requer SERPAPI_API_KEY no ambiente)
    totals, stars, names = get_top10_best_rated_total_stars_names(
        destino="Seattle WA",
        data_entrada="2026-01-15",
        dias_estadia=3,
        min_estrelas=3,
        max_estrelas=5,
        num_hospedes=2,
    )
    print("Totais:", totals)
    print("Estrelas:", stars)
    print("Nomes:", names)
