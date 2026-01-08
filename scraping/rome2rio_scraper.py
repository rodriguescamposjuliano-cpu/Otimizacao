from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

class Rome2RioScraper:
    def __init__(self, origin, destination):
        self.url = f"https://www.rome2rio.com/map/{origin}/{destination}"

    def extract_routes(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        driver.get(self.url)

        wait = WebDriverWait(driver, 30)

        # Espera o container principal aparecer
        container = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.bg-surface")
            )
        )

        time.sleep(2)  # garante carregamento completo

        route_cards = container.find_elements(By.CSS_SELECTOR, "a")

        routes = []

        for card in route_cards:
            try:
                routes.append({
                    "titulo": card.text.strip(),
                    "link": card.get_attribute("href")
                })
            except:
                continue

        driver.quit()
        return routes
