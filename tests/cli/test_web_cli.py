from pathlib import Path

from scrapling.web import _frontend_dir


def test_frontend_assets_exist():
    frontend_dir = _frontend_dir()
    assert frontend_dir.exists()
    assert (frontend_dir / "index.html").exists()
    assert (frontend_dir / "app.js").exists()


def test_frontend_page_contains_job_runner_heading():
    html = (Path(_frontend_dir()) / "index.html").read_text(encoding="utf-8")
    assert "Scrapling Job Runner" in html
