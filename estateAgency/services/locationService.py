from estateAgency.models import Location
from estateAgency.dto.locationDTO import LocationDTO

def get_all_locations():
    queryset = Location.objects.all()

    dtos = []

    for loc in queryset:
        dto = LocationDTO(
            id=loc.id,
            country=loc.country,
            city=loc.city,
            province=loc.province,
            latitude=float(loc.latitude) if loc.latitude else None,
            longitude=float(loc.longitude) if loc.longitude else None,
        )
        dtos.append(dto)

    return dtos