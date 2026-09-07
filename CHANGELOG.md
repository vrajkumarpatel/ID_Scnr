# Changelog

All notable changes to IDSCNR will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive installation scripts for Windows, macOS, and Linux
- Detailed installation guide (INSTALL.md) for all operating systems
- Portfolio showcase documentation (PORTFOLIO.md)
- Date utility module to reduce code duplication
- MIT License file
- Enhanced .gitignore for proper repository management

### Changed
- **BREAKING**: Removed Google OCR support completely - now uses Tesseract OCR only
- Refactored date parsing functions into reusable utility module
- Updated Docker configuration to include Tesseract OCR installation
- Improved code organization and removed duplicate functions
- Updated deployment guide to remove Google OCR references
- Enhanced README with comprehensive installation instructions

### Fixed
- Removed duplicate date parsing functions throughout codebase
- Fixed test imports to use new date utility module
- Cleaned up unused imports

### Security
- Removed dependency on external cloud APIs for OCR processing
- All OCR processing now happens locally

## [0.1.0] - 2025-01-XX

### Added
- Initial release
- FastAPI backend with RESTful API
- React frontend with modern UI
- Tesseract OCR integration
- Guest management system
- DNR (Do Not Rent) matching system
- Encrypted image storage
- PMS integration support
- Real-time check-in notifications
- Analytics and reporting
- Admin authentication system

---

## Upgrade Notes

### From Previous Versions

If upgrading from a version that used Google OCR:

1. **No migration needed** - The system automatically uses Tesseract OCR
2. **No API keys required** - All processing is local
3. **Database schema** - No changes, existing data is compatible
4. **Settings** - OCR provider setting is now fixed to "tesseract"

---

## Future Roadmap

- [ ] Multi-language OCR support
- [ ] Advanced image preprocessing
- [ ] Batch import/export
- [ ] Mobile app (React Native)
- [ ] Cloud backup integration
- [ ] Advanced analytics dashboard
- [ ] Webhook support for PMS integration
- [ ] Multi-tenant support


