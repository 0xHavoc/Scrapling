from time import perf_counter
from typing import Any, Callable, Dict, List, Tuple

from fastapi import HTTPException
from orjson import JSONDecodeError, loads as json_loads
from scrapling.core.utils._shell import _CookieParser, _ParseHeaders
from scrapling.fetchers import DynamicFetcher, Fetcher, StealthyFetcher
from scrapling.engines.toolbelt.custom import Response

from scrapling_web.schemas import EngineType, ExtractRequest, FetchRequest, ScrapeResponse


class ScraplingService:
    @staticmethod
    def _parse_json_data(json_string: str | None = None) -> Dict[str, Any] | None:
        if not json_string:
            return None
        try:
            return json_loads(json_string)
        except JSONDecodeError as err:
            raise HTTPException(status_code=400, detail=f"Invalid JSON data '{json_string}': {err}") from err

    @classmethod
    def _parse_extract_arguments(
        cls, headers: List[str], cookies: str | None, params: List[str], json: str | None = None
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, Any] | None]:
        try:
            parsed_headers, parsed_cookies = _ParseHeaders(headers)
        except ValueError as err:
            raise HTTPException(status_code=400, detail=str(err)) from err

        if cookies:
            try:
                for key, value in _CookieParser(cookies):
                    parsed_cookies[key] = value
            except Exception as err:
                raise HTTPException(status_code=400, detail=f"Could not parse cookies '{cookies}': {err}") from err

        parsed_json = cls._parse_json_data(json)
        parsed_params: Dict[str, str] = {}
        for param in params:
            if "=" in param:
                key, value = param.split("=", 1)
                parsed_params[key] = value

        return parsed_headers, parsed_cookies, parsed_params, parsed_json

    @classmethod
    def _build_request(cls, request: FetchRequest | ExtractRequest) -> Dict[str, Any]:
        parsed_headers, parsed_cookies, parsed_params, parsed_json = cls._parse_extract_arguments(
            request.headers,
            request.cookies,
            request.params,
            request.json,
        )
        request_kwargs: Dict[str, Any] = {
            "headers": parsed_headers if parsed_headers else None,
            "cookies": parsed_cookies if parsed_cookies else None,
            "timeout": request.timeout,
        }

        if parsed_json:
            request_kwargs["json"] = parsed_json
        if parsed_params:
            request_kwargs["params"] = parsed_params
        if request.proxy:
            request_kwargs["proxy"] = request.proxy
        if request.impersonate:
            if "," in request.impersonate:
                request_kwargs["impersonate"] = [browser.strip() for browser in request.impersonate.split(",")]
            else:
                request_kwargs["impersonate"] = request.impersonate

        request_kwargs["follow_redirects"] = request.follow_redirects
        request_kwargs["verify"] = request.verify
        request_kwargs["stealthy_headers"] = request.stealthy_headers
        if request.data is not None:
            request_kwargs["data"] = request.data

        return request_kwargs

    @staticmethod
    def _extract(response: Response, css: str | None = None, xpath: str | None = None) -> List[str]:
        if css:
            return [str(item) for item in response.css(css).getall()]
        if xpath:
            return [str(item) for item in response.xpath(xpath).getall()]
        return []

    @staticmethod
    def _execute(engine: EngineType, method: str, url: str, kwargs: Dict[str, Any]) -> Response:
        if engine == "fetcher":
            methods: Dict[str, Callable[..., Response]] = {
                "GET": Fetcher.get,
                "POST": Fetcher.post,
                "PUT": Fetcher.put,
                "DELETE": Fetcher.delete,
            }
            return methods[method](url, **kwargs)

        if method != "GET":
            raise HTTPException(status_code=400, detail=f"Engine '{engine}' only supports GET requests")

        browser_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key in {"timeout", "proxy", "cookies", "impersonate", "headers"}
        }
        if "headers" in browser_kwargs:
            browser_kwargs["extra_headers"] = browser_kwargs.pop("headers")

        if engine == "stealthy":
            return StealthyFetcher.fetch(url, **browser_kwargs)
        return DynamicFetcher.fetch(url, **browser_kwargs)

    @classmethod
    def handle_request(
        cls,
        request: FetchRequest | ExtractRequest,
        css_selector: str | None = None,
        xpath_selector: str | None = None,
    ) -> ScrapeResponse:
        kwargs = cls._build_request(request)
        start = perf_counter()
        try:
            response = cls._execute(request.engine, request.method, request.url, kwargs)
        except HTTPException:
            raise
        except (ValueError, TypeError) as err:
            raise HTTPException(status_code=400, detail=str(err)) from err
        except TimeoutError as err:
            raise HTTPException(status_code=504, detail=str(err)) from err
        except RuntimeError as err:
            raise HTTPException(status_code=502, detail=str(err)) from err
        except Exception as err:
            raise HTTPException(status_code=502, detail=f"Upstream fetch failed: {err}") from err

        elapsed = round((perf_counter() - start) * 1000, 2)
        extracted = cls._extract(response, css_selector, xpath_selector)

        return ScrapeResponse(
            engine=request.engine,
            method=request.method,
            content=response.get(),
            extracted=extracted,
            metadata={
                "status": response.status,
                "final_url": response.url,
                "reason": response.reason,
                "elapsed_ms": response.meta.get("timing_ms", elapsed),
            },
            request={
                "url": request.url,
                "kwargs": {k: v for k, v in kwargs.items() if v is not None},
            },
        )
