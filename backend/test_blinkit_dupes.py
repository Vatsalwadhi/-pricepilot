import sys
import json

sys.path.append('c:/Users/alwad/Documents/Codex/2026-07-10/build-a-production-ready-full-stack/outputs/pricepilot/backend')

from providers.blinkit import BlinkitProvider

provider = BlinkitProvider()
results = provider.search_product('milk')

print("Total parsed products:", len(results))
for p in results:
    rp = p.raw_payload
    print(f"ID: {rp.get('product_id')} | Name: {p.product_name} | Image: {rp.get('image_url')}")
