import sys
import os
import logging

logging.basicConfig(level=logging.DEBUG)

# Ensure the backend directory is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from providers.zepto import ZeptoProvider

def test_zepto():
    print("Initializing ZeptoProvider...")
    # Provide a default valid coordinate to ensure Zepto returns products
    provider = ZeptoProvider(timeout_seconds=30, debug=True)
    
    print("Testing ZeptoProvider (Serviceable Location - Bengaluru)...")
    results = provider.search_product("milk", lat=12.96902, lon=77.75395)
    print(f"Found {len(results)} products.")
    
    print("\nTesting ZeptoProvider (Non-serviceable Location - NYC)...")
    results_non_serv = provider.search_product("milk", lat=40.7128, lon=-74.0060)
    print(f"Found {len(results_non_serv)} products.")
    
    for offer in results[:3]:
        print("-" * 40)
        print(f"Brand: {offer.raw_payload.get('brand')}")
        print(f"Product: {offer.product_name}")
        print(f"Quantity: {offer.quantity}")
        print(f"Price: {offer.price}")
        print(f"MRP: {offer.raw_payload.get('mrp')}")
        print(f"Image URL: {offer.raw_payload.get('image_url')}")
        print(f"Inventory: {offer.raw_payload.get('inventory')}")
        print("-" * 40)

if __name__ == "__main__":
    test_zepto()
