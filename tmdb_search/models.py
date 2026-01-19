"""Data models for TMDB search results."""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class MediaType(Enum):
    """Media type enumeration."""
    MOVIE = "movie"
    TVSHOW = "tvshow"
    EPISODE = "episodedetails"


@dataclass
class Actor:
    """Actor information."""
    name: str
    role: str = ""
    thumb: str = ""
    order: int = 0


@dataclass
class TMDBMovieData:
    """Movie data from TMDB."""
    title: str = ""
    original_title: str = ""
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
    aired: str = ""


@dataclass
class TMDBTVShowData:
    """TV show data from TMDB."""
    title: str = ""
    original_title: str = ""
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
    aired: str = ""


@dataclass
class TMDBEpisodeData:
    """Episode data from TMDB."""
    title: str = ""
    original_title: str = ""
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
    season: str = ""
    episode: str = ""
    aired: str = ""
