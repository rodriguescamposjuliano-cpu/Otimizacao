from fastapi import FastAPI
from scraping.rome2rio_playwright import Rome2RioScraper

app = FastAPI(title="Route Optimizer")

@app.get("/routes")
async def get_routes(origin: str, destination: str):
    scraper = Rome2RioScraper(origin, destination)
    routes = await scraper.extract_routes()  # ← AGORA CORRETO

    return {
        "origem": origin,
        "destino": destination,
        "total_rotas": len(routes),
        "rotas_encontradas": routes
    }

@app.get("/route-detail")
async def get_route_detail(link: str):
    scraper = Rome2RioScraper("", "")
    details = await scraper.extract_route_detail(link)
    return {"link": link, "detalhes": details}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
