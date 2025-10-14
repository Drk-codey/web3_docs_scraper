from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Wide open CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Test server running"}

@app.post("/scrape")
def scrape(data: dict):
    return {"status": "ok", "received": data}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)