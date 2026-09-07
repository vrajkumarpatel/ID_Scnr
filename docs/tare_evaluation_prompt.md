# Tare Evaluation Prompt — IDscnr by Vraj (Google Vision OCR)

## Goal
- Evaluate whether the current implementation of IDscnr by Vraj fulfills all functional, user experience, and privacy objectives for hotel front-desk ID scanning, OCR extraction (via Google Vision), DNR management, and PMS integration.

## Environment
- Frontend: `http://localhost:5173/` (Vite React)
- Backend: `http://127.0.0.1:8000/` (FastAPI)
- Local storage paths:
  - Scans: `c:\project\IDscnr\scans\YYYY-MM-DD\`
  - Temp encrypted previews: `c:\project\IDscnr\backend\temp\`
  - PMS exports: `c:\project\IDscnr\backend\data\pms_exports\`
- Google Vision API key file: `backend/config/google_ocr.json`

## Overview
- Runs locally on hotel front-desk PCs.
- Scans IDs and passports; extracts text via Google Vision OCR (and fallback local OCR).
- Saves guest records in local encrypted DB; shows preview; supports edits.
- Detects and alerts on Do Not Rent (DNR) guests.
- Can export structured data for PMS and is designed to support auto-fill.
- Targets privacy-first operation (local-only storage; only OCR requests leave machine).

## Core Features to Verify
1. ID & Passport Scanning
   - Detect scanner/webcam; capture front and back.
   - Support: US driver’s licenses (all states) and US/international passports.
   - Send image(s) to Google Vision for TEXT_DETECTION; fallback to local OCR.
   - Extract fields:
     - First Name, Middle Name, Last Name
     - Address (Street, City, State, ZIP)
     - Date of Birth
     - ID/License/Passport Number
     - Expiration Date, Issue Date
     - Nationality/Country
     - Phone Country Code, Phone Number
   - Save images under `/scans/YYYY-MM-DD/` with filenames like `guestname_front.jpg`, `guestname_back.jpg`.
   - Show live preview and parsed text before confirming save.

2. Guest Record Management
   - Create guest in local SQLite DB with OCR data, timestamp, optional room number and remarks.
   - Link to front/back image paths.
   - Display searchable guest list with filters by date, name, room.
   - Allow edit/update of guest remarks and room info.

3. Do-Not-Rent (DNR) List
   - Add guest to DNR with reason + timestamp.
   - Scanning an existing DNR triggers full-screen alert: “⚠️ DO NOT RENT — GUEST IS BLACKLISTED”.
   - Optional admin PIN override; log override event.

4. PMS Auto-Fill Integration
   - Detect PMS window title via Win32 UI Automation API.
   - Map OCR fields (Name, DOB, Address, etc.) to PMS inputs.
   - Simulate key events to auto-type data on “Save & Fill”.

5. UI / Dashboard
   - Tabs: Today’s Check-ins, Scan New ID, Do Not Rent, Settings / Admin.
   - Dashboard summary: counts of today’s scans, total guests, DNR alerts.
   - Interface style: glassmorphism, blue/gray/amber palette, Framer Motion transitions, 1080p-friendly.

6. Settings / Admin Panel
   - Hotel name, logo, address.
   - Scanner device selection & refresh.
   - Google Vision API toggle and credentials upload.
   - Admin PIN setup/change.
   - Database backup folder.
   - PMS window title + field mapping editor.

## Privacy & Compliance Checks
Local Privacy Defaults:
- All images & OCR data are saved locally (no external DB).
- Only Google Vision OCR receives image data.
- OCR requests must be sent over HTTPS.
- Prefer sending only ID text regions (face/photo redacted) when supported.

Security Validation:
- SQLite database encrypted with AES-256.
- Admin PIN required for: viewing DNR, enabling Google OCR, modifying settings.
- Audit log maintained for scans, DNR actions, OCR method used.

Implementation Note for Tare:
- Current code sends full image content to Vision via `images:annotate` REST API. If redaction of face/photo is required, flag as non-compliant and suggest cropping/redaction (e.g., detect text bounding boxes and mask non-text regions).

## Evaluation Tasks for Tare
| Category | Task | Expected Outcome |
|---|---|---|
| OCR Accuracy | Scan sample IDs and passports | Text fields correctly extracted (names, DOB, ID number, address, expiry, issue date, nationality) |
| Google Vision API Calls | Inspect payloads | HTTPS used; only necessary content sent; redaction desired — flag if full images are sent |
| Guest Management | Add, search, and edit guest records | Functional, stable, data persists; images linked; remarks and room editable |
| DNR Handling | Scan a blacklisted guest | Immediate red alert; override requires PIN; override logged |
| PMS Auto-Fill | Open PMS mock window and trigger auto-fill | Fields auto-populated accurately |
| UI/UX Design | Navigate dashboard | Modern design, responsive, fast; follows glassmorphism palette |
| Data Privacy | Check local directories and network traffic | No unapproved external transmissions |
| Database Security | Attempt DB access without key | Access denied; encryption enforced |
| Logs | Review system logs | Accurate records of scans, DNR events, OCR method |

## Expected Deliverable from Tare
- Structured pass/fail report:

| Category | Pass/Fail | Notes | Improvement Suggestions |
|---|---|---|---|
| OCR & Extraction | ✅/❌ | … | … |
| DNR System | ✅/❌ | … | … |
| Guest Management | ✅/❌ | … | … |
| PMS Integration | ✅/❌ | … | … |
| UI & Design | ✅/❌ | … | … |
| Security & Privacy | ✅/❌ | … | … |
| Google Vision Compliance | ✅/❌ | … | … |
| Overall | ✅/❌ | Summary & Recommendations |  |

## Evaluation Question for Tare
Based on all requirements above, does the current implementation of “IDscnr by Vraj” fully satisfy the hotel use case for on-premises ID scanning, OCR extraction (via Google Vision), DNR management, and PMS integration while maintaining privacy compliance and security best practices?