from rest_framework import serializers

from .models import ComparisonResult, Platform, Product, SearchHistory


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ["id", "name", "slug", "provider_key", "is_active", "brand_color", "logo_url"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "display_name", "normalized_name", "quantity", "brand"]


class ComparisonResultSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    price_difference_from_cheapest = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    mrp = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()

    class Meta:
        model = ComparisonResult
        fields = [
            "id",
            "platform",
            "product",
            "product_name",
            "normalized_product_name",
            "quantity",
            "currency",
            "price",
            "delivery_charge",
            "total_price",
            "product_url",
            "is_cheapest",
            "error_message",
            "price_difference_from_cheapest",
            "image",
            "mrp",
            "brand",
            "created_at",
        ]

    def get_price_difference_from_cheapest(self, obj: ComparisonResult) -> str | None:
        cheapest = self.context.get("cheapest_total_price")
        if obj.total_price is None or cheapest is None:
            return None
        return str(obj.total_price - cheapest)

    def get_image(self, obj: ComparisonResult) -> str | None:
        return obj.raw_payload.get("image_url") or obj.raw_payload.get("image")

    def get_mrp(self, obj: ComparisonResult) -> float | None:
        return obj.raw_payload.get("mrp") or obj.raw_payload.get("market_price")

    def get_brand(self, obj: ComparisonResult) -> str | None:
        return obj.raw_payload.get("brand") or obj.raw_payload.get("brand_name")


class SearchHistoryListSerializer(serializers.ModelSerializer):
    cheapest_platform = PlatformSerializer(read_only=True)
    result_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = SearchHistory
        fields = [
            "id",
            "query",
            "normalized_query",
            "cheapest_platform",
            "cheapest_total_price",
            "highest_total_price",
            "savings",
            "result_count",
            "created_at",
        ]


class SearchHistoryDetailSerializer(serializers.ModelSerializer):
    cheapest_platform = PlatformSerializer(read_only=True)
    results = serializers.SerializerMethodField()

    class Meta:
        model = SearchHistory
        fields = [
            "id",
            "query",
            "normalized_query",
            "cheapest_platform",
            "cheapest_total_price",
            "highest_total_price",
            "savings",
            "results",
            "created_at",
        ]

    def get_results(self, obj: SearchHistory) -> list[dict]:
        from comparison.aggregators import aggregate_discovery_results
        
        # We fetch all successful results related to this search
        # Note: We can also pass all results (including errors) if we want to show errors,
        # but the aggregator ignores errors anyway for discovery purposes.
        all_results = list(obj.results.select_related("platform", "product").all())
        
        return aggregate_discovery_results(all_results)


class ProductSearchSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=255, trim_whitespace=True)
    lat = serializers.FloatField(required=False, allow_null=True)
    lon = serializers.FloatField(required=False, allow_null=True)
