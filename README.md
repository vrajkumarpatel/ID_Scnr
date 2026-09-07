# IDSCNR

**ID Scanner & Check-In Management System**

A modern, privacy-focused ID scanning and guest management application built with FastAPI and React. IDSCNR uses local Tesseract OCR to extract information from ID documents, ensuring your data never leaves your system.

**Developed by:** [Vrajkumar Patel](https://github.com/vrajkumar-patel)

---

## 🎯 Features

- **🔒 Privacy-First**: All OCR processing happens locally using Tesseract - no cloud APIs required
- **📸 ID Scanning**: Extract structured data from driver's licenses, passports, and ID cards
- **👥 Guest Management**: Track guest check-ins with full history and search capabilities
- **🚫 DNR (Do Not Rent) System**: Automated blacklist matching with configurable scoring
- **🔐 Secure Storage**: Encrypted image storage with AES encryption
- **📊 Analytics**: Daily/monthly statistics and DNR hit tracking
- **🎨 Modern UI**: Clean, responsive interface with dark mode support
- **🔌 PMS Integration**: Export guest data to Property Management Systems (JSON/CSV/API)
- **⚡ Real-time Updates**: Server-Sent Events for live check-in notifications

---

## 📋 Prerequisites

### System Requirements

- **Python 3.11+**
- **Node.js 18+** and npm
- **Tesseract OCR** (installation instructions below)
- **SQLite** (included with Python)
- **2GB+ RAM** recommended
- **10GB+ disk space** for image storage

### Installing Tesseract OCR

#### Windows

1. Download the installer from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer (e.g., `tesseract-ocr-w64-setup-5.x.x.exe`)
3. Add Tesseract to your PATH:
   - Add `C:\Program Files\Tesseract-OCR` to your system PATH
   - Or set environment variable: `TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata`
4. Verify installation:
   ```bash
   tesseract --version
   ```

#### macOS

```bash
# Using Homebrew
brew install tesseract

# Verify installation
tesseract --version
```

#### Linux (Ubuntu/Debian)

```bash
# Install Tesseract and English language data
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev

# Verify installation
tesseract --version
```

#### Linux (Fedora/RHEL)

```bash
# Install Tesseract
sudo dnf install tesseract tesseract-langpack-eng

# Verify installation
tesseract --version
```

---

## 🚀 Quick Start

### Option 1: Automated Installation (Recommended)

**Linux/macOS:**
```bash
git clone https://github.com/vrajkumar-patel/idscnr.git
cd idscnr
chmod +x scripts/install.sh
./scripts/install.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/vrajkumar-patel/idscnr.git
cd idscnr
.\scripts\install.ps1
```

### Option 2: Manual Local Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/vrajkumar-patel/idscnr.git
cd idscnr
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server (run from project root)
cd ..
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

#### 3. Frontend Setup

```bash
# In a new terminal, from the project root
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Option 2: Docker Deployment

#### Prerequisites

- Docker and Docker Compose installed
- Tesseract OCR installed on host (for volume mounting) or use the Docker image

#### Quick Start with Docker

```bash
# Clone repository
git clone https://github.com/vrajkumar-patel/idscnr.git
cd idscnr

# Create .env file (optional, for custom configuration)
cat > .env << EOF
JWT_SECRET=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
CORS_ORIGINS=http://localhost:5173
DEBUG=false
EOF

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f
```

Access:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## 📖 Usage Guide

### First Time Setup

1. **Access the Application**: Open `http://localhost:5173` in your browser
2. **Set Admin PIN**: Navigate to Settings and set your admin PIN
3. **Configure Scanner** (optional): If using a physical scanner, select your device in Settings
4. **Configure PMS Export** (optional): Set export path and format in Settings

### Scanning IDs

#### Method 1: Upload Images

1. Go to the **Guests** page
2. Click **"Upload ID Images"** or **"Scan"** button
3. Upload front and back images of the ID
4. The system will automatically:
   - Extract text using OCR
   - Parse structured data (name, DOB, address, etc.)
   - Check against DNR list
   - Save encrypted images

#### Method 2: Physical Scanner

1. Connect your scanner to the computer
2. In Settings, select your scanner device
3. Click **"Scan Duplex"** to scan both sides automatically
4. The system processes the scan automatically

### Managing Guests

- **View Guests**: Browse all check-ins on the Guests page
- **Edit Guest**: Click on a guest to edit their information
- **View History**: See all previous check-ins for the same person
- **Export to PMS**: Click "Export" to send data to your PMS system

### DNR (Do Not Rent) Management

1. **Add to DNR**: Go to DNR page, click "Add Entry"
2. **Automatic Matching**: System automatically flags guests matching DNR entries
3. **Override DNR**: Admins can override DNR matches with reason
4. **View Overrides**: Check admin panel for override history

---

## 🏗️ Architecture

```
IDSCNR/
├── backend/              # FastAPI backend
│   ├── main.py          # API routes and endpoints
│   ├── models.py        # SQLAlchemy database models
│   ├── schemas.py       # Pydantic validation schemas
│   ├── ocr_utils.py     # Tesseract OCR processing
│   ├── dnr_manager.py   # DNR matching logic
│   ├── security.py      # Encryption and authentication
│   ├── database.py      # Database initialization
│   └── utils/           # Utility functions
├── frontend/            # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx      # Main application component
│   │   ├── pages/       # Page components
│   │   ├── components/  # Reusable components
│   │   └── api.js       # API client
│   └── package.json
├── scans/               # Encrypted ID images (gitignored)
├── backup/              # Database backups (gitignored)
└── docker-compose.yml   # Docker orchestration
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# JWT Secret for authentication tokens
JWT_SECRET=your-secret-key-change-in-production

# Encryption key for image storage (auto-generated if not set)
ENCRYPTION_KEY=your-encryption-key

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Database URL (default: SQLite)
DATABASE_URL=sqlite:///./data/guestdb.sqlite

# Debug mode
DEBUG=false

# Log level
LOG_LEVEL=INFO
```

### Application Settings

Access Settings page in the UI to configure:
- OCR Provider (Tesseract only)
- Scanner device selection
- Auto PMS write
- Dark mode
- PMS export settings
- Autofill configuration

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
python -m pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm test
```

### End-to-End Tests

```bash
cd frontend
npm run test:e2e
```

---

## 📦 Production Deployment

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed production deployment instructions.

### Quick Production Checklist

- [ ] Set strong `JWT_SECRET` and `ENCRYPTION_KEY`
- [ ] Configure HTTPS/SSL certificates
- [ ] Set up reverse proxy (nginx/Apache)
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Set up monitoring and alerts
- [ ] Review and restrict CORS origins

---

## 🔒 Security Features

- **Encrypted Storage**: All ID images are encrypted at rest using AES-256
- **JWT Authentication**: Secure token-based authentication
- **PIN Protection**: Admin operations require PIN verification
- **Input Validation**: All inputs validated and sanitized
- **Rate Limiting**: Protection against brute force attacks
- **Secure Headers**: CORS and security headers configured
- **No External APIs**: All processing happens locally

---

## 🛠️ Development

### Project Structure

- **Backend**: FastAPI with SQLAlchemy ORM
- **Frontend**: React 18 with Vite, TailwindCSS, Framer Motion
- **Database**: SQLite (easily switchable to PostgreSQL)
- **OCR**: Tesseract OCR (local processing)

### Adding Features

1. **Backend**: Add routes in `backend/main.py`, models in `backend/models.py`
2. **Frontend**: Add pages in `frontend/src/pages/`, components in `frontend/src/components/`
3. **API**: Update `frontend/src/api.js` for new endpoints

### Code Style

- **Python**: Follow PEP 8, use type hints
- **JavaScript**: Use ES6+, follow React best practices
- **Formatting**: Use Black for Python, Prettier for JavaScript

---

## 📝 API Documentation

Interactive API documentation is available at `/docs` when the backend is running.

### Key Endpoints

- `GET /guests` - List guests
- `POST /scan/ingest` - Upload and process ID images
- `POST /scan/duplex` - Scan from physical scanner
- `GET /dnr` - List DNR entries
- `POST /dnr` - Add DNR entry
- `GET /stats/daily` - Daily statistics
- `GET /checkins/stream` - Real-time check-in stream (SSE)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Tesseract OCR** - Open-source OCR engine
- **FastAPI** - Modern Python web framework
- **React** - UI library
- **TailwindCSS** - Utility-first CSS framework

---

## 📞 Support

For issues, questions, or contributions:

- **GitHub Issues**: [Create an issue](https://github.com/vrajkumar-patel/idscnr/issues)
- **Email**: [Your email]
- **Documentation**: Check the `/docs` endpoint for API documentation

---

## 🗺️ Roadmap

- [ ] Multi-language OCR support
- [ ] Advanced image preprocessing
- [ ] Batch import/export
- [ ] Mobile app
- [ ] Cloud backup integration
- [ ] Advanced analytics dashboard
- [ ] API rate limiting improvements
- [ ] Webhook support for PMS integration

---

**Made with ❤️ by Vrajkumar Patel**
