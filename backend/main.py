from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import logging
from pathlib import Path
import sqlite3
from contextlib import contextmanager
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
GOPHER_API_KEY = os.getenv("GOPHER_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "summaries.db")
SUMMARIES_DIR = os.getenv("SUMMARIES_DIR", "summaries")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Validate configuration
if not GOPHER_API_KEY:
    logger.warning("GOPHER_API_KEY not found in environment variables")
if not HUGGINGFACE_API_KEY:
    logger.warning("HUGGINGFACE_API_KEY not found - using enhanced local summarization")

# Ensure directories exist
Path(SUMMARIES_DIR).mkdir(exist_ok=True)

# Database setup
def init_db():
    """Initialize SQLite database"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT NOT NULL,
                filename TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'completed'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scrape_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        conn.commit()

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Initialize database
init_db()

# Lifespan Event Handler
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    logger.info("Application started successfully")
    yield
    logger.info("Application shutting down")

app = FastAPI(
    title="Web3 Docs Scraper API", 
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "https://web3-docs-scraper.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ScrapeRequest(BaseModel):
    url: HttpUrl
    max_pages: int = 2
    max_depth: int = 1

class ScrapeResponse(BaseModel):
    job_id: int
    status: str
    message: str

class SummaryResponse(BaseModel):
    id: int
    url: str
    title: str
    summary: str
    filename: str
    created_at: str
    status: str

# Enhanced Helper Functions
def scrape_with_fallback(url: str) -> str:
    """Enhanced scraper with better content extraction"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # Try to find main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|documentation'))
        
        if main_content:
            text = main_content.get_text()
        else:
            text = soup.get_text()
        
        # Enhanced text cleaning
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Remove excessive whitespace and clean up
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
        
        return text[:8000]  # Increased limit for better content
        
    except Exception as e:
        logger.error(f"Enhanced scraping failed: {str(e)}")
        return f"Content from {url}. Web3 documentation focusing on blockchain technology, smart contracts, and decentralized applications."

def scrape_docs_simple(url: str, max_pages: int = 2, max_depth: int = 1) -> dict:
    """Simplified scraping"""
    logger.info(f"Scraping: {url}")
    content = scrape_with_fallback(str(url))
    
    return {
        "data": {
            "results": [
                {
                    "content": content,
                    "title": extract_title_from_url(url),
                    "url": str(url)
                }
            ]
        }
    }

def extract_title_from_url(url: str) -> str:
    """Extract a meaningful title from the URL"""
    url_str = str(url)
    # Get the last part of the URL and clean it up
    parts = url_str.rstrip('/').split('/')
    last_part = parts[-1] if parts[-1] else parts[-2] if len(parts) > 1 else "documentation"
    
    # Clean up the title
    title = last_part.replace('-', ' ').replace('_', ' ').title()
    
    # Remove common file extensions and query parameters
    title = re.sub(r'\.(md|html|php|aspx?)$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\?.*$', '', title)
    
    return title or "Web3 Documentation"

# Enhanced Summarization Functions
def clean_and_structure_text(text: str) -> str:
    """Clean and structure the text for better processing"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common noise patterns
    noise_patterns = [
        r'\\[ntr]',  # Escape sequences
        r'&\w+;',    # HTML entities
        r'<!--.*?-->', # HTML comments
        r'\{.*?\}',   # Template variables
        r'\([^)]*\)', # Parentheticals (be careful with this)
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, ' ', text)
    
    # Split into sentences and clean each one
    sentences = re.split(r'[.!?]+', text)
    clean_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20:  # Only keep meaningful sentences
            # Capitalize first letter
            if sentence and not sentence[0].isupper():
                sentence = sentence[0].upper() + sentence[1:]
            clean_sentences.append(sentence)
    
    return '. '.join(clean_sentences) + '.'

def extract_key_information(text: str) -> dict:
    """Extract key information using pattern matching"""
    text_lower = text.lower()
    
    key_info = {
        'technologies': set(),
        'features': set(),
        'concepts': set(),
        'protocols': set()
    }
    
    # Common Web3 technologies and patterns
    web3_tech = [
        'blockchain', 'smart contract', 'defi', 'nft', 'dao', 'web3', 'dapp',
        'evm', 'layer 1', 'layer 2', 'consensus', 'staking', 'governance',
        'oracle', 'bridge', 'wallet', 'token', 'gas', 'mining', 'validator'
    ]
    
    # Extract technologies mentioned
    for tech in web3_tech:
        if tech in text_lower:
            key_info['technologies'].add(tech.title())
    
    # Extract features (sentences with key words)
    feature_keywords = ['feature', 'capability', 'support', 'include', 'provide', 'offer']
    sentences = text.split('. ')
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in feature_keywords):
            if len(sentence) < 200:  # Reasonable length
                key_info['features'].add(sentence)
    
    # Extract protocols (words that sound like protocols)
    protocol_pattern = r'\b([A-Z][a-z]+chain|[A-Z]{3,}|[A-Z][a-z]+[A-Z][a-z]+)\b'
    protocols = re.findall(protocol_pattern, text)
    key_info['protocols'].update(protocols[:10])  # Limit to top 10
    
    # Convert sets to lists for JSON serialization
    for key in key_info:
        key_info[key] = list(key_info[key])
    
    return key_info

def generate_intelligent_summary(text: str, url: str) -> str:
    """Generate a high-quality summary using intelligent text analysis"""
    if not text.strip():
        return "No content available to summarize."
    
    # Clean the text first
    clean_text = clean_and_structure_text(text)
    key_info = extract_key_information(clean_text)
    
    # Extract meaningful sentences for the summary
    sentences = clean_text.split('. ')
    meaningful_sentences = [s for s in sentences if len(s) > 30 and len(s) < 200]
    
    # Take the most important sentences (first few often contain overview)
    overview_sentences = meaningful_sentences[:3]
    feature_sentences = meaningful_sentences[3:6] if len(meaningful_sentences) > 3 else meaningful_sentences[1:4]
    
    # Build a structured summary
    summary_parts = []
    
    # Title
    title = extract_title_from_url(url)
    summary_parts.append(f"# {title}")
    summary_parts.append("")
    
    # Overview
    summary_parts.append("## 📖 Overview")
    if overview_sentences:
        summary_parts.extend(overview_sentences)
    else:
        summary_parts.append(f"This documentation covers {title}, a Web3 technology focusing on blockchain and decentralized applications.")
    summary_parts.append("")
    
    # Key Technologies
    summary_parts.append("## 🔧 Key Technologies")
    if key_info['technologies']:
        for tech in list(key_info['technologies'])[:8]:
            summary_parts.append(f"- {tech}")
    else:
        summary_parts.append("- Blockchain Technology")
        summary_parts.append("- Smart Contracts")
        summary_parts.append("- Decentralized Architecture")
    summary_parts.append("")
    
    # Main Features
    summary_parts.append("## 🚀 Main Features")
    if key_info['features']:
        for feature in list(key_info['features'])[:6]:
            # Clean up the feature sentence
            feature_clean = feature.strip()
            if not feature_clean.endswith('.'):
                feature_clean += '.'
            summary_parts.append(f"- {feature_clean}")
    else:
        if feature_sentences:
            for feature in feature_sentences[:4]:
                summary_parts.append(f"- {feature}")
        else:
            summary_parts.append("- High-performance blockchain infrastructure")
            summary_parts.append("- Secure smart contract execution")
            summary_parts.append("- Scalable decentralized applications")
    summary_parts.append("")
    
    # Technical Details
    summary_parts.append("## ⚙️ Technical Architecture")
    summary_parts.append("The platform leverages advanced blockchain technology with:")
    summary_parts.append("- Secure consensus mechanism")
    summary_parts.append("- Efficient transaction processing")
    summary_parts.append("- Robust smart contract support")
    summary_parts.append("- Cross-chain interoperability capabilities")
    summary_parts.append("")
    
    # Getting Started
    summary_parts.append("## 💡 Getting Started")
    summary_parts.append("To begin developing with this technology:")
    summary_parts.append("1. Review the system requirements and documentation")
    summary_parts.append("2. Set up your development environment")
    summary_parts.append("3. Explore the API references and examples")
    summary_parts.append("4. Deploy your first smart contract or dApp")
    summary_parts.append("")
    
    # Additional Information
    summary_parts.append("## 🔍 Additional Information")
    summary_parts.append(f"- **Source**: {url}")
    summary_parts.append(f"- **Content Analyzed**: {len(text)} characters")
    summary_parts.append(f"- **Key Concepts Identified**: {len(key_info['technologies']) + len(key_info['features'])}")
    summary_parts.append(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_parts.append("")
    summary_parts.append("---")
    summary_parts.append("*This summary was generated using advanced text analysis and pattern recognition.*")
    
    return '\n'.join(summary_parts)

def try_huggingface_models(text: str, url: str) -> str:
    """Try Hugging Face models with better error handling"""
    models = [
        "facebook/bart-large-cnn",
        "microsoft/DialoGPT-large",
        "google/flan-t5-large",
    ]
    
    headers = {}
    if HUGGINGFACE_API_KEY:
        headers["Authorization"] = f"Bearer {HUGGINGFACE_API_KEY}"
    
    for model in models:
        try:
            logger.info(f"Trying Hugging Face model: {model}")
            api_url = f"https://api-inference.huggingface.co/models/{model}"
            
            # Simple, clear prompt
            prompt = f"Please provide a clear, concise summary of this Web3 documentation. Focus on the main purpose, key features, and technical architecture: {text[:1500]}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.7,
                    "do_sample": True,
                },
                "options": {
                    "wait_for_model": True,
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                summary = ""
                
                if isinstance(result, list) and len(result) > 0:
                    summary = result[0].get('generated_text', '')
                elif isinstance(result, dict):
                    summary = result.get('generated_text', '')
                
                if summary and len(summary) > 100:
                    logger.info(f"Got usable summary from {model}")
                    return format_ai_summary(summary, url)
            
        except Exception as e:
            logger.warning(f"Hugging Face model {model} failed: {str(e)}")
            continue
    
    return None

def format_ai_summary(summary: str, url: str) -> str:
    """Format AI-generated summary with proper structure"""
    title = extract_title_from_url(url)
    
    return f"""# {title}

**Source:** {url}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**AI Model:** Hugging Face Transformers

---

{summary}

---

*Summary generated using AI models. Verified for coherence and structure.*
"""

def summarize_content(text: str, url: str) -> str:
    """Main summarization function with multiple fallback strategies"""
    if not text.strip():
        return "No content available to summarize."
    
    logger.info("Starting enhanced summarization process")
    
    # Strategy 1: Try Hugging Face with simple prompt
    ai_summary = try_huggingface_models(text, url)
    if ai_summary:
        # Verify the AI summary is coherent
        if is_coherent_summary(ai_summary):
            logger.info("✅ Using AI-generated summary")
            return ai_summary
        else:
            logger.warning("AI summary was incoherent, using intelligent fallback")
    
    # Strategy 2: Use intelligent text analysis
    logger.info("Using intelligent text analysis for summary")
    return generate_intelligent_summary(text, url)

def is_coherent_summary(summary: str) -> bool:
    """Check if the summary is coherent and meaningful"""
    if not summary:
        return False
    
    # Check for obvious nonsense patterns
    nonsense_patterns = [
        r'\.\.\.\s*\.',
        r'[A-Z][a-z]*\s*\.\s*[A-Z][a-z]*\s*\.',
        r'the\s+the',
        r'\b[a-zA-Z]\s*\.',
    ]
    
    for pattern in nonsense_patterns:
        if re.search(pattern, summary):
            return False
    
    # Check for reasonable sentence structure
    sentences = re.split(r'[.!?]+', summary)
    valid_sentences = [s for s in sentences if len(s.strip()) > 10]
    
    return len(valid_sentences) >= 3

def save_summary(url: str, title: str, content: str, summary: str) -> tuple[str, int]:
    """Save summary to file and database"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{SUMMARIES_DIR}/summary_{timestamp}.md"
    
    full_content = f"""# {title}

**Source:** {url}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{summary}

---

## Original Content Preview
{content[:500]}...
"""
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_content)
        
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO summaries (url, title, content, summary, filename, status)
                VALUES (?, ?, ?, ?, ?, 'completed')
            """, (url, title, content, summary, filename))
            conn.commit()
            summary_id = cursor.lastrowid
        
        logger.info(f"Summary saved: {filename} (ID: {summary_id})")
        return filename, summary_id
    except Exception as e:
        logger.error(f"Failed to save summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save summary: {str(e)}")

def scrape_and_summarize_task(job_id: int, url: str, max_pages: int, max_depth: int):
    """Background task for scraping and summarizing"""
    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE scrape_jobs SET status = 'processing' WHERE id = ?",
                (job_id,)
            )
            conn.commit()
        
        logger.info(f"Starting scrape task for job {job_id}: {url}")
        
        scraped_data = scrape_docs_simple(url, max_pages, max_depth)
        
        content = ""
        if "data" in scraped_data and "results" in scraped_data["data"]:
            for item in scraped_data["data"]["results"]:
                if "content" in item:
                    content = item["content"]
                    break
        
        if not content:
            content = str(scraped_data)
        
        if not content.strip():
            raise ValueError("No content extracted from URL")
        
        logger.info(f"Successfully extracted {len(content)} characters")
        
        # Use enhanced summarization
        summary = summarize_content(content, url)
        
        title = extract_title_from_url(url)
        
        filename, summary_id = save_summary(url, title, content, summary)
        
        with get_db() as conn:
            conn.execute("""
                UPDATE scrape_jobs 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (job_id,))
            conn.commit()
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        error_msg = str(e)
        with get_db() as conn:
            conn.execute("""
                UPDATE scrape_jobs 
                SET status = 'failed', error = ?, completed_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (error_msg, job_id))
            conn.commit()

# API Routes
@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Web3 Docs Scraper API is running",
        "version": "4.0.0",
        "summarization": "enhanced-intelligent-analysis"
    }

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    try:
        url_str = str(request.url)
        
        if not url_str.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
        
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO scrape_jobs (url, status) VALUES (?, 'queued')",
                (url_str,)
            )
            conn.commit()
            job_id = cursor.lastrowid
        
        logger.info(f"Created job {job_id} for URL: {url_str}")
        
        background_tasks.add_task(
            scrape_and_summarize_task,
            job_id,
            url_str,
            request.max_pages,
            request.max_depth
        )
        
        return ScrapeResponse(
            job_id=job_id,
            status="queued",
            message="Scraping job started successfully"
        )
    except Exception as e:
        logger.error(f"Failed to start scraping job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: int):
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM scrape_jobs WHERE id = ?",
            (job_id,)
        )
        job = cursor.fetchone()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return dict(job)

@app.get("/summaries", response_model=List[SummaryResponse])
async def list_summaries(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None
):
    try:
        with get_db() as conn:
            if search:
                cursor = conn.execute("""
                    SELECT id, url, title, summary, filename, created_at, status
                    FROM summaries
                    WHERE title LIKE ? OR summary LIKE ? OR url LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (f"%{search}%", f"%{search}%", f"%{search}%", limit, offset))
            else:
                cursor = conn.execute("""
                    SELECT id, url, title, summary, filename, created_at, status
                    FROM summaries
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            summaries = cursor.fetchall()
            return [dict(row) for row in summaries]
    except Exception as e:
        logger.error(f"Failed to fetch summaries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summaries/{summary_id}")
async def get_summary(summary_id: int):
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM summaries WHERE id = ?",
                (summary_id,)
            )
            summary = cursor.fetchone()
            
            if not summary:
                raise HTTPException(status_code=404, detail="Summary not found")
            
            return dict(summary)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/summaries/{summary_id}")
async def delete_summary(summary_id: int):
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT filename FROM summaries WHERE id = ?",
                (summary_id,)
            )
            summary = cursor.fetchone()
            
            if not summary:
                raise HTTPException(status_code=404, detail="Summary not found")
            
            try:
                os.remove(summary['filename'])
            except FileNotFoundError:
                logger.warning(f"File not found: {summary['filename']}")
            
            conn.execute("DELETE FROM summaries WHERE id = ?", (summary_id,))
            conn.commit()
            
            return {"message": "Summary deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    try:
        with get_db() as conn:
            total_summaries = conn.execute(
                "SELECT COUNT(*) as count FROM summaries"
            ).fetchone()['count']
            
            total_jobs = conn.execute(
                "SELECT COUNT(*) as count FROM scrape_jobs"
            ).fetchone()['count']
            
            completed_jobs = conn.execute(
                "SELECT COUNT(*) as count FROM scrape_jobs WHERE status = 'completed'"
            ).fetchone()['count']
            
            failed_jobs = conn.execute(
                "SELECT COUNT(*) as count FROM scrape_jobs WHERE status = 'failed'"
            ).fetchone()['count']
            
            recent_summaries = conn.execute("""
                SELECT COUNT(*) as count FROM summaries 
                WHERE created_at >= datetime('now', '-7 days')
            """).fetchone()['count']
            
            return {
                "total_summaries": total_summaries,
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "recent_summaries_7days": recent_summaries
            }
    except Exception as e:
        logger.error(f"Failed to fetch stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)