import re
import time
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass


@dataclass
class ScrapedProperty:
    title: str
    url: str
    price: int | None
    size_m2: int | None
    rooms: int | None
    bathrooms: int | None
    floor: str | None
    image_url: str | None
    city: str


class FotocasaScraper:
    BASE_URL = "https://www.fotocasa.es"

    def __init__(self, delay=2):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Accept-Language": "es-ES,es;q=0.9",
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
        })

    def fetch(self, url):
        time.sleep(self.delay)
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        return response.text

    def normalize_html(self, html):
        return (
            html
            .replace("\\u002F", "/")
            .replace("\\/", "/")
            .replace("&amp;", "&")
        )
        
    def get_property_links(self, search_url, limit=10):
        for attempt in range(3):
            links = self._get_property_links_once(search_url, limit)

            if links:
                return links

            print(f"Fotocasa 0 links con requests, reintentando {attempt + 1}/3...")
            time.sleep(3 + attempt * 2)

        print("Fotocasa 0 links con requests, probando Playwright...")

        try:
            return self.get_property_links_with_playwright(search_url, limit)
        except Exception as error:
            print(f"Playwright falló: {error}")
            return []

    def _get_property_links_once(self, search_url, limit=10):
        html = self.fetch(search_url)
        normalized_html = self.normalize_html(html)
        soup = BeautifulSoup(normalized_html, "lxml")

        links = []

        def add_link(raw_url):
            if not raw_url:
                return

            raw_url = raw_url.strip().strip('"').strip("'")
            full_url = urljoin(self.BASE_URL, raw_url)
            full_url = full_url.split("?")[0].split("#")[0].rstrip("/")

            if not self.is_property_detail_url(full_url):
                return

            if full_url not in links:
                links.append(full_url)

        # 1. Enlaces normales
        for a in soup.select("a[href]"):
            add_link(a.get("href"))

            if len(links) >= limit:
                return links

        # 2. Enlaces dentro de JSON/scripts
        patterns = [
            r"https://www\.fotocasa\.es/es/(?:comprar|alquiler)/viviendas?/[^\"'<>\s]+?/d",
            r"/es/(?:comprar|alquiler)/viviendas?/[^\"'<>\s]+?/d",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, normalized_html)

            for match in matches:
                add_link(match)

                if len(links) >= limit:
                    return links

        print(f"Fotocasa links detectados: {len(links)}")
        return links
    
    def get_property_links_with_playwright(self, search_url, limit=10):
        from playwright.sync_api import sync_playwright

        links = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=self.session.headers["User-Agent"],
                locale="es-ES",
            )

            page.goto(search_url, wait_until="networkidle", timeout=60000)

            for _ in range(5):
                page.mouse.wheel(0, 2500)
                page.wait_for_timeout(1200)

            hrefs = page.eval_on_selector_all(
                "a[href]",
                "els => els.map(a => a.href)"
            )

            browser.close()

        for href in hrefs:
            full_url = href.split("?")[0].split("#")[0].rstrip("/")

            if self.is_property_detail_url(full_url) and full_url not in links:
                links.append(full_url)

            if len(links) >= limit:
                break

        return links

    def is_property_detail_url(self, url):
        parsed = urlparse(url)

        if "fotocasa.es" not in parsed.netloc:
            return False

        path = parsed.path.lower().rstrip("/")

        if "/es/comprar/" not in path and "/es/alquiler/" not in path:
            return False

        if "/vivienda/" not in path and "/viviendas/" not in path:
            return False

        return path.endswith("/d")
    
    def fetch_with_playwright(self, url):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            page = browser.new_page(
                user_agent=self.session.headers["User-Agent"],
                locale="es-ES",
            )

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            html = page.content()

            browser.close()

        return html

    def parse_detail(self, url, city):
        html = self.fetch(url)
        html = self.normalize_html(html)

        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True) + " " + html

        price = self.extract_price(text)

        # fallback: si requests no saca precio, renderizamos con Playwright
        if price is None:
            try:
                html = self.fetch_with_playwright(url)
                html = self.normalize_html(html)

                soup = BeautifulSoup(html, "lxml")
                text = soup.get_text(" ", strip=True) + " " + html
                price = self.extract_price(text)

            except Exception as error:
                print(f"Playwright detalle falló en {url}: {error}")

        title = self.extract_title(soup)
        size_m2 = self.extract_size(text)
        rooms = self.extract_rooms(text)
        bathrooms = self.extract_bathrooms(text)
        floor = self.extract_floor(text)
        image_url = self.extract_main_image(soup)

        return ScrapedProperty(
            title=title,
            url=url,
            price=price,
            size_m2=size_m2,
            rooms=rooms,
            bathrooms=bathrooms,
            floor=floor,
            image_url=image_url,
            city=city,
        )

    def extract_title(self, soup):
        h1 = soup.select_one("h1")
        if h1:
            title = h1.get_text(" ", strip=True)
            if title:
                return title

        og_title = soup.select_one("meta[property='og:title']")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        twitter_title = soup.select_one("meta[name='twitter:title']")
        if twitter_title and twitter_title.get("content"):
            return twitter_title["content"].strip()

        return "Vivienda importada desde Fotocasa"

    def extract_price(self, text):
        patterns = [
            r"(\d{1,3}(?:\.\d{3})+|\d+)\s*€",
            r'"price"\s*:\s*"?(\d+)"?',
            r'"amount"\s*:\s*"?(\d+)"?',
            r'"value"\s*:\s*"?(\d+)"?',
            r'"priceAmount"\s*:\s*"?(\d+)"?',
            r'"priceValue"\s*:\s*"?(\d+)"?',
            r'price&quot;\s*:\s*"?(\d+)"?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(".", ""))

        return None

    def extract_size(self, text):
        patterns = [
            r"(\d+)\s*m²",
            r"(\d+)\s*m2",
            r"Superficie\s+(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def extract_rooms(self, text):
        patterns = [
            r"(\d+)\s*hab(?:s|itaciones?)?",
            r"Habitaciones?\s+(\d+)",
            r"Dormitorios?\s+(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def extract_bathrooms(self, text):
        patterns = [
            r"(\d+)\s*bañ(?:o|os)?",
            r"Baños?\s+(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def extract_floor(self, text):
        match = re.search(r"(\d+)[ªº]?\s*planta", text, re.IGNORECASE)
        if match:
            return match.group(1)

        match = re.search(r"Planta\s+(\d+)", text, re.IGNORECASE)
        if match:
            return match.group(1)

        lowered = text.lower()

        for word in ["planta baja", "bajo", "ático", "atico", "entresuelo"]:
            if word in lowered:
                return word

        return None

    def is_valid_image(self, url):
        if not url:
            return False

        lowered = url.lower()

        bad_patterns = [
            "logo",
            "placeholder",
            "default",
            "no-image",
            "sprite",
            "icon",
        ]

        return not any(pattern in lowered for pattern in bad_patterns)

    def extract_main_image(self, soup):
        candidates = []

        og_image = soup.select_one("meta[property='og:image']")
        if og_image and og_image.get("content"):
            candidates.append(og_image["content"].strip())

        twitter_image = soup.select_one("meta[name='twitter:image']")
        if twitter_image and twitter_image.get("content"):
            candidates.append(twitter_image["content"].strip())

        for img in soup.select("img[src]"):
            src = img.get("src")
            if src and not src.startswith("data:"):
                candidates.append(urljoin(self.BASE_URL, src))

        for img in soup.select("img[data-src]"):
            src = img.get("data-src")
            if src and not src.startswith("data:"):
                candidates.append(urljoin(self.BASE_URL, src))

        for url in candidates:
            if self.is_valid_image(url):
                return url

        return None

    def scrape(self, search_url, city, limit=10):
        links = self.get_property_links(search_url, limit=limit)
        properties = []

        print(f"Fotocasa links finales: {len(links)}")
        for link in links:
            print(link)

        for link in links:
            try:
                properties.append(self.parse_detail(link, city))
            except Exception as error:
                print(f"Error leyendo {link}: {error}")

        return properties