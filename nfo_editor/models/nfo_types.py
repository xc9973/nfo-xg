"""NFO type definitions."""
from enum import Enum


class NfoType(Enum):
    """NFO file type enumeration."""
    MOVIE = "movie"
    TVSHOW = "tvshow"
    EPISODE = "episodedetails"
