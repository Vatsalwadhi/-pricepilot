from django.urls import path

from .views import (
    ComparisonDetailView,
    DeepComparisonView,
    ProductSearchView,
    ShoppingListParserView,
    ChatAssistantView,
    CartOptimizerView,
    SearchHistoryDeleteView,
    SearchHistoryView,
    ProductHistoryView,
    AlertCreateView,
    ProductOffersView,
)

urlpatterns = [
    path("search", ProductSearchView.as_view(), name="product-search"),
    path("comparison/deep", DeepComparisonView.as_view(), name="deep-comparison"),
    path("assistant/parse-list", ShoppingListParserView.as_view(), name="parse-list"),
    path("assistant/chat", ChatAssistantView.as_view(), name="assistant-chat"),
    path("cart/optimize", CartOptimizerView.as_view(), name="cart-optimize"),
    path("alerts/", AlertCreateView.as_view(), name="alert-create"),
    path("history", SearchHistoryView.as_view(), name="search-history"),
    path("comparison/<int:pk>", ComparisonDetailView.as_view(), name="comparison-detail"),
    path("history/<int:pk>", SearchHistoryDeleteView.as_view(), name="history-delete"),
    path("products/<str:normalized_name>/history", ProductHistoryView.as_view(), name="product-history"),
    path("products/<str:normalized_name>/offers", ProductOffersView.as_view(), name="product-offers"),
]
