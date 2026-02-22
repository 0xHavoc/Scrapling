from __future__ import annotations

from dataclasses import asdict
from typing import cast

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from scrapling.fetchers import Fetcher
from scrapling.webapp.backend.jobs import JobManager


class JobRequest(BaseModel):
    url: str
    extraction_type: str = Field(default="markdown")
    css_selector: str | None = None
    main_content_only: bool = True


job_manager = JobManager()
app = FastAPI(title="Scrapling Job API")


def _run_scrape(job_id: str) -> None:
    job = job_manager.start_job(job_id)
    if not job:
        return

    try:
        page = Fetcher.get(job.config["url"])
        content: str | list[str]
        if job.config["extraction_type"] == "html":
            content = page.html_content
        elif job.config["extraction_type"] == "text":
            content = page.text
        else:
            from markdownify import markdownify

            content = markdownify(cast(str, page.html_content))

        if job.config.get("css_selector"):
            content = [cast(str, element.get()) for element in page.css(job.config["css_selector"])]

        job_manager.complete_job(
            job_id,
            {
                "status": page.status,
                "url": page.url,
                "content": content,
            },
        )
    except Exception as exc:
        job_manager.fail_job(job_id, str(exc))


@app.post("/api/jobs")
def create_job(payload: JobRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
    job = job_manager.create_job(payload.model_dump())
    background_tasks.add_task(_run_scrape, job.job_id)
    return {"job_id": job.job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return asdict(job)


@app.delete("/api/jobs/{job_id}", status_code=204)
def delete_job(job_id: str) -> Response:
    deleted = job_manager.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    return Response(status_code=204)
