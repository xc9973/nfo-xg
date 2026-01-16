"""Tests for Preview API endpoints."""
import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from web.app import app, parser

client = TestClient(app)


class TestPreviewEndpoint:
    """Tests for /api/preview endpoint."""

    def test_preview_returns_lightweight_data(self, tmp_path):
        """预览返回轻量级数据"""
        # 创建测试 NFO 文件
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Test Movie</title>
    <originaltitle>Original Title</originaltitle>
    <year>2024</year>
    <rating>8.5</rating>
    <genre>Action</genre>
    <genre>Sci-Fi</genre>
    <runtime>120</runtime>
    <poster>poster.jpg</poster>
</movie>"""

        nfo_file = tmp_path / "test.nfo"
        nfo_file.write_text(nfo_content)

        response = client.post(
            "/api/preview",
            json={"paths": [str(nfo_file)]},
            auth=("test", "test")
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

        result = data["results"][0]
        assert result["success"] is True
        assert result["path"] == str(nfo_file)
        assert result["preview"]["title"] == "Test Movie"
        assert result["preview"]["year"] == "2024"
        assert len(result["preview"]["genres"]) == 2  # 限制类型数量

    def test_preview_with_multiple_files(self, tmp_path):
        """批量预览多个文件"""
        # 创建多个测试文件
        files = []
        for i in range(3):
            nfo_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Movie {i}</title>
    <year>202{i}</year>
    <rating>7.{i}</rating>
</movie>"""
            nfo_file = tmp_path / f"test{i}.nfo"
            nfo_file.write_text(nfo_content)
            files.append(str(nfo_file))

        response = client.post(
            "/api/preview",
            json={"paths": files},
            auth=("test", "test")
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3

        for i, result in enumerate(data["results"]):
            assert result["success"] is True
            assert result["preview"]["title"] == f"Movie {i}"

    def test_preview_with_nonexistent_file(self):
        """不存在的文件返回错误"""
        response = client.post(
            "/api/preview",
            json={"paths": ["/nonexistent/file.nfo"]},
            auth=("test", "test")
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

        result = data["results"][0]
        assert result["success"] is False
        assert result["error"] is not None

    def test_preview_with_invalid_nfo(self, tmp_path):
        """无效的 NFO 文件返回错误"""
        invalid_file = tmp_path / "invalid.nfo"
        invalid_file.write_text("not valid xml")

        response = client.post(
            "/api/preview",
            json={"paths": [str(invalid_file)]},
            auth=("test", "test")
        )

        assert response.status_code == 200
        data = response.json()

        result = data["results"][0]
        assert result["success"] is False

    def test_preview_with_empty_paths(self):
        """空路径列表返回空结果"""
        response = client.post(
            "/api/preview",
            json={"paths": []},
            auth=("test", "test")
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
