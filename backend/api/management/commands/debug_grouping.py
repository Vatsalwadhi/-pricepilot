from django.core.management.base import BaseCommand
from comparison.service import PriceComparisonService
from comparison.identity import parse_product_identity
import logging

class Command(BaseCommand):
    help = 'Generate grouping debugging report'

    def handle(self, *args, **options):
        # Disable overly verbose logging
        logging.disable(logging.CRITICAL)

        query = "milk"
        
        service = PriceComparisonService()
        search_history = service.search(query=query)

        # 1. Fetch all results
        offers = search_history.results.select_related('platform', 'product').all()
        
        # Group by platform
        platform_offers = {}
        for offer in offers:
            p_name = offer.platform.name if offer.platform else "Unknown"
            if p_name not in platform_offers:
                platform_offers[p_name] = []
            platform_offers[p_name].append(offer)

        # Group by normalized identity
        grouped_offers = {}
        for offer in offers:
            if not offer.total_price:
                continue # Skip errors
            n_name = offer.normalized_product_name
            if n_name not in grouped_offers:
                grouped_offers[n_name] = []
            grouped_offers[n_name].append(offer)

        # Print Provider Sections
        for p_name, p_offers in platform_offers.items():
            valid_offers = [o for o in p_offers if o.total_price is not None]
            
            self.stdout.write("================================================")
            self.stdout.write(f"Provider: {p_name}")
            self.stdout.write(f"Products returned: {len(valid_offers)}")
            
            for i, offer in enumerate(valid_offers, 1):
                brand = offer.raw_payload.get("brand") or offer.raw_payload.get("brand_name") or ""
                self.stdout.write(f"\nProduct {i}")
                self.stdout.write(f"Original name: {offer.product_name}")
                self.stdout.write(f"Normalized name: {offer.normalized_product_name}")
                self.stdout.write(f"Brand: {brand}")
                self.stdout.write(f"Quantity: {offer.quantity}")

        self.stdout.write("\n================================================")
        self.stdout.write("After all providers finish:")
        self.stdout.write("Print every grouping created by the comparison engine.")

        group_num = 1
        successfully_grouped_count = 0
        unmatched_count = 0

        for n_name, g_offers in grouped_offers.items():
            self.stdout.write(f"\nGroup {group_num}")
            
            # The canonical product name (we just pick the first offer's product_name)
            canonical = g_offers[0].product_name
            
            self.stdout.write(f"Canonical Product")
            self.stdout.write(f"{canonical} ({n_name})")
            self.stdout.write(f"Platforms")
            
            platforms_in_group = [o.platform.name for o in g_offers if o.platform]
            for p in platforms_in_group:
                self.stdout.write(f"{p}")
                
            self.stdout.write("------------------------------------------------")
            
            if len(platforms_in_group) > 1:
                successfully_grouped_count += len(platforms_in_group)
            else:
                unmatched_count += len(platforms_in_group)
                
            group_num += 1

        self.stdout.write("\n================================================")
        self.stdout.write("SUMMARY:")
        self.stdout.write("Products returned by each provider:")
        for p_name, p_offers in platform_offers.items():
            valid_count = len([o for o in p_offers if o.total_price is not None])
            self.stdout.write(f"  {p_name}: {valid_count}")
            
        self.stdout.write(f"\nProducts successfully grouped (in a group with >=2 platforms): {successfully_grouped_count}")
        self.stdout.write(f"Products unmatched (only 1 platform in group): {unmatched_count}")
        
        # Discarded usually means failed/error offers in this context
        discarded_count = len([o for o in offers if o.total_price is None])
        self.stdout.write(f"Products discarded (errors/no price): {discarded_count}")
