#!/bin/bash

echo "🚀 Web3 Docs Scraper Dashboard - Automated Setup"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "📦 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.9+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $(python3 --version) found${NC}"

# Check Node.js
echo "📦 Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 18+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js $(node --version) found${NC}"

# Backend Setup
echo ""
echo "🔧 Setting up Backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt --quiet

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit backend/.env and add your API keys${NC}"
fi

cd ..

# Frontend Setup
echo ""
echo "🔧 Setting up Frontend..."
cd frontend

# Install dependencies
echo "Installing Node.js dependencies..."
npm install --quiet

# Create .env.local if not exists
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local file..."
    cp .env.local.example .env.local
fi

# Create postcss.config.js if not exists
if [ ! -f "postcss.config.js" ]; then
    echo "Creating postcss.config.js..."
    cat > postcss.config.js << EOF
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF
fi

cd ..

echo ""
echo -e "${GREEN}✅ Setup completed successfully!${NC}"
echo ""
echo "📝 Next steps:"
echo "1. Edit backend/.env and add your API keys:"
echo "   - GOPHER_API_KEY"
echo "   - OPENAI_API_KEY"
echo ""
echo "2. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
echo "   python main.py"
echo ""
echo "3. Start the frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "🎉 Happy scraping!"