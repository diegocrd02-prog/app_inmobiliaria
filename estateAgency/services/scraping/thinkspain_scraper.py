import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
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

class ThinkSpainScraper:
    BASE_URL = "https://www.thinkspain.com"

    def __init__(self, delay=2):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-GB,en;q=0.9,es-ES;q=0.8,es;q=0.7",
        })

    def fetch(self, url):
        time.sleep(self.delay)
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        return response.text

    def get_property_links(self, search_url, limit=10):
        html = self.fetch(search_url)
        soup = BeautifulSoup(html, "lxml")
        
        links = []
        # ThinkSpain suele listar los resultados en divs o artículos con enlaces directos
        for a in soup.select("a.property-link, .search-result h2 a, .property-list-item a"):
            href = a.get("href", "")
            if "/property-for-sale/" in href or "/property-to-rent-" in href or "/holiday-rentals/" in href:
                full_url = urljoin(self.BASE_URL, href)
                if full_url not in links:
                    links.append(full_url)
            
            if len(links) >= limit:
                break
        return links

    def parse_detail(self, url, city):
        html = self.fetch(url)
        soup = BeautifulSoup(html, "lxml")
        
        # Obtenemos el texto completo para los extractores por RegEx
        text = soup.get_text(" ", strip=True)

        return ScrapedProperty(
            title=self.extract_title(soup),
            url=url,
            price=self.extract_price(soup, text),
            size_m2=self.extract_size(text),
            rooms=self.extract_rooms(text),
            bathrooms=self.extract_bathrooms(text),
            floor=self.extract_floor(text),
            city=city,
            image_url=self.extract_main_image(soup),
        )

    def extract_title(self, soup):
        h1 = soup.select_one("h1")
        return h1.get_text(strip=True) if h1 else "Property on ThinkSpain"

    def extract_price(self, soup, text):
        # Intentar primero por etiqueta específica
        price_tag = soup.select_one(".price, [itemprop='price']")
        if price_tag:
            price_str = re.sub(r"[^\d]", "", price_tag.get_text())
            return int(price_str) if price_str else None
        
        # Fallback a RegEx
        match = re.search(r"€\s*([\d,.]+)", text) or re.search(r"([\d,.]+)\s*€", text)
        if match:
            return int(match.group(1).replace(".", "").replace(",", ""))
        return None

    def extract_size(self, text):
        match = re.search(r"(\d+)\s*m²", text, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def extract_rooms(self, text):
        # Soporta "3 bedrooms" o "3 hab"
        match = re.search(r"(\d+)\s*(?:bed|hab)", text, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def extract_bathrooms(self, text):
        match = re.search(r"(\d+)\s*(?:bath|bañ)", text, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def extract_floor(self, text):
        match = re.search(r"(\d+)(?:st|nd|rd|th)?\s*floor", text, re.IGNORECASE)
        return match.group(1) if match else None

    def extract_main_image(self, soup):
        og_image = soup.select_one("meta[property='og:image']")
        if og_image:
            return og_image.get("content")
        img = soup.select_one("#property-photos img, .main-photo img")
        return img.get("src") if img else None

    def scrape(self, search_url, city, limit=10):
        links = self.get_property_links(search_url, limit=limit)
        properties = []
        for link in links:
            try:
                properties.append(self.parse_detail(link, city))
            except Exception as e:
                print(f"Error scraping {link}: {e}")
        return properties