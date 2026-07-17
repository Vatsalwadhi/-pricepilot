import json
from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating to search URL...")
        try:
            with page.expect_response(lambda r: "user-search-service/api/v3/search" in r.url and r.request.method == "POST", timeout=15000) as response_info:
                page.goto("https://www.zeptonow.com/search?q=milk")
                
            print("Response found!")
            print(json.dumps(response_info.value.json(), indent=2)[:4000])
        except Exception as e:
            print("Error:", e)
            
        browser.close()

if __name__ == "__main__":
    test()
