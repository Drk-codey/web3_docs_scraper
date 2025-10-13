from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests, openai, json, os

# Ensure required packages are installed
try:
    import fastapi
    import requests
    import openai
except ImportError as e:
    missing_package = str(e).split("'")[1]
    print(f"Error: The package '{missing_package}' is not installed. Please install it using 'pip install {missing_package}'.")
    raise
from datetime import datetime

# === CONFIGURATION ===
GOPHER_API_KEY = "YauHe2OIScMnjAd4XeWltpxgxjhh5xB0vxNignD1eu7XQIbN"
OPENAI_API_KEY = "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"
DOC_URL = "https://developers.gopher-ai.com/docs/masa-subnet"
SUMMARIES_DIR = "summaries"

os.makedirs(SUMMARIES_DIR, exist_ok=True)

app = FastAPI()

# Allow frontend access
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Helper Functions ===

def scrape_docs(url):
    endpoint = "https://data.gopher-ai.com/api/v1/search/live"
    headers = {
        "Authorization": f"Bearer {GOPHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "type": "web",
        "arguments": {
            "type": "scraper",
            "url": url,
            "max_pages": "3",
            "max_depth": "1"
        }
    }
    response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    return response.json()

def extract_text(scraped_data):
    contents = []
    results = scraped_data.get("data", {}).get("results", [])
    for item in results:
        if "content" in item:
            contents.append(item["content"])
    return "\n\n".join(contents)

def summarize_with_gpt(text):
    openai.api_key = OPENAI_API_KEY
    prompt = f"""
    Summarize the following Web3 documentation content into key developer points, setup steps, and integration details:
    {text[:6000]}
    """
    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return completion["choices"][0]["message"]["content"]

def save_summary(title, content):
    filename = f"{SUMMARIES_DIR}/summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{content}")
    return filename

# === ROUTES ===

@app.get("/")
def home():
    return {"message": "Web3 Docs Scraper API is running"}

@app.post("/scrape")
def run_scraper(url: str = DOC_URL):
    scraped = scrape_docs(url)
    text = extract_text(scraped)
    if not text.strip():
        return {"error": "No content found"}

    summary = summarize_with_gpt(text)
    filename = save_summary("Masa Subnet Docs Summary", summary)
    return {"status": "success", "file": filename, "summary": summary}

@app.get("/summaries")
def list_summaries():
    files = [f for f in os.listdir(SUMMARIES_DIR) if f.endswith(".md")]
    summaries = []
    for file in sorted(files, reverse=True):
        with open(os.path.join(SUMMARIES_DIR, file), "r", encoding="utf-8") as f:
            summaries.append({"filename": file, "content": f.read()})
    return summaries
