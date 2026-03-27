from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
import threading
import uuid
from typing import Any


@dataclass(slots=True)
class TaskRecord:
    task_id: str
    tool: str
    status: str
    created_at: str
    updated_at: str
    details: dict[str, Any] = field(default_factory=dict)
    error: str = ""


class TaskRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: dict[str, TaskRecord] = {}

    def start(self, tool: str, details: dict[str, Any] | None = None) -> str:
        now = datetime.now(UTC).isoformat()
        task_id = str(uuid.uuid4())
        record = TaskRecord(
            task_id=task_id,
            tool=tool,
            status="running",
            created_at=now,
            updated_at=now,
            details=details or {},
        )
        with self._lock:
            self._tasks[task_id] = record
        return task_id

    def finish(self, task_id: str, status: str = "completed", details: dict[str, Any] | None = None) -> None:
        with self._lock:
            record = self._tasks.get(task_id)
            if not record:
                return
            record.status = status
            record.updated_at = datetime.now(UTC).isoformat()
            if details:
                record.details.update(details)

    def fail(self, task_id: str, error: str) -> None:
        with self._lock:
            record = self._tasks.get(task_id)
            if not record:
                return
            record.status = "failed"
            record.error = error
            record.updated_at = datetime.now(UTC).isoformat()

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            record = self._tasks.get(task_id)
            if not record:
                return False
            record.status = "cancelled"
            record.updated_at = datetime.now(UTC).isoformat()
            return True

    def get(self, task_id: str) -> dict[str, Any]:
        with self._lock:
            record = self._tasks.get(task_id)
            if not record:
                return {"task_id": task_id, "error": "not found"}
            return {
                "task_id": record.task_id,
                "tool": record.tool,
                "status": record.status,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "details": dict(record.details),
                "error": record.error,
            }

    def list(self, only_running: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            records = list(self._tasks.values())
        if only_running:
            records = [record for record in records if record.status == "running"]
        return [self.get(record.task_id) for record in records]


registry = TaskRegistry()
