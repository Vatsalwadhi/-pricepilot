import json
from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        
        def log_request(request):
            url = request.url.lower()
            if any(k in url for k in ["search", "product", "api", "graphql", "bff"]):
                print(f"REQUEST: {request.method} {request.url}")
        
        def log_response(response):
            url = response.url.lower()
            if "search" in url and response.request.method == "POST":
                print(f"\n[!] INTERCEPTED POST SEARCH! URL: {response.url} Status: {response.status}")
                try:
                    # Also print the request payload
                    print("Request Payload:", response.request.post_data)
                    body = response.text()
                    print(f"Response BODY (first 1000 chars):\n{body[:1000]}")
                    with open("zepto_response.json", "w", encoding="utf-8") as f:
                        f.write(body)
                except Exception as e:
                    print("Failed to read body:", e)
                    
        page.on("request", log_request)
        page.on("response", log_response)
        
        print("Navigating to https://www.zepto.com ...")
        page.goto("https://www.zepto.com", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        
        print("Finding search UI...")
        try:
            search_trigger = page.locator('[href="/search"], [data-testid*="search"]').first
            if search_trigger.is_visible():
                print("Clicking search trigger...")
                search_trigger.click(timeout=3000)
                page.wait_for_timeout(2000)
        except Exception as e:
            print("No search trigger found or failed to click")
            
        try:
            search_input = page.locator('input[placeholder*="Search" i], input[aria-label*="Search" i], input[type="text"]').first
            search_input.wait_for(timeout=5000)
            search_input.click(timeout=5000)
            print("Filled search input with 'milk'...")
            search_input.fill("milk")
            search_input.press("Enter")
            print("Pressed Enter!")
            
            page.wait_for_timeout(8000)
        except Exception as e:
            print("Failed to interact with search input:", e)
            
        browser.close()

if __name__ == "__main__":
    test()
