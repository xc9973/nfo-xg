"""Tests for thread-safety in BatchProcessor."""
import pytest
import threading
from pathlib import Path
from nfo_editor.batch.processor import BatchProcessor
from nfo_editor.batch import TaskManager, TaskStatus, BatchTask
from nfo_editor.utils.xml_parser import XmlParser
from datetime import datetime


def test_concurrent_apply_increments_correctly(tmp_path):
    """Concurrent file processing should increment counters correctly."""
    # Create test files
    for i in range(10):
        nfo_path = tmp_path / f"movie{i}.nfo"
        nfo_path.write_text(
            f'<?xml version="1.0" encoding="UTF-8"?><movie><title>Movie {i}</title></movie>',
            encoding="utf-8"
        )

    manager = TaskManager()
    # Clean up any existing tasks to avoid hitting max concurrent limit
    for task in manager.list_all():
        manager.delete(task.task_id)

    # Create task with files
    preview_files = [
        {"path": str(tmp_path / f"movie{i}.nfo"), "filename": f"movie{i}.nfo", "title": f"Movie {i}"}
        for i in range(10)
    ]

    task = BatchTask(
        task_id="concurrent-test",
        status=TaskStatus.PENDING,
        total_files=10,
        processed_files=0,
        success_count=0,
        failed_count=0,
        errors=[],
        created_at=datetime.now(),
        field="studio",
        value="TestStudio",
        mode="overwrite",
        directory=str(tmp_path),
        preview_files=preview_files
    )
    manager.add(task)

    processor = BatchProcessor(XmlParser())

    # Apply (uses thread pool internally)
    updated_task = processor.apply(
        task_id="concurrent-test",
        files=preview_files,
        field="studio",
        value="TestStudio",
        mode="overwrite"
    )

    # Verify counts are accurate
    assert updated_task.success_count == 10
    assert updated_task.failed_count == 0
    assert updated_task.processed_files == 10
