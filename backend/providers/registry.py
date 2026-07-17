from __future__ import annotations

from .base import BaseProvider
from .bigbasket import BigBasketProvider
from .blinkit import BlinkitProvider
from .swiggy_instamart import SwiggyInstamartProvider
from .zepto import ZeptoProvider


PROVIDER_CLASSES: tuple[type[BaseProvider], ...] = (
    BlinkitProvider,
    ZeptoProvider,
    SwiggyInstamartProvider,
    BigBasketProvider,
)


def get_enabled_providers() -> list[BaseProvider]:
    return [provider_class() for provider_class in PROVIDER_CLASSES]
