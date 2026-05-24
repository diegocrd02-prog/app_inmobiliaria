from datetime import timedelta

from django.db.models import Avg, Count, Prefetch
from django.utils import timezone

from estateAgency.models import AreaStats, Listing, Location, Property


def _operation_values_from_flag(flag):
    if flag == "rent_short":
        return "rent", "short"

    if flag == "rent_long":
        return "rent", "long"

    return "sale", ""


def _filter_properties_by_operation(queryset, flag):
    if flag == "sale":
        return queryset.filter(operation_type="sale")

    if flag == "rent_short":
        return queryset.filter(operation_type="rent", rental_type="short")

    if flag == "rent_long":
        return queryset.filter(operation_type="rent", rental_type="long")

    return queryset


def _filter_listings_by_operation(queryset, flag):
    if flag == "sale":
        return queryset.filter(property__operation_type="sale")

    if flag == "rent_short":
        return queryset.filter(
            property__operation_type="rent",
            property__rental_type="short",
        )

    if flag == "rent_long":
        return queryset.filter(
            property__operation_type="rent",
            property__rental_type="long",
        )

    return queryset


def get_chart_data_by_operation(flag, city=None):
    queryset = Property.objects.select_related("location").prefetch_related(
        Prefetch(
            "listings",
            queryset=Listing.objects.order_by("-scraped_at"),
            to_attr="latest_listings",
        )
    )

    queryset = _filter_properties_by_operation(queryset, flag)

    if city:
        queryset = queryset.filter(location__city__iexact=city)

    labels = []
    prices = []
    prices_m2 = []
    rooms = []

    for prop in queryset:
        latest_listing = prop.latest_listings[0] if prop.latest_listings else None

        if not latest_listing:
            continue

        labels.append(prop.title[:28])
        prices.append(float(latest_listing.price or 0))
        prices_m2.append(float(latest_listing.price_per_m2 or 0))
        rooms.append(prop.rooms or 0)

    return {
        "labels": labels,
        "prices": prices,
        "prices_m2": prices_m2,
        "rooms": rooms,
    }

def create_market_summary(flag):
    operation_type, rental_type = _operation_values_from_flag(flag)
    locations = Location.objects.all()
    for location in locations:
        if location:
            summary = Listing.objects.select_related(
                "property",
                "property__location",
            ).filter(property__location=location)

            summary = _filter_listings_by_operation(summary, flag).aggregate(
                avg_price=Avg("price"),
                avg_price_m2=Avg("price_per_m2"),
                total=Count("id"),
            )

            if summary["total"]:
                AreaStats.objects.update_or_create(
                    location=location,
                    date=timezone.localdate(),
                    operation_type=operation_type,
                    rental_type=rental_type,
                    defaults={
                        "avg_price": summary["avg_price"] or 0,
                        "avg_price_m2": summary["avg_price_m2"] or 0,
                        "num_properties": summary["total"],
                    },
                )

def get_market_summary(flag, city=None):
    operation_type, rental_type = _operation_values_from_flag(flag)

    if city:
        location = Location.objects.filter(city__iexact=city).first()
        if location:
            min_valid_date = timezone.localdate() - timedelta(days=3)
            cached_stats = AreaStats.objects.filter(
                location=location,
                operation_type=operation_type,
                rental_type=rental_type,
                date__gte=min_valid_date,
            ).order_by("-date").first()

            if cached_stats:
                return {
                    "avg_price": cached_stats.avg_price,
                    "avg_price_m2": cached_stats.avg_price_m2,
                    "total": cached_stats.num_properties,
                }

            summary = Listing.objects.select_related(
                "property",
                "property__location",
            ).filter(property__location=location)

            summary = _filter_listings_by_operation(summary, flag).aggregate(
                avg_price=Avg("price"),
                avg_price_m2=Avg("price_per_m2"),
                total=Count("id"),
            )

            if summary["total"]:
                AreaStats.objects.update_or_create(
                    location=location,
                    date=timezone.localdate(),
                    operation_type=operation_type,
                    rental_type=rental_type,
                    defaults={
                        "avg_price": summary["avg_price"] or 0,
                        "avg_price_m2": summary["avg_price_m2"] or 0,
                        "num_properties": summary["total"],
                    },
                )

            return summary

    queryset = Listing.objects.select_related("property", "property__location")
    queryset = _filter_listings_by_operation(queryset, flag)

    if city:
        queryset = queryset.filter(property__location__city__iexact=city)

    return queryset.aggregate(
        avg_price=Avg("price"),
        avg_price_m2=Avg("price_per_m2"),
        total=Count("id"),
    )


def get_property_detail_chart_data(property_obj):
    listings = property_obj.listings.order_by("scraped_at")
    labels = []
    prices = []
    prices_m2 = []

    for listing in listings:
        labels.append(listing.scraped_at.strftime("%d/%m/%Y"))
        prices.append(float(listing.price or 0))
        prices_m2.append(float(listing.price_per_m2 or 0))

    return {
        "labels": labels,
        "prices": prices,
        "prices_m2": prices_m2,
    }
