from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import PriceAlert
from comparison.service import PriceComparisonService

class Command(BaseCommand):
    help = 'Checks active price alerts and notifies if price drops below target'

    def handle(self, *args, **options):
        alerts = PriceAlert.objects.filter(is_active=True)
        if not alerts.exists():
            self.stdout.write(self.style.SUCCESS("No active price alerts."))
            return

        service = PriceComparisonService()

        for alert in alerts:
            self.stdout.write(f"Checking alert for: {alert.product_name} (Target: {alert.target_price})")
            
            try:
                # Perform deep search (which bypasses cache and hits providers directly)
                search_history = service.deep_search(alert.product_name, lat=None, lon=None)
                
                # Find the absolute cheapest offer
                cheapest_offer = search_history.results.filter(total_price__isnull=False).order_by("total_price").first()
                
                if cheapest_offer and cheapest_offer.total_price <= alert.target_price:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"🚨 PRICE DROP ALERT! 🚨\n"
                            f"Product: {alert.product_name}\n"
                            f"Target: ₹{alert.target_price} | Current: ₹{cheapest_offer.total_price} "
                            f"on {cheapest_offer.platform.name}!\n"
                            f"Link: {cheapest_offer.product_url}\n"
                        )
                    )
                    
                    # Deactivate the alert so it doesn't spam (or we could keep it active)
                    alert.is_active = False
                    
                alert.last_checked_at = timezone.now()
                alert.save()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to check alert for {alert.product_name}: {e}"))

        self.stdout.write(self.style.SUCCESS("Finished checking all alerts."))
