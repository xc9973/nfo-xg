"""TMDB API Client for NFO Editor."""
import os
from typing import List, Dict, Optional
import logging

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


class TMDBClient:
    """TMDB API 客户端"""

    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

    def __init__(self, api_key: Optional[str] = None):
        """初始化 TMDB 客户端

        Args:
            api_key: TMDB API Key (可选，优先使用环境变量 TMDB_API_KEY)
        """
        self.api_key = api_key or os.environ.get("TMDB_API_KEY")
        if not self.api_key:
            logger.warning("TMDB API Key not found. Some functionality may be limited.")
        self.session = requests.Session()

    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """带重试的 API 请求"""
        if not self.api_key:
            raise ValueError("TMDB API Key is missing")

        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params["api_key"] = self.api_key

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Invalid TMDB API Key")
                raise ValueError("Invalid TMDB API Key") from e
            elif e.response.status_code == 404:
                logger.info(f"Resource not found: {url}")
                raise
            elif e.response.status_code == 429:
                # Rate limit - retry with exponential backoff
                logger.warning("TMDB API rate limit exceeded, retrying...")
                return self._retry_request(url, params)
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"TMDB API request failed: {e}")
            return self._retry_request(url, params)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _retry_request(self, url: str, params: Dict) -> Dict:
        """实际执行重试的请求"""
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def search_multi(self, query: str, page: int = 1) -> Dict:
        """搜索电影和电视剧

        Args:
            query: 搜索关键词
            page: 页码 (默认 1)

        Returns:
            搜索结果字典，包含 results 列表
        """
        params = {"query": query, "page": page, "include_adult": False}
        return self._request("/search/multi", params)

    def get_movie_details(self, tmdb_id: int) -> Dict:
        """获取电影详细信息

        Args:
            tmdb_id: TMDB 电影 ID

        Returns:
            电影详细信息字典
        """
        params = {
            "append_to_response": "credits,images",
            "language": "zh-CN,en-US",
        }
        return self._request(f"/movie/{tmdb_id}", params)

    def get_tv_details(self, tmdb_id: int) -> Dict:
        """获取电视剧详细信息

        Args:
            tmdb_id: TMDB 电视剧 ID

        Returns:
            电视剧详细信息字典
        """
        params = {
            "append_to_response": "credits,images",
            "language": "zh-CN,en-US",
        }
        return self._request(f"/tv/{tmdb_id}", params)

    def get_tv_episode_details(self, tmdb_id: int, season: int, episode: int) -> Dict:
        """获取单集详细信息

        Args:
            tmdb_id: TMDB 电视剧 ID
            season: 季数
            episode: 集数

        Returns:
            单集详细信息字典
        """
        params = {
            "append_to_response": "credits,images",
            "language": "zh-CN,en-US",
        }
        return self._request(f"/tv/{tmdb_id}/season/{season}/episode/{episode}", params)

    def get_image_url(self, path: str, size: str = "original") -> str:
        """获取完整图片 URL

        Args:
            path: 图片路径 (e.g. "/abc.jpg")
            size: 图片尺寸 (默认 "original", 可选 "w200", "w500" 等)

        Returns:
            完整图片 URL
        """
        if not path:
            return ""
        return f"{self.IMAGE_BASE_URL}/{size}{path}"
