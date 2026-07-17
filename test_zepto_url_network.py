import json
from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            geolocation={"latitude": 12.96902, "longitude": 77.75395}, # Grant location to prevent empty results
            permissions=["geolocation"]
        )
        page = context.new_page()
        
        def log_response(response):
            try:
                url = response.url.lower()
                if "user-search-service/api/v3/search" in url:
                    print(f"\n[!] INTERCEPTED SEARCH V3 API: {response.request.method} {response.url} Status: {response.status}")
                    print("Payload:", response.request.post_data)
                    body = response.text()
                    print("Body (first 500):", body[:500])
                elif "search" in url and "bff" in url:
                    print(f"\n[?] OTHER BFF SEARCH API: {response.request.method} {response.url} Status: {response.status}")
                    print("Payload:", response.request.post_data)
                    body = response.text()
                    print("Body (first 500):", body[:500])
            except Exception:
                pass
                    
        page.on("response", log_response)
        
        print("Navigating to search URL directly...")
        # Use a URL that triggers the product grid
        page.goto("https://www.zeptonow.com/search?q=milk", wait_until="domcontentloaded")
        page.wait_for_timeout(10000)
            
        browser.close()

if __name__ == "__main__":
    test()
