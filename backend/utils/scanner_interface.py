"""
Basic Windows scanner integration (WIA) helpers.

This module provides pragmatic WIA-based capture using the CommonDialog to
acquire images from an installed scanner device. It favors a simple, UI-driven
flow that works in most Windows environments without deep TWAIN/WIA handling.

Notes:
- Uses comtypes to access WIA CommonDialog.ShowAcquireImage, which will present
  the native device UI. This is acceptable for a local desktop app.
- Duplex capture is implemented as two successive acquisitions (front/back).
  Many devices support true duplex via properties, but this simple approach
  avoids vendor-specific complexity and still meets the functional need.
- If comtypes/WIA are unavailable, callers should handle exceptions and fall
  back to upload.
"""

from typing import List, Optional, Tuple
import os
import tempfile


def list_devices() -> List[str]:
    """Enumerate available WIA devices by name. Returns a best-effort list.
    If enumeration fails, returns a minimal list.
    """
    try:
        import comtypes.client
        dm = comtypes.client.CreateObject("WIA.DeviceManager")
        devices = []
        # WIA collections are 1-indexed
        for i in range(1, dm.DeviceInfos.Count + 1):
            info = dm.DeviceInfos.Item(i)
            try:
                name = info.Properties("Name").Value
            except Exception:
                name = "Scanner"
            devices.append(name)
        if not devices:
            devices = ["Scanner (WIA)"]
        return devices
    except Exception:
        # Fallback if WIA/comtypes not available
        return ["Upload Mode"]


def _wia_acquire_to_bytes() -> bytes:
    """Show the WIA acquisition dialog and return JPEG bytes.
    Saves to a temp file via ImageFile.SaveFile, then reads bytes.
    """
    import comtypes.client

    cd = comtypes.client.CreateObject("WIA.CommonDialog")
    # ShowAcquireImage args: DeviceType, Intent, WiaImageBias, FormatID, AlwaysSelectDevice, UseDeviceUI
    # Using defaults so the device UI decides format; ensure we save as JPEG if possible.
    img = cd.ShowAcquireImage()  # returns ImageFile

    # Persist to a temp path (WIA ImageFile exposes SaveFile method)
    fd, tmp = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    try:
        img.SaveFile(tmp)
        with open(tmp, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass


def capture_image_from_device(device_name: Optional[str] = None) -> bytes:
    """Capture a single image from the selected device via WIA.
    device_name is currently informational; the WIA dialog will allow selection.
    """
    try:
        return _wia_acquire_to_bytes()
    except Exception as e:
        raise RuntimeError(f"WIA capture failed: {e}")


def capture_duplex(device_name: Optional[str] = None) -> Tuple[bytes, Optional[bytes]]:
    """Capture front and back images via two successive WIA acquisitions.
    
    This will show the Windows scanner dialog twice:
    1. First dialog: Scan the FRONT of the ID
    2. Second dialog: Scan the BACK of the ID (can be cancelled)
    
    Returns (front_bytes, back_bytes). If back is skipped, returns None for back.
    """
    import logging
    
    logging.info("Starting front scan...")
    try:
        front = capture_image_from_device(device_name)
        logging.info(f"Front scan completed: {len(front)} bytes")
    except Exception as e:
        logging.error(f"Front scan failed: {e}")
        raise RuntimeError(f"Failed to scan front: {e}")
    
    logging.info("Starting back scan... (you can cancel if not needed)")
    try:
        back = capture_image_from_device(device_name)
        logging.info(f"Back scan completed: {len(back)} bytes")
    except Exception as e:
        logging.info(f"Back scan cancelled or failed: {e}")
        back = None
    
    return front, back