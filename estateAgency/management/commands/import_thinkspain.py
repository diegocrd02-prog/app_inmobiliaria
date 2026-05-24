from django.core.cache import cache
import unicodedata
from decimal import Decimal
import hashlib

from django.core.management.base import BaseCommand
from estateAgency.models import Source, Location, Property, Listing, ScrapingLog
# Asegúrate de haber guardado el scraper anterior como thinkspain_scraper.py
from estateAgency.services.scraping.thinkspain_scraper import ThinkSpainScraper

def make_external_id(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest()

def slugify_for_thinkspain(value):
    """ThinkSpain usa guiones simples y minúsculas"""
    value = value.lower().strip()
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.replace(" ", "-")
    return value

def detect_property_type(title):
    title = title.lower()
    # Mapeo extendido para términos en inglés (ThinkSpain) y español
    if any(word in title for word in ["piso", "apartment", "flat", "apartamento", "ático", "penthouse", "studio", "estudio", "loft", "duplex"]):
        return "flat"
    if any(word in title for word in ["casa", "house", "chalet", "villa", "detached", "adosado", "townhouse", "bungalow", "cortijo"]):
        return "house"
    return "unknown"

def build_thinkspain_url(location, operation, rentType=None):
    city_slug = slugify_for_thinkspain(location.city)

    if operation == "sale":
        return f"https://www.thinkspain.com/property-for-sale/{city_slug}"

    if operation == "rent":
        if rentType == "short":
            return f"https://www.thinkspain.com/holiday-rentals/{city_slug}"
        if rentType == "long":
            return f"https://www.thinkspain.com/property-to-rent-long-term/{city_slug}"
        else:
            raise ValueError(f"Tipo de alquiler no válido: {rentType}")

    raise ValueError(f"Operación no válida: {operation}")


class Command(BaseCommand):
    help = "Importa viviendas desde thinkspain.com evitando duplicidades"

    def add_arguments(self, parser):
        parser.add_argument(
            "--operation",
            choices=["sale", "rent"],
            default="sale"
        )
        parser.add_argument(
            "--rental-type",
            choices=["short", "long"],
            default=None
        )
        parser.add_argument("--limit", type=int, default=15)
        parser.add_argument(
            "--city",
            required=False,
            help="Opcional. Scrapea solo una ciudad concreta"
        )
        parser.add_argument(
            "--max-duplicates",
            type=int,
            default=5,
            help="Corta el scraping de una ciudad tras X duplicados seguidos"
        )

    def handle(self, *args, **options):
        # Evitar ejecuciones simultáneas
        cache.set("thinkspain_scraping_running", True, timeout=60 * 60 * 3)
        
        try:
            source, _ = Source.objects.get_or_create(
                name="thinkspain.com",
                defaults={"base_url": "https://www.thinkspain.com"}
            )

            scraper = ThinkSpainScraper(delay=2)

            locations = (
                Location.objects
                .filter(country__iexact="Spain")
                .exclude(city__isnull=True)
                .exclude(city="")
            )

            if options.get("city"):
                locations = locations.filter(city__iexact=options["city"])

            total_imported = 0
            total_updated = 0
            total_skipped = 0

            self.stdout.write(self.style.WARNING(f"Iniciando scraping ThinkSpain para {locations.count()} localizaciones"))

            for location in locations:
                try:
                    url = build_thinkspain_url(
                        location=location,
                        operation=options["operation"],
                        rentType=options["rental_type"]
                    )
                except ValueError as e:
                    self.stdout.write(self.style.ERROR(str(e)))
                    continue

                self.stdout.write(f"Scrapeando {location.city} -> {url}")

                try:
                    scraped_properties = scraper.scrape(
                        search_url=url,
                        city=location.city,
                        limit=options["limit"],
                    )

                    imported = 0
                    updated = 0
                    skipped = 0
                    duplicates_in_row = 0

                    for item in scraped_properties:
                        if not item.price:
                            skipped += 1
                            continue

                        # Generamos ID único basado en la URL de ThinkSpain
                        external_id = make_external_id(item.url)

                        prop, created = Property.objects.get_or_create(
                            external_id=external_id,
                            source=source,
                            defaults={
                                "location": location,
                                "url": item.url,
                                "title": item.title,
                                "description": "Vivienda importada desde thinkspain.com",
                                "property_type": detect_property_type(item.title),
                                "operation_type": options["operation"],
                                "rental_type": options["rental_type"],
                                "rooms": item.rooms,
                                "bathrooms": item.bathrooms,
                                "floor": item.floor,
                                "size_m2": item.size_m2,
                                "image_url": item.image_url,
                            }
                        )

                        price = Decimal(str(item.price))
                        price_per_m2 = None
                        if item.size_m2:
                            price_per_m2 = price / Decimal(str(item.size_m2))

                        if created:
                            Listing.objects.create(
                                property=prop,
                                price=price,
                                price_per_m2=price_per_m2,
                                is_active=True,
                            )
                            imported += 1
                            duplicates_in_row = 0
                            continue

                        # Si ya existía, comprobamos si el precio ha cambiado
                        duplicates_in_row += 1
                        latest_listing = (
                            Listing.objects
                            .filter(property=prop, is_active=True)
                            .order_by("-id")
                            .first()
                        )

                        if latest_listing and latest_listing.price == price:
                            skipped += 1
                        else:
                            if latest_listing:
                                latest_listing.is_active = False
                                latest_listing.save(update_fields=["is_active"])

                            Listing.objects.create(
                                property=prop,
                                price=price,
                                price_per_m2=price_per_m2,
                                is_active=True,
                            )
                            updated += 1

                        if duplicates_in_row >= options["max_duplicates"]:
                            self.stdout.write(self.style.WARNING(f"{location.city}: corte por duplicados"))
                            break

                    total_imported += imported
                    total_updated += updated
                    total_skipped += skipped

                    ScrapingLog.objects.create(
                        source=source,
                        status="success",
                        message=f"{location.city}: {imported} nuevas, {updated} actualizadas"
                    )
                    self.stdout.write(self.style.SUCCESS(f"Finalizado. Nuevas: {total_imported}, Actualizadas: {total_updated}"))
                except Exception as error:
                    ScrapingLog.objects.create(
                        source=source,
                        status="error",
                        message=f"Error en {location.city}: {str(error)}"
                    )
                    self.stdout.write(self.style.ERROR(f"Error en {location.city}: {error}"))

            self.stdout.write(self.style.SUCCESS(f"Finalizado. Nuevas: {total_imported}, Actualizadas: {total_updated}"))

        finally:
            cache.delete("thinkspain_scraping_running")