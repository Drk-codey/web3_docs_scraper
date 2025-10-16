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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
GOPHER_API_KEY = os.getenv("GOPHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_PATH = "summaries.db"
SUMMARIES_DIR = "summaries"

# Validate configuration
if not GOPHER_API_KEY:
    logger.warning("GOPHER_API_KEY not found in environment variables")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found in environment variables")

# Ensure directories exist
Path(SUMMARIES_DIR).mkdir(exist_ok=True)

# Initialize OpenAI client
from openai import OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

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

app = FastAPI(title="Web3 Docs Scraper API", lifespan=lifespan)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Helper Functions - SIMPLIFIED VERSION
def scrape_with_fallback(url: str) -> str:
    """Simple fallback scraper for demo purposes"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:5000]  # Limit length
        
    except Exception as e:
        logger.error(f"Fallback scraping failed: {str(e)}")
        # Return demo content for testing
        return f"""
        This is demo content for {url}. 
        
        In a real implementation, this would be the actual scraped content from the website.
        
        Web3 Documentation Summary:
        
        # Overview
        This is a demo Web3 documentation site that demonstrates the scraping functionality.
        
        # Key Features
        - Feature 1: Decentralized architecture
        - Feature 2: Smart contract support
        - Feature 3: Token economics
        
        # Technical Details
        Built on blockchain technology with support for multiple protocols.
        
        # Getting Started
        1. Install the SDK
        2. Configure your environment
        3. Deploy your first contract
        """

def scrape_docs_simple(url: str, max_pages: int = 2, max_depth: int = 1) -> dict:
    """Simplified scraping that uses fallback immediately"""
    logger.info(f"Using fallback scraper for: {url}")
    
    # For demo purposes, we'll use the fallback immediately
    # In production, you would try Gopher API first
    content = scrape_with_fallback(str(url))
    
    # Return in the expected format
    return {
        "data": {
            "results": [
                {
                    "content": content,
                    "title": url.split("/")[-1] or "Documentation",
                    "url": str(url)
                }
            ]
        }
    }

def summarize_with_gpt(text: str, url: str) -> str:
    """Summarize text using OpenAI GPT"""
    if not text.strip():
        raise ValueError("No content to summarize")
    
    # Truncate text if too long
    max_chars = 8000
    if len(text) > max_chars:
        logger.info(f"Truncating text from {len(text)} to {max_chars} characters")
        text = text[:max_chars] + "\n\n[Content truncated due to length]"
    
    prompt = f"""Please provide a concise summary of the following Web3 documentation:

URL: {url}

Content:
{text}

Please structure your summary with:
1. **Overview** - Brief description
2. **Key Features** - Main capabilities
3. **Technical Details** - Important technical information
4. **Getting Started** - Basic setup steps

Keep the summary focused and under 500 words."""

    try:
        if not openai_client:
            # Return demo summary if no API key
            return f"""
# Documentation Summary for {url}

## Overview
This is a demo summary generated for testing purposes. In a real implementation, this would be generated by OpenAI GPT.

## Key Features
- Decentralized architecture
- Smart contract capabilities
- Token management system

## Technical Details
Built on blockchain technology with support for multiple protocols and standards.

## Getting Started
1. Install the required dependencies
2. Configure your development environment
3. Deploy your first smart contract

*Note: This is demo content. Connect your OpenAI API key for real summaries.*
"""
        
        logger.info("Generating summary with GPT")
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a technical writer specializing in Web3 technologies."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        summary = completion.choices[0].message.content
        logger.info(f"Generated summary of {len(summary)} characters")
        return summary
    except Exception as e:
        logger.error(f"GPT summarization failed: {str(e)}")
        # Return fallback summary
        return f"Summary generation failed: {str(e)}\n\nOriginal content preview: {text[:500]}..."

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
        # Save to file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_content)
        
        # Save to database
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
        # Update job status
        with get_db() as conn:
            conn.execute(
                "UPDATE scrape_jobs SET status = 'processing' WHERE id = ?",
                (job_id,)
            )
            conn.commit()
        
        logger.info(f"Starting scrape task for job {job_id}: {url}")
        
        # Use simplified scraper (bypasses Gopher API issues)
        scraped_data = scrape_docs_simple(url, max_pages, max_depth)
        
        # Extract content
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
        
        # Summarize
        summary = summarize_with_gpt(content, url)
        
        # Extract title
        title = url.split("/")[-1].replace("-", " ").title() or "Documentation Summary"
        
        # Save
        filename, summary_id = save_summary(url, title, content, summary)
        
        # Update job as completed
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
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Web3 Docs Scraper API is running",
        "version": "2.3.0",
        "mode": "fallback-scraping"
    }

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """Start a scraping job (runs in background)"""
    try:
        url_str = str(request.url)
        
        if not url_str.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
        
        # Create job record
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO scrape_jobs (url, status) VALUES (?, 'queued')",
                (url_str,)
            )
            conn.commit()
            job_id = cursor.lastrowid
        
        logger.info(f"Created job {job_id} for URL: {url_str}")
        
        # Start background task
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
    """Get status of a scraping job"""
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
    """List all summaries with pagination and search"""
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
    """Get full summary by ID"""
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
    """Delete a summary"""
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT filename FROM summaries WHERE id = ?",
                (summary_id,)
            )
            summary = cursor.fetchone()
            
            if not summary:
                raise HTTPException(status_code=404, detail="Summary not found")
            
            # Delete file
            try:
                os.remove(summary['filename'])
            except FileNotFoundError:
                logger.warning(f"File not found: {summary['filename']}")
            
            # Delete from database
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
    """Get application statistics"""
    try:
        with get_db() as conn:
            # Get total summaries
            total_summaries = conn.execute(
                "SELECT COUNT(*) as count FROM summaries"
            ).fetchone()['count']
            
            # Get job statistics
            total_jobs = conn.execute(
                "SELECT COUNT(*) as count FROM scrape_jobs"
            ).fetchone()['count']
            
            completed_jobs = conn.execute(
                "SELECT COUNT(*) as count FROM scrape_jobs WHERE status = 'completed'"
            ).fetchone()['count']
            
            failed_jobs = conn.execute(
                "SELECT COUNT(*) as count FROM scrape_jobs WHERE status = 'failed'"
            ).fetchone()['count']
            
            processing_jobs = conn.execute(
                "SELECT COUNT(*) as count FROM scrape_jobs WHERE status = 'processing'"
            ).fetchone()['count']
            
            # Get recent summaries (last 7 days)
            recent_summaries = conn.execute("""
                SELECT COUNT(*) as count FROM summaries 
                WHERE created_at >= datetime('now', '-7 days')
            """).fetchone()['count']
            
            return {
                "total_summaries": total_summaries,
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "processing_jobs": processing_jobs,
                "recent_summaries_7days": recent_summaries
            }
    except Exception as e:
        logger.error(f"Failed to fetch stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)