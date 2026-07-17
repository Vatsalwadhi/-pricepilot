from .base import HttpJsonProvider


class BigBasketProvider(HttpJsonProvider):
    platform_name = "BigBasket"
    provider_key = "bigbasket"
    api_url_env = "BIGBASKET_API_URL"
    token_env = "BIGBASKET_API_TOKEN"
