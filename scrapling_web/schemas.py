from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

EngineType = Literal["fetcher", "stealthy", "dynamic"]
HTTPMethod = Literal["GET", "POST", "PUT", "DELETE"]


class SelectorQuery(BaseModel):
    css: Optional[str] = None
    xpath: Optional[str] = None


class BaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    engine: EngineType = "fetcher"
    method: HTTPMethod = "GET"
    headers: List[str] = Field(default_factory=list, description='Format: "Key: Value"')
    cookies: Optional[str] = Field(default=None, description='Format: "name1=value1; name2=value2"')
    params: List[str] = Field(default_factory=list, description='Format: "key=value"')
    json: Optional[str] = None
    data: Optional[str] = None
    timeout: int = 30
    proxy: Optional[str] = None
    follow_redirects: bool = True
    verify: bool = True
    impersonate: Optional[str] = None
    stealthy_headers: bool = True


class FetchRequest(BaseRequest):
    css_selector: Optional[str] = None


class ExtractRequest(BaseRequest):
    selectors: SelectorQuery = Field(default_factory=SelectorQuery)


class RequestMetadata(BaseModel):
    status: int
    final_url: str
    reason: str
    elapsed_ms: Optional[float] = None


class ScrapeResponse(BaseModel):
    engine: EngineType
    method: str
    content: str
    extracted: List[str]
    metadata: RequestMetadata
    request: Dict[str, Any]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
