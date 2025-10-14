# 🔧 Advanced Troubleshooting & Optimization

## Performance Optimization

### Backend Optimizations

#### 1. Database Connection Pooling
```python
# Add to main.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

#### 2. Add Caching
```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache stats for 5 minutes
stats_cache = {"data": None, "timestamp": None}

@app.get("/stats")
async def get_stats():
    now = datetime.now()
    if stats_cache["data"] and stats_cache["timestamp"]:
        if now - stats_cache["timestamp"] < timedelta(minutes=5):
            return stats_cache["data"]
    
    # Fetch fresh data
    stats = fetch_stats_from_db()
    stats_cache["data"] = stats
    stats_cache["timestamp"] = now
    return stats
```

#### 3. Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/scrape")
@limiter.limit("5/minute")
async def scrape_endpoint(request: Request, ...):
    # Your code here
    pass
```

### Frontend Optimizations

#### 1. Implement Pagination
```javascript
const [page, setPage] = useState(1);
const [hasMore, setHasMore] = useState(true);

const fetchMore = async () => {
  const res = await axios.get(`${BACKEND_URL}/summaries`, {
    params: { limit: 10, offset: page * 10 }
  });
  if (res.data.length < 10) setHasMore(false);
  setSummaries(prev => [...prev, ...res.data]);
  setPage(prev => prev + 1);
};
```

#### 2. Add Loading Skeletons
```javascript
// components/LoadingSkeleton.js
export default function LoadingSkeleton() {
  return (
    <div className="animate-pulse bg-gray-800 rounded-2xl p-6">
      <div className="h-4 bg-gray-700 rounded w-3/4 mb-4"></div>
      <div className="h-3 bg-gray-700 rounded w-1/2 mb-2"></div>
      <div className="h-20 bg-gray-700 rounded mt-4"></div>
    </div>
  );
}
```

#### 3. Optimize Bundle Size
```javascript
// next.config.js
module.exports = {
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          default: false,
          vendors: false,
          commons: {
            name: 'commons',
            chunks: 'all',
            minChunks: 2,
          },
        },
      };
    }
    return config;
  },
};
```

## Error Handling Improvements

### Backend Error Handler
```python
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG") else "An error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )
```

### Frontend Error Boundary
```javascript
// components/ErrorBoundary.js
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-black flex items-center justify-center p-4">
          <div className="bg-red-900/20 border border-red-500 rounded-2xl p-8 max-w-md">
            <h2 className="text-2xl font-bold text-red-400 mb-4">
              Something went wrong
            </h2>
            <p className="text-gray-300 mb-4">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-red-600 hover:bg-red-500 text-white px-6 py-3 rounded-lg"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

// Wrap in _app.js
function MyApp({ Component, pageProps }) {
  return (
    <ErrorBoundary>
      <Component {...pageProps} />
    </ErrorBoundary>
  );
}
```

## Monitoring & Logging

### Add Structured Logging
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

### Add Request Logging Middleware
```python
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response
```

## Database Migrations

### Migration Script
```python
# migrations/001_add_tags.py
def upgrade(conn):
    conn.execute("""
        ALTER TABLE summaries ADD COLUMN tags TEXT
    """)
    conn.commit()

def downgrade(conn):
    # SQLite doesn't support DROP COLUMN easily
    pass

# Run migrations
import sqlite3

def run_migrations():
    conn = sqlite3.connect("summaries.db")
    
    # Check if migrations table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Apply migrations
    migrations = [
        ("001_add_tags", upgrade_001),
    ]
    
    for name, upgrade_func in migrations:
        cursor = conn.execute(
            "SELECT 1 FROM migrations WHERE name = ?", (name,)
        )
        if not cursor.fetchone():
            upgrade_func(conn)
            conn.execute(
                "INSERT INTO migrations (name) VALUES (?)", (name,)
            )
            print(f"Applied migration: {name}")
    
    conn.close()
```

## Advanced Features

### 1. Webhook Notifications
```python
import httpx

async def send_webhook(url: str, data: dict):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=data, timeout=5.0)
        except Exception as e:
            logger.error(f"Webhook failed: {str(e)}")

# In scrape_and_summarize_task
if os.getenv("WEBHOOK_URL"):
    await send_webhook(os.getenv("WEBHOOK_URL"), {
        "event": "scrape_completed",
        "job_id": job_id,
        "summary_id": summary_id
    })
```

### 2. Scheduled Jobs with APScheduler
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def scheduled_scrape():
    # Scrape configured URLs
    urls = os.getenv("SCHEDULED_URLS", "").split(",")
    for url in urls:
        if url.strip():
            # Create scraping job
            pass

scheduler.add_job(scheduled_scrape, 'cron', hour=0)  # Daily at midnight
scheduler.start()
```

### 3. Export to PDF
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

@app.get("/summaries/{summary_id}/export/pdf")
async def export_pdf(summary_id: int):
    summary = get_summary_from_db(summary_id)
    
    pdf_path = f"export_{summary_id}.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph(summary['title'], styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(summary['summary'], styles['Normal']))
    
    doc.build(story)
    
    return FileResponse(pdf_path, media_type='application/pdf')
```

## Testing Improvements

### Integration Tests
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_scrape_workflow():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Start scrape
        response = await client.post("/scrape", json={
            "url": "https://example.com",
            "max_pages": 1,
            "max_depth": 1
        })
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # Check status
        response = await client.get(f"/jobs/{job_id}")
        assert response.status_code == 200
        
        # Wait for completion (with timeout)
        import asyncio
        for _ in range(30):
            response = await client.get(f"/jobs/{job_id}")
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(1)
        
        # Verify summary created
        response = await client.get("/summaries")
        assert len(response.json()) > 0
```

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] API keys rotated
- [ ] CORS properly restricted
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] Error tracking setup (Sentry)
- [ ] Database backups configured

### Post-Deployment
- [ ] Health check endpoint responding
- [ ] API documentation accessible
- [ ] Monitor error rates
- [ ] Check response times
- [ ] Verify HTTPS
- [ ] Test all features in production
- [ ] Set up monitoring alerts

## Maintenance Tips

### Database Maintenance
```bash
# Backup database
cp summaries.db summaries_backup_$(date +%Y%m%d).db

# Clean old summaries (> 90 days)
sqlite3 summaries.db "DELETE FROM summaries WHERE created_at < datetime('now', '-90 days')"

# Vacuum database
sqlite3 summaries.db "VACUUM"
```

### Log Rotation
```bash
# Add to crontab
0 0 * * * find /var/log/app -name "*.log" -mtime +7 -delete
```

### Monitor Disk Usage
```python
import shutil

def check_disk_space():
    total, used, free = shutil.disk_usage("/")
    percent_used = (used / total) * 100
    
    if percent_used > 90:
        logger.warning(f"Disk space critical: {percent_used:.1f}% used")
        # Send alert
    
    return {"total_gb": total // (2**30), "free_gb": free // (2**30)}

# Add to stats endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "disk_space": check_disk_space(),
        "database_size_mb": os.path.getsize(DATABASE_PATH) / (1024**2),
        "summaries_count": get_summaries_count()
    }
```

## Common Production Issues

### Issue: Memory Leak
**Symptoms:** Backend memory usage grows over time

**Solution:**
```python
# Add memory monitoring
import psutil
import gc

@app.get("/debug/memory")
async def memory_info():
    process = psutil.Process()
    return {
        "memory_mb": process.memory_info().rss / 1024**2,
        "memory_percent": process.memory_percent(),
        "gc_stats": gc.get_stats()
    }

# Force garbage collection after large operations
def scrape_and_summarize_task(...):
    try:
        # ... existing code ...
    finally:
        gc.collect()
```

### Issue: Database Locks
**Symptoms:** "database is locked" errors

**Solution:**
```python
# Increase timeout and use WAL mode
conn = sqlite3.connect(
    DATABASE_PATH,
    timeout=30.0,
    check_same_thread=False
)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=30000")
```

### Issue: Slow API Responses
**Symptoms:** Requests taking > 1 second

**Solution:**
```python
# Add query optimization
# Index frequently queried columns
with get_db() as conn:
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON summaries(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON summaries(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_url ON summaries(url)")

# Use SELECT specific columns instead of *
cursor = conn.execute("""
    SELECT id, url, title, summary, created_at, status
    FROM summaries
    WHERE status = 'completed'
    ORDER BY created_at DESC
    LIMIT ?
""", (limit,))
```

### Issue: OpenAI Rate Limits
**Symptoms:** 429 errors from OpenAI

**Solution:**
```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def summarize_with_gpt_retry(text: str, url: str) -> str:
    try:
        return summarize_with_gpt(text, url)
    except openai.RateLimitError as e:
        logger.warning(f"Rate limit hit, retrying: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        raise
```

## Security Hardening

### 1. Input Validation
```python
from pydantic import validator, HttpUrl
import re

class ScrapeRequest(BaseModel):
    url: HttpUrl
    max_pages: int = Field(ge=1, le=50)
    max_depth: int = Field(ge=1, le=10)
    
    @validator('url')
    def validate_url(cls, v):
        # Block local/internal URLs
        blocked_patterns = [
            r'localhost',
            r'127\.0\.0\.1',
            r'192\.168\.',
            r'10\.',
            r'172\.(1[6-9]|2[0-9]|3[01])\.'
        ]
        url_str = str(v)
        for pattern in blocked_patterns:
            if re.search(pattern, url_str, re.IGNORECASE):
                raise ValueError("Internal URLs are not allowed")
        return v
```

### 2. API Key Rotation Helper
```python
# scripts/rotate_keys.py
import os
from cryptography.fernet import Fernet

def rotate_api_key(service: str, new_key: str):
    """Safely rotate API keys"""
    # Load encryption key
    cipher = Fernet(os.getenv("ENCRYPTION_KEY").encode())
    
    # Encrypt new key
    encrypted = cipher.encrypt(new_key.encode())
    
    # Save to secure storage
    with open(f".secrets/{service}.enc", "wb") as f:
        f.write(encrypted)
    
    print(f"✅ {service} key rotated successfully")

# Usage:
# python rotate_keys.py openai sk-new-key-here
```

### 3. Request Signing
```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook requests are authentic"""
    secret = os.getenv("WEBHOOK_SECRET", "").encode()
    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.post("/webhook")
async def webhook_handler(request: Request):
    signature = request.headers.get("X-Signature")
    payload = await request.body()
    
    if not verify_webhook_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook
    pass
```

## Monitoring & Alerts

### Setup Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST

# Metrics
scrape_requests = Counter('scrape_requests_total', 'Total scrape requests')
scrape_duration = Histogram('scrape_duration_seconds', 'Scrape duration')
active_jobs = Gauge('active_jobs', 'Number of active scraping jobs')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Use in endpoints
@app.post("/scrape")
async def scrape_endpoint(...):
    scrape_requests.inc()
    active_jobs.inc()
    
    with scrape_duration.time():
        # ... scraping logic ...
    
    active_jobs.dec()
```

### Health Check Improvements
```python
@app.get("/health/detailed")
async def detailed_health():
    checks = {
        "database": check_database_health(),
        "openai": check_openai_health(),
        "gopher": check_gopher_health(),
        "disk_space": check_disk_space(),
    }
    
    all_healthy = all(check["healthy"] for check in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }

def check_database_health():
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        return {"healthy": True}
    except Exception as e:
        return {"healthy": False, "error": str(e)}

def check_openai_health():
    try:
        # Quick test request
        client = OpenAI(api_key=OPENAI_API_KEY)
        client.models.list()
        return {"healthy": True}
    except Exception as e:
        return {"healthy": False, "error": str(e)}
```

## Backup & Recovery

### Automated Backups
```python
import shutil
from datetime import datetime, timedelta

def backup_database():
    """Create timestamped database backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"backups/summaries_{timestamp}.db"
    
    os.makedirs("backups", exist_ok=True)
    shutil.copy2(DATABASE_PATH, backup_path)
    
    # Keep only last 7 days of backups
    cleanup_old_backups(days=7)
    
    logger.info(f"Database backed up to {backup_path}")

def cleanup_old_backups(days: int):
    """Remove backups older than specified days"""
    cutoff = datetime.now() - timedelta(days=days)
    
    for filename in os.listdir("backups"):
        filepath = os.path.join("backups", filename)
        if os.path.getmtime(filepath) < cutoff.timestamp():
            os.remove(filepath)
            logger.info(f"Removed old backup: {filename}")

# Schedule daily backups
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(backup_database, 'cron', hour=2)  # 2 AM daily
scheduler.start()
```

### Recovery Procedure
```bash
#!/bin/bash
# scripts/recover.sh

echo "🔄 Starting recovery process..."

# Stop application
echo "Stopping application..."
pkill -f "python main.py"
pkill -f "next"

# Restore database
echo "Restoring database from backup..."
LATEST_BACKUP=$(ls -t backups/*.db | head -1)
cp "$LATEST_BACKUP" summaries.db
echo "✅ Database restored from $LATEST_BACKUP"

# Verify integrity
echo "Verifying database integrity..."
sqlite3 summaries.db "PRAGMA integrity_check"

# Restart application
echo "Restarting application..."
cd backend && source venv/bin/activate && python main.py &
cd frontend && npm run start &

echo "✅ Recovery complete!"
```

## Performance Benchmarks

### Expected Performance Metrics
```
Endpoint                Response Time    Throughput
---------------------------------------------------
GET /                   < 10ms          10,000 req/s
GET /summaries          < 50ms          2,000 req/s
GET /summaries/{id}     < 30ms          5,000 req/s
POST /scrape            < 100ms         50 req/s
GET /stats              < 20ms          5,000 req/s
```

### Load Testing Script
```python
import asyncio
import aiohttp
import time

async def load_test():
    url = "http://127.0.0.1:8000/summaries"
    requests = 1000
    concurrent = 50
    
    async with aiohttp.ClientSession() as session:
        start = time.time()
        
        async def fetch():
            async with session.get(url) as response:
                return await response.json()
        
        tasks = [fetch() for _ in range(requests)]
        results = await asyncio.gather(*tasks)
        
        duration = time.time() - start
        
        print(f"✅ Completed {requests} requests in {duration:.2f}s")
        print(f"📊 Throughput: {requests/duration:.1f} req/s")
        print(f"⏱️  Average latency: {(duration/requests)*1000:.1f}ms")

asyncio.run(load_test())
```

## Scaling Strategies

### Horizontal Scaling
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scraper-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: scraper-backend
  template:
    metadata:
      labels:
        app: scraper-backend
    spec:
      containers:
      - name: backend
        image: scraper-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_PATH
          value: "/data/summaries.db"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Queue-Based Processing
```python
from celery import Celery

celery_app = Celery('scraper', broker='redis://localhost:6379')

@celery_app.task
def scrape_task(url: str, max_pages: int, max_depth: int):
    """Process scraping in background worker"""
    try:
        scraped = scrape_docs(url, max_pages, max_depth)
        text = extract_text(scraped)
        summary = summarize_with_gpt(text, url)
        save_summary(url, "Title", text, summary)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Scrape task failed: {str(e)}")
        return {"status": "failed", "error": str(e)}

@app.post("/scrape")
async def scrape_endpoint(request: ScrapeRequest):
    # Queue task instead of running synchronously
    task = scrape_task.delay(
        str(request.url),
        request.max_pages,
        request.max_depth
    )
    return {"task_id": task.id, "status": "queued"}
```

## Final Production Checklist

### Security
- [ ] All API keys in environment variables
- [ ] HTTPS enforced
- [ ] CORS restricted to production domains
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS protection headers set

### Performance
- [ ] Database indexes created
- [ ] Query optimization applied
- [ ] Caching implemented
- [ ] CDN for frontend assets
- [ ] Gzip compression enabled
- [ ] Image optimization

### Monitoring
- [ ] Error tracking (Sentry/Rollbar)
- [ ] Performance monitoring (New Relic/DataDog)
- [ ] Uptime monitoring (Pingdom/UptimeRobot)
- [ ] Log aggregation (ELK/Splunk)
- [ ] Alerting configured

### Reliability
- [ ] Automated backups scheduled
- [ ] Recovery procedures documented
- [ ] Health check endpoints working
- [ ] Graceful degradation implemented
- [ ] Circuit breakers for external APIs

### Documentation
- [ ] API documentation up to date
- [ ] Deployment guide written
- [ ] Runbook for common issues
- [ ] Architecture diagrams created
- [ ] Onboarding guide for new developers

---

**Remember:** Always test changes in a staging environment before deploying to production!