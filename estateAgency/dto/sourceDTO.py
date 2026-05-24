from dataclasses import dataclass
from typing import Optional


@dataclass
class SourceDTO:
    """DTO for Source model - represents real estate portals/sources"""
    id: Optional[int] = None
    name: str = ""
    base_url: Optional[str] = None
