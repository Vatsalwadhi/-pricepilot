import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

os.environ["DEBUG_IDENTITY"] = "1"

from comparison.identity_ai import normalize_product
from providers.base import ProductOffer
from decimal import Decimal

offers = [
    ProductOffer(product_name="Amul Taaza Homogenised Toned Milk (Tetra Pack)", quantity="1pack - 200ml", price=Decimal("10"), delivery_charge=Decimal("10"), total_price=Decimal("20"), platform="Blinkit", provider_key="blinkit", raw_payload={"brand": "Amul", "category": "Milk"}),
    ProductOffer(product_name="Amul Taaza Toned Milk", quantity="200 ml", price=Decimal("10"), delivery_charge=Decimal("10"), total_price=Decimal("20"), platform="Zepto", provider_key="zepto", raw_payload={"brand": "Amul", "category": "Milk"}),
    ProductOffer(product_name="Amul Taaza Homogenised Toned Milk (Tetra Pack)", quantity="1pack - 200ml", price=Decimal("10"), delivery_charge=Decimal("10"), total_price=Decimal("20"), platform="Instamart", provider_key="instamart", raw_payload={"brand": "Amul", "category": "Milk"}),
]

print("--- Testing AI Identity Parser ---")
for offer in offers:
    print(f"\nProcessing: {offer.product_name} ({offer.quantity})")
    identity = normalize_product(offer)
    print(f"Final Identity: {identity}")
