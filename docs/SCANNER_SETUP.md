# Scanner Setup Guide for IDSCNR

## Overview

IDSCNR supports physical scanners (bizcard scanners, document scanners, etc.) to automatically scan ID front and back, extract information using OCR, and display it in guest details.

## Supported Scanners

- **Windows Image Acquisition (WIA)** compatible scanners
- Most modern document scanners
- Bizcard scanners
- Flatbed scanners
- ADF (Automatic Document Feeder) scanners

## Setup Steps

### 1. Install Scanner Drivers

1. Connect your scanner to your computer
2. Install the scanner drivers from the manufacturer
3. Test the scanner using Windows Scanner app to ensure it works

### 2. Configure Scanner in IDSCNR

1. Open IDSCNR application
2. Go to **Settings** page
3. In the **Scanner Device** dropdown, select your scanner
4. If your scanner doesn't appear, click "Refresh" or restart the app

### 3. Using the Scanner

#### Method 1: Scan Duplex (Recommended)

1. Click the **"Scan Duplex (Front & Back)"** button in the Guests page
2. **First dialog**: Place ID front-side down and scan
3. **Second dialog**: Flip ID to back-side and scan (or cancel if you only need front)
4. The system will:
   - Extract text using OCR
   - Parse name, DOB, address, ID number, etc.
   - Create a guest record
   - Display the information in guest details
   - Check against DNR list automatically

#### Method 2: Upload Images

If scanner doesn't work:
1. Use your scanner's software to scan images
2. Save images to your computer
3. Click **"Upload Front"** and **"Upload Back"** buttons
4. Click **"Process ID"** to extract information

## Troubleshooting

### Scanner Not Detected

1. **Check Windows Scanner App**: Open Windows "Scanner" app and verify your scanner works there
2. **Check Device Manager**: Ensure scanner appears in Device Manager without errors
3. **Restart Application**: Close and reopen IDSCNR
4. **Check Settings**: Go to Settings and verify scanner is selected

### Scanner Dialog Doesn't Open

1. **Check Permissions**: Ensure IDSCNR has permission to access scanner
2. **Check Drivers**: Reinstall scanner drivers
3. **Try Different Scanner**: Test with Windows Scanner app first
4. **Check Logs**: Look at `backend/data/app.log` for error messages

### OCR Not Extracting Data

1. **Image Quality**: Ensure scans are clear and well-lit
2. **Check Debug Endpoint**: Visit `http://localhost:8000/guest/{id}/ocr-debug` to see what was extracted
3. **Check Logs**: Look for OCR errors in `backend/data/app.log`
4. **Manual Entry**: If OCR fails, you can manually edit the guest details

### Scanner Works But No Data Shows

1. **Check Guest Details**: After scanning, the guest should appear in the list
2. **Click on Guest**: Select the guest from the list to see details
3. **Check OCR Debug**: Use the debug endpoint to see what was extracted
4. **Verify Images**: Check that front/back images are visible in guest details

## Scanner Workflow

```
1. Click "Scan Duplex"
   ↓
2. Windows Scanner Dialog Opens
   ↓
3. Scan Front of ID → Click OK
   ↓
4. Windows Scanner Dialog Opens Again
   ↓
5. Scan Back of ID → Click OK (or Cancel)
   ↓
6. Images Saved & Encrypted
   ↓
7. OCR Extracts Text
   ↓
8. Data Parsed (Name, DOB, Address, etc.)
   ↓
9. Guest Record Created
   ↓
10. DNR Check Performed
   ↓
11. Guest Appears in List with Details
```

## Tips for Best Results

1. **Good Lighting**: Ensure ID is well-lit when scanning
2. **Clean ID**: Remove any smudges or dirt
3. **Flat Surface**: Place ID flat on scanner bed
4. **High Resolution**: Use 300 DPI or higher if available
5. **Both Sides**: Scanning both front and back improves accuracy
6. **Barcode**: If ID has a barcode, it will be read automatically (more accurate than OCR)

## Manual Entry

If OCR doesn't extract data correctly:
1. The guest record will still be created
2. Click on the guest in the list
3. Manually enter/edit the information
4. Click "Save" to update

## Testing Scanner

To test if your scanner is working:

1. Open Windows "Scanner" app
2. Try scanning a document
3. If that works, IDSCNR should work too

## Support

If you continue to have issues:
1. Check `backend/data/app.log` for detailed error messages
2. Verify scanner works in Windows Scanner app
3. Try a different scanner if available
4. Use Upload mode as fallback

---

**Note**: Scanner integration requires Windows and WIA-compatible scanners. On other operating systems, use the Upload mode instead.


