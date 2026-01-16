"""Tests for TMDB API endpoints."""
import pytest
import responses
from fastapi.testclient import TestClient

from web.app import app, tmdb_client


client = TestClient(app)


class TestTMDBSearchEndpoint:
    """Tests for /api/tmdb/search endpoint."""

    @responses.activate
    def test_search_returns_results(self, monkeypatch):
        """搜索返回结果"""
        # 直接设置客户端的 API Key
        monkeypatch.setattr(tmdb_client, "api_key", "test_key")

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

        response = client.get("/api/tmdb/search?query=test", auth=("test", "test"))

        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 1
        assert len(data["results"]) == 1

    def test_search_without_query_returns_error(self):
        """没有搜索关键词时返回错误"""
        response = client.get("/api/tmdb/search", auth=("test", "test"))
        # 应该返回 422 (Unprocessable Entity) 因为缺少 query 参数
        assert response.status_code == 422

    @responses.activate
    def test_search_with_invalid_api_key(self, monkeypatch):
        """无效 API Key 返回 401"""
        # 设置一个无效的 API Key
        monkeypatch.setattr(tmdb_client, "api_key", "invalid_key")

        responses.add(
            responses.GET,
            "https://api.themoviedb.org/3/search/multi",
            status=401
        )

        response = client.get("/api/tmdb/search?query=test", auth=("test", "test"))
        assert response.status_code == 401


class TestTMDBMovieEndpoint:
    """Tests for /api/tmdb/movie/{tmdb_id} endpoint."""

    @responses.activate
    def test_get_movie_returns_nfo_data(self, monkeypatch):
        """获取电影详情返回 NFO 格式数据"""
        monkeypatch.setattr(tmdb_client, "api_key", "test_key")

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

        response = client.get("/api/tmdb/movie/550", auth=("test", "test"))

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Fight Club"
        assert data["nfo_type"] == "movie"
        assert data["year"] == "1999"
        assert data["rating"] == "8.4"
        assert len(data["actors"]) == 1

    @responses.activate
    def test_get_movie_with_invalid_id(self, monkeypatch):
        """无效电影 ID 返回 500 (因为 HTTPError 被捕获)"""
        monkeypatch.setattr(tmdb_client, "api_key", "test_key")

        responses.add(
            responses.GET,
            "https://api.themoviedb.org/3/movie/999999",
            status=404
        )

        response = client.get("/api/tmdb/movie/999999", auth=("test", "test"))
        # 404 错误会引发 HTTPError，被包装成 500
        assert response.status_code == 500


class TestTMDBTVEndpoint:
    """Tests for /api/tmdb/tv/{tmdb_id} endpoint."""

    @responses.activate
    def test_get_tv_returns_nfo_data(self, monkeypatch):
        """获取电视剧详情返回 NFO 格式数据"""
        monkeypatch.setattr(tmdb_client, "api_key", "test_key")

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

        response = client.get("/api/tmdb/tv/1396", auth=("test", "test"))

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Breaking Bad"
        assert data["nfo_type"] == "tvshow"
        assert data["year"] == "2008"


class TestTMDBEpisodeEndpoint:
    """Tests for /api/tmdb/tv/{tmdb_id}/season/{season}/episode/{episode} endpoint."""

    @responses.activate
    def test_get_episode_returns_nfo_data(self, monkeypatch):
        """获取单集详情返回 NFO 格式数据"""
        monkeypatch.setattr(tmdb_client, "api_key", "test_key")

        responses.add(
            responses.GET,
            "https://api.themoviedb.org/3/tv/1396/season/1/episode/1",
            json={
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
                    "cast": [],
                    "crew": []
                }
            },
            status=200
        )

        response = client.get("/api/tmdb/tv/1396/season/1/episode/1", auth=("test", "test"))

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Pilot"
        assert data["nfo_type"] == "episodedetails"
        assert data["season"] == "1"
        assert data["episode"] == "1"


class TestTMDBConfigEndpoint:
    """Tests for /api/tmdb/config endpoint."""

    def test_config_updates_api_key(self):
        """配置接口更新 API Key"""
        response = client.post(
            "/api/tmdb/config",
            json={"api_key": "new_test_key"},
            auth=("test", "test")
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "已更新" in data["message"]

    def test_config_with_empty_key(self):
        """空 API Key 也能更新（用户选择不使用 TMDB）"""
        response = client.post(
            "/api/tmdb/config",
            json={"api_key": ""},
            auth=("test", "test")
        )

        assert response.status_code == 200
