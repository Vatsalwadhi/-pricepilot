from django.test import Client

normalized_id = "missing-product-123"
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
