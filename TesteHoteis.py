from dotenv import load_dotenv
load_dotenv()

from scraping.hotels_serpapi import get_top10_best_rated_total_and_stars

totais, estrelas = get_top10_best_rated_total_and_stars(
    destino="Seattle WA",
    data_entrada="2026-01-15",
    dias_estadia=3,
    min_estrelas=3,
    max_estrelas=5,
    num_hospedes=2
)

print("Totais:", totais)
print("Estrelas:", estrelas)
