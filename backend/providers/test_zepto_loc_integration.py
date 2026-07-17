import os
from zepto import ZeptoProvider
import json

def test():
    provider = ZeptoProvider(debug=True)
    results = provider.search_product("milk", lat=28.5355, lon=77.3910)
    print(f"Found {len(results)} products.")
    for p in results[:3]:
        print(p.product_name, p.price, p.raw_payload.get('store_id'), p.raw_payload.get('eta'))
        
    print("Caching test: ")
    results2 = provider.search_product("bread", lat=28.5355, lon=77.3910)
    print(f"Found {len(results2)} products on second search.")

if __name__ == "__main__":
    test()
