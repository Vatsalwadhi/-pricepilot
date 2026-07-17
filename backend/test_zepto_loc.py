from playwright.sync_api import sync_playwright
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def test_api():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            geolocation={"latitude": 40.7128, "longitude": -74.0060},
            permissions=["geolocation"]
        )
        page = context.new_page()
        
        def handle_route(route):
            req = route.request
            if "lms/api/v2/get_page" in req.url and req.method == "GET":
                parsed = urlparse(req.url)
                query = parse_qs(parsed.query)
                query['latitude'] = ["40.7128"]
                query['longitude'] = ["-74.0060"]
                new_query = urlencode(query, doseq=True)
                new_url = urlunparse(parsed._replace(query=new_query))
                print("Rewriting URL to:", new_url)
                route.continue_(url=new_url)
            else:
                route.continue_()
        
        page.route("**/*", handle_route)
        
        with page.expect_response(lambda r: "lms/api/v2/get_page" in r.url) as resp_info:
            page.goto("https://www.zepto.com", timeout=30000)
        
        try:
            data = resp_info.value.json()
            print("Response length:", len(str(data)))
            v2 = data.get("storeServiceableResponseV2")
            print("storeServiceableResponseV2:", v2)
            store = data.get("storeServiceableResponse")
            print("storeServiceableResponse:", store)
        except Exception as e:
            print("Error parsing:", e)
        
        browser.close()

if __name__ == "__main__":
    test_api()
