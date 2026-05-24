from django.core.cache import cache
from django.core.management.base import BaseCommand

import hashlib
import unicodedata
from decimal import Decimal

from estateAgency.models import Source, Location, Property, Listing, ScrapingLog
from estateAgency.services.scraping.fotocasa_scraper import FotocasaScraper


def make_external_id(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def slugify_for_fotocasa(value):
    value = value.lower().strip()
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.replace(" ", "-")
    value = value.replace("_", "-")
    return value


def detect_property_type(title, url=""):
    text = f"{title} {url}".lower()

    if any(word in text for word in [
        "piso",
        "apartamento",
        "ático",
        "atico",
        "estudio",
        "loft",
        "duplex",
        "dúplex",
        "planta-baja",
        "planta baja",
    ]):
        return "flat"

    if any(word in text for word in [
        "casa",
        "chalet",
        "adosado",
        "villa",
        "unifamiliar",
        "pareado",
        "cortijo",
        "masia",
        "masía",
    ]):
        return "house"

    return "unknown"

def build_fotocasa_url(location, operation, rental_type=None, use_capital=False):
    city_slug = slugify_for_fotocasa(location.city)

    if use_capital:
        city_slug = f"{city_slug}-capital"

    if operation == "sale":
        return (
            f"https://www.fotocasa.es/es/comprar/viviendas/"
            f"{city_slug}/todas-las-zonas/l"
        )

    if operation == "rent":
        if rental_type == "long":
            return (
                f"https://www.fotocasa.es/es/alquiler/viviendas/"
                f"{city_slug}/todas-las-zonas/larga-duracion/l"
            )

        if rental_type == "short":
            return (
                f"https://www.fotocasa.es/es/alquiler/viviendas/"
                f"{city_slug}/todas-las-zonas/alquiler-temporal/l"
            )

        raise ValueError("Para alquiler debes pasar rental_type long o short")

    raise ValueError(f"Operación no válida: {operation}")


class Command(BaseCommand):
    help = "Importa viviendas desde Fotocasa evitando duplicidades"

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
        cache.set("fotocasa_scraping_running", True, timeout=60 * 60 * 3)

        try:
            source, _ = Source.objects.get_or_create(
                name="fotocasa.es",
                defaults={"base_url": "https://www.fotocasa.es"}
            )

            scraper = FotocasaScraper(delay=2)

            locations = (
                Location.objects
                .filter(country__iexact="Spain")
                .exclude(city__isnull=True)
                .exclude(city="")
                .order_by("city")
            )

            if options.get("city"):
                locations = locations.filter(city__iexact=options["city"])

            total_imported = 0
            total_updated = 0
            total_skipped = 0

            self.stdout.write(
                self.style.WARNING(
                    f"Iniciando scraping Fotocasa para {locations.count()} localizaciones"
                )
            )

            for location in locations:
                try:
                    url = build_fotocasa_url(
                        location=location,
                        operation=options["operation"],
                        rental_type=options["rental_type"]
                    )

                    self.stdout.write(f"Scrapeando {location.city} -> {url}")

                    scraped_properties = scraper.scrape(
                        search_url=url,
                        city=location.city,
                        limit=options["limit"],
                    )

                    if not scraped_properties:
                        fallback_url = build_fotocasa_url(
                            location=location,
                            operation=options["operation"],
                            rental_type=options["rental_type"],
                            use_capital=True,
                        )

                        self.stdout.write(
                            self.style.WARNING(
                                f"{location.city}: sin resultados, probando fallback -> {fallback_url}"
                            )
                        )

                        scraped_properties = scraper.scrape(
                            search_url=fallback_url,
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
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Omitida sin precio: {item.title} -> {item.url}"
                                )
                            )
                            continue

                        external_id = make_external_id(item.url)

                        prop, created = Property.objects.get_or_create(
                            external_id=external_id,
                            source=source,
                            defaults={
                                "location": location,
                                "url": item.url,
                                "title": item.title,
                                "description": "Vivienda importada desde Fotocasa",
                                "property_type": detect_property_type(
                                    item.title,
                                    item.url
                                ),
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
                            self.stdout.write(
                                self.style.WARNING(
                                    f"{location.city}: corte por "
                                    f"{duplicates_in_row} duplicados seguidos"
                                )
                            )
                            break

                    total_imported += imported
                    total_updated += updated
                    total_skipped += skipped

                    ScrapingLog.objects.create(
                        source=source,
                        status="success",
                        message=(
                            f"Fotocasa {location.city}: "
                            f"{imported} nuevas, "
                            f"{updated} actualizadas, "
                            f"{skipped} omitidas"
                        )
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{location.city}: "
                            f"{imported} nuevas, "
                            f"{updated} actualizadas, "
                            f"{skipped} omitidas"
                        )
                    )

                except Exception as error:
                    ScrapingLog.objects.create(
                        source=source,
                        status="error",
                        message=f"Error Fotocasa en {location.city}: {str(error)}"
                    )

                    self.stdout.write(
                        self.style.ERROR(
                            f"Error scrapeando {location.city}: {error}"
                        )
                    )

                    continue

            self.stdout.write(
                self.style.SUCCESS(
                    f"Scraping Fotocasa terminado. "
                    f"Nuevas: {total_imported}, "
                    f"Actualizadas: {total_updated}, "
                    f"Omitidas: {total_skipped}"
                )
            )

        finally:
            cache.delete("fotocasa_scraping_running")