# IDSCNR Installation Guide

Quick installation guide for different operating systems.

## Windows

### Prerequisites

1. **Python 3.11+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation
   - Verify: `python --version`

2. **Node.js 18+**
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify: `node --version` and `npm --version`

3. **Tesseract OCR**
   - Download installer from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - Install to default location: `C:\Program Files\Tesseract-OCR`
   - Add to PATH:
     - Open System Properties → Environment Variables
     - Add `C:\Program Files\Tesseract-OCR` to System PATH
   - Verify: `tesseract --version`

### Installation Steps

```powershell
# Clone repository
git clone https://github.com/vrajkumar-patel/idscnr.git
cd idscnr

# Backend setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -c "from database import init_db; from security import ensure_keys_initialized; ensure_keys_initialized(); init_db()"

# Frontend setup (new terminal)
cd frontend
npm install

# Start services
# Terminal 1 - Backend
cd backend
venv\Scripts\activate
python -m uvicorn main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

---

## macOS

### Prerequisites

1. **Homebrew** (if not installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Python 3.11+**
   ```bash
   brew install python@3.11
   ```

3. **Node.js 18+**
   ```bash
   brew install node
   ```

4. **Tesseract OCR**
   ```bash
   brew install tesseract
   ```

### Installation Steps

```bash
# Clone repository
git clone https://github.com/vrajkumar-patel/idscnr.git
cd idscnr

# Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "from database import init_db; from security import ensure_keys_initialized; ensure_keys_initialized(); init_db()"

# Frontend setup
cd ../frontend
npm install

# Start services
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

---

## Linux (Ubuntu/Debian)

### Prerequisites

```bash
# Update package list
sudo apt-get update

# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Tesseract OCR
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev
```

### Installation Steps

```bash
# Clone repository
git clone https://github.com/vrajkumar-patel/idscnr.git
cd idscnr

# Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "from database import init_db; from security import ensure_keys_initialized; ensure_keys_initialized(); init_db()"

# Frontend setup
cd ../frontend
npm install

# Start services
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0

# Terminal 2 - Frontend
cd frontend
npm run dev
```

---

## Linux (Fedora/RHEL/CentOS)

### Prerequisites

```bash
# Install Python 3.11
sudo dnf install -y python3.11 python3.11-pip

# Install Node.js 18+
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo dnf install -y nodejs

# Install Tesseract OCR
sudo dnf install -y tesseract tesseract-langpack-eng
```

### Installation Steps

Same as Ubuntu/Debian above.

---

## Docker Installation (All Platforms)

### Prerequisites

- Docker Desktop (Windows/macOS) or Docker Engine (Linux)
- Docker Compose

### Installation Steps

```bash
# Clone repository
git clone https://github.com/vrajkumar-patel/idscnr.git
cd idscnr

# Create .env file
cat > .env << EOF
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=http://localhost:5173
EOF

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Note:** For Windows, use PowerShell or Git Bash for the `openssl` command, or generate secrets manually.

---

## Verification

After installation, verify everything works:

1. **Backend Health Check**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"ok"}
   ```

2. **OCR Health Check**
   ```bash
   curl http://localhost:8000/ocr/health
   # Should return: {"ok":true,"provider":"tesseract"}
   ```

3. **Frontend Access**
   - Open browser to `http://localhost:5173`
   - Should see the IDSCNR interface

---

## Troubleshooting

### Tesseract Not Found

**Windows:**
- Verify Tesseract is in PATH: `tesseract --version`
- Restart terminal after adding to PATH

**macOS/Linux:**
- Verify installation: `tesseract --version`
- Check TESSDATA_PREFIX: `echo $TESSDATA_PREFIX`

### Python Module Errors

```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Node Module Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Port Already in Use

```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
# macOS/Linux:
lsof -i :8000

# Kill process or change port in configuration
```

---

## Next Steps

1. Set up admin PIN in Settings
2. Configure scanner device (if using physical scanner)
3. Review [README.md](./README.md) for usage guide
4. Check [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for production setup

---

**Need Help?** Open an issue on [GitHub](https://github.com/vrajkumar-patel/idscnr/issues)


