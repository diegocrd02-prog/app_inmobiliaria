from django.core.management.base import BaseCommand
from requests import options
from estateAgency.models import (
    Source, Location, Property, Listing, ScrapingLog
)
import random
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed database with realistic test data'
    
    def add_arguments(self, parser):
        parser.add_argument("--seedProperties", required=False, default=False)

    def handle(self, *args, **options):
        Property.objects.all().delete()
        Location.objects.all().delete()
        Listing.objects.all().delete()
        Source.objects.all().delete()
        ScrapingLog.objects.all().delete()
        self.stdout.write("Seeding database...")

        source, _ = Source.objects.get_or_create(
            name="pisos.com",
            defaults={"base_url": "https://www.pisos.com"}
        )

        cityGroup = {
            'Spain': [
                ("Madrid", "Madrid", 40.4168, -3.7038),
                ("Barcelona", "Barcelona", 41.3874, 2.1686),
                ("Valencia", "Valencia", 39.4699, -0.3763),
                ("Sevilla", "Andalucia", 37.3891, -5.9845),
                ("Bilbao", "Pais Vasco", 43.2630, -2.9350),
            ]
        }
        """("Zaragoza", "Aragon", 41.6488, -0.8891),
                ("Badajoz", "Extremadura", 38.8794, -6.9707),
                
                ("Granada", "Andalucia", 37.1773, -3.5986),
                ("Salamanca", "Castilla y Leon", 40.9701, -5.6635),
                ("Alicante", "Valencia", 38.3452, -0.4810),"""
        locations = []
        for country, cities in cityGroup.items():
            for city, province, lat, lon in cities:
                loc, _ = Location.objects.get_or_create(
                    country=country,
                    city=city,
                    province=province,
                    defaults={
                        "latitude": lat,
                        "longitude": lon
                    }
                )
                locations.append(loc)
        seedProperties = options["seedProperties"]
        if seedProperties:
            properties = []
            operationTypes = []
            for i in range(120):
                location = random.choice(locations)
                
                operation_type = random.choice(["sale", "rent"])
                operationTypes.append(operation_type)
                rental_type = None
                if operation_type == "rent":
                    rental_type = random.choice(["short", "long"])
                if operation_type == "sale":
                    base_price = random.randint(120000, 500000)
                elif rental_type == "long":
                    base_price = random.randint(600, 2000)
                else:  # short
                    base_price = random.randint(50, 200)

                prop = Property.objects.create(
                    external_id=f"prop_{i}",
                    source=source,
                    location=location,
                    url=f"https://example.com/property/{i}",
                    title=f"Piso en {location.city} #{i}",
                    description="Piso bonito y bien ubicado",
                    property_type="flat",
                    operation_type=operation_type,
                    rooms=random.randint(1, 5),
                    bathrooms=random.randint(1, 3),
                    size_m2=random.randint(50, 150),
                    floor=str(random.randint(1, 10)),
                    energy_rating=random.choice(["A", "B", "C", "D"]),
                    rental_type=rental_type
                )

                properties.append(prop)

                base_price = random.randint(100000, 500000)

                for j in range(5):
                    if operation_type == "sale":
                        price = base_price - j * random.randint(1000, 5000)
                    elif rental_type == "long":
                        price = base_price + random.randint(-100, 100)
                    else:  # short
                        price = base_price + random.randint(-10, 10)

                    Listing.objects.create(
                        property=prop,
                        price=price,
                        price_per_m2=price / prop.size_m2 if prop.size_m2 else None,
                        published_at=timezone.now() - timedelta(days=30 * j),
                        scraped_at=timezone.now() - timedelta(days=30 * j),
                        is_active=(j == 0)
                    )
        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))