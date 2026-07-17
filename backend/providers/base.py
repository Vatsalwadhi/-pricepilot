from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import logging
import os
from typing import Any, Iterable

import httpx
from django.conf import settings


logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Raised when a platform provider cannot retrieve or parse data."""


class ProviderConfigurationError(ProviderError):
    """Raised when a provider is active but missing its endpoint configuration."""


@dataclass(slots=True)
class ProductOffer:
    platform: str
    provider_key: str
    product_name: str
    quantity: str
    price: Decimal
    delivery_charge: Decimal
    total_price: Decimal
    product_url: str = ""
    currency: str = "INR"
    raw_payload: dict[str, Any] = field(default_factory=dict)


class BaseProvider:
    platform_name: str
    provider_key: str
    api_url_env: str
    token_env: str

    def __init__(self) -> None:
        self.api_url = os.getenv(self.api_url_env, "").strip()
        self.api_token = os.getenv(self.token_env, "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_url)

    def search_product(self, product_name: str, lat: float | None = None, lon: float | None = None) -> list[ProductOffer]:
        raise NotImplementedError

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "PricePilot/1.0"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers


class HttpJsonProvider(BaseProvider):
    """Generic adapter for official, partner, or otherwise legal JSON endpoints."""

    result_keys = ("results", "products", "items", "data")

    def search_product(self, product_name: str, lat: float | None = None, lon: float | None = None) -> list[ProductOffer]:
        if not self.is_configured:
            raise ProviderConfigurationError(
                f"{self.platform_name} is not configured. Set {self.api_url_env}."
            )

        params = {"q": product_name}
        if settings.PROVIDER_LOCATION:
            params["location"] = settings.PROVIDER_LOCATION
        if lat is not None and lon is not None:
            params["lat"] = str(lat)
            params["lon"] = str(lon)

        try:
            with httpx.Client(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
                response = client.get(
                    self.api_url, params=params, headers=self._headers(), follow_redirects=True
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            logger.exception("%s retrieval failed for %r", self.platform_name, product_name)
            raise ProviderError(f"{self.platform_name} request failed: {exc}") from exc
        except ValueError as exc:
            logger.exception("%s returned invalid JSON", self.platform_name)
            raise ProviderError(f"{self.platform_name} returned invalid JSON") from exc

        offers = [self._offer_from_item(item) for item in self._extract_items(payload)]
        return [offer for offer in offers if offer is not None]

    def _extract_items(self, payload: Any) -> Iterable[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []

        for key in self.result_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested = value.get("items") or value.get("products") or value.get("results")
                if isinstance(nested, list):
                    return [item for item in nested if isinstance(item, dict)]

        return [payload]

    def _offer_from_item(self, item: dict[str, Any]) -> ProductOffer | None:
        name = self._first_text(item, "product_name", "name", "title", "display_name")
        price = self._decimal_from(item, "price", "selling_price", "sale_price", "mrp")
        if not name or price is None:
            return None

        delivery = self._decimal_from(
            item, "delivery_charge", "delivery_fee", "shipping_fee", "platform_fee"
        )
        if delivery is None:
            delivery = Decimal("0")

        explicit_total = self._decimal_from(item, "total_price", "total", "payable_amount")
        total = explicit_total if explicit_total is not None else price + delivery

        return ProductOffer(
            platform=self.platform_name,
            provider_key=self.provider_key,
            product_name=name,
            quantity=self._first_text(item, "quantity", "size", "pack_size", "weight") or "",
            price=price,
            delivery_charge=delivery,
            total_price=total,
            product_url=self._first_text(item, "product_url", "url", "deep_link") or "",
            currency=self._first_text(item, "currency") or "INR",
            raw_payload=item,
        )

    @staticmethod
    def _first_text(item: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = item.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    @staticmethod
    def _decimal_from(item: dict[str, Any], *keys: str) -> Decimal | None:
        for key in keys:
            value = item.get(key)
            if value is None or value == "":
                continue
            try:
                return Decimal(str(value).replace(",", "").strip()).quantize(Decimal("0.01"))
            except (InvalidOperation, ValueError):
                continue
        return None
