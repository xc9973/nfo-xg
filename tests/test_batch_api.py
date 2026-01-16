"""Tests for batch editing API endpoints."""
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from web.app import app


client = TestClient(app)


def _create_nfo(path: Path, title: str, studio: str = "Old Studio", genre: str = "Action") -> None:
    path.write_text(
        f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<movie>
    <title>{title}</title>
    <studio>{studio}</studio>
    <genre>{genre}</genre>
</movie>""",
        encoding="utf-8"
    )


class TestBatchPreviewEndpoint:
    """Tests for /api/batch/preview endpoint."""

    def test_preview_returns_task_and_samples(self, tmp_path):
        """Preview returns task_id, total_files, and sample_files with new_value."""
        _create_nfo(tmp_path / "movie1.nfo", "Movie 1")
        _create_nfo(tmp_path / "movie2.nfo", "Movie 2")

        response = client.post(
            "/api/batch/preview",
            json={
                "directory": str(tmp_path),
                "field": "studio",
                "value": "Disney",
                "mode": "overwrite"
            },
            auth=("test", "test")
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 2
        assert len(data["sample_files"]) == 2
        assert data["sample_files"][0]["new_value"] == "Disney"

    def test_preview_invalid_directory(self, tmp_path):
        """Preview returns 404 for missing directory."""
        missing_dir = tmp_path / "missing"

        response = client.post(
            "/api/batch/preview",
            json={
                "directory": str(missing_dir),
                "field": "studio",
                "value": "Disney",
                "mode": "overwrite"
            },
            auth=("test", "test")
        )

        assert response.status_code == 404


class TestBatchApplyEndpoint:
    """Tests for /api/batch/apply endpoint."""

    def test_apply_starts_task(self, tmp_path):
        """Apply returns running status for valid task."""
        _create_nfo(tmp_path / "movie1.nfo", "Movie 1")

        preview = client.post(
            "/api/batch/preview",
            json={
                "directory": str(tmp_path),
                "field": "studio",
                "value": "Disney",
                "mode": "overwrite"
            },
            auth=("test", "test")
        )
        task_id = preview.json()["task_id"]

        response = client.post(
            "/api/batch/apply",
            json={"task_id": task_id, "confirmed": True},
            auth=("test", "test")
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "running"

    def test_apply_invalid_task(self):
        """Apply returns 404 for invalid task id."""
        response = client.post(
            "/api/batch/apply",
            json={"task_id": "missing-task", "confirmed": True},
            auth=("test", "test")
        )

        assert response.status_code == 404


class TestBatchStatusEndpoint:
    """Tests for /api/batch/status endpoint."""

    def test_status_returns_task(self, tmp_path):
        """Status returns current task details."""
        _create_nfo(tmp_path / "movie1.nfo", "Movie 1")

        preview = client.post(
            "/api/batch/preview",
            json={
                "directory": str(tmp_path),
                "field": "studio",
                "value": "Disney",
                "mode": "overwrite"
            },
            auth=("test", "test")
        )
        task_id = preview.json()["task_id"]

        response = client.get(
            f"/api/batch/status/{task_id}",
            auth=("test", "test")
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "pending"
        assert data["total"] == 1

    def test_status_invalid_task(self):
        """Status returns 404 for invalid task id."""
        response = client.get(
            "/api/batch/status/missing-task",
            auth=("test", "test")
        )

        assert response.status_code == 404


class TestScanDepthLimit:
    """Tests for recursion depth limit in _scan_nfo_files."""

    def test_scan_depth_limit_raises_error(self, tmp_path):
        """Deeply nested directories should raise RuntimeError."""
        from nfo_editor.batch.processor import BatchProcessor
        from nfo_editor.utils.xml_parser import XmlParser

        processor = BatchProcessor(XmlParser())

        # Create deeply nested structure (deeper than MAX_SCAN_DEPTH)
        current = tmp_path
        for i in range(60):  # Exceeds MAX_SCAN_DEPTH of 50
            current = current / f"level_{i}"
            current.mkdir()

        # Add an NFO file at the bottom
        (current / "movie.nfo").write_text(
            '<?xml version="1.0" encoding="UTF-8"?><movie><title>Deep Movie</title></movie>',
            encoding="utf-8"
        )

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Maximum scan depth"):
            processor.preview(str(tmp_path), "studio", "TestStudio")


class TestFileCountLimit:
    """Tests for file count limit validation."""

    def test_max_files_limit_enforced(self, tmp_path):
        """Should raise RuntimeError when file count exceeds limit."""
        from nfo_editor.batch.processor import BatchProcessor, MAX_FILES_PER_BATCH
        from nfo_editor.utils.xml_parser import XmlParser
        from unittest.mock import patch, MagicMock

        processor = BatchProcessor(XmlParser())

        # Mock _scan_nfo_files to return more files than allowed
        mock_files = [MagicMock(name=f"file{i}.nfo") for i in range(MAX_FILES_PER_BATCH + 100)]

        with patch.object(processor, '_scan_nfo_files', return_value=mock_files):
            with pytest.raises(RuntimeError, match="Too many files"):
                processor.preview(str(tmp_path), "studio", "Test")

    def test_max_files_limit_enforced_in_apply(self, tmp_path):
        """Should raise RuntimeError when file count exceeds limit in apply."""
        import uuid
        from datetime import datetime
        from nfo_editor.batch.processor import BatchProcessor, MAX_FILES_PER_BATCH
        from nfo_editor.batch.models import BatchTask, TaskStatus
        from nfo_editor.utils.xml_parser import XmlParser

        processor = BatchProcessor(XmlParser())

        # Create a task
        task = BatchTask(
            task_id=str(uuid.uuid4()),
            status=TaskStatus.PENDING,
            total_files=0,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="studio",
            value="TestStudio",
            mode="overwrite",
            directory=str(tmp_path)
        )
        processor.task_manager.add(task)

        # Create mock files exceeding limit
        mock_files = [{"path": f"/fake/path/file{i}.nfo", "filename": f"file{i}.nfo"}
                      for i in range(MAX_FILES_PER_BATCH + 100)]

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Too many files"):
            processor.apply(task.task_id, mock_files, "studio", "TestStudio", "overwrite")

    def test_max_files_limit_api_returns_413(self, tmp_path):
        """API should return 413 when file count exceeds limit."""
        from nfo_editor.batch.processor import MAX_FILES_PER_BATCH
        from nfo_editor.batch.processor import BatchProcessor
        from nfo_editor.utils.xml_parser import XmlParser
        from unittest.mock import patch, MagicMock
        from web.app import batch_processor

        # Mock _scan_nfo_files to return more files than allowed
        mock_files = [MagicMock(name=f"file{i}.nfo") for i in range(MAX_FILES_PER_BATCH + 100)]

        with patch.object(batch_processor, '_scan_nfo_files', return_value=mock_files):
            response = client.post(
                "/api/batch/preview",
                json={
                    "directory": str(tmp_path),
                    "field": "studio",
                    "value": "Disney",
                    "mode": "overwrite"
                },
                auth=("test", "test")
            )

            assert response.status_code == 413
            assert "Too many files" in response.json()["detail"]


class TestAppendModePreviewApplyConsistency:
    """Tests for append mode consistency between preview and apply."""

    def test_append_mode_preview_apply_consistency(self, tmp_path):
        """Preview and apply should have same behavior for append mode."""
        from nfo_editor.batch.processor import BatchProcessor
        from nfo_editor.batch import TaskManager, TaskStatus, BatchTask
        from nfo_editor.utils.xml_parser import XmlParser
        from datetime import datetime

        # Create NFO with existing genre
        nfo_path = tmp_path / "movie.nfo"
        nfo_path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?><movie><title>Test</title><genre>Action</genre></movie>',
            encoding="utf-8"
        )

        processor = BatchProcessor(XmlParser())

        # Preview append mode
        preview_result = processor.preview(str(tmp_path), "genre", "Action", "append")

        # Get the previewed new_value
        preview_new_value = preview_result[0]["new_value"]

        # Apply with same parameters
        manager = TaskManager()
        task = BatchTask(
            task_id="append-test",
            status=TaskStatus.PENDING,
            total_files=1,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="genre",
            value="Action",
            mode="append",
            directory=str(tmp_path),
            preview_files=preview_result
        )
        manager.add(task)

        processor.apply("append-test", preview_result, "genre", "Action", "append")

        # Read result
        data = processor.parser.parse(str(nfo_path))

        # The preview showed what it would do, apply should match
        # Preview and apply are now consistent: both allow appending duplicate values
        # This test verifies that what preview shows is exactly what apply does
        assert ", ".join(data.genres) == preview_new_value
