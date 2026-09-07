import os
import time
import json
import win32gui
import win32api
import win32con
import win32clipboard

def _enum_windows():
    wins = []
    def cb(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            t = win32gui.GetWindowText(hwnd)
            if t:
                wins.append((hwnd, t))
    win32gui.EnumWindows(cb, None)
    return wins

def _find_window(title_substr: str | None):
    if not title_substr:
        return None
    title_substr = title_substr.lower()
    for hwnd, t in _enum_windows():
        if title_substr in t.lower():
            return hwnd
    return None

def _set_clipboard_text(s: str):
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, s)
    finally:
        win32clipboard.CloseClipboard()

def _send_ctrl_v():
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(ord('V'), 0, 0, 0)
    time.sleep(0.01)
    win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

def _send_tab():
    win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)
    time.sleep(0.01)
    win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)

def autofill_guest(hwnd, guest, tab_order: list[str], delay_ms: int = 30):
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(max(0.05, delay_ms/1000.0))
    filled = []
    for key in tab_order:
        val = getattr(guest, key, None)
        if val is None:
            _send_tab()
            time.sleep(max(0.01, delay_ms/1000.0))
            continue
        _set_clipboard_text(str(val))
        _send_ctrl_v()
        time.sleep(max(0.01, delay_ms/1000.0))
        filled.append(key)
        _send_tab()
        time.sleep(max(0.01, delay_ms/1000.0))
    return {"filled": filled}
