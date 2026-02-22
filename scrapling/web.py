from pathlib import Path

from click import command, option


def _frontend_dir() -> Path:
    return Path(__file__).parent / "webapp" / "frontend"


def create_app():
    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    from scrapling_web.app import app as api_app

    app = FastAPI(title="Scrapling Web UI")
    app.mount("/api", api_app)

    frontend_dir = _frontend_dir()
    app.mount("/assets", StaticFiles(directory=frontend_dir), name="assets")

    @app.get("/")
    def index():
        return FileResponse(frontend_dir / "index.html")

    @app.get("/app.js")
    def app_js():
        return FileResponse(frontend_dir / "app.js")

    return app


@command(help="Run Scrapling Web UI server.")
@option("--host", default="127.0.0.1", show_default=True, help="Host interface to bind")
@option("--port", default=8765, type=int, show_default=True, help="Port to bind")
@option("--reload", is_flag=True, default=False, help="Enable auto reload for development")
def web(host: str, port: int, reload: bool) -> None:
    from uvicorn import run

    run("scrapling.web:create_app", host=host, port=port, reload=reload, factory=True)
