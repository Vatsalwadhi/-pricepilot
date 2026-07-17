import json
import time
from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Add a real user agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        
        print("Navigating to https://www.zeptonow.com")
        try:
            page.goto("https://www.zeptonow.com", wait_until="domcontentloaded")
            time.sleep(3) # wait for react
        except Exception as e:
            print("Navigation error:", e)
        
        # Take a screenshot to see what it looks like
        page.screenshot(path="zepto_home.png")
        
        # Dump the HTML
        with open("zepto_home.html", "w", encoding="utf-8") as f:
            f.write(page.content())
            
        browser.close()

if __name__ == "__main__":
    test()
