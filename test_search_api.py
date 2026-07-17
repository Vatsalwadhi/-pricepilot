import requests
import json

def test():
    print("Testing /api/search/ endpoint...")
    url = "http://127.0.0.1:8000/api/search"
    payload = {
        "query": "milk",
        "latitude": 12.96902,
        "longitude": 77.75395
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        print("Status:", response.status_code)
        if response.status_code == 500:
            print("Received HTTP 500. Body:")
            print(response.text)
        else:
            print("Success! Body:")
            print(response.text[:500])
    except Exception as e:
        print("Request failed:", e)

if __name__ == "__main__":
    test()
