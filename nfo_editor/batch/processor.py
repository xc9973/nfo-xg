"""Batch processor for NFO file operations."""
import uuid
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from nfo_editor.batch.models import BatchTask, TaskStatus
from nfo_editor.batch.task_manager import TaskManager
from nfo_editor.utils.xml_parser import XmlParser
from nfo_editor.utils.validation import validate_nfo_data


MAX_WORKERS = 10
MAX_SCAN_DEPTH = 50
MAX_FILES_PER_BATCH = 2000


class BatchProcessor:
    """Processor for batch NFO file operations."""

    def __init__(self, parser: XmlParser, max_workers: int = MAX_WORKERS):
        """Initialize BatchProcessor.

        Args:
            parser: XmlParser instance for parsing NFO files
            max_workers: Maximum number of concurrent worker threads
        """
        self.parser = parser
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_manager = TaskManager()

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

    def _preview_file(self, file_path: Path, field: str, value: str, mode: str) -> Dict[str, Any]:
        """Preview single file modifications.

        Args:
            file_path: Path to NFO file
            field: Field to check current value
            value: New value to apply
            mode: Operation mode ('overwrite' or 'append')

        Returns:
            Dict with file info including current field value
        """
        try:
            data = self.parser.parse(str(file_path))

            file_info = {
                "path": str(file_path),
                "filename": file_path.name,
                "title": data.title or file_path.stem,
            }

            # Add current field value based on field type
            current_value = ""
            if field == "studio":
                current_value = data.studio or ""
            elif field == "genre":
                current_value = ", ".join(data.genres) if data.genres else ""
            elif field == "director":
                current_value = ", ".join(data.directors) if data.directors else ""

            # Calculate new_value based on mode
            new_value = ""
            if mode == "overwrite":
                new_value = value
            elif mode == "append" and current_value:
                new_value = f"{current_value}, {value}"
            elif mode == "append":
                new_value = value

            file_info["current_value"] = current_value
            file_info["new_value"] = new_value

            return file_info

        except Exception:
            # If parsing fails, return basic info
            return {
                "path": str(file_path),
                "filename": file_path.name,
                "title": file_path.stem,
                "current_value": "",
                "error": "Failed to parse file"
            }

    def preview(self, directory: str, field: str, value: str, mode: str = "overwrite") -> List[Dict[str, Any]]:
        """Preview batch modifications.

        Args:
            directory: Directory path to scan
            field: Field to modify ('studio', 'genre', 'director')
            value: New value to apply
            mode: Operation mode ('overwrite' or 'append')

        Returns:
            List of file info dicts that would be modified

        Raises:
            FileNotFoundError: If directory doesn't exist
            ValueError: If directory is not a directory
        """
        dir_path = Path(directory)

        # Validate directory
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        # Scan for NFO files
        nfo_files = self._scan_nfo_files(dir_path)

        # Validate file count
        if len(nfo_files) > MAX_FILES_PER_BATCH:
            raise RuntimeError(
                f"Too many files ({len(nfo_files)}). Maximum allowed: {MAX_FILES_PER_BATCH}"
            )

        if not nfo_files:
            return []

        # Preview files concurrently
        preview_files = []
        futures = []

        for file_path in nfo_files:
            future = self.executor.submit(self._preview_file, file_path, field, value, mode)
            futures.append(future)

        for future in as_completed(futures):
            try:
                file_info = future.result()
                if "error" not in file_info:
                    preview_files.append(file_info)
            except Exception:
                # Skip files that fail during preview
                pass

        return preview_files

    def _apply_field(self, data: Any, field: str, value: str, mode: str) -> None:
        """Apply field modification to NFO data.

        Args:
            data: NfoData object to modify
            field: Field to modify ('studio', 'genre', 'director')
            value: New value to apply
            mode: Operation mode ('overwrite' or 'append')
        """
        if field == "studio":
            # Studio is single-value, only overwrite mode
            data.studio = value
        elif field == "genre":
            if mode == "overwrite":
                data.genres = [value]
            elif mode == "append":
                data.genres.append(value)
            else:
                raise ValueError(f"Invalid mode '{mode}' for field '{field}'")
        elif field == "director":
            if mode == "overwrite":
                data.directors = [value]
            elif mode == "append":
                data.directors.append(value)
            else:
                raise ValueError(f"Invalid mode '{mode}' for field '{field}'")

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

    def apply(self, task_id: str, files: List[Dict[str, Any]], field: str,
              value: str, mode: str) -> BatchTask:
        """Execute batch modifications.

        Args:
            task_id: Task ID for tracking
            files: List of file info dicts from preview
            field: Field to modify
            value: New value to apply
            mode: Operation mode ('overwrite' or 'append')

        Returns:
            Updated BatchTask with results
        """
        # Get task from manager
        task = self.task_manager.get(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        # Validate file count
        if len(files) > MAX_FILES_PER_BATCH:
            raise RuntimeError(
                f"Too many files ({len(files)}). Maximum allowed: {MAX_FILES_PER_BATCH}"
            )

        # Update task status
        task.status = TaskStatus.RUNNING
        task.total_files = len(files)

        # Apply modifications concurrently
        futures = []

        for file_info in files:
            future = self.executor.submit(
                self._apply_file,
                file_info,
                field,
                value,
                mode,
                task
            )
            futures.append(future)

        # Wait for all tasks to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception:
                # Error already recorded in _apply_file
                pass

            # Update progress
            task.increment_processed()

        # Update final status
        if task.failed_count > 0 and task.success_count == 0:
            task.status = TaskStatus.FAILED
        else:
            task.status = TaskStatus.COMPLETED

        return task
