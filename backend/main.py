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
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
DATABASE_PATH = "summaries.db"
SUMMARIES_DIR = "summaries"

# Validate configuration
if not GOPHER_API_KEY:
    raise ValueError("GOPHER_API_KEY not found in environment variables")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Ensure directories exist
Path(SUMMARIES_DIR).mkdir(exist_ok=True)

# Initialize OpenAI client
from openai import OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
    allow_headers=["*"],120
)

# Pydantic models
class ScrapeRequest(BaseModel):
    url: HttpUrl
    max_pages: int = 5
    max_depth: int = 2

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

# Helper Functions
def scrape_docs(url: str, max_pages: int = 5, max_depth: int = 2) -> dict:
    """Scrape documentation using Gopher API with improved error handling"""
    endpoint = "https://data.gopher-ai.com/api/v1/search/live"
    headers = {
        "Authorization": f"Bearer {GOPHER_API_KEY}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    # Try different payload formats
    payloads = [
        {
            "type": "web",
            "arguments": {
                "type": "scraper",
                "url": str(url),
                "max_pages": max_pages,
                "max_depth": max_depth
            }
        },
        {
            "url": str(url),
            "max_pages": max_pages,
            "max_depth": max_depth
        },
        {
            "query": str(url),
            "type": "scrape",
            "max_pages": max_pages,
            "max_depth": max_depth
        }
    ]
    
    for i, payload in enumerate(payloads):
        try:
            logger.info(f"Attempting payload format {i+1} for URL: {url}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                endpoint, 
                headers=headers, 
                json=payload,
                timeout=60
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Success with payload format {i+1}")
                logger.debug(f"Response keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
                
                # Handle different response formats
                if isinstance(result, dict):
                    # Check for direct content
                    if "data" in result and "results" in result.get("data", {}):
                        return result
                    # Check for job ID in different field names
                    for job_id_field in ["uuid", "job_id", "id", "task_id"]:
                        if job_id_field in result:
                            logger.info(f"Found job ID field '{job_id_field}': {result[job_id_field]}")
                            return poll_gopher_results(result[job_id_field])
                    # If we have content but no specific structure, return as-is
                    if any(key in result for key in ["content", "results", "data"]):
                        return result
                
                # If we get here but have a 200, return the result anyway
                return result
                
            elif response.status_code == 202:
                # Accepted - async processing
                result = response.json()
                logger.info("Request accepted for async processing")
                for job_id_field in ["uuid", "job_id", "id", "task_id"]:
                    if job_id_field in result:
                        return poll_gopher_results(result[job_id_field])
                raise HTTPException(
                    status_code=500,
                    detail="Async job started but no job ID found in response"
                )
                
            else:
                logger.warning(f"Payload format {i+1} failed with status {response.status_code}")
                if i == len(payloads) - 1:  # Last attempt
                    logger.error(f"Final attempt failed. Response: {response.text}")
                    response.raise_for_status()
                    
        except requests.exceptions.RequestException as e:
            logger.warning(f"Payload format {i+1} failed with exception: {str(e)}")
            if i == len(payloads) - 1:  # Last attempt
                raise
    
    raise HTTPException(
        status_code=500,
        detail="All scraping attempts failed"
    )

def poll_gopher_results(job_id: str, max_attempts: int = 20) -> dict:
    """Poll Gopher API for job results with improved endpoint discovery"""
    # Try different endpoint patterns
    endpoint_patterns = [
        f"https://data.gopher-ai.com/api/v1/search/{job_id}",
        f"https://data.gopher-ai.com/api/v1/search/live/{job_id}",
        f"https://data.gopher-ai.com/api/v1/jobs/{job_id}",
        f"https://data.gopher-ai.com/api/v1/tasks/{job_id}",
    ]
    
    headers = {
        "Authorization": f"Bearer {GOPHER_API_KEY}",
        "accept": "application/json"
    }
    
    logger.info(f"Polling for job results: {job_id}")
    
    for attempt in range(max_attempts):
        for endpoint in endpoint_patterns:
            try:
                logger.debug(f"Attempt {attempt + 1}: Trying endpoint {endpoint}")
                time.sleep(3)  # Wait 3 seconds between attempts
                
                response = requests.get(endpoint, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successfully retrieved results from {endpoint}")
                    
                    # Check for completion
                    status = result.get("status", "").lower()
                    if status in ["completed", "done", "success"] or "data" in result or "results" in result:
                        logger.info("Job completed successfully")
                        return result
                    elif status in ["failed", "error"]:
                        error_msg = result.get("error", "Unknown error")
                        logger.error(f"Job failed: {error_msg}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Scraping job failed: {error_msg}"
                        )
                    elif status in ["processing", "running", "pending"]:
                        logger.debug(f"Job still processing (status: {status})")
                        break  # Break out of endpoint loop, continue to next attempt
                    else:
                        # No status field, assume completed if we have data
                        if "data" in result or "results" in result:
                            return result
                        logger.debug("No status field and no data found, continuing...")
                
                elif response.status_code == 404:
                    logger.debug(f"Endpoint not found: {endpoint}")
                    continue  # Try next endpoint pattern
                    
                else:
                    logger.warning(f"Unexpected status {response.status_code} from {endpoint}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {endpoint}: {str(e)}")
                continue  # Try next endpoint pattern
        
        logger.info(f"Polling attempt {attempt + 1}/{max_attempts} completed")
    
    # If we get here, all attempts failed
    logger.error(f"Failed to retrieve results after {max_attempts} attempts")
    raise HTTPException(
        status_code=504,
        detail="Scraping job timed out. Please try again with a smaller site or check the URL."
    )

def extract_text(scraped_data: dict) -> str:
    """Extract text content from scraped data with multiple format support"""
    contents = []
    
    # Try different data structures
    possible_paths = [
        ["data", "results"],
        ["results"],
        ["content"],
        ["data", "content"],
        ["pages"],
        ["data", "pages"],
    ]
    
    for path in possible_paths:
        current = scraped_data
        try:
            for key in path:
                current = current[key]
            if current and isinstance(current, list):
                for item in current:
                    if isinstance(item, dict):
                        # Try different content fields
                        for content_field in ["content", "text", "body", "html", "markdown"]:
                            if content_field in item and item[content_field]:
                                contents.append(str(item[content_field]))
                                break
                        # If no content field found, use the entire item as string
                        if not any(field in item for field in ["content", "text", "body"]):
                            contents.append(str(item))
                    else:
                        contents.append(str(item))
                if contents:
                    logger.info(f"Found content using path: {path}")
                    break
        except (KeyError, TypeError):
            continue
    
    # If no structured content found, try to stringify the entire response
    if not contents:
        logger.warning("No structured content found, using raw response")
        contents.append(json.dumps(scraped_data, indent=2))
    
    result = "\n\n".join(contents)
    logger.info(f"Extracted {len(result)} characters of text")
    return result

def summarize_with_gpt(text: str, url: str) -> str:
    """Summarize text using OpenAI GPT"""
    if not text.strip():
        raise ValueError("No content to summarize")
    
    # Truncate text if too long (GPT context limit)
    max_chars = 12000
    if len(text) > max_chars:
        logger.info(f"Truncating text from {len(text)} to {max_chars} characters")
        text = text[:max_chars] + "\n\n[Content truncated due to length]"
    
    prompt = f"""Analyze and summarize the following Web3 documentation from {url}.

Provide a structured summary with:
1. **Overview** - What is this project/feature?
2. **Key Features** - Main capabilities and features
3. **Setup & Integration** - How to get started
4. **Technical Details** - Important technical information
5. **API/SDK Information** - Available interfaces
6. **Best Practices** - Recommendations for developers

Content:
{text}

Provide a comprehensive but concise summary formatted in Markdown."""

    try:
        logger.info("Generating summary with GPT")
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a technical documentation expert specializing in Web3 technologies."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        summary = completion.choices[0].message.content
        logger.info(f"Generated summary of {len(summary)} characters")
        return summary
    except Exception as e:
        logger.error(f"GPT summarization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

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
    """Background task for scraping and summarizing with comprehensive error handling"""
    try:
        # Update job status
        with get_db() as conn:
            conn.execute(
                "UPDATE scrape_jobs SET status = 'processing' WHERE id = ?",
                (job_id,)
            )
            conn.commit()
        
        logger.info(f"Starting scrape task for job {job_id}: {url}")
        
        # Scrape
        scraped_data = scrape_docs(url, max_pages, max_depth)
        text_content = extract_text(scraped_data)
        
        if not text_content.strip():
            raise ValueError("No content extracted from URL. The site might be blocked, require JavaScript, or have no textual content.")
        
        logger.info(f"Successfully extracted {len(text_content)} characters")
        
        # Summarize
        summary = summarize_with_gpt(text_content, url)
        
        # Extract title from URL or use default
        title = url.split("/")[-1].replace("-", " ").title() or "Documentation Summary"
        if not title or title == "Documentation Summary":
            # Try to get from scraped data
            if isinstance(scraped_data, dict) and "data" in scraped_data:
                first_result = scraped_data.get("data", {}).get("results", [{}])[0]
                title = first_result.get("title", title)
        
        # Save
        filename, summary_id = save_summary(url, title, text_content, summary)
        
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
        "version": "2.1.0"
    }

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """Start a scraping job (runs in background)"""
    try:
        # Validate URL
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start scraping job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")

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
            
            return {
                "total_summaries": total_summaries,
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs
            }
    except Exception as e:
        logger.error(f"Failed to fetch stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)