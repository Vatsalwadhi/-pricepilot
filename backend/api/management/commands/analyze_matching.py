from django.core.management.base import BaseCommand
from comparison.service import PriceComparisonService
from comparison.normalization import normalize_string, normalize_product_name, normalize_quantity, normalize_identity
import logging

class Command(BaseCommand):
    help = 'Analyze matching logic'

    def handle(self, *args, **options):
        logging.disable(logging.CRITICAL)

        query = "Amul Masti Pouch Curd"
        self.stdout.write(f"Executing search for: '{query}'")

        service = PriceComparisonService()
        search_history = service.search(query=query)

        self.stdout.write(f"\n--- Retrieved {search_history.results.count()} offers ---")

        for offer in search_history.results.select_related('platform').filter(total_price__isnull=False):
            brand = offer.raw_payload.get("brand") or offer.raw_payload.get("brand_name") or ""
            
            self.stdout.write(f"\nPlatform: {offer.platform.name}")
            self.stdout.write(f"Original Product Name: {offer.product_name}")
            self.stdout.write(f"Brand: {brand}")
            self.stdout.write(f"Quantity: {offer.quantity}")
            
            n_brand = normalize_string(brand)
            n_name = normalize_product_name(offer.product_name or "")
            n_qty = normalize_quantity(offer.quantity or "")
            
            self.stdout.write(f"Normalized Brand: {n_brand}")
            self.stdout.write(f"Normalized Product Name: {n_name}")
            self.stdout.write(f"Normalized Quantity: {n_qty}")
            self.stdout.write(f"Normalized ID: {offer.normalized_product_name}")

        self.stdout.write("\nFinished Analysis.")
