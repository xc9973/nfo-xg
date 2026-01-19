"""TMDB Data Mapper for converting API responses to data models."""
from typing import Dict, List
import logging

from tmdb_search.models import (
    Actor,
    TMDBMovieData,
    TMDBTVShowData,
    TMDBEpisodeData,
)
from tmdb_search.client import TMDBClient

logger = logging.getLogger(__name__)


class TMDBMapper:
    """TMDB 数据映射器"""

    def __init__(self, tmdb_client: TMDBClient):
        """初始化映射器

        Args:
            tmdb_client: TMDB API 客户端
        """
        self.client = tmdb_client

    def _get_year(self, date_str: str) -> str:
        """从日期字符串提取年份"""
        if not date_str:
            return ""
        try:
            return date_str.split("-")[0]
        except IndexError:
            return ""

    def _get_runtime(self, runtime: int) -> str:
        """格式化运行时长"""
        return str(runtime) if runtime else ""

    def _get_rating(self, vote_average: float) -> str:
        """格式化评分"""
        return f"{vote_average:.1f}" if vote_average else ""

    def _get_genres(self, genres_data: List[Dict]) -> List[str]:
        """提取类型列表"""
        return [g.get("name", "") for g in genres_data if g.get("name")]

    def _get_directors(self, crew_data: List[Dict]) -> List[str]:
        """提取导演列表"""
        return [
            c.get("name", "")
            for c in crew_data
            if c.get("job") == "Director" and c.get("name")
        ]

    def _get_actors(self, cast_data: List[Dict]) -> List[Actor]:
        """提取演员列表"""
        actors = []
        for i, c in enumerate(cast_data):
            if not c.get("name"):
                continue
            actors.append(
                Actor(
                    name=c.get("name", ""),
                    role=c.get("character", ""),
                    thumb=self.client.get_image_url(c.get("profile_path"), "w200"),
                    order=i,
                )
            )
        return actors

    def _get_studio(self, production_companies: List[Dict]) -> str:
        """提取第一个制片公司"""
        if not production_companies:
            return ""
        return production_companies[0].get("name", "")

    def map_movie(self, tmdb_data: Dict) -> TMDBMovieData:
        """映射电影数据

        Args:
            tmdb_data: TMDB 电影详情数据

        Returns:
            TMDBMovieData 对象
        """
        credits = tmdb_data.get("credits", {})

        return TMDBMovieData(
            title=tmdb_data.get("title", ""),
            original_title=tmdb_data.get("original_title", ""),
            year=self._get_year(tmdb_data.get("release_date")),
            plot=tmdb_data.get("overview", ""),
            runtime=self._get_runtime(tmdb_data.get("runtime")),
            genres=self._get_genres(tmdb_data.get("genres", [])),
            directors=self._get_directors(credits.get("crew", [])),
            actors=self._get_actors(credits.get("cast", [])),
            studio=self._get_studio(tmdb_data.get("production_companies", [])),
            rating=self._get_rating(tmdb_data.get("vote_average")),
            poster=self.client.get_image_url(tmdb_data.get("poster_path")),
            fanart=self.client.get_image_url(tmdb_data.get("backdrop_path")),
            aired=tmdb_data.get("release_date", ""),
        )

    def map_tv_show(self, tmdb_data: Dict) -> TMDBTVShowData:
        """映射电视剧数据

        Args:
            tmdb_data: TMDB 电视剧详情数据

        Returns:
            TMDBTVShowData 对象
        """
        credits = tmdb_data.get("credits", {})

        return TMDBTVShowData(
            title=tmdb_data.get("name", ""),
            original_title=tmdb_data.get("original_name", ""),
            year=self._get_year(tmdb_data.get("first_air_date")),
            plot=tmdb_data.get("overview", ""),
            runtime=self._get_runtime(
                next(iter(tmdb_data.get("episode_run_time", [])), None)
            ),
            genres=self._get_genres(tmdb_data.get("genres", [])),
            directors=self._get_directors(credits.get("crew", [])),
            actors=self._get_actors(credits.get("cast", [])),
            studio=self._get_studio(tmdb_data.get("production_companies", [])),
            rating=self._get_rating(tmdb_data.get("vote_average")),
            poster=self.client.get_image_url(tmdb_data.get("poster_path")),
            fanart=self.client.get_image_url(tmdb_data.get("backdrop_path")),
            aired=tmdb_data.get("first_air_date", ""),
        )

    def map_episode(self, tmdb_data: Dict) -> TMDBEpisodeData:
        """映射单集数据

        Args:
            tmdb_data: TMDB 单集详情数据

        Returns:
            TMDBEpisodeData 对象
        """
        credits = tmdb_data.get("credits", {})

        return TMDBEpisodeData(
            title=tmdb_data.get("name", ""),
            original_title=tmdb_data.get("name", ""),  # 单集通常没有独立的原标题
            year=self._get_year(tmdb_data.get("air_date")),
            plot=tmdb_data.get("overview", ""),
            runtime=self._get_runtime(tmdb_data.get("runtime")),
            genres=[],  # 单集通常不单独设置类型
            directors=self._get_directors(credits.get("crew", [])),
            actors=self._get_actors(credits.get("cast", [])),
            studio="",  # 单集通常不单独设置工作室
            rating=self._get_rating(tmdb_data.get("vote_average")),
            poster=self.client.get_image_url(tmdb_data.get("still_path")),
            fanart="",  # 单集通常没有 fanart
            season=str(tmdb_data.get("season_number", "")),
            episode=str(tmdb_data.get("episode_number", "")),
            aired=tmdb_data.get("air_date", ""),
        )
