from dotenv import load_dotenv
load_dotenv()

from crawler.hotels_serpapi import get_top10_best_rated_total_stars_names

totais, estrelas, nomes = get_top10_best_rated_total_stars_names(
    destino="Rio Grande do Sul",
    data_entrada="2026-01-15",
    dias_estadia=3,
    min_estrelas=3,
    max_estrelas=5,
    num_hospedes=2
)

print("Totais:", totais)
print("Estrelas:", estrelas)
print("Nome dos hotéis:", nomes)
