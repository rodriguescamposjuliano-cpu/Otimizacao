from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import asyncio
from playwright.async_api import Page

async def buscar_rotas(origem: str, destino: str):
    url = f"https://www.rome2rio.com/map/{origem}/{destino}"
    routes = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # ⏳ Espera o React hidratar cards principais
        try:
            await page.wait_for_selector(
                'div[data-testid^="trip-search-result"]',
                timeout=15000  # ✅ curto, mas suficiente
            )
        except PlaywrightTimeout:
            print("Nenhum resultado carregado.")
            await browser.close()
            return routes

        # ✅ Clica nos "Show more" se existirem
        while True:
            buttons = page.locator("button")
            count = await buttons.count()
            found = False
            for i in range(count):
                btn = buttons.nth(i)
                if not await btn.is_visible():
                    continue
                text = (await btn.inner_text()).lower()
                if "show" in text and "more" in text:
                    await btn.click()
                    await page.wait_for_timeout(1500)
                    found = True
                    break
            if not found:
                break

        # 🔽 Scroll suave para lazy-load
        previous_count = 0
        while True:
            cards = page.locator('div[data-testid^="trip-search-result"] a[href*="#r/"]')
            current_count = await cards.count()
            if current_count == previous_count:
                break
            previous_count = current_count
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await page.wait_for_timeout(500)

        # 🔍 Extrai os dados
        count = await cards.count()
        for i in range(count):
            card = cards.nth(i)

            # Ícones de transporte
            icons = card.locator("svg")
            icon_count = await icons.count()

            transport_types = []
            for j in range(icon_count):
                svg = icons.nth(j)
                class_attr = await svg.get_attribute("class")
                if class_attr:
                    if "plane" in class_attr:
                        transport_types.append("plane")
                    elif "bus" in class_attr:
                        transport_types.append("bus")
                    elif "train" in class_attr:
                        transport_types.append("train")
                    elif "car" in class_attr:
                        transport_types.append("car")

            # 🔎 Filtro: somente voo
            if not (len(transport_types) == 1 and transport_types[0] == "plane"):
                continue  # ignora rota multimodal

            link = await card.get_attribute("href")
            title = await card.locator("h1").inner_text()
            duration = await card.locator("time").inner_text()
            price = await card.locator("span").inner_text()

            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--disable-dev-shm-usage",
                    "--window-size=1920,1080"
                ]
            )

            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                java_script_enabled=True
            )

            page = await context.new_page()
            await page.goto(f"https://www.rome2rio.com{link}", wait_until="domcontentloaded", timeout=60000)

            detalhes = await extract_route_detail_from_link(page=page)

            routes.append({
                "titulo": title.strip(),
                "duracao": duration.strip(),
                "Preço entre": price,
                "modal": "Voo",
                "link": f"https://www.rome2rio.com{link}",
                "detalhes": detalhes
            })

        await browser.close()
    return routes

async def extract_route_detail_from_link(page: Page):
        """
        Coleta todos os schedules e roteiro de um card já aberto.
        """
        resultados = []

        try:
            await page.wait_for_selector('li[data-testid="scheduleCell"]', timeout=15000)
            
            schedules_locator = page.locator('li[data-testid="scheduleCell"]')
        except Exception as e:
            print(f"[ERRO] Nenhum schedule encontrado: {e}")
            return resultados


        timeout_total = 25
        end_time = asyncio.get_event_loop().time() + timeout_total

        
        # 🔽 Scroll adaptativo até carregar todos os schedules
        previous_count = 0
        stable_iterations = 0
        while stable_iterations < 3:
            current_count = await schedules_locator.count()
            if current_count == previous_count:
                stable_iterations += 1
            else:
                stable_iterations = 0
            previous_count = current_count
            await page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(0.7)




        schedule_count = await schedules_locator.count()
        print(f"[INFO] {schedule_count} schedules encontrados")

        for i in range(schedule_count):
            try:
                leg = schedules_locator.nth(i)

                # Horário de saída e chegada
                times = leg.locator("time")
                departure = await times.nth(0).inner_text() if await times.count() > 0 else ""
                arrival = await times.nth(1).inner_text() if await times.count() > 1 else ""

                # Tenta pegar dia da chegada
                arrival_day_p = await leg.locator("span[id^='schedule-cell-times'] p").nth(0).inner_text() \
                    if await leg.locator("span[id^='schedule-cell-times'] p").count() > 0 else ""
                if arrival_day_p:
                    arrival += " " + arrival_day_p.strip()

                # 💰 Valor da passagem
                price = ""

                price_button = leg.locator(
                    "button:has-text('R$'), button:has-text('$'), button:has-text('€')"
                )

                if await price_button.count() > 0:
                    raw_price = await price_button.first.inner_text()
                    # remove texto auxiliar e quebra de linha
                    price = raw_price.replace("Book your ticket", "").strip()

                # Duração e conexões
                details_button = leg.locator('button[aria-label="View details"]')
                roteiro = []

                # 🔹 Tempo total e número de conexões
                duration = ""
                connections = 0

                try:
                    span_text = await leg.locator('span:has(time.whitespace-nowrap)').inner_text()
                    # span_text será algo como "25h 6min • 2 changes"
                    parts = span_text.split("•")
                    duration = parts[0].strip()  # "25h 6min"
                    if len(parts) > 1:
                        connections_str = parts[1].strip()
                        # extrai apenas número
                        import re
                        match = re.search(r'(\d+)', connections_str)
                        if match:
                            connections = int(match.group(1))
                except Exception:
                    pass


                if await details_button.count():
                    await details_button.click()
                    steps_locator = leg.locator('div[data-testid="timeline-line"] >> xpath=..')

                    # Espera adaptativa pelo container do roteiro
                    timeout = 10
                    end_time = asyncio.get_event_loop().time() + timeout
                    while asyncio.get_event_loop().time() < end_time:
                        if await steps_locator.count() > 0:
                            break
                        await asyncio.sleep(0.5)

                    for s in range(await steps_locator.count()):
                        step = steps_locator.nth(s)
                        step_text = await step.inner_text()
                        roteiro.append({"etapa": step_text, "ordem": s})

                resultados.append({
                    "saida": departure.strip(),
                    "chegada": arrival.strip(),
                    "tempo_total": duration,
                    "conexoes": connections,
                    "roteiro": roteiro,
                    "Preco": price
                })

            except Exception as e:
                print(f"[ERRO] Falha no schedule {i}: {e}")
                continue

        return resultados
