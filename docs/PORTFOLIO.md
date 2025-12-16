# IDSCNR - Portfolio Showcase

## Project Overview

**IDSCNR** is a modern, privacy-focused ID scanning and guest management system designed for hospitality and property management. Built with FastAPI and React, it provides secure, local OCR processing without relying on cloud APIs.

---

## Tagline

**"Privacy-First ID Scanning & Guest Management - Your Data, Your Control"**

---

## Short Description

IDSCNR is a full-stack web application that automates guest check-in processes by scanning and extracting data from ID documents. Unlike cloud-based solutions, all OCR processing happens locally using Tesseract, ensuring sensitive guest information never leaves your infrastructure. The system includes automated DNR (Do Not Rent) matching, encrypted image storage, and seamless PMS integration.

---

## Key Features

### 🔒 Privacy & Security
- **Local OCR Processing**: All text extraction happens on-premises using Tesseract OCR
- **Encrypted Storage**: AES-256 encryption for all ID images at rest
- **No External APIs**: Zero dependency on cloud services for core functionality
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
- **RESTful API**: Well-structured endpoints with OpenAPI documentation
- **Modular Design**: Separated concerns (OCR, DNR, security, database)
- **Type Safety**: Type hints throughout Python codebase
- **Error Handling**: Comprehensive exception handling with user-friendly messages
- **Logging**: Structured JSON logging for production monitoring

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

- **Lines of Code**: ~5,000+ (Backend + Frontend)
- **API Endpoints**: 30+ RESTful endpoints
- **Database Tables**: 2 main tables (Guests, Blacklist)
- **Components**: 15+ React components
- **Test Coverage**: Unit tests for critical functions

---

## Development Highlights

- **Privacy-First Design**: No cloud dependencies for core functionality
- **Production-Ready**: Comprehensive error handling, logging, and monitoring
- **Scalable Architecture**: Easy to extend with new features
- **Developer-Friendly**: Clear code structure, documentation, and testing
- **Cross-Platform**: Works on Windows, macOS, and Linux

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

- **GitHub**: [github.com/vrajkumar-patel/idscnr](https://github.com/vrajkumar-patel/idscnr)
- **License**: MIT
- **Status**: Production Ready
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


