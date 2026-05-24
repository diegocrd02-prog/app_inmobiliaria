from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime


@dataclass
class ListingDTO:
    """DTO for Listing model - represents price history of properties"""
    id: Optional[int] = None
    property_id: Optional[int] = None
    price: Decimal = Decimal("0.00")
    price_per_m2: Optional[Decimal] = None
    published_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None
    is_active: bool = True
