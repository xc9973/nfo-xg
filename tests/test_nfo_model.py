"""Unit tests for NFO data models."""
import pytest
from nfo_editor.models import NfoType, Actor, NfoData


class TestNfoType:
    """Tests for NfoType enumeration."""

    def test_movie_type_value(self):
        assert NfoType.MOVIE.value == "movie"

    def test_tvshow_type_value(self):
        assert NfoType.TVSHOW.value == "tvshow"

    def test_episode_type_value(self):
        assert NfoType.EPISODE.value == "episodedetails"


class TestActor:
    """Tests for Actor dataclass."""

    def test_actor_creation_with_name_only(self):
        actor = Actor(name="John Doe")
        assert actor.name == "John Doe"
        assert actor.role == ""
        assert actor.thumb == ""
        assert actor.order == 0

    def test_actor_creation_with_all_fields(self):
        actor = Actor(name="Jane Doe", role="Lead", thumb="thumb.jpg", order=1)
        assert actor.name == "Jane Doe"
        assert actor.role == "Lead"
        assert actor.thumb == "thumb.jpg"
        assert actor.order == 1

    def test_actor_data_integrity(self):
        """Test that actor fields maintain their values."""
        actor = Actor(name="Test Actor", role="Hero", thumb="hero.jpg", order=5)
        # Verify all fields are accessible and correct
        assert actor.name == "Test Actor"
        assert actor.role == "Hero"
        assert actor.thumb == "hero.jpg"
        assert actor.order == 5


class TestNfoData:
    """Tests for NfoData dataclass."""

    def test_nfo_data_creation_minimal(self):
        """Test creating NfoData with only required field."""
        nfo = NfoData(nfo_type=NfoType.MOVIE)
        assert nfo.nfo_type == NfoType.MOVIE
        assert nfo.title == ""
        assert nfo.genres == []
        assert nfo.actors == []

    def test_nfo_data_creation_with_basic_fields(self):
        """Test creating NfoData with common fields."""
        nfo = NfoData(
            nfo_type=NfoType.MOVIE,
            title="Test Movie",
            year="2024",
            plot="A test movie plot.",
            runtime="120"
        )
        assert nfo.title == "Test Movie"
        assert nfo.year == "2024"
        assert nfo.plot == "A test movie plot."
        assert nfo.runtime == "120"

    def test_nfo_data_with_genres(self):
        """Test NfoData with multiple genres."""
        nfo = NfoData(
            nfo_type=NfoType.MOVIE,
            genres=["Action", "Sci-Fi", "Drama"]
        )
        assert len(nfo.genres) == 3
        assert "Action" in nfo.genres
        assert "Sci-Fi" in nfo.genres
        assert "Drama" in nfo.genres

    def test_nfo_data_with_actors(self):
        """Test NfoData with multiple actors."""
        actors = [
            Actor(name="Actor 1", role="Role 1", order=0),
            Actor(name="Actor 2", role="Role 2", order=1),
        ]
        nfo = NfoData(nfo_type=NfoType.MOVIE, actors=actors)
        assert len(nfo.actors) == 2
        assert nfo.actors[0].name == "Actor 1"
        assert nfo.actors[1].name == "Actor 2"

    def test_nfo_data_tvshow_specific_fields(self):
        """Test TV show specific fields."""
        nfo = NfoData(
            nfo_type=NfoType.TVSHOW,
            title="Test Show",
            season="1",
            episode="5",
            aired="2024-01-15"
        )
        assert nfo.nfo_type == NfoType.TVSHOW
        assert nfo.season == "1"
        assert nfo.episode == "5"
        assert nfo.aired == "2024-01-15"

    def test_nfo_data_extra_tags(self):
        """Test that extra_tags can store unknown tags."""
        nfo = NfoData(
            nfo_type=NfoType.MOVIE,
            extra_tags={"custom_tag": "custom_value", "another": "value"}
        )
        assert nfo.extra_tags["custom_tag"] == "custom_value"
        assert nfo.extra_tags["another"] == "value"

    def test_nfo_data_field_access(self):
        """Test all field access for NfoData."""
        nfo = NfoData(
            nfo_type=NfoType.EPISODE,
            title="Episode Title",
            originaltitle="Original Title",
            year="2024",
            plot="Episode plot",
            runtime="45",
            genres=["Drama"],
            directors=["Director 1"],
            actors=[Actor(name="Actor")],
            studio="Studio Name",
            rating="8.5",
            poster="poster.jpg",
            fanart="fanart.jpg",
            season="2",
            episode="10",
            aired="2024-06-01"
        )
        assert nfo.nfo_type == NfoType.EPISODE
        assert nfo.title == "Episode Title"
        assert nfo.originaltitle == "Original Title"
        assert nfo.studio == "Studio Name"
        assert nfo.rating == "8.5"
        assert nfo.poster == "poster.jpg"
        assert nfo.fanart == "fanart.jpg"
        assert len(nfo.directors) == 1
