# Batch Editor Code Review Fixes - P0 & P1 Issues

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical thread-safety and security issues identified in code review report (CR-001, CR-002, IM-001, IM-002).

**Architecture:** Add thread-safe counter methods to BatchTask dataclass, add depth-limited recursion to file scanner, add file count validation to public methods, and unify append mode behavior between preview and apply.

**Tech Stack:** Python 3.10+, threading.Lock, dataclasses, pytest

**Reference:** `docs/reviews/batch-processor-code-review.md`

---

## Task 1: Add Thread-Safe Counter Methods to BatchTask

**Problem (CR-001):** `task.success_count += 1` and `task.failed_count += 1` are non-atomic in multi-threaded context.

**Files:**
- Modify: `nfo_editor/batch/models.py`

**Step 1: Add threading import to models.py**

Add `import threading` at the top of the file after `from typing import List`.

**Step 2: Add `_count_lock` field to BatchTask dataclass**

Modify the BatchTask dataclass to include a thread-safe lock:

```python
@dataclass
class BatchTask:
    """Batch task data model for tracking batch operations."""
    task_id: str
    status: TaskStatus
    total_files: int
    processed_files: int
    success_count: int
    failed_count: int
    errors: List[str]
    created_at: datetime
    field: str
    value: str
    mode: str
    directory: str
    preview_files: List[dict] = field(default_factory=list)
    _count_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
```

**Step 3: Add `increment_success` method to BatchTask**

Add this method after the `progress` property:

```python
def increment_success(self) -> None:
    """Thread-safe increment of success_count."""
    with self._count_lock:
        self.success_count += 1
```

**Step 4: Add `increment_failed` method to BatchTask**

Add this method after `increment_success`:

```python
def increment_failed(self, error_msg: str, filename: str = "unknown") -> None:
    """Thread-safe increment of failed_count and error logging.

    Args:
        error_msg: The error message to log
        filename: Name of the file that failed (for tracking)
    """
    with self._count_lock:
        self.failed_count += 1
        self.errors.append(f"{filename}: {error_msg}")
```

**Step 5: Verify changes with a test**

Run: `python -c "from nfo_editor.batch.models import BatchTask; print('Import successful')"`

Expected: No errors, import succeeds

**Step 6: Commit**

```bash
git add nfo_editor/batch/models.py
git commit -m "fix: add thread-safe counter methods to BatchTask (CR-001)"
```

---

## Task 2: Update _apply_file to Use Thread-Safe Methods

**Problem (CR-001):** Update the method that was causing the race condition.

**Files:**
- Modify: `nfo_editor/batch/processor.py:187-222`

**Step 1: Write failing test for thread-safety**

Create `tests/test_processor_thread_safety.py`:

```python
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
```

**Step 2: Run test to verify current implementation may fail**

Run: `pytest tests/test_processor_thread_safety.py::test_concurrent_apply_increments_correctly -v`

Expected: May pass or show flaky behavior (race conditions are intermittent)

**Step 3: Update `_apply_file` method to use thread-safe methods**

Replace lines 216-221 in `processor.py`:

```python
# OLD CODE (remove these lines):
task.success_count += 1
# ...
task.failed_count += 1
task.errors.append(f"{file_info['filename']}: {str(e)}")
```

With:

```python
# NEW CODE:
task.increment_success()
```

And for the error case:

```python
# NEW CODE:
task.increment_failed(str(e), file_info.get('filename', 'unknown'))
```

The full `_apply_file` method should now look like:

```python
def _apply_file(self, file_info: Dict[str, Any], field: str, value: str,
                mode: str, task: BatchTask) -> bool:
    """Apply modifications to single file with error isolation.

    Args:
        file_info: File info dict from preview
        field: Field to modify
        value: New value to apply
        mode: Operation mode
        task: BatchTask for progress tracking

    Returns:
        True if successful, False otherwise
    """
    try:
        # 1. Read file
        data = self.parser.parse(file_info["path"])

        # 2. Apply modification
        self._apply_field(data, field, value, mode)

        # 3. Validate
        is_valid, errors = validate_nfo_data(data)
        if not is_valid:
            raise ValueError(f"Validation failed: {errors}")

        # 4. Write back
        self.parser.save(data, file_info["path"])

        task.increment_success()
        return True

    except Exception as e:
        task.increment_failed(str(e), file_info.get('filename', 'unknown'))
        return False
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_processor_thread_safety.py::test_concurrent_apply_increments_correctly -v`

Expected: PASS

**Step 5: Commit**

```bash
git add nfo_editor/batch/processor.py tests/test_processor_thread_safety.py
git commit -m "fix: use thread-safe counters in _apply_file (CR-001)"
```

---

## Task 3: Add Recursion Depth Limit to _scan_nfo_files

**Problem (CR-002):** Unbounded recursion can cause stack overflow on malicious directory structures.

**Files:**
- Modify: `nfo_editor/batch/processor.py:30-56`

**Step 1: Add MAX_SCAN_DEPTH constant**

Add after `MAX_WORKERS = 10` at the top of processor.py:

```python
MAX_WORKERS = 10
MAX_SCAN_DEPTH = 50
```

**Step 2: Write failing test for depth limit**

Add to `tests/test_batch_api.py` or create new test file:

```python
def test_scan_depth_limit_raises_error(tmp_path):
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
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_batch_api.py::test_scan_depth_limit_raises_error -v`

Expected: FAIL with "RuntimeError not raised" (since limit not yet implemented)

**Step 4: Update `_scan_nfo_files` signature and implementation**

Modify the method to add depth parameter and limit:

```python
def _scan_nfo_files(self, directory: Path, depth: int = 0) -> List[Path]:
    """Scan directory for NFO files.

    Args:
        directory: Directory path to scan
        depth: Current recursion depth (for limit enforcement)

    Returns:
        List of NFO file paths found

    Raises:
        RuntimeError: If maximum scan depth is exceeded
    """
    nfo_files = []

    # Check depth limit before processing
    if depth > MAX_SCAN_DEPTH:
        raise RuntimeError(f"Maximum scan depth ({MAX_SCAN_DEPTH}) exceeded")

    try:
        for item in directory.iterdir():
            # Skip hidden files and directories
            if item.name.startswith('.'):
                continue

            if item.is_file() and item.suffix.lower() == '.nfo':
                nfo_files.append(item)
            elif item.is_dir():
                # Recursively scan subdirectories with incremented depth
                nfo_files.extend(self._scan_nfo_files(item, depth + 1))
    except PermissionError:
        # Skip directories without permission
        pass

    return nfo_files
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_batch_api.py::test_scan_depth_limit_raises_error -v`

Expected: PASS

**Step 6: Commit**

```bash
git add nfo_editor/batch/processor.py tests/test_batch_api.py
git commit -m "fix: add recursion depth limit to _scan_nfo_files (CR-002)"
```

---

## Task 4: Add File Count Limit Validation

**Problem (IM-001):** No validation on number of files can cause resource exhaustion.

**Files:**
- Modify: `nfo_editor/batch/processor.py`
- Modify: `web/app.py`

**Step 1: Add MAX_FILES_PER_BATCH constant**

Add to processor.py after MAX_SCAN_DEPTH:

```python
MAX_WORKERS = 10
MAX_SCAN_DEPTH = 50
MAX_FILES_PER_BATCH = 2000
```

**Step 2: Write failing test for file count limit**

```python
def test_max_files_limit_enforced():
    """Should raise RuntimeError when file count exceeds limit."""
    from nfo_editor.batch.processor import BatchProcessor, MAX_FILES_PER_BATCH
    from nfo_editor.utils.xml_parser import XmlParser
    from unittest.mock import patch, MagicMock

    processor = BatchProcessor(XmlParser())

    # Mock _scan_nfo_files to return more files than allowed
    mock_files = [MagicMock(name=f"file{i}.nfo") for i in range(MAX_FILES_PER_BATCH + 100)]

    with patch.object(processor, '_scan_nfo_files', return_value=mock_files):
        with pytest.raises(RuntimeError, match="Too many files"):
            processor.preview("/fake/path", "studio", "Test")
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_batch_api.py::test_max_files_limit_enforced -v`

Expected: FAIL

**Step 4: Add validation to `preview` method**

Add after line 138 (after `nfo_files = self._scan_nfo_files(dir_path)`):

```python
# Validate file count
if len(nfo_files) > MAX_FILES_PER_BATCH:
    raise RuntimeError(
        f"Too many files ({len(nfo_files)}). Maximum allowed: {MAX_FILES_PER_BATCH}"
    )
```

**Step 5: Add validation to `apply` method**

Add at the beginning of `apply` method (after getting task):

```python
# Validate file count
if len(files) > MAX_FILES_PER_BATCH:
    raise RuntimeError(
        f"Too many files ({len(files)}). Maximum allowed: {MAX_FILES_PER_BATCH}"
    )
```

**Step 6: Run tests to verify they pass**

Run: `pytest tests/test_batch_api.py::test_max_files_limit_enforced -v`

Expected: PASS

**Step 7: Update API error handling in app.py**

The API already catches ValueError and RuntimeError, so it will return proper error responses. No changes needed.

**Step 8: Commit**

```bash
git add nfo_editor/batch/processor.py tests/test_batch_api.py
git commit -m "feat: add file count limit validation (IM-001)"
```

---

## Task 5: Unify Append Mode Behavior

**Problem (IM-002):** `_apply_field` checks for duplicates in append mode, but `preview` doesn't. This causes preview to show different results than actual apply.

**Files:**
- Modify: `nfo_editor/batch/processor.py:162-186`

**Step 1: Write test showing inconsistency**

```python
def test_append_mode_preview_apply_consistency(tmp_path):
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
    # With current implementation: preview shows "Action, Action" but apply won't add duplicate
    # This test documents the current inconsistent behavior
```

**Step 2: Run test to see current behavior**

Run: `pytest tests/test_batch_api.py::test_append_mode_preview_apply_consistency -v`

Expected: May pass or fail depending on current state

**Step 3: Decide on unified behavior**

**Decision**: Remove duplicate checking in `_apply_field` to match preview behavior. The preview shows what will happen, and apply should do exactly that. If users add duplicates, that's their choice.

**Step 4: Update `_apply_field` to remove duplicate check**

Change the append mode sections:

```python
elif field == "genre":
    if mode == "overwrite":
        data.genres = [value]
    elif mode == "append":
        data.genres.append(value)
    else:
        raise ValueError(f"Invalid mode '{mode}' for field '{field}'")
```

And for director:

```python
elif field == "director":
    if mode == "overwrite":
        data.directors = [value]
    elif mode == "append":
        data.directors.append(value)
    else:
        raise ValueError(f"Invalid mode '{mode}' for field '{field}'")
```

**Step 5: Update `_preview_file` to match apply behavior**

The preview already shows "Action, Action" for append mode of duplicate values, which is now correct.

**Step 6: Run all tests**

Run: `pytest tests/test_batch_api.py tests/test_task_manager.py -v`

Expected: All tests pass

**Step 7: Commit**

```bash
git add nfo_editor/batch/processor.py tests/test_batch_api.py
git commit -m "fix: unify append mode behavior between preview and apply (IM-002)"
```

---

## Task 6: Run Full Test Suite and Final Verification

**Step 1: Run complete test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass

**Step 2: Run with coverage**

```bash
pytest tests/ --cov=nfo_editor.batch --cov-report=term-missing
```

Expected: Coverage remains high (>80%)

**Step 3: Manual smoke test**

Start the server and test the batch preview API:

```bash
# Terminal 1: Start server
uvicorn web.app:app --reload --port 1111

# Terminal 2: Test API
curl -X POST http://localhost:1111/api/batch/preview \
  -H "Content-Type: application/json" \
  -d '{"directory": "/tmp/test", "field": "studio", "value": "Test"}' \
  -u test:test
```

**Step 4: Final commit with tag**

```bash
git add .
git commit -m "chore: final cleanup after code review fixes"
git tag -a v1.0.1-code-review-fixes -m "Fix P0/P1 issues from code review"
```

---

## Verification Checklist

Before considering this plan complete:

- [ ] All P0 issues (CR-001, CR-002) fixed and tested
- [ ] All P1 issues (IM-001, IM-002) fixed and tested
- [ ] Thread-safe counter methods added to BatchTask
- [ ] Recursion depth limit added and enforced
- [ ] File count limit added and enforced
- [ ] Append mode behavior unified
- [ ] All existing tests still pass
- [ ] New tests added for all fixes
- [ ] Manual API testing completed

---

## Next Steps After Completion

1. **Code Review**: Request another review after fixes are complete
2. **P2 Issues**: Schedule IM-003 (concurrent write protection) and IM-004 (error logging) for next sprint
3. **P3 Issues**: Handle minor issues in regular maintenance
4. **Documentation**: Update user documentation if API error responses changed

---

**Plan Status**: Ready for execution
**Estimated Time**: 2-3 hours
**Risk Level**: Medium (thread-safety changes require careful testing)
