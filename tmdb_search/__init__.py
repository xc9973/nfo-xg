"""TMDB Search - Independent TMDB API client and data mapper.

This package provides functionality to search and retrieve movie/TV show
information from The Movie Database (TMDB) API.

Example:
    >>> from tmdb_search import TMDBClient, TMDBMapper
    >>> client = TMDBClient(api_key="your_key")
    >>> mapper = TMDBMapper(client)
    >>> data = client.get_movie_details(550)
    >>> nfo_data = mapper.map_movie(data)
"""

from tmdb_search.client import TMDBClient
from tmdb_search.mapper import TMDBMapper

__all__ = ["TMDBClient", "TMDBMapper"]
__version__ = "0.1.0"
