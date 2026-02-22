from pathlib import Path

from click import command, option


@command(help="Run Scrapling Web UI server.")
@option("--host", default="127.0.0.1", show_default=True, help="Host interface to bind")
@option("--port", default=8765, type=int, show_default=True, help="Port to bind")
@option("--reload", is_flag=True, default=False, help="Enable auto reload for development")
def web(host: str, port: int, reload: bool) -> None:
    from uvicorn import run

    app_path = "scrapling.webapp:app"
    run(app_path, host=host, port=port, reload=reload)


def read_ui() -> str:
    return Path(__file__).with_name("webapp.html").read_text(encoding="utf-8")
