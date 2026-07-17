from playwright.sync_api import sync_playwright
import time
import json

def test_blinkit():
    payload = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def handle_response(response):
            nonlocal payload
            if "/v1/layout/search" in response.url:
                print(f"Intercepted: {response.url} {response.status}")
                if response.status == 200:
                    try:
                        payload = response.json()
                        print("Got JSON payload")
                    except Exception as e:
                        print(f"Failed to get JSON: {e}")

        page.on("response", handle_response)
        
        print("Navigating to Blinkit...")
        page.goto("https://blinkit.com/")
        
        # Wait for the search bar or location prompt
        try:
            # wait a bit for any popups
            page.wait_for_timeout(3000)
            
            # If there's a location prompt, we might need to handle it, 
            # but let's try direct navigation to search page first
            print("Navigating to search page...")
            page.goto("https://blinkit.com/s/?q=milk")
            page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"Error during interaction: {e}")
            
        browser.close()
        
    if payload:
        print("Success, found payload keys:", payload.keys())
    else:
        print("Failed to capture payload")

if __name__ == "__main__":
    test_blinkit()
