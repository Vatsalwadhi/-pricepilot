from django.test import Client
import traceback

def run():
    normalized_id = "amul-gold-full-cream-milk"
    search_id = "101"
    print(f"Testing with normalized_id: {normalized_id}, search_id: {search_id}")

    client = Client()
    try:
        response = client.get(f'/api/products/{normalized_id}/offers?search_id={search_id}')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.content.decode()}")
    except Exception as e:
        print("Traceback:")
        traceback.print_exc()

    print("\n--- Additional Info ---")
    try:
        from django.apps import apps
        ComparisonResult = apps.get_model('comparison', 'ComparisonResult')
        search_results = ComparisonResult.objects.filter(search_id=search_id)
        print(f"offers.count(): {search_results.filter(total_price__isnull=False).count()}")
        print(f"provider_errors.count(): {search_results.filter(error_message__isnull=False).exclude(error_message='').count()}")
        first_offer = search_results.filter(total_price__isnull=False).first()
        if first_offer:
            print(f"first offer: platform={first_offer.platform}, normalized_product_name={first_offer.normalized_product_name}, search_id={first_offer.search_id}, created_at={first_offer.created_at}")
        else:
            print("first offer: None")
    except Exception as e:
        print(f"Error getting additional info: {e}")

if __name__ == "__main__":
    run()
