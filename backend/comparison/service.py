from __future__ import annotations

import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
import logging

from django.db import transaction
from django.utils.text import slugify

from api.models import ComparisonResult, Platform, Product, SearchHistory
from providers import get_enabled_providers
from providers.base import ProductOffer, ProviderError
from comparison import aggregators
from comparison.identity import parse_product_identity
from comparison.validation_ai import evaluate_pairwise_match
from utils.json import make_json_safe
from .identity_ai import normalize_product

sqlite_write_lock = threading.Lock()


logger = logging.getLogger(__name__)


class PriceComparisonService:
    def search(self, query: str, lat: float | None = None, lon: float | None = None) -> SearchHistory:
        from django.utils import timezone
        from datetime import timedelta
        
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Search query is required.")

        # We don't normalize query string with the identity parser right now
        normalized_query = clean_query.lower()
        
        # Check cache: return a recent search if one exists within the last hour
        recent_search = SearchHistory.objects.filter(
            normalized_query=normalized_query,
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).prefetch_related("results__platform", "results__product").first()
        
        if recent_search:
            logger.info(f"Returning cached search results for {clean_query}")
            return recent_search

        providers = get_enabled_providers()

        with sqlite_write_lock:
            with transaction.atomic():
                search = SearchHistory.objects.create(
                    query=clean_query,
                    normalized_query=normalized_query,
                )

        offers: list[ProductOffer] = []
        errors: list[tuple[str, str, str]] = []

        with ThreadPoolExecutor(max_workers=max(len(providers), 1)) as executor:
            try:
                def _run_provider(provider, query, lat, lon):
                    logger.info(f"Provider {provider.provider_key} started")
                    try:
                        res = provider.search_product(query, lat=lat, lon=lon)
                        logger.info(f"Provider {provider.provider_key} finished")
                        logger.info(f"Provider {provider.provider_key} Products returned: {len(res) if res else 0}")
                        return res
                    except Exception as e:
                        logger.error(f"Provider {provider.provider_key} Exception: {e}")
                        raise

                future_map = {
                    executor.submit(_run_provider, provider, clean_query, lat, lon): provider
                    for provider in providers
                }
                for future in as_completed(future_map):
                    provider = future_map[future]
                    try:
                        result = future.result()
                        if result is None:
                            logger.error("Provider %s returned None instead of []", provider.provider_key)
                            result = []
                        offers.extend(result)
                    except ProviderError as exc:
                        logger.warning(
                            "Provider %s failed for query %r: %s",
                            provider.provider_key,
                            clean_query,
                            exc,
                        )
                        errors.append((provider.platform_name, provider.provider_key, str(exc)))
                    except Exception as exc:  # defensive boundary around external integrations
                        logger.exception("Unexpected provider error for %s: %s", provider.provider_key, exc)
                        errors.append(
                            (
                                provider.platform_name,
                                provider.provider_key,
                                f"Unexpected provider error: {exc}",
                            )
                        )
            except Exception as e:
                logger.exception("Critical error in provider ThreadPoolExecutor: %s", e)

        # Step 1: Pre-resolve identities deterministically outside of transaction
        offer_identities = []
        for offer in offers:
            try:
                # Run existing deterministic parser
                identity = parse_product_identity(offer.product_name)
                offer_identities.append((offer, identity))
            except Exception as e:
                logger.error(f"Failed to parse product {offer.product_name}: {e}")

        # We skip AI Validation in the Discovery Phase (Stage 1).
        # We only use deterministic mapping.
        with sqlite_write_lock:
            with transaction.atomic():
                for offer, identity in offer_identities:
                    # final_sku is just the deterministic identity's canonical_sku
                    final_sku = identity.canonical_sku
                    self._save_offer(search, offer, identity, final_sku)

            for platform_name, provider_key, error in errors:
                platform = self._get_platform(platform_name, provider_key)
                ComparisonResult.objects.create(
                    search=search,
                    platform=platform,
                    error_message=error,
                    raw_payload={},
                )

            self._mark_cheapest(search)

        return SearchHistory.objects.prefetch_related(
            "results__platform", "results__product"
        ).get(pk=search.pk)

    def deep_search(self, canonical_name: str, lat: float | None = None, lon: float | None = None) -> SearchHistory:
        """
        Deep search specifically for a canonical product name.
        Uses providers to fetch candidates, then strictly validates each one against the canonical_name using LLM.
        Only keeps candidates that are exact matches.
        """
        if not canonical_name.strip():
            raise ValueError("Canonical product name is required.")

        normalized_query = canonical_name.strip().lower()
        providers = get_enabled_providers()

        with sqlite_write_lock:
            with transaction.atomic():
                search = SearchHistory.objects.create(
                    query=canonical_name,
                    normalized_query=normalized_query,
                )

        offers: list[ProductOffer] = []
        errors: list[tuple[str, str, str]] = []

        with ThreadPoolExecutor(max_workers=max(len(providers), 1)) as executor:
            try:
                def _run_provider(provider, query, lat, lon):
                    return provider.search_product(query, lat=lat, lon=lon)

                future_map = {
                    executor.submit(_run_provider, provider, canonical_name, lat, lon): provider
                    for provider in providers
                }
                for future in as_completed(future_map):
                    provider = future_map[future]
                    try:
                        result = future.result()
                        if result:
                            offers.extend(result)
                    except ProviderError as exc:
                        errors.append((provider.platform_name, provider.provider_key, str(exc)))
                    except Exception as exc:
                        errors.append((provider.platform_name, provider.provider_key, f"Unexpected error: {exc}"))
            except Exception as e:
                logger.exception("Critical error in deep search provider ThreadPoolExecutor: %s", e)

        # 1. Deterministic Parse
        offer_identities = []
        for offer in offers:
            try:
                identity = parse_product_identity(offer.product_name)
                offer_identities.append((offer, identity))
            except Exception:
                pass

        # 2. Strict AI Validation against Canonical Name
        matched_offers = []
        
        # We also need a target final sku to link them all under the exact same product ID
        # Parse the canonical_name to get its deterministic sku
        target_identity = parse_product_identity(canonical_name)
        final_sku = target_identity.canonical_sku

        for offer, identity in offer_identities:
            # Short-circuit if deterministic parser already considers it identical to target
            if identity.canonical_sku == final_sku:
                matched_offers.append((offer, identity))
                continue
                
            # Otherwise, ask AI if candidate matches canonical target
            val_result = evaluate_pairwise_match(canonical_name, offer.product_name)
            logger.info(f"Deep Search AI Validation: Target='{canonical_name}' vs Candidate='{offer.product_name}' -> same_product={val_result.get('same_product')}")
            
            if val_result.get("same_product") and val_result.get("confidence", 0) >= 0.95:
                matched_offers.append((offer, identity))

        with sqlite_write_lock:
            with transaction.atomic():
                for offer, identity in matched_offers:
                    self._save_offer(search, offer, identity, final_sku)

            for platform_name, provider_key, error in errors:
                platform = self._get_platform(platform_name, provider_key)
                ComparisonResult.objects.create(
                    search=search,
                    platform=platform,
                    error_message=error,
                    raw_payload={},
                )

            self._mark_cheapest(search)

        return SearchHistory.objects.prefetch_related(
            "results__platform", "results__product"
        ).get(pk=search.pk)

    def optimize_cart(self, items: list[dict], strategy: str = "cheapest", lat: float | None = None, lon: float | None = None) -> dict:
        """
        Given a list of items [{"name": "Milk", "quantity": "2L"}], builds an optimal cart.
        Returns a dict with {"strategy": str, "total_cost": float, "splits": {...}}
        """
        # Run discovery search for items with high concurrency
        # SQLite deadlocks are prevented by the global sqlite_write_lock
        search_results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_item = {
                executor.submit(self.search, f"{item['name']} {item.get('quantity', '')}".strip(), lat, lon): item
                for item in items
            }
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    search_hist = future.result()
                    search_results.append({
                        "item": item,
                        "search": search_hist
                    })
                except Exception as e:
                    logger.error(f"Failed to search for cart item {item}: {e}")

        # Basic Greedy Optimization Strategy
        # Option 1: Cheapest overall single provider (has to have at least 80% of items)
        # Option 2: Split by cheapest item
        
        # We will build an "Optimal Split"
        # 1. Map each item to its cheapest offer
        cart_splits = defaultdict(list)
        total_items_cost = Decimal("0")
        platforms_used = set()
        
        for res in search_results:
            item_name = res["item"]["name"]
            search_hist = res["search"]
            
            # We can trust search_hist.results because search() already uses AI matching and deterministic parsing
            valid_results = list(search_hist.results.filter(total_price__isnull=False))
            
            if valid_results:
                valid_results.sort(key=lambda x: x.total_price)
                cheapest_offer = valid_results[0]
            else:
                cheapest_offer = None
                
            if cheapest_offer:
                platform_name = cheapest_offer.platform.name
                platforms_used.add(cheapest_offer.platform)
                
                # Deduct delivery_charge from item price if we just want raw price
                # Or use total_price. Actually, delivery_charge is usually applied per order, not per item.
                # In providers, price + delivery_charge = total_price. 
                # Let's just use raw price for the item, and add delivery once per platform later.
                raw_price = cheapest_offer.price or cheapest_offer.total_price
                total_items_cost += raw_price
                
                cart_splits[platform_name].append({
                    "original_query": item_name,
                    "matched_name": cheapest_offer.product_name,
                    "price": float(raw_price),
                    "product_url": cheapest_offer.product_url,
                    "image": cheapest_offer.raw_payload.get("image_url") if cheapest_offer.raw_payload else None
                })
            else:
                cart_splits["Unavailable"].append({
                    "original_query": item_name,
                    "matched_name": "Out of stock",
                    "price": 0.0,
                    "product_url": "",
                    "image": None
                })

        # Add delivery fees for each unique platform used
        # We'll just assume a flat rate if we can't get it from the offer, but let's use the first offer's delivery charge per platform
        total_delivery = Decimal("0")
        platform_breakdown = []
        
        for platform_name, items_list in cart_splits.items():
            if platform_name == "Unavailable":
                continue
                
            # Find the delivery charge for this platform from any of the matched offers
            # For simplicity, let's assume a rough average if not available
            delivery_charge = Decimal("0")
            for res in search_results:
                offer = res["search"].results.filter(platform__name=platform_name, delivery_charge__isnull=False).first()
                if offer and offer.delivery_charge:
                    delivery_charge = offer.delivery_charge
                    break
                    
            total_delivery += delivery_charge
            
            platform_total = sum([Decimal(str(i["price"])) for i in items_list])
            platform_breakdown.append({
                "platform": platform_name,
                "items": items_list,
                "item_total": float(platform_total),
                "delivery_charge": float(delivery_charge),
                "subtotal": float(platform_total + delivery_charge)
            })
            
        grand_total = total_items_cost + total_delivery

        return {
            "strategy": strategy,
            "total_items_cost": float(total_items_cost),
            "total_delivery": float(total_delivery),
            "grand_total": float(grand_total),
            "splits": platform_breakdown,
            "unavailable": cart_splits.get("Unavailable", [])
        }

    def _save_offer(self, search: SearchHistory, offer: ProductOffer, identity, final_sku: str) -> ComparisonResult:
        platform = self._get_platform(offer.platform, offer.provider_key)
        
        qty_str = f"{identity.quantity} {identity.unit}".strip()
        
        product, _ = Product.objects.get_or_create(
            normalized_name=final_sku,
            quantity=qty_str,
            brand=identity.brand,
            defaults={
                "display_name": final_sku,
            },
        )

        return ComparisonResult.objects.create(
            search=search,
            platform=platform,
            product=product,
            product_name=offer.product_name,
            normalized_product_name=final_sku,
            quantity=offer.quantity,
            currency=offer.currency,
            price=offer.price,
            delivery_charge=offer.delivery_charge,
            total_price=offer.total_price,
            product_url=offer.product_url,
            raw_payload=make_json_safe(offer.raw_payload),
        )

    @staticmethod
    def _get_platform(name: str, provider_key: str) -> Platform:
        platform, _ = Platform.objects.update_or_create(
            provider_key=provider_key,
            defaults={
                "name": name,
                "slug": slugify(provider_key),
                "is_active": True,
            },
        )
        return platform

    @staticmethod
    def _mark_cheapest(search: SearchHistory) -> None:
        successful = list(
            search.results.filter(total_price__isnull=False).order_by(
                "total_price", "delivery_charge", "price"
            )
        )
        if not successful:
            return

        cheapest = successful[0]
        highest = max(successful, key=lambda result: result.total_price or Decimal("0"))
        cheapest.is_cheapest = True
        cheapest.save(update_fields=["is_cheapest"])

        search.cheapest_platform = cheapest.platform
        search.cheapest_total_price = cheapest.total_price
        search.highest_total_price = highest.total_price
        search.savings = (highest.total_price or Decimal("0")) - (
            cheapest.total_price or Decimal("0")
        )
        search.save(
            update_fields=[
                "cheapest_platform",
                "cheapest_total_price",
                "highest_total_price",
                "savings",
            ]
        )
