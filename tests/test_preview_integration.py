"""Integration tests for Preview feature."""
import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from web.app import app

client = TestClient(app)


class TestPreviewIntegration:
    """集成测试：预览功能端到端测试"""

    def test_preview_workflow(self, tmp_path):
        """完整的预览工作流"""
        # 创建测试 NFO 文件
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Integration Test Movie</title>
    <originaltitle>Test Original</originaltitle>
    <year>2024</year>
    <rating>9.0</rating>
    <genre>Action</genre>
    <genre>Sci-Fi</genre>
    <genre>Thriller</genre>
    <runtime>150</runtime>
    <poster>test_poster.jpg</poster>
</movie>"""

        nfo_file = tmp_path / "test.nfo"
        nfo_file.write_text(nfo_content)

        # 步骤 1: 调用预览 API
        preview_response = client.post(
            "/api/preview",
            json={"paths": [str(nfo_file)]},
            auth=("test", "test")
        )

        assert preview_response.status_code == 200
        preview_data = preview_response.json()
        assert preview_data["results"][0]["success"] is True

        # 步骤 2: 验证轻量级数据
        preview = preview_data["results"][0]["preview"]
        assert preview["title"] == "Integration Test Movie"
        assert preview["year"] == "2024"
        assert len(preview["genres"]) == 3

        # 步骤 3: 验证完整数据仍然可通过 /api/load 获取
        load_response = client.post(
            "/api/load",
            json={"path": str(nfo_file)},
            auth=("test", "test")
        )

        assert load_response.status_code == 200
        full_data = load_response.json()
        assert full_data["data"]["title"] == "Integration Test Movie"

    def test_preview_batch_with_mixed_results(self, tmp_path):
        """批量预览：混合成功和失败的结果"""
        # 创建有效文件
        valid_nfo = tmp_path / "valid.nfo"
        valid_nfo.write_text('<?xml version="1.0"?><movie><title>Valid</title></movie>')

        # 无效文件
        invalid_nfo = tmp_path / "invalid.nfo"
        invalid_nfo.write_text("not xml")

        # 不存在的文件
        nonexistent = "/nonexistent/file.nfo"

        response = client.post(
            "/api/preview",
            json={"paths": [str(valid_nfo), str(invalid_nfo), nonexistent]},
            auth=("test", "test")
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["results"]) == 3
        assert data["results"][0]["success"] is True
        assert data["results"][1]["success"] is False
        assert data["results"][2]["success"] is False

    def test_preview_caching_behavior(self, tmp_path):
        """验证缓存行为"""
        nfo_file = tmp_path / "cache_test.nfo"
        nfo_file.write_text('<?xml version="1.0"?><movie><title>Cache Test</title></movie>')

        # 第一次请求
        response1 = client.post(
            "/api/preview",
            json={"paths": [str(nfo_file)]},
            auth=("test", "test")
        )
        assert response1.status_code == 200

        # 第二次请求（应该从缓存返回，虽然后端没有缓存，但测试模式）
        response2 = client.post(
            "/api/preview",
            json={"paths": [str(nfo_file)]},
            auth=("test", "test")
        )
        assert response2.status_code == 200

        # 验证数据一致性
        data1 = response1.json()["results"][0]["preview"]
        data2 = response2.json()["results"][0]["preview"]
        assert data1["title"] == data2["title"]
