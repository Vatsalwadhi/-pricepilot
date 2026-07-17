import sys
import json

sys.path.append('c:/Users/alwad/Documents/Codex/2026-07-10/build-a-production-ready-full-stack/outputs/pricepilot/backend')

from providers.blinkit import BlinkitProvider

provider = BlinkitProvider()
results = provider.search_product('milk')

if results:
    product = results[0]
    print("Found image url:", product.raw_payload.get("image_url"))
else:
    print('No results')
