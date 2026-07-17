import json
from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating...")
        # Let's try zeptonow.com as zepto.com is a different company usually
        page.goto("https://www.zeptonow.com")
        
        print("Waiting for search bar...")
        # Most search inputs have placeholder containing search or id containing search
        page.wait_for_selector('input[type="text"]')
        inputs = page.locator('input[type="text"]').all()
        for inp in inputs:
            print("Found input:", inp.get_attribute("placeholder"))
            
        print("Trying to type in the first input...")
        inputs[0].fill("milk")
        inputs[0].press("Enter")
        
        print("Waiting for response...")
        with page.expect_response(lambda r: "search" in r.url and r.request.method == "POST", timeout=10000) as response_info:
            response = response_info.value
            try:
                print("Response JSON:")
                print(json.dumps(response.json(), indent=2)[:2000]) # First 2000 chars
            except Exception as e:
                print("Error parsing JSON", e)

        browser.close()

if __name__ == "__main__":
    test()
