import dataclasses
from decimal import Decimal
from typing import Any, Dict, List, Optional
from collections import defaultdict
from api.models import ComparisonResult, Platform

@dataclasses.dataclass
class ProductDiscovery:
    id: str
    normalized_id: str
    brand: str
    display_name: str
    quantity: str
    variant: str
    image: str
    category: str
    available_platforms: List[dict]
    lowest_price: Decimal
    highest_price: Decimal
    offers_count: int

def aggregate_discovery_results(results: List[ComparisonResult]) -> List[dict]:
    """
    Groups ComparisonResult objects into ProductDiscovery objects based on their normalized identity.
    Returns a list of dicts suitable for serialization.
    """
    grouped = defaultdict(list)
    
    for result in results:
        if result.error_message or not result.total_price:
            continue
        grouped[result.normalized_product_name].append(result)
        
    discoveries = []
    
    for normalized_id, items in grouped.items():
        if not items:
            continue
            
        prices = [item.total_price for item in items]
        lowest_price = min(prices)
        highest_price = max(prices)
        
        # Pick the best representative item for display data
        # Usually the one with the lowest price, but we prefer one with an image if possible
        rep_item = next((item for item in sorted(items, key=lambda x: x.total_price) 
                         if item.raw_payload.get("image_url") or item.raw_payload.get("image")), items[0])
        
        platforms_seen = set()
        available_platforms = []
        for item in items:
            if item.platform and item.platform.name not in platforms_seen:
                platforms_seen.add(item.platform.name)
                available_platforms.append({
                    "name": item.platform.name,
                    "logo_url": item.platform.logo_url,
                    "brand_color": item.platform.brand_color,
                    "provider_key": item.platform.provider_key,
                })
                
        # Sort platforms by name
        available_platforms.sort(key=lambda x: x["name"])
        
        brand = rep_item.raw_payload.get("brand") or rep_item.raw_payload.get("brand_name") or ""
        image = rep_item.raw_payload.get("image_url") or rep_item.raw_payload.get("image") or ""
        
        discovery = ProductDiscovery(
            id=str(rep_item.id), # We just use the representative item's ID or the normalized_id itself as the primary key for the frontend list
            normalized_id=normalized_id,
            brand=brand,
            display_name=rep_item.product_name,
            quantity=rep_item.quantity,
            variant="", # Variant is currently embedded in name/qty
            image=image,
            category="",
            available_platforms=available_platforms,
            lowest_price=lowest_price,
            highest_price=highest_price,
            offers_count=len(items)
        )
        discoveries.append(dataclasses.asdict(discovery))
        
    # Sort by lowest price or by offers_count
    # Usually sorting by offers_count descending (most popular) then price ascending is good
    discoveries.sort(key=lambda x: (-x["offers_count"], x["lowest_price"]))
    
    return discoveries
