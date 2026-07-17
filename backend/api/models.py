from django.db import models


class Platform(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    provider_key = models.CharField(max_length=80, unique=True)
    base_url = models.URLField(blank=True)
    brand_color = models.CharField(max_length=7, blank=True)
    logo_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    display_name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255, db_index=True)
    quantity = models.CharField(max_length=80, blank=True)
    brand = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["normalized_name", "quantity"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["normalized_name", "quantity", "brand"],
                name="unique_normalized_product_variant",
            )
        ]
        ordering = ["display_name"]

    def __str__(self) -> str:
        return f"{self.display_name} {self.quantity}".strip()


class SearchHistory(models.Model):
    query = models.CharField(max_length=255)
    normalized_query = models.CharField(max_length=255, db_index=True)
    cheapest_platform = models.ForeignKey(
        Platform,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cheapest_searches",
    )
    cheapest_total_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    highest_total_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    savings = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.query


class ComparisonResult(models.Model):
    search = models.ForeignKey(
        SearchHistory, on_delete=models.CASCADE, related_name="results"
    )
    platform = models.ForeignKey(
        Platform, null=True, blank=True, on_delete=models.SET_NULL, related_name="results"
    )
    product = models.ForeignKey(
        Product, null=True, blank=True, on_delete=models.SET_NULL, related_name="results"
    )
    product_name = models.CharField(max_length=255, blank=True)
    normalized_product_name = models.CharField(max_length=255, blank=True, db_index=True)
    quantity = models.CharField(max_length=80, blank=True)
    currency = models.CharField(max_length=8, default="INR")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_charge = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, db_index=True
    )
    product_url = models.URLField(blank=True)
    is_cheapest = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["total_price", "delivery_charge", "price", "platform__name"]
        indexes = [
            models.Index(fields=["search", "total_price"]),
        ]

    def __str__(self) -> str:
        platform = self.platform.name if self.platform else "Unknown"
        return f"{platform}: {self.product_name or self.error_message}"

class ProductIdentityCache(models.Model):
    cache_key = models.CharField(max_length=512, unique=True, db_index=True)
    raw_title = models.CharField(max_length=512)
    brand = models.CharField(max_length=120, blank=True)
    family = models.CharField(max_length=120, blank=True)
    variant = models.CharField(max_length=120, blank=True)
    flavour = models.CharField(max_length=120, blank=True)
    size = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=120, blank=True)
    canonical_name = models.CharField(max_length=255)
    confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.canonical_name


class SubstituteCache(models.Model):
    product_a_name = models.CharField(max_length=255, db_index=True)
    product_b_name = models.CharField(max_length=255, db_index=True)
    comparable = models.BooleanField(default=False)
    score = models.FloatField(default=0.0)
    reason = models.TextField(blank=True)
    same_brand = models.BooleanField(default=False)
    same_variant = models.BooleanField(default=False)
    same_quantity = models.BooleanField(default=False)
    same_category = models.BooleanField(default=False)
    preferred_match = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["product_a_name", "product_b_name"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["product_a_name", "product_b_name"],
                name="unique_substitute_pair",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product_a_name} vs {self.product_b_name} ({self.score})"


class ProductValidationCache(models.Model):
    product_a_raw = models.CharField(max_length=255, db_index=True)
    product_b_raw = models.CharField(max_length=255, db_index=True)
    same_product = models.BooleanField(default=False)
    confidence = models.FloatField(default=0.0)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["product_a_raw", "product_b_raw"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["product_a_raw", "product_b_raw"],
                name="unique_validation_pair",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product_a_raw} vs {self.product_b_raw} (Same: {self.same_product})"


class PriceAlert(models.Model):
    product_name = models.CharField(max_length=255)
    normalized_product_name = models.CharField(max_length=255, db_index=True)
    target_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Alert for {self.product_name} < {self.target_price}"
