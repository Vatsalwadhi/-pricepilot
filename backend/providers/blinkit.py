from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
import json
import logging
import os
import sys
from typing import Any

import httpx


logger = logging.getLogger(__name__)


from .base import ProductOffer

Product = dict[str, Any]

SENSITIVE_HEADER_NAMES = {"authorization", "auth_key", "cookie"}
HEADER_CHECKLIST = (
    "session_uuid",
    "auth_key",
    "device_id",
    "app_version",
    "web_app_version",
    "rn_bundle_version",
    "app_client",
    "lat",
    "lon",
    "cookie",
    "referer",
    "origin",
    "user-agent",
    "accept-language",
    "sec-fetch-site",
    "sec-fetch-mode",
    "sec-fetch-dest",
    "sec-ch-ua",
    "sec-ch-ua-mobile",
    "sec-ch-ua-platform",
)


class BlinkitProvider:
    """Blinkit product-search provider.

    This class intentionally reads all session and location values from
    environment variables. Use only cookies/auth/device values that you are
    authorized to send to Blinkit.
    """

    platform_name = "Blinkit"
    provider_key = "blinkit"
    search_url = os.getenv("BLINKIT_SEARCH_URL", "https://blinkit.com/v1/layout/search")

    def __init__(
        self,
        *,
        timeout_seconds: float | None = None,
        default_limit: int | None = None,
        debug: bool | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds or float(os.getenv("BLINKIT_TIMEOUT_SECONDS", "30"))
        self.default_limit = default_limit or int(os.getenv("BLINKIT_SEARCH_LIMIT", "20"))
        self.debug = (
            debug
            if debug is not None
            else os.getenv("BLINKIT_DEBUG", "").lower() in {"1", "true", "yes", "on"}
        )

    def search_product(self, query: str, lat: float | None = None, lon: float | None = None) -> list[ProductOffer]:
        """Search Blinkit and return cleaned product dictionaries.

        Returns an empty list when Blinkit cannot be reached, rejects the
        request, returns invalid JSON, or changes its response shape.
        """
        
        self.current_lat = lat
        self.current_lon = lon

        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        params = {
            "q": cleaned_query,
            "actual_query": cleaned_query,
            "offset": "0",
            "limit": str(self.default_limit),
        }

        class FakeResponse:
            def __init__(self, status_code: int, headers: dict[str, str], text_content: str):
                self.status_code = status_code
                self.headers = headers
                self.text_content = text_content
            @property
            def text(self):
                return self.text_content

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context_args = {}
                user_agent = os.getenv(
                    "BLINKIT_USER_AGENT",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                )
                context_args["user_agent"] = user_agent
                
                context = browser.new_context(**context_args)
                
                cookies_str = os.getenv("BLINKIT_COOKIES", "").strip()
                if cookies_str:
                    cookie_list = []
                    for c in cookies_str.split(";"):
                        if "=" in c:
                            name, value = c.strip().split("=", 1)
                            cookie_list.append({"name": name, "value": value, "domain": ".blinkit.com", "path": "/"})
                    if cookie_list:
                        context.add_cookies(cookie_list)
                        
                page = context.new_page()
                search_url = f"https://blinkit.com/s/?q={cleaned_query}"
                
                if self.debug:
                    class FakeRequest:
                        method = "GET"
                        url = search_url
                        headers = self._headers()
                        content = b""
                    self._debug_request(FakeRequest(), params) # type: ignore
                
                # Navigate to homepage first to establish session/cookies if necessary
                try:
                    page.goto("https://blinkit.com/", timeout=self.timeout_seconds * 1000)
                    page.wait_for_timeout(1000)
                except Exception:
                    pass

                with page.expect_response(lambda r: "/v1/layout/search" in r.url and r.request.method != "OPTIONS", timeout=self.timeout_seconds * 1000) as response_info:
                    page.goto(search_url, timeout=self.timeout_seconds * 1000)
                
                response = response_info.value
                
                if response.status >= 400:
                    fake_resp = FakeResponse(response.status, response.headers, response.text())
                    if self.debug:
                        self._debug_failed_response(fake_resp) # type: ignore
                    logger.exception(
                        "Blinkit returned HTTP %s for query %r. %s",
                        response.status,
                        cleaned_query,
                        self._explain_http_failure(fake_resp), # type: ignore
                    )
                    browser.close()
                    return []
                    
                try:
                    payload = response.json()
                except Exception:
                    logger.exception("Blinkit returned invalid JSON for query %r", cleaned_query)
                    browser.close()
                    return []
                    
                browser.close()

        except Exception as exc:
            if type(exc).__name__ == "TimeoutError":
                logger.exception("Blinkit search timed out for query %r", cleaned_query)
                return []
            
            err_str = str(exc).lower()
            if "net::err_name_not_resolved" in err_str or "net::err_connection_refused" in err_str:
                logger.exception("Blinkit connection failed for query %r", cleaned_query)
            else:
                logger.exception("Blinkit HTTP request failed for query %r", cleaned_query)
            return []

        return self._parse_products(payload)

    def _headers(self) -> dict[str, str]:
        headers = {
            "accept": "application/json",
            "accept-language": os.getenv("BLINKIT_ACCEPT_LANGUAGE", "en-US,en;q=0.9"),
            "content-type": "application/json",
            "origin": "https://blinkit.com",
            "referer": "https://blinkit.com/",
            "user-agent": os.getenv(
                "BLINKIT_USER_AGENT",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36",
            ),
            "sec-fetch-dest": os.getenv("BLINKIT_SEC_FETCH_DEST", "empty"),
            "sec-fetch-mode": os.getenv("BLINKIT_SEC_FETCH_MODE", "cors"),
            "sec-fetch-site": os.getenv("BLINKIT_SEC_FETCH_SITE", "same-origin"),
        }

        optional_headers = {
            "session_uuid": os.getenv("BLINKIT_SESSION_UUID", ""),
            "auth_key": os.getenv("BLINKIT_AUTH_KEY", ""),
            "device_id": os.getenv("BLINKIT_DEVICE_ID", ""),
            "lat": str(getattr(self, "current_lat", None) or os.getenv("BLINKIT_LATITUDE", "")),
            "lon": str(getattr(self, "current_lon", None) or os.getenv("BLINKIT_LONGITUDE", "")),
            "latitude": str(getattr(self, "current_lat", None) or os.getenv("BLINKIT_LATITUDE", "")),
            "longitude": str(getattr(self, "current_lon", None) or os.getenv("BLINKIT_LONGITUDE", "")),
            "app_client": os.getenv("BLINKIT_APP_CLIENT", "consumer_web"),
            "app_version": os.getenv("BLINKIT_APP_VERSION", ""),
            "web_app_version": os.getenv("BLINKIT_WEB_APP_VERSION", ""),
            "rn_bundle_version": os.getenv("BLINKIT_RN_BUNDLE_VERSION", ""),
            "sec-ch-ua": os.getenv("BLINKIT_SEC_CH_UA", ""),
            "sec-ch-ua-mobile": os.getenv("BLINKIT_SEC_CH_UA_MOBILE", ""),
            "sec-ch-ua-platform": os.getenv("BLINKIT_SEC_CH_UA_PLATFORM", ""),
        }

        for key, value in optional_headers.items():
            if value:
                headers[key] = value

        cookies = os.getenv("BLINKIT_COOKIES", "").strip()
        if cookies:
            headers["cookie"] = cookies

        headers.update(self._browser_headers_from_env())

        return headers

    def _request_json_body(self) -> dict[str, Any]:
        raw_body = os.getenv("BLINKIT_REQUEST_BODY_JSON", "").strip()
        if not raw_body:
            return {}

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.warning("BLINKIT_REQUEST_BODY_JSON is not valid JSON; using {}")
            return {}

        if isinstance(parsed, dict):
            return parsed

        logger.warning("BLINKIT_REQUEST_BODY_JSON must decode to an object; using {}")
        return {}

    def _browser_headers_from_env(self) -> dict[str, str]:
        """Load copied Chrome DevTools headers for exact comparison/override.

        Supported formats:
        - BLINKIT_BROWSER_HEADERS_JSON='{"header-name": "value"}'
        - BLINKIT_BROWSER_HEADERS='header: value\nother-header: value'
        """

        json_headers = os.getenv("BLINKIT_BROWSER_HEADERS_JSON", "").strip()
        if json_headers:
            try:
                parsed = json.loads(json_headers)
            except json.JSONDecodeError:
                logger.warning("BLINKIT_BROWSER_HEADERS_JSON is not valid JSON")
            else:
                if isinstance(parsed, dict):
                    return self._safe_header_dict(parsed)

        raw_headers = os.getenv("BLINKIT_BROWSER_HEADERS", "").strip()
        if not raw_headers:
            return {}

        headers: dict[str, str] = {}
        for line in raw_headers.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
        return self._safe_header_dict(headers)

    def _safe_header_dict(self, headers: dict[Any, Any]) -> dict[str, str]:
        safe_headers: dict[str, str] = {}
        skipped = {"content-length", "host"}
        for key, value in headers.items():
            name = str(key).strip()
            if not name or name.startswith(":") or name.lower() in skipped:
                continue
            safe_headers[name] = str(value)
        return safe_headers

    def _debug_request(self, request: httpx.Request, params: dict[str, str]) -> None:
        if not self.debug:
            return

        self._debug("\n=== Blinkit Prepared Request ===")
        self._debug(f"Method: {request.method}")
        self._debug(f"URL: {request.url}")
        self._debug(f"Query parameters: {json.dumps(params, indent=2)}")
        self._debug("Headers:")
        for key, value in sorted(request.headers.items(), key=lambda item: item[0].lower()):
            self._debug(f"  {key}: {self._mask_header_value(key, value)}")
        self._debug(f"Cookies: {self._mask_header_value('cookie', request.headers.get('cookie', ''))}")
        self._debug(f"Request body: {self._request_body_text(request)}")
        self._debug_header_checklist(request.headers)
        self._debug_browser_header_comparison(request.headers)

    def _debug_header_checklist(self, headers: httpx.Headers) -> None:
        self._debug("Header checklist:")
        for name in HEADER_CHECKLIST:
            value = headers.get(name)
            status = "present" if value else "missing"
            self._debug(f"  {name}: {status}")

    def _debug_browser_header_comparison(self, python_headers: httpx.Headers) -> None:
        browser_headers = self._browser_headers_from_env()
        if not browser_headers:
            self._debug(
                "Browser comparison: no BLINKIT_BROWSER_HEADERS_JSON or "
                "BLINKIT_BROWSER_HEADERS value provided."
            )
            return

        normalized_browser = {key.lower(): value for key, value in browser_headers.items()}
        normalized_python = {key.lower(): value for key, value in python_headers.items()}

        missing = sorted(set(normalized_browser) - set(normalized_python))
        extra = sorted(set(normalized_python) - set(normalized_browser))
        modified = sorted(
            key
            for key in set(normalized_browser) & set(normalized_python)
            if normalized_browser[key] != normalized_python[key]
        )

        self._debug("Browser vs Python header comparison:")
        self._debug(f"  Missing in Python: {missing or 'none'}")
        self._debug(f"  Extra in Python: {extra or 'none'}")
        if modified:
            self._debug("  Modified values:")
            for key in modified:
                self._debug(
                    "    "
                    f"{key}: browser={self._mask_header_value(key, normalized_browser[key])} "
                    f"python={self._mask_header_value(key, normalized_python[key])}"
                )
        else:
            self._debug("  Modified values: none")

    def _debug_failed_response(self, response: httpx.Response) -> None:
        self._debug("\n=== Blinkit Failed Response ===")
        self._debug(f"Status: {response.status_code}")
        self._debug("Response headers:")
        for key, value in sorted(response.headers.items(), key=lambda item: item[0].lower()):
            self._debug(f"  {key}: {self._mask_header_value(key, value)}")
        self._debug(f"Response body first 1000 chars:\n{response.text[:1000]}")
        self._debug(f"Failure explanation: {self._explain_http_failure(response)}")

    def _explain_http_failure(self, response: httpx.Response) -> str:
        signals = self._anti_bot_signals(response)
        if response.status_code == 403 and signals:
            return (
                "The request appears to be blocked by an anti-bot or edge-protection "
                f"layer. Signals: {', '.join(signals)}."
            )
        if response.status_code == 403:
            return (
                "Blinkit rejected the request. The usual cause is a mismatch from the "
                "browser request: missing/expired cookies, session_uuid, auth_key, "
                "device_id, location headers, app version headers, or browser client hints."
            )
        return "Blinkit returned a non-success HTTP status."

    def _anti_bot_signals(self, response: httpx.Response) -> list[str]:
        body = response.text[:2000].lower()
        headers = {key.lower(): value.lower() for key, value in response.headers.items()}
        signals: list[str] = []

        if "cloudflare" in body or "cf-ray" in headers or "cf-cache-status" in headers:
            signals.append("Cloudflare")
        if "akamai" in body or any("akamai" in value for value in headers.values()):
            signals.append("Akamai")
        if "access denied" in body:
            signals.append("access denied page")
        if "captcha" in body:
            signals.append("captcha challenge")
        if "bot" in body:
            signals.append("bot-detection text")
        return signals

    def _request_body_text(self, request: httpx.Request) -> str:
        content = request.content
        if not content:
            return ""
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return repr(content[:1000])

    def _mask_header_value(self, key: str, value: str) -> str:
        if key.lower() not in SENSITIVE_HEADER_NAMES or not value:
            return value
        if len(value) <= 12:
            return "***"
        return f"{value[:6]}...{value[-4:]}"

    def _debug(self, message: str) -> None:
        print(message, file=sys.stderr)

    def _parse_products(self, payload: Any) -> list[ProductOffer]:
        products_by_id: dict[str, ProductOffer] = {}

        for candidate in self._walk_dicts(payload):
            product = self._product_from_candidate(candidate)
            if product is None:
                continue

            product_id = str(product.raw_payload.get("product_id") or "")
            if not product_id:
                continue

            if product_id in products_by_id:
                existing = products_by_id[product_id]
                
                new_image = product.raw_payload.get("image_url")
                if new_image and not existing.raw_payload.get("image_url"):
                    existing.raw_payload["image_url"] = new_image
                    
                new_merchant = product.raw_payload.get("merchant_id")
                if new_merchant and not existing.raw_payload.get("merchant_id"):
                    existing.raw_payload["merchant_id"] = new_merchant
                    
                new_mrp = product.raw_payload.get("mrp")
                if new_mrp is not None and existing.raw_payload.get("mrp") is None:
                    existing.raw_payload["mrp"] = new_mrp
                    
                new_brand = product.raw_payload.get("brand")
                if new_brand and not existing.raw_payload.get("brand"):
                    existing.raw_payload["brand"] = new_brand
            else:
                products_by_id[product_id] = product

        return list(products_by_id.values())

    def _product_from_candidate(self, candidate: dict[str, Any]) -> ProductOffer | None:
        name = self._first_text(
            candidate,
            ("display_name",),
            ("name",),
            ("title",),
            ("product", "display_name"),
            ("product", "name"),
        )
        price = self._first_decimal(
            candidate,
            ("price",),
            ("selling_price",),
            ("offer_price",),
            ("normal_price",),
            ("product", "price"),
            ("product", "selling_price"),
        )

        if not name or price is None or price <= 0:
            return None

        quantity = self._first_text(
            candidate,
            ("unit",),
            ("quantity",),
            ("pack_size",),
            ("product", "unit"),
            ("product", "quantity"),
        )

        mrp = self._first_decimal(
            candidate,
            ("mrp",),
            ("market_price",),
            ("maximum_retail_price",),
            ("product", "mrp"),
        )

        brand = self._first_text(
            candidate,
            ("brand",),
            ("brand_name",),
            ("product", "brand"),
            ("product", "brand_name"),
        )

        image_url = self._first_text(
            candidate,
            ("image_url",),
            ("image",),
            ("product", "image_url"),
            ("images", 0, "url"),
            ("media_container", "items", 0, "image", "url"),
        )
        
        product_id = self._first_text(
            candidate,
            ("product_id",),
            ("id",),
            ("product", "product_id"),
            ("product", "id"),
            ("identity", "id"),
        )
        
        merchant_id = self._first_text(
            candidate,
            ("merchant_id",),
            ("merchant", "id"),
            ("store", "merchant_id"),
            ("product", "merchant_id"),
        )

        inventory = self._first_value(
            candidate,
            ("inventory",),
            ("inventory_count",),
            ("available_quantity",),
            ("product", "inventory"),
        )

        raw_payload = {
            "mrp": mrp,
            "brand": brand,
            "image_url": image_url,
            "product_id": product_id,
            "merchant_id": merchant_id,
            "inventory": inventory,
        }

        return ProductOffer(
            platform=self.platform_name,
            provider_key=self.provider_key,
            product_name=name,
            quantity=quantity,
            price=Decimal(str(price)),
            delivery_charge=Decimal("0"),
            total_price=Decimal(str(price)),
            currency="INR",
            product_url=f"https://blinkit.com/prn/-/prid/{product_id}" if product_id else "https://blinkit.com",
            raw_payload=raw_payload,
        )

    def _walk_dicts(self, value: Any) -> Iterable[dict[str, Any]]:
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from self._walk_dicts(child)
        elif isinstance(value, list):
            for item in value:
                yield from self._walk_dicts(item)

    def _first_text(self, data: dict[str, Any], *paths: tuple[str | int, ...]) -> str:
        for path in paths:
            value = self._get_path(data, path)
            if value is None:
                continue
            if isinstance(value, dict):
                value = value.get("text") or value.get("value") or value.get("name")
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    def _first_decimal(self, data: dict[str, Any], *paths: tuple[str | int, ...]) -> float | None:
        for path in paths:
            parsed = self._decimal_from_value(self._get_path(data, path))
            if parsed is not None:
                return float(parsed)
        return None

    def _first_value(self, data: dict[str, Any], *paths: tuple[str | int, ...]) -> Any:
        for path in paths:
            value = self._get_path(data, path)
            if value is not None:
                return value
        return None

    def _get_path(self, data: Any, path: tuple[str | int, ...]) -> Any:
        value = data
        for key in path:
            if isinstance(key, int):
                if not isinstance(value, list) or len(value) <= key:
                    return None
                value = value[key]
                continue
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        return value

    def _decimal_from_value(self, value: Any) -> Decimal | None:
        if value is None or value == "":
            return None
        if isinstance(value, dict):
            value = (
                value.get("value")
                or value.get("amount")
                or value.get("price")
                or value.get("text")
            )
        if isinstance(value, str):
            value = value.replace(",", "").replace("₹", "").strip()

        try:
            amount = Decimal(str(value)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError, TypeError):
            return None

        return amount if amount >= 0 else None
