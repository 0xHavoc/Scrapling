from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Literal
from uuid import uuid4

JobState = Literal["queued", "running", "succeeded", "failed"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class JobRecord:
    job_id: str
    config: dict[str, Any]
    state: JobState = "queued"
    created_at: datetime = field(default_factory=utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


class JobManager:
    """In-memory, thread-safe job manager."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = RLock()

    def create_job(self, config: dict[str, Any]) -> JobRecord:
        with self._lock:
            job_id = uuid4().hex
            job = JobRecord(job_id=job_id, config=config)
            self._jobs[job_id] = job
            return job

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def start_job(self, job_id: str) -> JobRecord | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.state != "queued":
                return job
            job.state = "running"
            job.started_at = utcnow()
            return job

    def complete_job(self, job_id: str, result: dict[str, Any]) -> JobRecord | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.state = "succeeded"
            if job.started_at is None:
                job.started_at = utcnow()
            job.finished_at = utcnow()
            job.result = result
            job.error = None
            return job

    def fail_job(self, job_id: str, error: str) -> JobRecord | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.state = "failed"
            if job.started_at is None:
                job.started_at = utcnow()
            job.finished_at = utcnow()
            job.error = error
            job.result = None
            return job

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None
