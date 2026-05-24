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


class PisosScraper:
    BASE_URL = "https://www.pisos.com"

    def __init__(self, delay=2):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 TFG academic scraper",
            "Accept-Language": "es-ES,es;q=0.9",
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
        for a in soup.select("a[href]"):
            href = a.get("href", "")

            if "/comprar/" in href or "/alquilar/" in href:
                full_url = urljoin(self.BASE_URL, href)

                if full_url not in links:
                    links.append(full_url)

            if len(links) >= limit:
                break

        return links

    def parse_detail(self, url, city):
        html = self.fetch(url)
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)

        title = self.extract_title(soup)
        price = self.extract_price(text)
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
            city=city,
            image_url=image_url,
        )

    def extract_title(self, soup):
        h1 = soup.select_one("h1")
        if h1:
            return h1.get_text(strip=True)

        og_title = soup.select_one("meta[property='og:title']")
        if og_title:
            return og_title.get("content", "").strip()

        return "Vivienda importada desde pisos.com"

    def extract_price(self, text):
        match = re.search(r"([\d\.]+)\s*€", text)
        if not match:
            return None

        return int(match.group(1).replace(".", ""))

    def extract_size(self, text):
        match = re.search(r"(\d+)\s*m²", text)
        if not match:
            match = re.search(r"(\d+)\s*m2", text)

        return int(match.group(1)) if match else None

    def extract_rooms(self, text):
        match = re.search(r"(\d+)\s*hab", text, re.IGNORECASE)
        return int(match.group(1)) if match else None
    
    def extract_bathrooms(self, text):
        match = re.search(r"(\d+)\s*bañ", text, re.IGNORECASE)
        return int(match.group(1)) if match else None
    
    def extract_floor(self, text):
        match = re.search(r"(\d+)[ªº]?\s*planta", text, re.IGNORECASE)
        if match:
            return match.group(1)

        for word in ["bajo", "ático", "entresuelo"]:
            if word in text.lower():
                return word

        return None
    
    def extract_main_image(self, soup):
        og_image = soup.select_one("meta[property='og:image']")
        if og_image and og_image.get("content"):
            return og_image["content"].strip()

        twitter_image = soup.select_one("meta[name='twitter:image']")
        if twitter_image and twitter_image.get("content"):
            return twitter_image["content"].strip()

        img = soup.select_one("img[src]")
        if img and img.get("src"):
            return urljoin(self.BASE_URL, img["src"])

        return None

    def scrape(self, search_url, city, limit=10):
        links = self.get_property_links(search_url, limit=limit)
        properties = []

        for link in links:
            try:
                properties.append(self.parse_detail(link, city))
            except Exception as error:
                print(f"Error leyendo {link}: {error}")

        return properties
