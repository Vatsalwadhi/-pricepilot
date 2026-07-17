from django.test import Client
from comparison.models import ComparisonResult

normalized_id = "amul-taaza-toned-milk"
print(f"Testing with normalized_id: {normalized_id}")

client = Client()
try:
    response = client.get(f'/api/products/{normalized_id}/offers')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.content.decode()}")
except Exception as e:
    import traceback
    print("Traceback:")
    traceback.print_exc()

print("\n--- All ComparisonResult normalized_product_names ---")
for name in ComparisonResult.objects.values_list('normalized_product_name', flat=True).distinct()[:10]:
    print(name)
