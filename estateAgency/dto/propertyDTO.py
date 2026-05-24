from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime


@dataclass
class PropertyDTO:
    """DTO for Property model - represents real estate properties"""
    id: Optional[int] = None
    external_id: str = ""
    source_id: Optional[int] = None
    location_id: Optional[int] = None
    image_url: Optional[str] = None
    url: str = ""
    title: str = ""
    description: Optional[str] = None
    property_type: str = ""  # flat, house, studio, penthouse, duplex, land, other
    operation_type: str = ""  # sale, rent
    rooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size_m2: Optional[Decimal] = None
    floor: Optional[str] = None
    energy_rating: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    province: Optional[str] = None
    city: Optional[str] = None
    price: Optional[Decimal] = None
    price_per_m2: Optional[Decimal] = None
    
