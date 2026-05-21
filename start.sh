#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
# MediBot AI — Quick Start Script
# Usage: bash start.sh
# ════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}"
echo "  ███╗   ███╗███████╗██████╗ ██╗██████╗  ██████╗ ████████╗    █████╗ ██╗"
echo "  ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗██╔═══██╗╚══██╔══╝   ██╔══██╗██║"
echo "  ██╔████╔██║█████╗  ██║  ██║██║██████╔╝██║   ██║   ██║      ███████║██║"
echo "  ██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██╗██║   ██║   ██║      ██╔══██║██║"
echo "  ██║ ╚═╝ ██║███████╗██████╔╝██║██████╔╝╚██████╔╝   ██║      ██║  ██║██║"
echo "  ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═════╝  ╚═════╝    ╚═╝      ╚═╝  ╚═╝╚═╝"
echo -e "${NC}"
echo -e "${GREEN}Advanced Generative AI Healthcare Assistant v2.0${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $(python3 --version)${NC}"

# Check .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}📝 Please edit .env and add your AI API key, then re-run this script.${NC}"
    echo -e "   Recommended: Get a FREE Gemini API key at ${CYAN}https://aistudio.google.com/app/apikey${NC}"
    exit 0
fi
echo -e "${GREEN}✅ .env file found${NC}"

# Check venv
if [ ! -d "venv" ]; then
    echo -e "${CYAN}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install deps
echo -e "${CYAN}📦 Installing dependencies (this may take a moment)...${NC}"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create dirs
mkdir -p logs uploads data/vectorstore data/medical_docs

# Launch
echo ""
echo -e "${GREEN}🚀 Starting MediBot AI...${NC}"
echo -e "   ${CYAN}Local:${NC}   http://localhost:8000"
echo -e "   ${CYAN}API Docs:${NC} http://localhost:8000/api/docs"
echo ""

PYTHONPATH=. uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0
