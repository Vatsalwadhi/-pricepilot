import json
from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        
        print("Navigating to https://www.zeptonow.com")
        page.goto("https://www.zeptonow.com", wait_until="networkidle")
        
        print("Finding search input...")
        try:
            page.wait_for_selector('input')
            inputs = page.locator('input').all()
            for inp in inputs:
                print("Input:", inp.get_attribute("placeholder"), inp.get_attribute("type"))
            
            search_input = page.locator('input[type="text"]').first
            search_input.click()
            search_input.fill("milk")
            
            # Wait for search API
            with page.expect_response(lambda r: "user-search-service/api/v3/search" in r.url and r.request.method == "POST", timeout=10000) as response_info:
                search_input.press("Enter")
            
            response = response_info.value
            print("Found API response!")
            print(json.dumps(response.json())[:500])
            
        except Exception as e:
            print("Error:", e)
            
        browser.close()

if __name__ == "__main__":
    test()
