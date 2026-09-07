#!/bin/bash
# IDSCNR Installation Script for Linux/macOS
# This script automates the installation process

set -e  # Exit on error

echo "=========================================="
echo "IDSCNR Installation Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Please do not run as root${NC}"
   exit 1
fi

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    if [ -f /etc/debian_version ]; then
        DISTRO="debian"
    elif [ -f /etc/redhat-release ]; then
        DISTRO="redhat"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS${NC}"
echo ""

# Check for Python
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed${NC}"
    echo "Please install Python 3.11+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}Python version: $PYTHON_VERSION${NC}"

# Check for Node.js
echo "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed${NC}"
    echo "Please install Node.js 18+ and try again"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}Node.js version: $NODE_VERSION${NC}"

# Check for Tesseract
echo "Checking Tesseract OCR installation..."
if ! command -v tesseract &> /dev/null; then
    echo -e "${YELLOW}Tesseract OCR is not installed${NC}"
    echo "Installing Tesseract OCR..."
    
    if [ "$OS" == "linux" ]; then
        if [ "$DISTRO" == "debian" ]; then
            sudo apt-get update
            sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev
        elif [ "$DISTRO" == "redhat" ]; then
            sudo dnf install -y tesseract tesseract-langpack-eng
        fi
    elif [ "$OS" == "macos" ]; then
        if ! command -v brew &> /dev/null; then
            echo -e "${RED}Homebrew is not installed. Please install Homebrew first.${NC}"
            exit 1
        fi
        brew install tesseract
    fi
else
    TESSERACT_VERSION=$(tesseract --version | head -n1)
    echo -e "${GREEN}$TESSERACT_VERSION${NC}"
fi

echo ""
echo "=========================================="
echo "Installing Backend Dependencies"
echo "=========================================="

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

# Database and encryption keys will be initialized automatically on first backend start

echo ""
echo "=========================================="
echo "Installing Frontend Dependencies"
echo "=========================================="

cd ../frontend

# Install Node dependencies
echo "Installing Node.js packages..."
npm install

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo -e "${GREEN}✓ Backend dependencies installed${NC}"
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
echo -e "${GREEN}✓ Database initialized${NC}"
echo ""
echo "To start the application:"
echo ""
echo "  Terminal 1 - Backend:"
echo "    cd backend && source venv/bin/activate"
echo "    cd .."
echo "    python -m uvicorn backend.main:app --reload"
echo ""
echo "  Terminal 2 - Frontend:"
echo "    cd frontend"
echo "    npm run dev"
echo ""
echo "Then open http://localhost:5173 in your browser"
echo ""


