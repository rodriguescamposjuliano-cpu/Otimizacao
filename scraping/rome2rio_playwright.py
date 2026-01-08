from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import asyncio
from playwright.async_api import Page

class Rome2RioScraper:

    def __init__(self, origin: str, destination: str):
        self.origin = origin
        self.destination = destination

    async def extract_routes(self):
        url = f"https://www.rome2rio.com/map/{self.origin}/{self.destination}"
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
                link = await card.get_attribute("href")
                title = await card.locator("h1").inner_text()
                duration = await card.locator("time").inner_text()
                price = await card.locator("span").inner_text()
                routes.append({
                    "titulo": title.strip(),
                    "duracao": duration.strip(),
                    "preco": price.strip(),
                    "link": f"https://www.rome2rio.com{link}"
                })

            await browser.close()
        return routes

    async def extract_route_detail(self, route_url: str):
        async with async_playwright() as p:
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
            await page.goto(route_url, wait_until="domcontentloaded", timeout=60000)

            locator = page.locator("div.rounded-xl")
            count = await locator.count()

            

            # ⏳ Espera adaptativa pelos schedules
            schedules_locator = page.locator('li[data-testid="scheduleCell"]')
            timeout_total = 25
            end_time = asyncio.get_event_loop().time() + timeout_total

            while True:
                if await schedules_locator.count() > 0:
                    break
                if asyncio.get_event_loop().time() > end_time:
                    print("Nenhum schedule encontrado dentro do tempo limite")
                    await browser.close()
                    return []
                await page.evaluate("window.scrollBy(0, 400)")
                await asyncio.sleep(0.5)

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
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(0.7)

            resultados = []

            for i in range(await schedules_locator.count()):
                leg = schedules_locator.nth(i)

                # Horário de saída e chegada
                times = leg.locator("time")
                departure = await times.nth(0).inner_text() if await times.count() > 0 else ""
                arrival = await times.nth(1).inner_text() if await times.count() > 1 else ""

                # Tenta pegar o dia da chegada (se existir)
                arrival_day_p = await leg.locator("span[id^='schedule-cell-times'] p").nth(0).inner_text() if await leg.locator("span[id^='schedule-cell-times'] p").count() > 0 else ""
                if arrival_day_p:
                    arrival += " " + arrival_day_p.strip()
                    
                # Duração e conexões
                details_button = leg.locator('button[aria-label="View details"]')
                duration_changes_text = await details_button.inner_text() if await details_button.count() else ""
                if "•" in duration_changes_text:
                    duration_text, changes_text = duration_changes_text.split("•")
                else:
                    duration_text, changes_text = duration_changes_text, "0"

                # Companhia e tipo de transporte
                airline_imgs = leg.locator('button[aria-label] img')
                airline = ""
                transport_type = ""
                for j in range(await airline_imgs.count()):
                    alt = await airline_imgs.nth(j).get_attribute("alt")
                    if alt:
                        airline = alt
                        transport_type = alt
                        break

                # Preço
                price_btns = leg.locator('button:has-text("R$")')
                price = ""
                for k in range(await price_btns.count()):
                    try:
                        price = await price_btns.nth(k).inner_text()
                        if price:
                            break
                    except:
                        continue

                # Link de reserva
                link_tag = leg.locator('a[href*="r/"]')
                link = await link_tag.get_attribute("href") if await link_tag.count() else ""

                roteiro = []

                if await details_button.count():
                    try:
                        await details_button.click()
                        # ⏳ Espera adaptativa pelo container do roteiro
                        timeout = 10
                        end_time = asyncio.get_event_loop().time() + timeout
                        container_visible = False

                        while asyncio.get_event_loop().time() < end_time:
                            steps_locator = leg.locator('div[data-testid="timeline-line"] >> xpath=..')
                            if await steps_locator.count() > 0:
                                container_visible = True
                                break
                            await asyncio.sleep(0.5)

                        if container_visible:
                            for s in range(await steps_locator.count()):
                                step = steps_locator.nth(s)

                                # 🔹 Debug: imprime todo o texto do step
                                step_text = ""
                                try:
                                    step_text = await step.inner_text()
                                    print(f"Step {s} completo:\n{step_text}\n{'-'*30}")
                                except Exception as e:
                                    print(f"Erro lendo step {s}: {e}")
                                
                                roteiro.append({"etapa": step_text, "ordem": s})
                        else:
                            print(f"Nenhum roteiro encontrado no card {i}")

                    except Exception as e:
                        print(f"Erro ao extrair roteiro do card {i}: {e}")


                resultados.append({
                    "saida": departure.strip(),
                    "chegada": arrival.strip(),
                    "duracao": duration_text.strip(),
                    "conexoes": changes_text.strip(),
                    "companhia": airline.strip(),
                    "tipo_transporte": transport_type.strip(),
                    "preco": price.strip(),
                    "link_reserva": f"https://www.rome2rio.com{link}" if link else "",
                    "roteiro": roteiro
                })

            await browser.close()
            return resultados


    async def extract_route_detail(self, route_url: str):
        """
        Função principal que coleta todos os roteiros de uma rota.
        - Para cada card em div.rounded-xl, abre em nova aba e coleta detalhes.
        - Se não houver cards, coleta detalhes direto da página.
        """
        async with async_playwright() as p:
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
            await page.goto(route_url, wait_until="domcontentloaded", timeout=60000)

            # Tenta localizar os cards
            try:
                await page.wait_for_selector("div.rounded-xl", timeout=15000)
            except:
                print("[INFO] Nenhum card rounded-xl apareceu")

            await page.wait_for_timeout(2000)

            # Localiza todos os links dentro dos cards
            link_locator = page.locator('div.rounded-xl a[href*="/map/"]')
            count = await link_locator.count()
            print(f"[INFO] {count} links de roteiro encontrados")

            resultados = []

            if count > 0:
                for i in range(count):
                    try:
                        # Pega o href "fresh" dentro do loop
                        link_tag = page.locator('div.rounded-xl a[href*="/map/"]').nth(i)
                        href = await link_tag.get_attribute("href")
                        print(f"[INFO] Card {i} - link encontrado: {href}")

                        if not href:
                            print(f"[WARN] Card {i} - href vazio, pulando")
                            continue

                        # Abre o link em nova aba
                        new_page = await context.new_page()
                        full_link = f"https://www.rome2rio.com{href}"
                        await new_page.goto(full_link, wait_until="domcontentloaded")
                        await new_page.wait_for_timeout(2000)

                        # Chama função que coleta detalhes passando a nova página
                        detalhes = await self.extract_route_detail_from_link(page=new_page)
                        resultados.extend(detalhes)

                        await new_page.close()

                    except Exception as e:
                        print(f"[ERRO] Card {i} - falha ao processar link {href}: {e}")

            else:
                # Não existem cards, coleta detalhes direto da página original
                print("[INFO] Nenhum card encontrado, coletando detalhes direto da página...")
                detalhes = await self.extract_route_detail_from_link(page=page)
                resultados.extend(detalhes)

            await browser.close()
            return resultados



    async def extract_route_detail_from_link(self, page: Page):
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

                # Duração e conexões
                details_button = leg.locator('button[aria-label="View details"]')
                roteiro = []

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
                    "roteiro": roteiro
                })

            except Exception as e:
                print(f"[ERRO] Falha no schedule {i}: {e}")
                continue

        return resultados
