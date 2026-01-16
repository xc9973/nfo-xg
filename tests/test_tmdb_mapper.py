"""Tests for TMDB Mapper."""
import pytest

from nfo_editor.models.nfo_model import NfoData, Actor
from nfo_editor.models.nfo_types import NfoType
from nfo_editor.services.tmdb_client import TMDBClient
from nfo_editor.services.tmdb_mapper import TMDBMapper


class TestTMDBMapper:
    """Tests for TMDBMapper class."""

    def test_init(self):
        """初始化映射器"""
        client = TMDBClient(api_key="test_key")
        mapper = TMDBMapper(tmdb_client=client)
        assert mapper.client == client

    def test_map_movie(self):
        """映射电影数据"""
        client = TMDBClient(api_key="test_key")
        mapper = TMDBMapper(tmdb_client=client)

        tmdb_data = {
            "id": 550,
            "title": "Fight Club",
            "original_title": "Fight Club",
            "release_date": "1999-10-15",
            "overview": "A ticking-time-bomb insomniac...",
            "runtime": 139,
            "vote_average": 8.4,
            "genres": [{"name": "Drama"}, {"name": "Thriller"}],
            "production_companies": [{"name": "Fox 2000 Pictures"}],
            "poster_path": "/poster.jpg",
            "backdrop_path": "/backdrop.jpg",
            "credits": {
                "cast": [
                    {
                        "name": "Brad Pitt",
                        "character": "Tyler Durden",
                        "profile_path": "/brad.jpg",
                        "order": 0
                    },
                    {
                        "name": "Edward Norton",
                        "character": "Narrator",
                        "profile_path": "/edward.jpg",
                        "order": 1
                    }
                ],
                "crew": [
                    {"name": "David Fincher", "job": "Director"},
                    {"name": "Jim Uhls", "job": "Screenplay"}
                ]
            }
        }

        result = mapper.map_movie(tmdb_data)

        assert isinstance(result, NfoData)
        assert result.nfo_type == NfoType.MOVIE
        assert result.title == "Fight Club"
        assert result.originaltitle == "Fight Club"
        assert result.year == "1999"
        assert result.plot == "A ticking-time-bomb insomniac..."
        assert result.runtime == "139"
        assert result.rating == "8.4"
        assert result.genres == ["Drama", "Thriller"]
        assert result.directors == ["David Fincher"]
        assert result.studio == "Fox 2000 Pictures"
        assert result.poster == "https://image.tmdb.org/t/p/original/poster.jpg"
        assert result.fanart == "https://image.tmdb.org/t/p/original/backdrop.jpg"
        assert result.aired == "1999-10-15"

        assert len(result.actors) == 2
        assert result.actors[0].name == "Brad Pitt"
        assert result.actors[0].role == "Tyler Durden"
        assert result.actors[0].thumb == "https://image.tmdb.org/t/p/w200/brad.jpg"
        assert result.actors[0].order == 0

    def test_map_movie_with_missing_fields(self):
        """映射缺少字段的电影数据"""
        client = TMDBClient(api_key="test_key")
        mapper = TMDBMapper(tmdb_client=client)

        tmdb_data = {
            "id": 1,
            "title": "Test Movie",
            "original_title": "Test Movie",
            "credits": {
                "cast": [],
                "crew": []
            }
        }

        result = mapper.map_movie(tmdb_data)

        assert result.title == "Test Movie"
        assert result.year == ""
        assert result.plot == ""
        assert result.runtime == ""
        assert result.rating == ""
        assert result.genres == []
        assert result.directors == []
        assert result.actors == []
        assert result.studio == ""
        assert result.poster == ""
        assert result.fanart == ""

    def test_map_tv_show(self):
        """映射电视剧数据"""
        client = TMDBClient(api_key="test_key")
        mapper = TMDBMapper(tmdb_client=client)

        tmdb_data = {
            "id": 1396,
            "name": "Breaking Bad",
            "original_name": "Breaking Bad",
            "first_air_date": "2008-01-20",
            "overview": "A high school chemistry teacher...",
            "episode_run_time": [45],
            "vote_average": 8.9,
            "genres": [{"name": "Drama"}, {"name": "Crime"}],
            "production_companies": [{"name": "Sony Pictures"}],
            "poster_path": "/poster.jpg",
            "backdrop_path": "/backdrop.jpg",
            "credits": {
                "cast": [
                    {
                        "name": "Bryan Cranston",
                        "character": "Walter White",
                        "profile_path": "/bryan.jpg",
                        "order": 0
                    }
                ],
                "crew": [
                    {"name": "Vince Gilligan", "job": "Director"}
                ]
            }
        }

        result = mapper.map_tv_show(tmdb_data)

        assert isinstance(result, NfoData)
        assert result.nfo_type == NfoType.TVSHOW
        assert result.title == "Breaking Bad"
        assert result.originaltitle == "Breaking Bad"
        assert result.year == "2008"
        assert result.runtime == "45"
        assert result.aired == "2008-01-20"

    def test_map_episode(self):
        """映射单集数据"""
        client = TMDBClient(api_key="test_key")
        mapper = TMDBMapper(tmdb_client=client)

        tmdb_data = {
            "id": 62161,
            "name": "Pilot",
            "overview": "Episode plot",
            "air_date": "2008-01-20",
            "runtime": 45,
            "vote_average": 8.0,
            "still_path": "/still.jpg",
            "season_number": 1,
            "episode_number": 1,
            "credits": {
                "cast": [
                    {
                        "name": "Bryan Cranston",
                        "character": "Walter White",
                        "profile_path": "/bryan.jpg",
                        "order": 0
                    }
                ],
                "crew": [
                    {"name": "Vince Gilligan", "job": "Director"}
                ]
            }
        }

        result = mapper.map_episode(tmdb_data)

        assert isinstance(result, NfoData)
        assert result.nfo_type == NfoType.EPISODE
        assert result.title == "Pilot"
        assert result.year == "2008"
        assert result.season == "1"
        assert result.episode == "1"
        assert result.aired == "2008-01-20"
        assert result.poster == "https://image.tmdb.org/t/p/original/still.jpg"
        assert result.fanart == ""

    def test_map_movie_with_various_ratings(self):
        """测试不同评分的格式化"""
        client = TMDBClient(api_key="test_key")
        mapper = TMDBMapper(tmdb_client=client)

        # 测试 8.4 -> "8.4"
        tmdb_data = {
            "id": 1,
            "title": "Test",
            "original_title": "Test",
            "vote_average": 8.4,
            "credits": {"cast": [], "crew": []}
        }
        result = mapper.map_movie(tmdb_data)
        assert result.rating == "8.4"

        # 测试 8.0 -> "8.0"
        tmdb_data["vote_average"] = 8.0
        result = mapper.map_movie(tmdb_data)
        assert result.rating == "8.0"

        # 测试 None -> ""
        tmdb_data["vote_average"] = None
        result = mapper.map_movie(tmdb_data)
        assert result.rating == ""

    def test_map_movie_with_various_dates(self):
        """测试不同日期格式的年份提取"""
        client = TMDBClient(api_key="test_key")
        mapper = TMDBMapper(tmdb_client=client)

        base_data = {
            "id": 1,
            "title": "Test",
            "original_title": "Test",
            "credits": {"cast": [], "crew": []}
        }

        # 测试正常日期
        base_data["release_date"] = "2024-01-15"
        result = mapper.map_movie(base_data)
        assert result.year == "2024"

        # 测试空日期
        base_data["release_date"] = ""
        result = mapper.map_movie(base_data)
        assert result.year == ""

        # 测试 None
        base_data["release_date"] = None
        result = mapper.map_movie(base_data)
        assert result.year == ""

    def test_get_genres_filters_empty_names(self):
        """测试类型提取过滤空名字"""
        client = TMDBClient(api_key="test_key")
        mapper = TMDBMapper(tmdb_client=client)

        tmdb_data = {
            "id": 1,
            "title": "Test",
            "original_title": "Test",
            "genres": [
                {"name": "Action"},
                {"name": "Drama"},
                {"id": 123}  # 没有 name 字段
            ],
            "credits": {"cast": [], "crew": []}
        }

        result = mapper.map_movie(tmdb_data)
        assert result.genres == ["Action", "Drama"]

    def test_get_directors_filters_correctly(self):
        """测试导演提取只过滤 Director 角色"""
        client = TMDBClient(api_key="test_key")
        mapper = TMDBMapper(tmdb_client=client)

        tmdb_data = {
            "id": 1,
            "title": "Test",
            "original_title": "Test",
            "credits": {
                "cast": [],
                "crew": [
                    {"name": "Christopher Nolan", "job": "Director"},
                    {"name": "Emma Thomas", "job": "Producer"},
                    {"job": "Writer"}
                ]
            }
        }

        result = mapper.map_movie(tmdb_data)
        assert result.directors == ["Christopher Nolan"]

    def test_get_actors_filters_missing_names(self):
        """测试演员提取过滤缺少名字的条目"""
        client = TMDBClient(api_key="test_key")
        mapper = TMDBMapper(tmdb_client=client)

        tmdb_data = {
            "id": 1,
            "title": "Test",
            "original_title": "Test",
            "credits": {
                "cast": [
                    {"name": "Actor One", "character": "Role One", "profile_path": "/actor1.jpg"},
                    {"name": "Actor Two", "character": "Role Two", "profile_path": "/actor2.jpg"},
                    {"id": 123}  # 没有 name 字段
                ],
                "crew": []
            }
        }

        result = mapper.map_movie(tmdb_data)
        assert len(result.actors) == 2
        assert result.actors[0].name == "Actor One"
        assert result.actors[0].role == "Role One"
        assert result.actors[0].thumb == "https://image.tmdb.org/t/p/w200/actor1.jpg"
        assert result.actors[0].order == 0

    def test_get_studio_handles_various_cases(self):
        """测试制片公司提取的各种情况"""
        client = TMDBClient(api_key="test_key")
        mapper = TMDBMapper(tmdb_client=client)

        # 测试有制片公司
        tmdb_data = {
            "id": 1,
            "title": "Test",
            "original_title": "Test",
            "production_companies": [{"name": "Warner Bros."}, {"name": "Legendary"}],
            "credits": {"cast": [], "crew": []}
        }
        result = mapper.map_movie(tmdb_data)
        assert result.studio == "Warner Bros."

        # 测试空列表
        tmdb_data["production_companies"] = []
        result = mapper.map_movie(tmdb_data)
        assert result.studio == ""

        # 测试缺少 name 字段
        tmdb_data["production_companies"] = [{}]
        result = mapper.map_movie(tmdb_data)
        assert result.studio == ""
