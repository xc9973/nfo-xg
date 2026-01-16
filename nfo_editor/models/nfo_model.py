"""NFO data models."""
from dataclasses import dataclass, field
from typing import List, Dict, Any

from .nfo_types import NfoType


@dataclass
class Actor:
    """Actor information in NFO file."""
    name: str
    role: str = ""
    thumb: str = ""
    order: int = 0


@dataclass
class NfoData:
    """NFO file data model containing all NFO fields."""
    nfo_type: NfoType
    title: str = ""
    originaltitle: str = ""
    year: str = ""
    plot: str = ""
    runtime: str = ""
    genres: List[str] = field(default_factory=list)
    directors: List[str] = field(default_factory=list)
    actors: List[Actor] = field(default_factory=list)
    studio: str = ""
    rating: str = ""
    poster: str = ""
    fanart: str = ""
    # TV Show / Episode specific fields
    season: str = ""
    episode: str = ""
    aired: str = ""
    # Preserve unknown tags
    extra_tags: Dict[str, Any] = field(default_factory=dict)
