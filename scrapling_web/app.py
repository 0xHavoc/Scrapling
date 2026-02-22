from fastapi import FastAPI

from scrapling_web.schemas import ExtractRequest, FetchRequest, HealthResponse, ScrapeResponse
from scrapling_web.services.scrapling_service import ScraplingService

app = FastAPI(title="Scrapling Web API", version="0.1.0")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/api/fetch", response_model=ScrapeResponse)
def fetch(request: FetchRequest) -> ScrapeResponse:
    return ScraplingService.handle_request(request, css_selector=request.css_selector)


@app.post("/api/extract", response_model=ScrapeResponse)
def extract(request: ExtractRequest) -> ScrapeResponse:
    return ScraplingService.handle_request(
        request,
        css_selector=request.selectors.css,
        xpath_selector=request.selectors.xpath,
    )
