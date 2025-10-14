# 🧪 Testing Guide

## Manual Testing Checklist

### Backend API Tests

#### 1. Health Check
```bash
curl http://127.0.0.1:8000/
# Expected: {"status": "online", "message": "...", "version": "2.0.0"}
```

#### 2. Create Scraping Job
```bash
curl -X POST "http://127.0.0.1:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://developers.gopher-ai.com/docs/masa-subnet",
    "max_pages": 3,
    "max_depth": 1
  }'
# Expected: {"job_id": 1, "status": "queued", "message": "..."}
```

#### 3. Check Job Status
```bash
curl http://127.0.0.1:8000/jobs/1
# Expected: {"id": 1, "url": "...", "status": "processing/completed/failed", ...}
```

#### 4. List Summaries
```bash
curl "http://127.0.0.1:8000/summaries?limit=10&offset=0"
# Expected: [{"id": 1, "title": "...", "summary": "...", ...}]
```

#### 5. Search Summaries
```bash
curl "http://127.0.0.1:8000/summaries?search=ethereum"
# Expected: Filtered results
```

#### 6. Get Summary Details
```bash
curl http://127.0.0.1:8000/summaries/1
# Expected: Full summary object with content
```

#### 7. Get Statistics
```bash
curl http://127.0.0.1:8000/stats
# Expected: {"total_summaries": 5, "total_jobs": 10, ...}
```

#### 8. Delete Summary
```bash
curl -X DELETE http://127.0.0.1:8000/summaries/1
# Expected: {"message": "Summary deleted successfully"}
```

### Frontend UI Tests

#### Homepage Load
- [ ] Page loads without errors
- [ ] Stats panel displays correct numbers
- [ ] Search bar is visible and functional
- [ ] "New Scrape" button is clickable

#### Create New Scrape
- [ ] Click "New Scrape" button
- [ ] Modal opens smoothly
- [ ] URL input validates proper URLs
- [ ] Sliders adjust max_pages and max_depth
- [ ] Submit starts job and shows polling status
- [ ] Modal closes after submission

#### View Summaries
- [ ] Summary cards display correctly
- [ ] Title, URL, date are visible
- [ ] Status badge shows correct color
- [ ] "View Full" button opens detail modal
- [ ] Delete button shows confirmation

#### Summary Detail Modal
- [ ] Full summary content displays
- [ ] Markdown formatting renders correctly
- [ ] Download button creates .md file
- [ ] External link opens in new tab
- [ ] Close button works

#### Search & Filter
- [ ] Search updates results in real-time
- [ ] Debouncing prevents excessive requests
- [ ] Refresh button re-fetches data
- [ ] Empty state shows when no results

#### Error Handling
- [ ] Backend down shows error message
- [ ] Invalid API response handled gracefully
- [ ] Failed jobs show error status
- [ ] Network errors display user-friendly messages

## Automated Testing (Future)

### Backend Tests (pytest)
```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_create_scrape_job():
    response = client.post("/scrape", json={
        "url": "https://example.com",
        "max_pages": 3,
        "max_depth": 1
    })
    assert response.status_code == 200
    assert "job_id" in response.json()
```

### Frontend Tests (Jest + React Testing Library)
```javascript
// __tests__/index.test.js
import { render, screen, fireEvent } from '@testing-library/react'
import Home from '../pages/index'

test('renders dashboard title', () => {
  render(<Home />)
  expect(screen.getByText(/Web3 Docs Scraper/i)).toBeInTheDocument()
})

test('opens scrape modal on button click', () => {
  render(<Home />)
  fireEvent.click(screen.getByText(/New Scrape/i))
  expect(screen.getByText(/Documentation URL/i)).toBeInTheDocument()
})
```

## Load Testing

### Using Apache Bench
```bash
# Test concurrent scraping requests
ab -n 10 -c 2 -p scrape.json -T application/json \
  http://127.0.0.1:8000/scrape
```

### Using Python
```python
import requests
import concurrent.futures

def scrape_test(i):
    response = requests.post("http://127.0.0.1:8000/scrape", json={
        "url": f"https://example.com/{i}",
        "max_pages": 2,
        "max_depth": 1
    })
    return response.status_code

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(scrape_test, range(10)))
    print(f"Success rate: {results.count(200)}/10")
```

## Common Issues & Solutions

### Issue: "Port already in use"
**Solution:**
```bash
# Find process
lsof -i :8000
# Kill process
kill -9 <PID>
```

### Issue: "Module not found"
**Solution:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "CORS error in browser"
**Solution:**
- Check `CORS_ORIGINS` in backend `.env`
- Restart backend after changing CORS settings
- Ensure frontend URL matches CORS origin

### Issue: "API key invalid"
**Solution:**
- Verify keys in `.env` file
- Check for extra spaces or quotes
- Test keys independently
- Ensure sufficient API credits

### Issue: "Database locked"
**Solution:**
```bash
# Close all connections
cd backend
rm summaries.db
python main.py  # Recreates database
```

## Performance Benchmarks

### Expected Response Times
- Health check: < 10ms
- List summaries: < 50ms
- Start scrape job: < 100ms
- GPT summarization: 5-15 seconds
- Full scrape cycle: 30-60 seconds (depends on site)

### Resource Usage
- Backend RAM: ~200-500MB
- Frontend RAM: ~150-300MB
- Database size: ~1-5MB per 100 summaries

## Security Testing

### Check for API Key Exposure
```bash
# Should NOT find any keys
grep -r "sk-" .
grep -r "Bearer" .
```

### Test CORS Protection
```bash
# Should fail from unauthorized origin
curl -H "Origin: http://malicious-site.com" \
  http://127.0.0.1:8000/summaries
```

### SQL Injection Test
```bash
# Should be safely handled
curl "http://127.0.0.1:8000/summaries?search='; DROP TABLE summaries; --"
```

## Deployment Verification

After deploying to production:
- [ ] HTTPS enabled
- [ ] Environment variables set correctly
- [ ] CORS limited to production domain
- [ ] API keys rotated
- [ ] Database backups configured
- [ ] Error logging enabled
- [ ] Rate limiting active
- [ ] Health check endpoint accessible