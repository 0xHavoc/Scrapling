from scrapling.webapp.backend.jobs import JobManager


def test_job_lifecycle_success():
    manager = JobManager()
    job = manager.create_job({"url": "https://example.com"})

    assert job.state == "queued"
    manager.start_job(job.job_id)
    manager.complete_job(job.job_id, {"ok": True})

    saved = manager.get_job(job.job_id)
    assert saved is not None
    assert saved.state == "succeeded"
    assert saved.result == {"ok": True}
    assert saved.error is None
    assert saved.started_at is not None
    assert saved.finished_at is not None


def test_job_lifecycle_failure_and_delete():
    manager = JobManager()
    job = manager.create_job({"url": "https://example.com"})

    manager.start_job(job.job_id)
    manager.fail_job(job.job_id, "boom")

    saved = manager.get_job(job.job_id)
    assert saved is not None
    assert saved.state == "failed"
    assert saved.error == "boom"

    assert manager.delete_job(job.job_id) is True
    assert manager.get_job(job.job_id) is None
