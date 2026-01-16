"""Batch editing data models."""
from datetime import datetime
from dataclasses import dataclass, field
from typing import List
from enum import Enum
import threading

from pydantic import BaseModel, field_validator


class TaskStatus(Enum):
    """Batch task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


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

    @property
    def progress(self) -> float:
        """Calculate progress percentage."""
        if self.total_files == 0:
            return 0.0
        return self.processed_files / self.total_files * 100

    def increment_success(self) -> None:
        """Thread-safe increment of success_count."""
        with self._count_lock:
            self.success_count += 1

    def increment_failed(self, error_msg: str, filename: str = "unknown") -> None:
        """Thread-safe increment of failed_count and error logging.

        Args:
            error_msg: The error message to log
            filename: Name of the file that failed (for tracking)
        """
        with self._count_lock:
            self.failed_count += 1
            self.errors.append(f"{filename}: {error_msg}")

    def increment_processed(self) -> None:
        """Thread-safe increment of processed_files."""
        with self._count_lock:
            self.processed_files += 1


class BatchPreviewRequest(BaseModel):
    """Batch preview request model."""
    directory: str
    field: str  # Field to modify: 'studio', 'genre', or 'director'
    value: str
    mode: str = "overwrite"  # Operation mode: 'overwrite' or 'append'

    @field_validator('field')
    @classmethod
    def validate_field(cls, v: str) -> str:
        """Validate field is one of: studio, genre, director."""
        if v not in ('studio', 'genre', 'director'):
            raise ValueError("field must be 'studio', 'genre', or 'director'")
        return v

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate mode is either 'overwrite' or 'append'."""
        if v not in ('overwrite', 'append'):
            raise ValueError("mode must be 'overwrite' or 'append'")
        return v


class BatchApplyRequest(BaseModel):
    """Batch apply request model."""
    task_id: str
    confirmed: bool = True


class BatchPreviewResponse(BaseModel):
    """Batch preview response model."""
    task_id: str
    total_files: int
    sample_files: List[dict]


class BatchStatusResponse(BaseModel):
    """Batch status response model."""
    task_id: str
    status: str
    progress: float
    processed: int
    total: int
    success: int
    failed: int
    errors: List[str]
