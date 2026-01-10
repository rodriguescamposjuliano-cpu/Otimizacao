import asyncio
from crawler.crawler_rome2rio import buscar_rotas
from domain.models import Alternativa
from domain.parsers import parse_tempo, parse_preco

class RouteService:

    @staticmethod
    def buscar_alternativas(origem, destino, data):
        rotas_raw = asyncio.run(
            buscar_rotas(origem, destino, data)
        )

        alternativas = []

        for r in rotas_raw:
            for d in r.get("detalhes", []):
                alternativas.append(
                    Alternativa(
                        tempo=parse_tempo(d.get("tempo_total")),
                        preco=parse_preco(d.get("Preco")),
                        conexoes=int(d.get("conexoes", 0)),
                        saida=d.get("saida"),
                        chegada=d.get("chegada"),
                        tempo_total=d.get("tempo_total"),
                        roteiro=d.get("roteiro", []),
                        preco_str=d.get("Preco")
                    )
                )
        return alternativas
