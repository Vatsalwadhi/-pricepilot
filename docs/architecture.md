# Architecture

```text
React + Tailwind
  |
  | HTTP
  v
Django REST Framework
  |
  v
PriceComparisonService
  |
  v
Provider classes
  |
  v
Configured legal platform data sources
```

The provider boundary keeps platform-specific retrieval separate from API and persistence code. `PriceComparisonService` handles orchestration, persistence, ranking, and failure recording.

## Provider Contract

Every provider exposes:

```python
search_product(product_name: str) -> list[ProductOffer]
```

`ProductOffer` contains platform, product name, quantity, price, delivery charge, total price, currency, URL, and raw payload.
