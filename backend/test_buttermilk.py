import os
import django
import sys
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

os.environ["DEBUG_IDENTITY"] = "1"

from comparison.identity_ai import normalize_product
from providers.base import ProductOffer

offers = [
    ProductOffer(product_name="Amul Masti Spiced Salted Buttermilk", quantity="200 ml", price=Decimal("15"), delivery_charge=Decimal("0"), total_price=Decimal("15"), platform="Blinkit", provider_key="blinkit", raw_payload={"brand": "Amul", "category": "Dairy"}),
    ProductOffer(product_name="Amul Masti Spiced Buttermilk", quantity="200 ml", price=Decimal("15"), delivery_charge=Decimal("0"), total_price=Decimal("15"), platform="Zepto", provider_key="zepto", raw_payload={"brand": "Amul", "category": "Dairy"}),
]

print("--- Testing AI Identity Parser with Buttermilk ---")
for offer in offers:
    print(f"\nProcessing: {offer.product_name} ({offer.quantity})")
    identity = normalize_product(offer)
    print(f"Final Identity: {identity}")
