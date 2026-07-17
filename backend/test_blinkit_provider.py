from __future__ import annotations

import json
import logging

from providers.blinkit import BlinkitProvider


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    products = BlinkitProvider().search_product("milk")
    print(json.dumps(products, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
