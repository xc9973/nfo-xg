"""Tests for TaskManager singleton and task management."""
import pytest
import time
import threading
from datetime import datetime, timedelta

from nfo_editor.batch import TaskManager, TaskStatus, BatchTask


class TestTaskManagerSingleton:
    """Test TaskManager singleton pattern."""

    def test_singleton_returns_same_instance(self):
        """Test that TaskManager returns the same instance."""
        manager1 = TaskManager()
        manager2 = TaskManager()
        assert manager1 is manager2

    def test_singleton_thread_safety(self):
        """Test that TaskManager is thread-safe."""
        instances = []
        lock = threading.Lock()

        def get_instance():
            instance = TaskManager()
            with lock:
                instances.append(instance)

        threads = [
            threading.Thread(target=get_instance) for _ in range(10)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All instances should be the same
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance

    def test_singleton_state_shared(self):
        """Test that state is shared across all references."""
        manager1 = TaskManager()
        manager2 = TaskManager()

        # Clean up any existing tasks to avoid hitting max concurrent limit
        for task in manager1.list_all():
            manager1.delete(task.task_id)

        task = BatchTask(
            task_id="test-shared-state",
            status=TaskStatus.PENDING,
            total_files=10,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="studio",
            value="Disney",
            mode="overwrite",
            directory="/movies"
        )

        manager1.add(task)

        # Should be accessible from manager2
        retrieved_task = manager2.get("test-shared-state")
        assert retrieved_task is not None
        assert retrieved_task.task_id == "test-shared-state"


class TestTaskManagerAdd:
    """Test TaskManager.add() method."""

    def test_add_task(self):
        """Test adding a task to the manager."""
        manager = TaskManager()

        # Clean up any existing tasks to avoid hitting max concurrent limit
        for task in manager.list_all():
            manager.delete(task.task_id)

        task = BatchTask(
            task_id="test-add-1",
            status=TaskStatus.PENDING,
            total_files=5,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="genre",
            value="Action",
            mode="append",
            directory="/movies"
        )

        manager.add(task)

        retrieved = manager.get("test-add-1")
        assert retrieved is not None
        assert retrieved.task_id == "test-add-1"
        assert retrieved.status == TaskStatus.PENDING

    def test_add_multiple_tasks(self):
        """Test adding multiple tasks."""
        manager = TaskManager()

        # Clean up first to ensure fresh state
        for task in manager.list_all():
            manager.delete(task.task_id)

        tasks = [
            BatchTask(
                task_id=f"task-{i}",
                status=TaskStatus.PENDING,
                total_files=i + 1,
                processed_files=0,
                success_count=0,
                failed_count=0,
                errors=[],
                created_at=datetime.now(),
                field="studio",
                value=f"Studio {i}",
                mode="overwrite",
                directory="/movies"
            )
            for i in range(5)
        ]

        for task in tasks:
            manager.add(task)

        all_tasks = manager.list_all()
        assert len(all_tasks) == 5

    def test_add_overwrites_existing_task(self):
        """Test that adding a task with same ID overwrites the old one."""
        manager = TaskManager()

        # Clean up first to ensure fresh state
        for task in manager.list_all():
            manager.delete(task.task_id)

        task1 = BatchTask(
            task_id="test-overwrite",
            status=TaskStatus.PENDING,
            total_files=10,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="studio",
            value="Original",
            mode="overwrite",
            directory="/movies"
        )

        task2 = BatchTask(
            task_id="test-overwrite",
            status=TaskStatus.RUNNING,
            total_files=20,
            processed_files=5,
            success_count=5,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="studio",
            value="Updated",
            mode="overwrite",
            directory="/movies"
        )

        manager.add(task1)
        manager.add(task2)

        retrieved = manager.get("test-overwrite")
        assert retrieved.status == TaskStatus.RUNNING
        assert retrieved.total_files == 20
        assert retrieved.value == "Updated"


class TestTaskManagerGet:
    """Test TaskManager.get() method."""

    def test_get_existing_task(self):
        """Test getting an existing task."""
        manager = TaskManager()

        # Clean up first to ensure fresh state
        for task in manager.list_all():
            manager.delete(task.task_id)

        task = BatchTask(
            task_id="test-get-1",
            status=TaskStatus.COMPLETED,
            total_files=10,
            processed_files=10,
            success_count=10,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="director",
            value="Nolan",
            mode="overwrite",
            directory="/movies"
        )

        manager.add(task)

        retrieved = manager.get("test-get-1")
        assert retrieved is not None
        assert retrieved.task_id == "test-get-1"
        assert retrieved.status == TaskStatus.COMPLETED
        assert retrieved.success_count == 10

    def test_get_nonexistent_task(self):
        """Test getting a task that doesn't exist."""
        manager = TaskManager()

        retrieved = manager.get("nonexistent-task")
        assert retrieved is None

    def test_get_returns_correct_task_type(self):
        """Test that get returns a BatchTask instance."""
        manager = TaskManager()

        # Clean up first to ensure fresh state
        for task in manager.list_all():
            manager.delete(task.task_id)

        task = BatchTask(
            task_id="test-type",
            status=TaskStatus.PENDING,
            total_files=1,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="studio",
            value="Test",
            mode="overwrite",
            directory="/movies"
        )

        manager.add(task)

        retrieved = manager.get("test-type")
        assert isinstance(retrieved, BatchTask)
        assert hasattr(retrieved, 'progress')


class TestTaskManagerDelete:
    """Test TaskManager.delete() method."""

    def test_delete_existing_task(self):
        """Test deleting an existing task."""
        manager = TaskManager()

        # Clean up first to ensure fresh state
        for task in manager.list_all():
            manager.delete(task.task_id)

        task = BatchTask(
            task_id="test-delete-1",
            status=TaskStatus.PENDING,
            total_files=5,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="genre",
            value="Horror",
            mode="overwrite",
            directory="/movies"
        )

        manager.add(task)
        result = manager.delete("test-delete-1")

        assert result is True
        assert manager.get("test-delete-1") is None

    def test_delete_nonexistent_task(self):
        """Test deleting a task that doesn't exist."""
        manager = TaskManager()

        result = manager.delete("nonexistent-task")
        assert result is False

    def test_delete_removes_from_list_all(self):
        """Test that deleted tasks are not in list_all()."""
        manager = TaskManager()

        # Clean up first to ensure fresh state
        for task in manager.list_all():
            manager.delete(task.task_id)

        tasks = [
            BatchTask(
                task_id=f"task-{i}",
                status=TaskStatus.PENDING,
                total_files=i + 1,
                processed_files=0,
                success_count=0,
                failed_count=0,
                errors=[],
                created_at=datetime.now(),
                field="studio",
                value=f"Studio {i}",
                mode="overwrite",
                directory="/movies"
            )
            for i in range(5)
        ]

        for task in tasks:
            manager.add(task)

        manager.delete("task-2")

        all_tasks = manager.list_all()
        assert len(all_tasks) == 4
        task_ids = [t.task_id for t in all_tasks]
        assert "task-2" not in task_ids


class TestTaskManagerListAll:
    """Test TaskManager.list_all() method."""

    def test_list_all_empty(self):
        """Test list_all when manager is empty."""
        manager = TaskManager()

        # Clean up any existing tasks from other tests
        for task in manager.list_all():
            manager.delete(task.task_id)

        all_tasks = manager.list_all()
        assert all_tasks == []

    def test_list_all_returns_all_tasks(self):
        """Test that list_all returns all tasks."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        tasks = [
            BatchTask(
                task_id=f"list-task-{i}",
                status=TaskStatus.PENDING,
                total_files=i + 1,
                processed_files=0,
                success_count=0,
                failed_count=0,
                errors=[],
                created_at=datetime.now(),
                field="genre",
                value=f"Genre {i}",
                mode="append",
                directory="/movies"
            )
            for i in range(3)
        ]

        for task in tasks:
            manager.add(task)

        all_tasks = manager.list_all()
        assert len(all_tasks) == 3

        task_ids = {t.task_id for t in all_tasks}
        assert task_ids == {"list-task-0", "list-task-1", "list-task-2"}

    def test_list_all_returns_list_of_batch_tasks(self):
        """Test that list_all returns list of BatchTask instances."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        task = BatchTask(
            task_id="test-list-type",
            status=TaskStatus.RUNNING,
            total_files=10,
            processed_files=5,
            success_count=4,
            failed_count=1,
            errors=["Error"],
            created_at=datetime.now(),
            field="studio",
            value="Test",
            mode="overwrite",
            directory="/movies"
        )

        manager.add(task)

        all_tasks = manager.list_all()
        assert len(all_tasks) == 1
        assert isinstance(all_tasks[0], BatchTask)
        assert all_tasks[0].task_id == "test-list-type"


class TestTaskManagerCleanupExpired:
    """Test TaskManager.cleanup_expired() method."""

    def test_cleanup_expired_removes_old_tasks(self):
        """Test that cleanup removes expired tasks."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        old_time = datetime.now() - timedelta(seconds=2000)  # Older than 30 min
        recent_time = datetime.now() - timedelta(seconds=100)  # Recent

        old_task = BatchTask(
            task_id="old-task",
            status=TaskStatus.COMPLETED,
            total_files=10,
            processed_files=10,
            success_count=10,
            failed_count=0,
            errors=[],
            created_at=old_time,
            field="studio",
            value="Old",
            mode="overwrite",
            directory="/movies"
        )

        recent_task = BatchTask(
            task_id="recent-task",
            status=TaskStatus.PENDING,
            total_files=5,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=recent_time,
            field="studio",
            value="Recent",
            mode="overwrite",
            directory="/movies"
        )

        manager.add(old_task)
        manager.add(recent_task)

        cleaned_count = manager.cleanup_expired()

        assert cleaned_count == 1
        assert manager.get("old-task") is None
        assert manager.get("recent-task") is not None

    def test_cleanup_expired_returns_zero_when_no_expired(self):
        """Test cleanup returns 0 when no tasks are expired."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        recent_time = datetime.now() - timedelta(seconds=100)

        task = BatchTask(
            task_id="recent-task",
            status=TaskStatus.PENDING,
            total_files=5,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=recent_time,
            field="genre",
            value="Action",
            mode="append",
            directory="/movies"
        )

        manager.add(task)

        cleaned_count = manager.cleanup_expired()

        assert cleaned_count == 0
        assert manager.get("recent-task") is not None

    def test_cleanup_expired_with_multiple_expired(self):
        """Test cleanup with multiple expired tasks."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        old_time = datetime.now() - timedelta(seconds=2000)
        recent_time = datetime.now() - timedelta(seconds=100)

        # Add 3 old tasks and 2 recent tasks
        for i in range(3):
            task = BatchTask(
                task_id=f"old-task-{i}",
                status=TaskStatus.COMPLETED,
                total_files=10,
                processed_files=10,
                success_count=10,
                failed_count=0,
                errors=[],
                created_at=old_time,
                field="studio",
                value=f"Old {i}",
                mode="overwrite",
                directory="/movies"
            )
            manager.add(task)

        for i in range(2):
            task = BatchTask(
                task_id=f"recent-task-{i}",
                status=TaskStatus.PENDING,
                total_files=5,
                processed_files=0,
                success_count=0,
                failed_count=0,
                errors=[],
                created_at=recent_time,
                field="genre",
                value=f"Recent {i}",
                mode="append",
                directory="/movies"
            )
            manager.add(task)

        cleaned_count = manager.cleanup_expired()

        assert cleaned_count == 3

        # Verify old tasks are gone
        for i in range(3):
            assert manager.get(f"old-task-{i}") is None

        # Verify recent tasks remain
        for i in range(2):
            assert manager.get(f"recent-task-{i}") is not None

    def test_cleanup_expired_empty_manager(self):
        """Test cleanup on empty manager."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        cleaned_count = manager.cleanup_expired()

        assert cleaned_count == 0

    def test_cleanup_expired_boundary_case(self):
        """Test cleanup at exactly TTL boundary."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        # Task exactly at TTL boundary (should be cleaned up)
        boundary_time = datetime.now() - timedelta(seconds=1800)

        task = BatchTask(
            task_id="boundary-task",
            status=TaskStatus.COMPLETED,
            total_files=10,
            processed_files=10,
            success_count=10,
            failed_count=0,
            errors=[],
            created_at=boundary_time,
            field="studio",
            value="Boundary",
            mode="overwrite",
            directory="/movies"
        )

        manager.add(task)
        cleaned_count = manager.cleanup_expired()

        # Task should be cleaned up (created_at < expired_threshold)
        assert cleaned_count == 1
        assert manager.get("boundary-task") is None


class TestTaskManagerThreadSafety:
    """Test TaskManager thread safety."""

    def test_concurrent_add_operations(self):
        """Test that concurrent add operations are safe."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        results = {"success": 0, "error": 0}
        lock = threading.Lock()

        def add_task(task_num):
            try:
                task = BatchTask(
                    task_id=f"concurrent-task-{task_num}",
                    status=TaskStatus.PENDING,
                    total_files=task_num + 1,
                    processed_files=0,
                    success_count=0,
                    failed_count=0,
                    errors=[],
                    created_at=datetime.now(),
                    field="studio",
                    value=f"Studio {task_num}",
                    mode="overwrite",
                    directory="/movies"
                )
                manager.add(task)
                with lock:
                    results["success"] += 1
            except RuntimeError:
                # Expected when hitting max concurrent tasks limit
                with lock:
                    results["error"] += 1

        # Try to add more than MAX_CONCURRENT_TASKS
        threads = [
            threading.Thread(target=add_task, args=(i,)) for i in range(10)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have some successes and some errors due to limit
        assert results["success"] > 0
        assert results["success"] <= manager.MAX_CONCURRENT_TASKS
        all_tasks = manager.list_all()
        assert len(all_tasks) <= manager.MAX_CONCURRENT_TASKS

    def test_concurrent_get_and_delete(self):
        """Test concurrent get and delete operations."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        # Add initial tasks (within limit)
        for i in range(5):
            task = BatchTask(
                task_id=f"task-{i}",
                status=TaskStatus.PENDING,
                total_files=10,
                processed_files=0,
                success_count=0,
                failed_count=0,
                errors=[],
                created_at=datetime.now(),
                field="genre",
                value="Test",
                mode="overwrite",
                directory="/movies"
            )
            manager.add(task)

        results = {"gets": 0, "deletes": 0}
        lock = threading.Lock()

        def get_tasks():
            for _ in range(50):
                manager.get("task-1")
                with lock:
                    results["gets"] += 1

        def delete_tasks():
            for i in range(3):
                manager.delete(f"task-{i}")
                with lock:
                    results["deletes"] += 1

        threads = [
            threading.Thread(target=get_tasks),
            threading.Thread(target=delete_tasks)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert results["gets"] == 50
        assert results["deletes"] == 3


class TestTaskManagerTTL:
    """Test TaskManager TTL configuration."""

    def test_ttl_seconds_constant(self):
        """Test that TTL_SECONDS is set to 1800 (30 minutes)."""
        manager = TaskManager()
        assert manager._TTL_SECONDS == 1800

    def test_ttl_respected_in_cleanup(self):
        """Test that cleanup respects the TTL setting."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        # Create tasks at different ages
        now = datetime.now()

        # Task just created (0 seconds old)
        task_0s = BatchTask(
            task_id="task-0s",
            status=TaskStatus.PENDING,
            total_files=1,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=now - timedelta(seconds=0),
            field="studio",
            value="0s",
            mode="overwrite",
            directory="/movies"
        )

        # Task 10 minutes old (600 seconds)
        task_600s = BatchTask(
            task_id="task-600s",
            status=TaskStatus.PENDING,
            total_files=1,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=now - timedelta(seconds=600),
            field="studio",
            value="600s",
            mode="overwrite",
            directory="/movies"
        )

        # Task 20 minutes old (1200 seconds)
        task_1200s = BatchTask(
            task_id="task-1200s",
            status=TaskStatus.PENDING,
            total_files=1,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=now - timedelta(seconds=1200),
            field="studio",
            value="1200s",
            mode="overwrite",
            directory="/movies"
        )

        # Task 40 minutes old (2400 seconds) - should be expired
        task_2400s = BatchTask(
            task_id="task-2400s",
            status=TaskStatus.PENDING,
            total_files=1,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=now - timedelta(seconds=2400),
            field="studio",
            value="2400s",
            mode="overwrite",
            directory="/movies"
        )

        manager.add(task_0s)
        manager.add(task_600s)
        manager.add(task_1200s)
        manager.add(task_2400s)

        cleaned_count = manager.cleanup_expired()

        # Only the 2400s task should be cleaned up
        assert cleaned_count == 1
        assert manager.get("task-0s") is not None
        assert manager.get("task-600s") is not None
        assert manager.get("task-1200s") is not None
        assert manager.get("task-2400s") is None


class TestTaskManagerMaxConcurrentTasks:
    """Test TaskManager max concurrent tasks limit."""

    def test_max_concurrent_tasks_limit(self):
        """Test that max concurrent tasks limit is enforced."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        # Add exactly MAX_CONCURRENT_TASKS tasks
        for i in range(manager.MAX_CONCURRENT_TASKS):
            task = BatchTask(
                task_id=f"task-{i}",
                status=TaskStatus.PENDING,
                total_files=10,
                processed_files=0,
                success_count=0,
                failed_count=0,
                errors=[],
                created_at=datetime.now(),
                field="studio",
                value=f"Studio {i}",
                mode="overwrite",
                directory="/movies"
            )
            manager.add(task)

        # Should have exactly MAX_CONCURRENT_TASKS tasks
        assert len(manager.list_all()) == manager.MAX_CONCURRENT_TASKS

        # Adding one more should raise RuntimeError
        extra_task = BatchTask(
            task_id="extra-task",
            status=TaskStatus.PENDING,
            total_files=10,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="studio",
            value="Extra",
            mode="overwrite",
            directory="/movies"
        )

        with pytest.raises(RuntimeError, match="Maximum concurrent tasks limit"):
            manager.add(extra_task)

    def test_max_concurrent_tasks_with_expired_cleanup(self):
        """Test that expired tasks are cleaned up before enforcing limit."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        old_time = datetime.now() - timedelta(seconds=2000)

        # Add MAX_CONCURRENT_TASKS old tasks
        for i in range(manager.MAX_CONCURRENT_TASKS):
            task = BatchTask(
                task_id=f"old-task-{i}",
                status=TaskStatus.COMPLETED,
                total_files=10,
                processed_files=10,
                success_count=10,
                failed_count=0,
                errors=[],
                created_at=old_time,
                field="studio",
                value=f"Old {i}",
                mode="overwrite",
                directory="/movies"
            )
            manager.add(task)

        # Now add a new task - should succeed after cleanup
        new_task = BatchTask(
            task_id="new-task",
            status=TaskStatus.PENDING,
            total_files=5,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="studio",
            value="New",
            mode="overwrite",
            directory="/movies"
        )

        # This should succeed because old tasks are cleaned up first
        manager.add(new_task)

        # Verify only the new task remains
        all_tasks = manager.list_all()
        assert len(all_tasks) == 1
        assert all_tasks[0].task_id == "new-task"

    def test_max_concurrent_tasks_constant(self):
        """Test that MAX_CONCURRENT_TASKS is set to 5."""
        manager = TaskManager()
        assert manager.MAX_CONCURRENT_TASKS == 5


class TestTaskManagerAutomaticCleanup:
    """Test TaskManager automatic cleanup mechanism."""


class TestBatchProcessorPreview:
    """Tests for BatchProcessor preview functionality."""

    def test_preview_returns_current_and_new_values(self, tmp_path):
        """Preview includes current_value and new_value for overwrite mode."""
        from nfo_editor.batch.processor import BatchProcessor
        from nfo_editor.utils.xml_parser import XmlParser

        nfo_path = tmp_path / "movie.nfo"
        nfo_path.write_text(
            """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<movie>
    <title>Test Movie</title>
    <studio>Old Studio</studio>
</movie>""",
            encoding="utf-8"
        )

        processor = BatchProcessor(XmlParser())
        result = processor.preview(str(tmp_path), "studio", "Disney", "overwrite")

        assert len(result) == 1
        assert result[0]["current_value"] == "Old Studio"
        assert result[0]["new_value"] == "Disney"

    def test_preview_append_mode_uses_existing_value(self, tmp_path):
        """Append mode should concatenate existing and new values."""
        from nfo_editor.batch.processor import BatchProcessor
        from nfo_editor.utils.xml_parser import XmlParser

        nfo_path = tmp_path / "movie.nfo"
        nfo_path.write_text(
            """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<movie>
    <title>Test Movie</title>
    <genre>Action</genre>
</movie>""",
            encoding="utf-8"
        )

        processor = BatchProcessor(XmlParser())
        result = processor.preview(str(tmp_path), "genre", "Comedy", "append")

        assert len(result) == 1
        assert result[0]["current_value"] == "Action"
        assert result[0]["new_value"] == "Action, Comedy"


class TestBatchProcessorApply:
    """Tests for BatchProcessor apply functionality."""

    def test_apply_updates_files_and_task_counts(self, tmp_path):
        """Apply should update file content and task counters."""
        from datetime import datetime
        from nfo_editor.batch import TaskManager, TaskStatus, BatchTask
        from nfo_editor.batch.processor import BatchProcessor
        from nfo_editor.utils.xml_parser import XmlParser

        nfo_path = tmp_path / "movie.nfo"
        nfo_path.write_text(
            """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<movie>
    <title>Test Movie</title>
    <studio>Old Studio</studio>
</movie>""",
            encoding="utf-8"
        )

        manager = TaskManager()
        task = BatchTask(
            task_id="apply-task-1",
            status=TaskStatus.PENDING,
            total_files=0,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="studio",
            value="Disney",
            mode="overwrite",
            directory=str(tmp_path),
            preview_files=[{"path": str(nfo_path), "filename": "movie.nfo", "title": "Test Movie"}]
        )
        manager.add(task)

        processor = BatchProcessor(XmlParser())
        updated_task = processor.apply(
            task_id="apply-task-1",
            files=task.preview_files,
            field="studio",
            value="Disney",
            mode="overwrite"
        )

        content = nfo_path.read_text(encoding="utf-8")
        assert "<studio>Disney</studio>" in content
        assert updated_task.processed_files == 1
        assert updated_task.success_count == 1
        assert updated_task.failed_count == 0
        assert updated_task.status == TaskStatus.COMPLETED

    def test_apply_invalid_task_raises(self, tmp_path):
        """Apply should raise for unknown task id."""
        from nfo_editor.batch.processor import BatchProcessor
        from nfo_editor.utils.xml_parser import XmlParser
        import pytest

        processor = BatchProcessor(XmlParser())

        with pytest.raises(ValueError, match="Task not found"):
            processor.apply(
                task_id="missing-task",
                files=[],
                field="studio",
                value="Disney",
                mode="overwrite"
            )

    def test_automatic_cleanup_every_100_adds(self):
        """Test that cleanup runs every CLEANUP_INTERVAL additions."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        old_time = datetime.now() - timedelta(seconds=2000)

        # Add MAX_CONCURRENT_TASKS old tasks
        for i in range(manager.MAX_CONCURRENT_TASKS):
            task = BatchTask(
                task_id=f"old-task-{i}",
                status=TaskStatus.COMPLETED,
                total_files=10,
                processed_files=10,
                success_count=10,
                failed_count=0,
                errors=[],
                created_at=old_time,
                field="studio",
                value=f"Old {i}",
                mode="overwrite",
                directory="/movies"
            )
            manager.add(task)

        # Should have MAX_CONCURRENT_TASKS tasks
        assert len(manager.list_all()) == manager.MAX_CONCURRENT_TASKS

        # Manually set add_count to trigger cleanup on next add
        manager._add_count = manager.CLEANUP_INTERVAL - 1

        # Add one more task - this should trigger automatic cleanup
        new_task = BatchTask(
            task_id="new-task",
            status=TaskStatus.PENDING,
            total_files=5,
            processed_files=0,
            success_count=0,
            failed_count=0,
            errors=[],
            created_at=datetime.now(),
            field="studio",
            value="New",
            mode="overwrite",
            directory="/movies"
        )
        manager.add(new_task)

        # After cleanup, only the new task should remain
        all_tasks = manager.list_all()
        assert len(all_tasks) == 1
        assert all_tasks[0].task_id == "new-task"

    def test_cleanup_interval_constant(self):
        """Test that CLEANUP_INTERVAL is set to 100."""
        manager = TaskManager()
        assert manager.CLEANUP_INTERVAL == 100

    def test_automatic_cleanup_respects_lock(self):
        """Test that automatic cleanup is thread-safe."""
        manager = TaskManager()

        # Clean up first
        for task in manager.list_all():
            manager.delete(task.task_id)

        success = True
        errors = []
        results = {"added": 0, "errors": 0}
        lock = threading.Lock()

        def add_many_tasks(start_id):
            try:
                for i in range(10):
                    task = BatchTask(
                        task_id=f"task-{start_id}-{i}",
                        status=TaskStatus.PENDING,
                        total_files=10,
                        processed_files=0,
                        success_count=0,
                        failed_count=0,
                        errors=[],
                        created_at=datetime.now(),
                        field="studio",
                        value=f"Studio {i}",
                        mode="overwrite",
                        directory="/movies"
                    )
                    try:
                        manager.add(task)
                        with lock:
                            results["added"] += 1
                    except RuntimeError:
                        # Expected when hitting max concurrent tasks limit
                        with lock:
                            results["errors"] += 1
            except Exception as e:
                nonlocal success
                success = False
                errors.append(str(e))

        threads = [
            threading.Thread(target=add_many_tasks, args=(0,)),
            threading.Thread(target=add_many_tasks, args=(1,))
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert success, f"Thread-safe cleanup failed: {errors}"
        # Should have some additions and some errors due to limit
        assert results["added"] > 0
        assert results["added"] <= manager.MAX_CONCURRENT_TASKS
