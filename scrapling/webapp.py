from time import perf_counter

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from scrapling.fetchers import DynamicFetcher, Fetcher, StealthyFetcher
from scrapling.web import read_ui


class FetchRequest(BaseModel):
    url: str
    fetcher: str = Field(default="http")
    method: str = Field(default="GET")
    css_selector: str | None = None
    timeout: int = Field(default=30)
    headless: bool = Field(default=True)
    network_idle: bool = Field(default=False)


app = FastAPI(title="Scrapling Web UI", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return read_ui()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/fetch")
def fetch(payload: FetchRequest) -> dict:
    started = perf_counter()
    method = payload.method.upper()

    try:
        if payload.fetcher == "http":
            if method not in {"GET", "POST", "PUT", "DELETE"}:
                raise HTTPException(status_code=400, detail="Unsupported method for http fetcher")
            response = getattr(Fetcher, method.lower())(payload.url, timeout=payload.timeout)
        elif payload.fetcher == "dynamic":
            if method != "GET":
                raise HTTPException(status_code=400, detail="Dynamic fetcher supports GET only")
            response = DynamicFetcher.fetch(
                payload.url,
                headless=payload.headless,
                network_idle=payload.network_idle,
                timeout=payload.timeout * 1000,
            )
        elif payload.fetcher == "stealthy":
            if method != "GET":
                raise HTTPException(status_code=400, detail="Stealthy fetcher supports GET only")
            response = StealthyFetcher.fetch(
                payload.url,
                headless=payload.headless,
                network_idle=payload.network_idle,
                timeout=payload.timeout * 1000,
            )
        else:
            raise HTTPException(status_code=400, detail="Unknown fetcher type")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    extracted = None
    if payload.css_selector:
        extracted = [node.get_all_text(strip=True) for node in response.css(payload.css_selector)]

    elapsed_ms = int((perf_counter() - started) * 1000)
    return {
        "url": response.url,
        "status": response.status,
        "elapsed_ms": elapsed_ms,
        "extracted": extracted,
        "html": response.html_content,
    }
