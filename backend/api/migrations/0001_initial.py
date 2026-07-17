from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Platform",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("provider_key", models.CharField(max_length=80, unique=True)),
                ("base_url", models.URLField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(max_length=255)),
                ("normalized_name", models.CharField(db_index=True, max_length=255)),
                ("quantity", models.CharField(blank=True, max_length=80)),
                ("brand", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["display_name"]},
        ),
        migrations.CreateModel(
            name="SearchHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("query", models.CharField(max_length=255)),
                ("normalized_query", models.CharField(db_index=True, max_length=255)),
                ("cheapest_total_price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("highest_total_price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("savings", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("cheapest_platform", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="cheapest_searches", to="api.platform")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ComparisonResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(blank=True, max_length=255)),
                ("normalized_product_name", models.CharField(blank=True, db_index=True, max_length=255)),
                ("quantity", models.CharField(blank=True, max_length=80)),
                ("currency", models.CharField(default="INR", max_length=8)),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("delivery_charge", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("total_price", models.DecimalField(blank=True, db_index=True, decimal_places=2, max_digits=10, null=True)),
                ("product_url", models.URLField(blank=True)),
                ("is_cheapest", models.BooleanField(default=False)),
                ("error_message", models.TextField(blank=True)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("platform", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="results", to="api.platform")),
                ("product", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="results", to="api.product")),
                ("search", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="results", to="api.searchhistory")),
            ],
            options={"ordering": ["total_price", "delivery_charge", "price", "platform__name"]},
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["normalized_name", "quantity"], name="api_product_normali_8c26de_idx"),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(fields=("normalized_name", "quantity", "brand"), name="unique_normalized_product_variant"),
        ),
        migrations.AddIndex(
            model_name="comparisonresult",
            index=models.Index(fields=["search", "total_price"], name="api_compari_search__585c5f_idx"),
        ),
    ]
