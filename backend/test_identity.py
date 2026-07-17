import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from comparison.identity import parse_product_identity

products = [
    ("Amul Taaza Toned Milk", "Amul", ""),
    ("Amul Taaza Homogenised Toned Milk (Tetra Pack)", "Amul", "1pack - 200ml"),
    ("Amul Taaza Toned Fresh Milk | Pouch", "Amul", "1pack - 500ml"),
    ("Mother Dairy FIT Life Homogenized Double Toned Milk (450 ml)", "Mother Dairy", "450 ml"),
    ("Nandini Good Life Toned UHT Milk (Fino Pouch)", "Nandini", "1pack - 180ml"),
    ("Nandini Toned Fresh Milk | Pouch", "Nandini", "1pack - 500ml"),
    ("Heritage Toned Fresh Milk | Pouch", "Heritage", "1pack - 500ml"),
    ("Heritage Nourish+ Fresh Milk | 18g Protein | Pouch", "Heritage", "1pack - 500ml"),
    ("Akshayakalpa Amrutha - A2 Farm Organic Cow Fresh Milk | Pouch", "Akshayakalpa", "1pack - 500ml")
]

print("--- Testing Identity Parser ---")
for p_name, p_brand, p_qty in products:
    print(f"\nOriginal: {p_name}")
    print(f"Raw Qty: {p_qty}")
    identity = parse_product_identity(p_name, p_brand, p_qty)
    print(f"Parsed Brand: {identity.brand}")
    print(f"Parsed Family: {identity.family}")
    print(f"Parsed Variant: {identity.variant}")
    print(f"Parsed Quantity: {identity.quantity}")
    print(f"Parsed Unit: {identity.unit}")
    print(f"Canonical SKU: {identity.canonical_sku}")
