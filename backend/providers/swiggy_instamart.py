from .base import HttpJsonProvider


class SwiggyInstamartProvider(HttpJsonProvider):
    platform_name = "Swiggy Instamart"
    provider_key = "swiggy_instamart"
    api_url_env = "SWIGGY_INSTAMART_API_URL"
    token_env = "SWIGGY_INSTAMART_API_TOKEN"
