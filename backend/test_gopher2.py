import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOPHER_API_KEY")
print(f"Testing with API key: {API_KEY[:20]}...\n")

# Test scraping
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "accept": "application/json"
}

payload = {
    "type": "web",
    "arguments": {
        "type": "scraper",
        "url": "https://ethereum.org/en/developers/docs/",
        "max_pages": 2,
        "max_depth": 1
    }
}

print("Sending request to Gopher API...")
try:
    response = requests.post(
        "https://data.gopher-ai.com/api/v1/search/live",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}\n")
    
    if response.status_code == 200:
        result = response.json()
        
        if "uuid" in result:
            uuid = result["uuid"]
            print(f"✅ Got UUID: {uuid}")
            print("Polling for results...\n")
            
            # Poll for results
            for i in range(10):
                time.sleep(3)
                poll_response = requests.get(
                    f"https://data.gopher-ai.com/api/v1/search/{uuid}",
                    headers=headers,
                    timeout=30
                )
                
                print(f"Poll attempt {i+1}: Status {poll_response.status_code}")
                
                if poll_response.status_code == 200:
                    poll_result = poll_response.json()
                    
                    if poll_result.get("status") == "completed" or "data" in poll_result:
                        print("\n✅ Scraping completed!")
                        print(f"Result preview: {str(poll_result)[:500]}...")
                        break
                    else:
                        print(f"Status: {poll_result.get('status', 'processing')}")
        else:
            print("✅ Got direct response (not async)")
            print(f"Preview: {str(result)[:500]}...")
            
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Message: {response.text}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")