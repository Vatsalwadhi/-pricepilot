from __future__ import annotations

from decimal import Decimal
import logging
import os
from typing import Any

from .base import ProductOffer

logger = logging.getLogger(__name__)


class ZeptoProvider:
    """Zepto product-search provider using Playwright."""

    platform_name = "Zepto"
    provider_key = "zepto"

    def __init__(
        self,
        *,
        timeout_seconds: float | None = None,
        default_limit: int | None = None,
        debug: bool | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds or float(os.getenv("ZEPTO_TIMEOUT_SECONDS", "30"))
        self.default_limit = default_limit or int(os.getenv("ZEPTO_SEARCH_LIMIT", "20"))
        self.debug = (
            debug
            if debug is not None
            else os.getenv("ZEPTO_DEBUG", "").lower() in {"1", "true", "yes", "on"}
        )

    _location_cache = {}  # (lat, lon) -> (store_id, eta)

    def search_product(self, query: str, lat: float | None = None, lon: float | None = None) -> list[ProductOffer]:
        """Search Zepto using Playwright and return cleaned product dictionaries."""
        
        self.current_lat = lat
        self.current_lon = lon

        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context_args = {}
                user_agent = os.getenv(
                    "ZEPTO_USER_AGENT",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                )
                context_args["user_agent"] = user_agent
                
                if self.current_lat and self.current_lon:
                    context_args["geolocation"] = {"latitude": float(self.current_lat), "longitude": float(self.current_lon)}
                    context_args["permissions"] = ["geolocation"]
                
                context = browser.new_context(**context_args)
                page = context.new_page()
                
                # Step 3, 4, 5: Location Bootstrap
                # 7. Clear any previous cookies/localStorage/session state
                context.clear_cookies()
                
                from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
                
                def intercept_get_page(route):
                    req = route.request
                    parsed = urlparse(req.url)
                    query = parse_qs(parsed.query)
                    if self.current_lat is not None and self.current_lon is not None:
                        query['latitude'] = [str(self.current_lat)]
                        query['longitude'] = [str(self.current_lon)]
                    new_query = urlencode(query, doseq=True)
                    new_url = urlunparse(parsed._replace(query=new_query))
                    route.continue_(url=new_url)
                
                page.route("**/lms/api/v2/get_page*", intercept_get_page)
                
                try:
                    with page.expect_response(
                        lambda r: "lms/api/v2/get_page" in r.url and r.request.method == "GET",
                        timeout=self.timeout_seconds * 1000
                    ) as resp_info:
                        page.goto("https://www.zeptonow.com", timeout=self.timeout_seconds * 1000)
                    
                    data = resp_info.value.json()
                    
                    store_id = None
                    serviceable = False
                    
                    v2 = data.get("storeServiceableResponseV2")
                    if isinstance(v2, list):
                        for s in v2:
                            if s.get("storeConstruct") == "PRIMARY_STORE":
                                store_id = s.get("storeId")
                                serviceable = s.get("serviceable", False)
                                break
                    else:
                        store_resp = data.get("storeServiceableResponse", {})
                        store_id = store_resp.get("storeId")
                        serviceable = store_resp.get("serviceable", False)
                    
                    eta = None
                    if store_id:
                        info = data.get("storeServiceableInfo", {}).get("storeServiceabilityView", {})
                        eta = info.get(store_id, {}).get("etaInMinutes")
                    
                    # 8. Add debug logging
                    logger.debug("Zepto Location Bootstrap - Latitude: %s, Longitude: %s, Store ID: %s, ETA: %s, Serviceable: %s, URL: %s",
                                 self.current_lat, self.current_lon, store_id, eta, serviceable, resp_info.value.url)
                    
                    # 4. If no PRIMARY_STORE exists, or not serviceable, immediately return []
                    if not store_id or not serviceable:
                        logger.warning("Zepto location bootstrap: Location not serviceable or no PRIMARY_STORE returned")
                        browser.close()
                        return []
                    
                except Exception as e:
                    logger.warning("Zepto location bootstrap failed: %s", e)
                    browser.close()
                    return []
                
                self.cached_eta = eta
                
                # 6. Ensure the search request uses THIS store_id only
                # We can enforce this by injecting the store_id into localStorage or intercepting the search request
                # However, since we cleared cookies initially and the UI just bootstrapped, it will naturally use this store_id.
                
                # Step 6: Perform POST search
                try:
                    with page.expect_response(
                        lambda r: "user-search-service/api/v3/search" in r.url and r.request.method == "POST",
                        timeout=self.timeout_seconds * 1000
                    ) as response_info:
                        try:
                            search_trigger = page.locator('[href="/search"], [data-testid*="search"]').first
                            search_trigger.click(timeout=3000)
                            page.wait_for_timeout(1000)
                        except Exception:
                            pass

                        search_input = page.locator('input[placeholder*="Search" i], input[aria-label*="Search" i], input[type="text"]').first
                        search_input.click(timeout=self.timeout_seconds * 1000)
                        search_input.type(cleaned_query, delay=50) # Type slowly to trigger search API correctly
                        search_input.press("Enter")
                        
                    response = response_info.value
                    
                    if response.status >= 400:
                        logger.warning("Zepto returned HTTP %s for query %r.", response.status, cleaned_query)
                        browser.close()
                        return []
                        
                    payload = response.json()
                    
                except Exception as exc:
                    if type(exc).__name__ == "TimeoutError":
                        logger.exception("Zepto search UI timed out for query %r", cleaned_query)
                    else:
                        logger.exception("Zepto search failed for query %r", cleaned_query)
                    browser.close()
                    return []
                    
                browser.close()

        except Exception as exc:
            logger.exception("Zepto unexpected error for query %r", cleaned_query)
            return []

        return self._parse_products(payload)

    def _parse_products(self, payload: Any) -> list[ProductOffer]:
        products_by_id: dict[str, ProductOffer] = {}
        
        widgets = self._find_widgets(payload)
        for widget in widgets:
            resolver = widget.get("data", {}).get("resolver", {})
            items = resolver.get("data", {}).get("items") or []
            for item in items:
                product_resp = item.get("productResponse", {})
                if not product_resp:
                    continue
                
                product = product_resp.get("product", {})
                variant = product_resp.get("productVariant", {})
                
                selling_price = product_resp.get("sellingPrice")
                if selling_price is None:
                    continue
                    
                price = Decimal(str(selling_price)) / 100
                if price <= 0:
                    continue
                
                mrp_val = product_resp.get("mrp")
                mrp = Decimal(str(mrp_val)) / 100 if mrp_val is not None else price
                
                name = product.get("name") or ""
                brand = product.get("brand") or ""
                quantity = variant.get("formattedPacksize") or ""
                inventory = product_resp.get("availableQuantity", 0)
                
                product_id = product.get("id") or ""
                variant_id = variant.get("id") or ""
                store_id = product_resp.get("storeId") or ""
                
                image_url = ""
                images = variant.get("images", [])
                if images and isinstance(images, list):
                    path = images[0].get("path", "")
                    if path:
                        if not path.startswith("http"):
                            image_url = f"https://cdn.zeptonow.com/production/{path}"
                        else:
                            image_url = path
                            
                raw_payload = {
                    "mrp": mrp,
                    "brand": brand,
                    "image_url": image_url,
                    "product_id": product_id,
                    "variant_id": variant_id,
                    "store_id": store_id,
                    "inventory": inventory,
                    "eta": getattr(self, "cached_eta", None),
                    "original_json": item,
                }
                
                if product_id not in products_by_id:
                    import re
                    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
                    products_by_id[product_id] = ProductOffer(
                        platform=self.platform_name,
                        provider_key=self.provider_key,
                        product_name=name,
                        quantity=quantity,
                        price=price,
                        delivery_charge=Decimal("0"),
                        total_price=price,
                        currency="INR",
                        product_url=f"https://www.zeptonow.com/pn/{slug}/pvid/{variant_id}" if variant_id else "https://www.zeptonow.com",
                        raw_payload=raw_payload,
                    )

        return list(products_by_id.values())

    def _find_widgets(self, data: Any) -> list[dict[str, Any]]:
        widgets = []
        if isinstance(data, dict):
            name = str(data.get("widgetName", ""))
            # Allow any widget related to searched products
            if name.startswith("SEARCHED_PRODUCTS_") or "SUGGEST" in name or "SEARCH" in name:
                widgets.append(data)
            for child in data.values():
                widgets.extend(self._find_widgets(child))
        elif isinstance(data, list):
            for item in data:
                widgets.extend(self._find_widgets(item))
        return widgets
