"""Tests for TMDB Client."""
import pytest
import responses
from requests.exceptions import HTTPError

from nfo_editor.services.tmdb_client import TMDBClient


class TestTMDBClient:
    """Tests for TMDBClient class."""

    def test_init_with_api_key(self):
        """初始化时提供 API Key"""
        client = TMDBClient(api_key="test_key")
        assert client.api_key == "test_key"

    def test_init_without_api_key(self):
        """初始化时不提供 API Key，使用环境变量"""
        import os
        original_key = os.environ.get("TMDB_API_KEY")
        try:
            os.environ["TMDB_API_KEY"] = "env_key"
            client = TMDBClient()
            assert client.api_key == "env_key"
        finally:
            if original_key is None:
                os.environ.pop("TMDB_API_KEY", None)
            else:
                os.environ["TMDB_API_KEY"] = original_key

    def test_get_image_url_with_path(self):
        """获取完整图片 URL"""
        client = TMDBClient(api_key="test_key")
        url = client.get_image_url("/abc123.jpg", "original")
        assert url == "https://image.tmdb.org/t/p/original/abc123.jpg"

    def test_get_image_url_with_default_size(self):
        """使用默认图片尺寸"""
        client = TMDBClient(api_key="test_key")
        url = client.get_image_url("/abc123.jpg")
        assert url == "https://image.tmdb.org/t/p/original/abc123.jpg"

    def test_get_image_url_with_empty_path(self):
        """空路径返回空字符串"""
        client = TMDBClient(api_key="test_key")
        url = client.get_image_url("", "original")
        assert url == ""
        url = client.get_image_url(None, "original")
        assert url == ""

    @responses.activate
    def test_search_multi_success(self):
        """成功搜索电影和电视剧"""
        responses.add(
            responses.GET,
            "https://api.themoviedb.org/3/search/multi",
            json={
                "page": 1,
                "results": [
                    {
                        "id": 123,
                        "media_type": "movie",
                        "title": "Test Movie",
                        "original_title": "Test Movie",
                        "release_date": "2024-01-01",
                        "poster_path": "/test.jpg",
                        "overview": "Test overview"
                    }
                ],
                "total_pages": 1,
                "total_results": 1
            },
            status=200
        )

        client = TMDBClient(api_key="test_key")
        result = client.search_multi("test")

        assert result["total_results"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "Test Movie"

    @responses.activate
    def test_get_movie_details_success(self):
        """成功获取电影详情"""
        responses.add(
            responses.GET,
            "https://api.themoviedb.org/3/movie/550",
            json={
                "id": 550,
                "title": "Fight Club",
                "original_title": "Fight Club",
                "release_date": "1999-10-15",
                "overview": "Test plot",
                "runtime": 139,
                "vote_average": 8.4,
                "genres": [{"name": "Drama"}],
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
                        }
                    ],
                    "crew": [
                        {"name": "David Fincher", "job": "Director"}
                    ]
                }
            },
            status=200
        )

        client = TMDBClient(api_key="test_key")
        result = client.get_movie_details(550)

        assert result["title"] == "Fight Club"
        assert result["runtime"] == 139
        assert len(result["credits"]["cast"]) == 1

    @responses.activate
    def test_get_tv_details_success(self):
        """成功获取电视剧详情"""
        responses.add(
            responses.GET,
            "https://api.themoviedb.org/3/tv/1396",
            json={
                "id": 1396,
                "name": "Breaking Bad",
                "original_name": "Breaking Bad",
                "first_air_date": "2008-01-20",
                "overview": "Test plot",
                "episode_run_time": [45],
                "vote_average": 8.9,
                "genres": [{"name": "Drama"}],
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
            },
            status=200
        )

        client = TMDBClient(api_key="test_key")
        result = client.get_tv_details(1396)

        assert result["name"] == "Breaking Bad"
        assert result["episode_run_time"] == [45]

    @responses.activate
    def test_get_tv_episode_details_success(self):
        """成功获取单集详情"""
        responses.add(
            responses.GET,
            "https://api.themoviedb.org/3/tv/1396/season/1/episode/1",
            json={
                "id": 62161,
                "name": "Pilot",
                "overview": "Test plot",
                "air_date": "2008-01-20",
                "runtime": 45,
                "vote_average": 8.0,
                "still_path": "/still.jpg",
                "season_number": 1,
                "episode_number": 1,
                "credits": {
                    "cast": [],
                    "crew": []
                }
            },
            status=200
        )

        client = TMDBClient(api_key="test_key")
        result = client.get_tv_episode_details(1396, 1, 1)

        assert result["name"] == "Pilot"
        assert result["season_number"] == 1

    def test_request_without_api_key(self):
        """没有 API Key 时抛出异常"""
        client = TMDBClient(api_key=None)
        import os
        original_key = os.environ.get("TMDB_API_KEY")
        try:
            os.environ.pop("TMDB_API_KEY", None)
            with pytest.raises(ValueError, match="TMDB API Key is missing"):
                client.search_multi("test")
        finally:
            if original_key is not None:
                os.environ["TMDB_API_KEY"] = original_key

    @responses.activate
    def test_request_with_invalid_api_key(self):
        """无效 API Key 返回 ValueError"""
        responses.add(
            responses.GET,
            "https://api.themoviedb.org/3/search/multi",
            status=401
        )

        client = TMDBClient(api_key="invalid_key")
        with pytest.raises(ValueError, match="Invalid TMDB API Key"):
            client.search_multi("test")

    @responses.activate
    def test_request_with_404(self):
        """资源不存在返回 404 HTTPError"""
        responses.add(
            responses.GET,
            "https://api.themoviedb.org/3/movie/999999",
            status=404
        )

        client = TMDBClient(api_key="test_key")
        with pytest.raises(HTTPError):
            client.get_movie_details(999999)
