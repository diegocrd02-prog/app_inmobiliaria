from django.db.models import Prefetch

from estateAgency.models import AreaStats, Listing, Property


def _operation_data(property_obj):
    if property_obj.operation_type == "sale":
        return "sale", "", "Compra"

    if property_obj.rental_type == "short":
        return "rent", "short", "Alquiler de temporada"

    return "rent", "long", "Alquiler de larga estancia"


def _latest_area_stats(property_obj):
    operation_type, rental_type, _ = _operation_data(property_obj)

    return AreaStats.objects.filter(
        location=property_obj.location,
        operation_type=operation_type,
        rental_type=rental_type,
    ).order_by("-date").first()


def _normalize(value, minimum, maximum, fallback):
    if value is None:
        return 0

    if maximum == minimum:
        return fallback

    return (value - minimum) / (maximum - minimum)

def _build_item(property_obj):
    latest_listing = property_obj.latest_listings[0] if property_obj.latest_listings else None
    area_stats = _latest_area_stats(property_obj)
    price = float(latest_listing.price) if latest_listing else 0
    size_m2 = float(property_obj.size_m2) if property_obj.size_m2 else 0
    price_per_m2 = float(latest_listing.price_per_m2) if latest_listing and latest_listing.price_per_m2 else 0

    if not price_per_m2 and price and size_m2:
        price_per_m2 = price / size_m2

    market_avg_m2 = float(area_stats.avg_price_m2) if area_stats else None
    market_delta_pct = None

    if market_avg_m2 and price_per_m2:
        market_delta_pct = ((market_avg_m2 - price_per_m2) / market_avg_m2) * 100

    _, _, operation_label = _operation_data(property_obj)

    return {
        "id": property_obj.id,
        "title": property_obj.title,
        "url": property_obj.url,
        "city": property_obj.location.city,
        "operation_label": operation_label,
        "property_type": property_obj.property_type,
        "price": price,
        "size_m2": size_m2,
        "rooms": property_obj.rooms or 0,
        "bathrooms": property_obj.bathrooms or 0,
        "price_per_m2": price_per_m2,
        "market_avg_m2": market_avg_m2,
        "market_delta_pct": market_delta_pct,
        "image_url": property_obj.image_url,
        "score": 0,
        "score_reason": "",
    }


def compare_properties(property_ids):
    ids = [int(property_id) for property_id in property_ids if str(property_id).isdigit()]

    if not ids:
        return {
            "items": [],
            "best": None,
            "conclusion": "Selecciona al menos dos viviendas para generar una comparativa.",
        }

    queryset = Property.objects.select_related("location", "source").prefetch_related(
        Prefetch(
            "listings",
            queryset=Listing.objects.order_by("-scraped_at"),
            to_attr="latest_listings",
        )
    ).filter(id__in=ids)

    properties_by_id = {property_obj.id: property_obj for property_obj in queryset}
    items = []

    for property_id in ids:
        if property_id not in properties_by_id:
            continue

        property_obj = properties_by_id[property_id]
        items.append(_build_item(property_obj))

    if len(items) < 2:
        return {
            "items": items,
            "best": items[0] if items else None,
            "conclusion": "Selecciona al menos dos viviendas para que la recomendacion tenga sentido.",
        }

    valid_m2 = [item["price_per_m2"] for item in items if item["price_per_m2"]]
    valid_sizes = [item["size_m2"] for item in items if item["size_m2"]]
    valid_rooms = [item["rooms"] for item in items if item["rooms"]]

    min_m2 = min(valid_m2) if valid_m2 else 0
    max_m2 = max(valid_m2) if valid_m2 else 0
    min_size = min(valid_sizes) if valid_sizes else 0
    max_size = max(valid_sizes) if valid_sizes else 0
    min_rooms = min(valid_rooms) if valid_rooms else 0
    max_rooms = max(valid_rooms) if valid_rooms else 0

    for item in items:
        price_component = (1 - _normalize(item["price_per_m2"], min_m2, max_m2, 0.5)) * 45
        size_component = _normalize(item["size_m2"], min_size, max_size, 0.5) * 20
        rooms_component = _normalize(item["rooms"], min_rooms, max_rooms, 0.5) * 15

        if item["market_delta_pct"] is None:
            market_component = 8
        else:
            market_component = max(0, min(20, 10 + item["market_delta_pct"]))

        item["score"] = round(price_component + size_component + rooms_component + market_component, 1)

    best = max(items, key=lambda item: item["score"])
    reasons = []

    if best["price_per_m2"] == min_m2 and best["price_per_m2"]:
        reasons.append("tiene el precio por metro cuadrado mas competitivo del grupo")

    if best["market_delta_pct"] and best["market_delta_pct"] > 0:
        reasons.append("esta por debajo de la media de su zona")

    if best["size_m2"] == max_size and best["size_m2"]:
        reasons.append("ofrece la mayor superficie")

    if best["rooms"] == max_rooms and best["rooms"]:
        reasons.append("aporta mas habitaciones que las alternativas")

    if not reasons:
        reasons.append("presenta el equilibrio mas solido entre precio, metros y caracteristicas")

    best["score_reason"] = ", ".join(reasons)
    conclusion = (
        f"Recomendacion: la vivienda \"{best['title']}\" parece la opcion mas interesante "
        f"porque {best['score_reason']}. Su puntuacion global es {best['score']} sobre 100."
    )

    return {
        "items": sorted(items, key=lambda item: item["score"], reverse=True),
        "best": best,
        "conclusion": conclusion,
    }
