import json
import time
from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Using a valid user agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        
        saved_responses = []
        
        def log_response(response):
            try:
                # 2. Log every POST request...
                if response.request.method == "POST":
                    url = response.url
                    req_payload = response.request.post_data or ""
                    
                    # 4. Ignore requests whose payload contains: "mode": "AUTOSUGGEST"
                    if "AUTOSUGGEST" in req_payload:
                        return
                        
                    try:
                        body = response.text()
                    except Exception:
                        return
                        
                    # 3. Save every JSON response
                    try:
                        json.loads(body) # Verify it's JSON
                        fname = f"zepto_response_{len(saved_responses)+1}.json"
                        with open(fname, "w", encoding="utf-8") as f:
                            f.write(body)
                        saved_responses.append(fname)
                    except Exception:
                        pass
                    
                    # 7. Specifically search for JSON containing: products, productName, sellingPrice, variants, inventory, productCard
                    if any(kw in body for kw in ["products", "productName", "sellingPrice", "variants", "inventory", "productCard"]):
                        print("\n" + "="*50)
                        print("[!] FOUND THE PRODUCT GRID API REQUEST!")
                        print("URL:", url)
                        print("Request payload:", req_payload)
                        print("Response status:", response.status)
                        print("First 500 characters of the JSON:\n", body[:500])
                        print("="*50 + "\n")
                    else:
                        print(f"Logged POST to {url}, did not contain product keywords.")
            except Exception as e:
                pass
                    
        page.on("response", log_response)
        
        print("Navigating to https://www.zepto.com ...")
        page.goto("https://www.zepto.com", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        
        try:
            search_trigger = page.locator('[href="/search"], [data-testid*="search"]').first
            if search_trigger.is_visible():
                print("Clicking search trigger...")
                search_trigger.click(timeout=3000)
                page.wait_for_timeout(2000)
        except Exception:
            pass
            
        try:
            search_input = page.locator('input[placeholder*="Search" i], input[aria-label*="Search" i], input[type="text"]').first
            search_input.wait_for(timeout=5000)
            search_input.click(timeout=5000)
            print("Typing 'milk' slowly...")
            
            # Type slowly so React registers it and shows suggestions
            search_input.type("milk", delay=100)
            
            # Wait for autosuggest to fire
            page.wait_for_timeout(2000)
            
            print("Pressing Enter...")
            search_input.press("Enter")
            
            print("Waiting 10 seconds for POST requests...")
            # 1. Do not stop after the first intercepted response. Wait 10s.
            page.wait_for_timeout(10000)
            
        except Exception as e:
            print("Failed to interact with search input:", e)
            
        browser.close()

if __name__ == "__main__":
    test()
