from django.db.models import Prefetch
from estateAgency.models import Property, Listing
from estateAgency.dto.propertyDTO import PropertyDTO

def get_properties_by_location(city=None, province=None):
    
    queryset = Property.objects.select_related("location").prefetch_related(
        Prefetch(
            "listings",
            queryset=Listing.objects.order_by("-scraped_at"),
            to_attr="prefetched_listings"
        )
    )

    if city:
        queryset = queryset.filter(location__city__iexact=city)

    if province:
        queryset = queryset.filter(location__province__iexact=province)

    dtos = []

    for p in queryset:
        latest_listing = p.prefetched_listings[0] if p.prefetched_listings else None

        dto = PropertyDTO(
            id=p.id,
            title=p.title,
            price=float(latest_listing.price) if latest_listing else None,
            city=p.location.city if p.location else None,
            province=p.location.province if p.location else None,
            rooms=p.rooms,
            size_m2=float(p.size_m2) if p.size_m2 else None,
            price_per_m2=float(latest_listing.price_per_m2) if latest_listing and latest_listing.price_per_m2 else None,
            image_url=p.image_url
        )

        dtos.append(dto)

    return dtos

def get_properties_by_operation(flag, city= None):

    queryset = Property.objects.select_related("location").prefetch_related(
        Prefetch(
            "listings",
            queryset=Listing.objects.order_by("-scraped_at"),
            to_attr="prefetched_listings"
        )
    )

    if flag == "sale":
        queryset = queryset.filter(operation_type="sale")

    elif flag == "rent_short":
        queryset = queryset.filter(operation_type="rent", rental_type="short")

    elif flag == "rent_long":
        queryset = queryset.filter(operation_type="rent", rental_type="long")
        
    if city:
        queryset = queryset.filter(location__city__iexact=city)

    dtos = []

    for p in queryset:
        latest_listing = p.prefetched_listings[0] if p.prefetched_listings else None

        dtos.append(PropertyDTO(
            id=p.id,
            title=p.title,
            price=float(latest_listing.price) if latest_listing else None,
            city=p.location.city if p.location else None,
            province=p.location.province if p.location else None,
            image_url=p.image_url,
            rooms=p.rooms,
            size_m2=float(p.size_m2) if p.size_m2 else None,
            price_per_m2=float(latest_listing.price_per_m2) if latest_listing and latest_listing.price_per_m2 else None,
        ))

    return dtos
