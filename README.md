# Web3 Documentation Scraper

### Overview
An AI-powered documentation scraper and summarizer for Web3 projects. Built with FastAPI, Next.js, Gopher AI and Hugging face Transformer. Built specifically for blockchain developers, it helps you understand complex Web3 technologies in minutes instead of hours.

 Features
🔍 Smart Scraping - Crawl documentation sites with configurable depth
🤖 AI Summarization - GPT-4 powered intelligent summaries
📊 Dashboard UI - Modern, responsive interface with Tailwind CSS
💾 Persistent Storage - SQLite database for history tracking
🔄 Background Processing - Non-blocking scraping jobs
🔎 Search & Filter - Find summaries quickly
📥 Export - Download summaries as Markdown
📈 Analytics - Track scraping statistics

### Technology Stack
1. Gopher AI SDK - Web scraping API
2. Hugging face Transformer - Multiple AI models
3. FastAPI - Backend framework
4. Next.js - Frontend framework
5. Tailwind CSS - Styling

### Deployment
- **Vercel** - Frontend hosting platform
- **Render/Railway** - Backend deployment options

## Key Setup Steps

### Prerequisites
- Python 3.8+
- Node.js 16+
- Gopher API
- Hugging Face API token (free)

### Installation
1. Clone & Setup
```bash
git clone <your-repo>
cd web3-docs-scraper-dashboard
```

2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your API keys
```
4. Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Configure your backend URL in .env.local
```

5. Run the Application

```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend  
cd frontend
npm run dev
2. Configure API keys and endpoints
3. Deploy validator node
```

### License
MIT License - feel free to use this project for personal or commercial purposes.

### Support
If you encounter issues:

- Check the troubleshooting section
- Review backend logs
- Open an issue on GitHub

Built with ❤️ for the Web3 community
