import os
import django
import sys
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pricepilot.settings')
django.setup()

from comparison.service import PriceComparisonService
from comparison.normalization import normalize_string, normalize_product_name, normalize_quantity, normalize_identity

logging.disable(logging.CRITICAL)

query = "Amul Masti Pouch Curd"
print(f"Executing search for: '{query}'")

service = PriceComparisonService()
search_history = service.search(query=query)

print(f"\n--- Retrieved {search_history.results.count()} offers ---")

for offer in search_history.results.select_related('platform').filter(total_price__isnull=False):
    brand = offer.raw_payload.get("brand") or offer.raw_payload.get("brand_name") or ""
    
    print(f"\nPlatform: {offer.platform.name}")
    print(f"Original Product Name: {offer.product_name}")
    print(f"Brand: {brand}")
    print(f"Quantity: {offer.quantity}")
    
    n_brand = normalize_string(brand)
    n_name = normalize_product_name(offer.product_name or "")
    n_qty = normalize_quantity(offer.quantity or "")
    
    print(f"Normalized Brand: {n_brand}")
    print(f"Normalized Product Name: {n_name}")
    print(f"Normalized Quantity: {n_qty}")
    print(f"Normalized ID: {offer.normalized_product_name}")

print("\nFinished Analysis.")
