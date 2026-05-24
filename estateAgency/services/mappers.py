from estateAgency.dto.propertyDTO import PropertyDTO
from estateAgency.dto.listingDTO import ListingDTO
from estateAgency.dto.locationDTO import LocationDTO
from estateAgency.dto.sourceDTO import SourceDTO


def property_to_dto(property_obj):
    latest_listing = property_obj.listings.order_by('-scraped_at').first()

    return PropertyDTO(
        id=property_obj.id,
        title=property_obj.title,
        price=latest_listing.price if latest_listing else None,
        city=property_obj.location.city if property_obj.location else None,
        province=property_obj.location.province if property_obj.location else None,
        rooms=property_obj.rooms,
        size_m2=property_obj.size_m2
    )
    
def source_to_dto(source_obj):
    """Convert Source model to SourceDTO"""
    return SourceDTO(
        id=source_obj.id,
        name=source_obj.name,
        base_url=source_obj.base_url
    )


def location_to_dto(location_obj):
    """Convert Location model to LocationDTO"""
    return LocationDTO(
        id=location_obj.id,
        country=location_obj.country,
        region=location_obj.region,
        province=location_obj.province,
        city=location_obj.city,
        district=location_obj.district,
        neighborhood=location_obj.neighborhood,
        postal_code=location_obj.postal_code,
        latitude=location_obj.latitude,
        longitude=location_obj.longitude
    )

def listing_to_dto(listing_obj):
    return ListingDTO(
        id=listing_obj.id,
        property_id=listing_obj.property_id,
        price=listing_obj.price,
        price_per_m2=listing_obj.price_per_m2,
        published_at=listing_obj.published_at,
        scraped_at=listing_obj.scraped_at,
        is_active=listing_obj.is_active
    )