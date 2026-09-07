# IDSCNR - Portfolio Showcase

## Project Overview

**IDSCNR** is a privacy-focused ID scanning and guest management system designed for hospitality and property management. Built with FastAPI and React, it defaults to secure, local Tesseract OCR processing rather than a cloud API — with an opt-in cloud OCR provider (Google Vision) available if you supply your own key. See the [README](./README.md) for the full, verified feature list and known limitations.

---

## Tagline

**"Privacy-First ID Scanning & Guest Management - Your Data, Your Control"**

---

## Short Description

IDSCNR is a full-stack web application that automates guest check-in by scanning and extracting data from ID documents. By default, OCR runs locally via Tesseract, so guest data never leaves the machine — a Google Vision cloud OCR option exists but is opt-in and off by default. The system includes automated DNR (Do Not Rent) matching, AES-256-GCM encrypted image storage, and PMS export via JSON/CSV files, an HTTP POST, or Windows keystroke-based autofill into another application's window.

---

## Key Features

### 🔒 Privacy & Security
- **Local OCR by Default**: Text extraction runs on-premises using Tesseract OCR; a cloud Google Vision provider is available but opt-in only
- **Encrypted Storage**: AES-256-GCM encryption for all ID images at rest
- **No External APIs Required**: The default configuration has zero cloud dependency for OCR
- **JWT Authentication**: Secure token-based access control
- **PIN Protection**: Admin operations require PIN verification

### 📸 ID Processing
- **Multi-Format Support**: Driver's licenses, passports, and ID cards
- **Barcode Reading**: Automatic PDF417 barcode parsing for AAMVA data
- **Smart Text Extraction**: Advanced OCR with image preprocessing
- **Date Normalization**: Handles multiple date formats (MM/DD/YYYY, ISO, MRZ)
- **Field Parsing**: Extracts name, DOB, address, ID number, expiration dates

### 👥 Guest Management
- **Check-In Tracking**: Complete history of guest visits
- **Search & Filter**: Find guests by name, date, or ID number
- **Edit Capabilities**: Update guest information with validation
- **Image Viewing**: Secure, encrypted image retrieval
- **Real-Time Updates**: Server-Sent Events for live notifications

### 🚫 DNR System
- **Automated Matching**: Fuzzy matching algorithm for blacklist entries
- **Multi-Tier Scoring**: Configurable match confidence levels
- **Override Tracking**: Audit trail for DNR overrides
- **Cascade Updates**: Automatic tagging across guest history
- **Admin Controls**: PIN-protected DNR management

### 📊 Analytics & Reporting
- **Daily Statistics**: Check-in counts by day
- **Monthly Trends**: MTD (Month-to-Date) metrics
- **DNR Analytics**: Hit rates and override statistics
- **Export Capabilities**: JSON, CSV, and API integration

### 🔌 PMS Integration
- **Multiple Export Formats**: JSON, CSV, or direct API calls
- **Auto-Fill Support**: Windows-based form automation
- **Configurable Mapping**: Custom field mapping for different PMS systems
- **Batch Processing**: Export multiple guests at once

### 🎨 Modern UI/UX
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark Mode**: Eye-friendly dark theme
- **Smooth Animations**: Framer Motion for polished interactions
- **Intuitive Navigation**: Clean, organized interface
- **Real-Time Feedback**: Loading states and error handling

---

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework with automatic API documentation
- **SQLAlchemy**: ORM for database management
- **Tesseract OCR**: Open-source OCR engine for text extraction
- **Pillow**: Image processing and manipulation
- **Cryptography**: AES encryption for secure storage
- **Pydantic**: Data validation and serialization

### Frontend
- **React 18**: Modern UI library with hooks
- **Vite**: Fast build tool and dev server
- **TailwindCSS**: Utility-first CSS framework
- **Framer Motion**: Animation library
- **Axios**: HTTP client for API calls

### Infrastructure
- **SQLite**: Lightweight database (easily switchable to PostgreSQL)
- **Docker**: Containerization for easy deployment
- **Nginx**: Reverse proxy and static file serving (production)

---

## Technical Highlights

### Architecture
- **RESTful API**: FastAPI endpoints with auto-generated OpenAPI docs at `/docs`
- **Modular Design**: Separated concerns (OCR, DNR, security, database) across dedicated modules
- **Type Safety**: Pydantic schemas and type hints on the Python side
- **Error Handling**: Exception handling with HTTP error responses throughout `main.py`
- **Logging**: Plain-text application logging to `backend/data/app.log` (not structured/JSON)

### Performance
- **Async Operations**: FastAPI async endpoints for concurrent requests
- **Database Indexing**: Optimized queries with proper indexes
- **Image Optimization**: JPEG compression and efficient storage
- **Caching**: Browser caching for static assets

### Code Quality
- **Clean Code**: DRY principles, modular functions
- **Documentation**: Comprehensive docstrings and comments
- **Testing**: Unit tests and E2E tests with Playwright
- **Linting**: Code quality checks and formatting

---

## Use Cases

1. **Hotels & Motels**: Streamline guest check-in with automated ID scanning
2. **Property Management**: Track tenant information and manage DNR lists
3. **Event Venues**: Quick attendee registration and verification
4. **Rental Properties**: Verify guest identity and check against blacklists
5. **Security Services**: ID verification and record keeping

---

## Project Statistics

- **Lines of Code**: ~5,400 (Backend ~3,800 + Frontend ~1,600), counted from the tracked source files
- **API Endpoints**: 38 RESTful endpoints (counted in `backend/main.py`)
- **Database Tables**: 2 main tables (Guests, Blacklist)
- **Components**: 5 page/component files (App, Header, Guests, DNR, Settings)
- **Test Coverage**: Test files exist for backend (pytest) and frontend (Vitest + Playwright) covering date parsing/validation, API smoke, image security, and key UI flows — not run/measured as part of this integration, so no coverage percentage is claimed

---

## Development Highlights

- **Privacy-First by Default**: Tesseract OCR runs locally with no cloud dependency; a Google Vision cloud OCR provider exists as an explicit opt-in, not the default
- **Local Prototype, Not Yet Production-Hardened**: functional error handling and file logging exist, but there's no CI, an unsalted PIN hash, and a hardcoded JWT fallback secret — see the README for the full list
- **Modular Architecture**: OCR, DNR matching, security, and PMS export are cleanly separated modules, making it straightforward to extend
- **Windows-Dependent Features**: physical scanner capture and PMS window autofill require Windows (`pywin32`/`comtypes`); OCR-via-upload works cross-platform

---

## Future Enhancements

- Multi-language OCR support
- Advanced image preprocessing
- Batch import/export
- Mobile app (React Native)
- Cloud backup integration
- Advanced analytics dashboard
- Webhook support for PMS integration
- Multi-tenant support

---

## Repository Information

- **GitHub**: [github.com/vrajkumarpatel/ID_Scnr](https://github.com/vrajkumarpatel/ID_Scnr)
- **License**: MIT
- **Status**: Working local prototype — see [README.md § Limitations](./README.md#limitations) for what's not yet production-hardened (no CI, unsalted PIN hash, hardcoded JWT fallback secret, no Docker/Electron despite being documented)
- **Maintainer**: Vrajkumar Patel

---

## Screenshots

*[Add screenshots of:*
- *Main guest list interface*
- *ID scanning workflow*
- *DNR management page*
- *Settings and configuration*
- *Analytics dashboard*]*

---

## Demo

*[Add link to live demo or video demonstration]*

---

**Built with ❤️ by Vrajkumar Patel**


