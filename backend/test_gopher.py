# test_gopher.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GOPHER_API_KEY = os.getenv("GOPHER_API_KEY")

def test_gopher_api():
    endpoint = "https://data.gopher-ai.com/api/v1/search/live"
    headers = {
        "Authorization": f"Bearer {GOPHER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Test with a simple payload
    payload = {
        "type": "web",
        "arguments": {
            "type": "scraper",
            "url": "https://docs.soliditylang.org/en/latest/",
            "max_pages": "1",
            "max_depth": "1"
        }
    }
    
    try:
        print("Testing Gopher API connection...")
        response = requests.post(
            endpoint, 
            headers=headers, 
            json=payload,
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_gopher_api()