from django.contrib import admin

from .models import ComparisonResult, Platform, Product, SearchHistory


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("name", "provider_key", "is_active", "base_url", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "provider_key")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("display_name", "quantity", "brand", "normalized_name")
    search_fields = ("display_name", "normalized_name", "brand")


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "query",
        "cheapest_platform",
        "cheapest_total_price",
        "savings",
        "created_at",
    )
    search_fields = ("query", "normalized_query")
    date_hierarchy = "created_at"


@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = (
        "search",
        "platform",
        "product_name",
        "quantity",
        "price",
        "delivery_charge",
        "total_price",
        "is_cheapest",
    )
    list_filter = ("platform", "is_cheapest")
    search_fields = ("product_name", "normalized_product_name", "error_message")
