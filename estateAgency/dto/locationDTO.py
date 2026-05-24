from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass
class LocationDTO:
    """DTO for Location model - represents geographical location information"""
    id: Optional[int] = None
    country: Optional[str] = None
    region: Optional[str] = None
    province: Optional[str] = None
    city: str = ""
    district: Optional[str] = None
    neighborhood: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
