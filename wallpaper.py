import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes

VIDEO = r"C:\Wallpaper\yaemiko.mp4"
MPV = r"C:\Program Files\MPV Player\mpv.exe"
TITLE = "MPV_WALLPAPER"

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32
user32.FindWindowW.restype = wintypes.HWND
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowExW.restype = wintypes.HWND
user32.FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.SendMessageTimeoutW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                                       wintypes.LPARAM, wintypes.UINT, wintypes.UINT,
                                       ctypes.c_void_p]
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.SetParent.restype = wintypes.HWND
user32.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
user32.MoveWindow.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_int,
                              ctypes.c_int, ctypes.c_int, wintypes.BOOL]
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
user32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.c_void_p, ctypes.c_void_p, wintypes.LPARAM]

EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
MonitorProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE, wintypes.HDC,
                                 ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)

GWL_STYLE = -16
WS_POPUP = 0x80000000
WS_CHILD = 0x40000000


def get_workerw():
    progman = user32.FindWindowW("Progman", None)
    user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0, 1000, None)
    found = []

    def callback(hwnd, lparam):
        if user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None):
            w = user32.FindWindowExW(None, hwnd, "WorkerW", None)
            if w:
                found.append(w)
        return True

    user32.EnumWindows(EnumProc(callback), 0)
    if found:
        return found[0]
    return user32.FindWindowExW(progman, None, "WorkerW", None)


def get_monitors():
    rects = []

    def cb(hmon, hdc, lprc, lparam):
        r = lprc.contents
        rects.append((r.left, r.top, r.right, r.bottom))
        return True

    user32.EnumDisplayMonitors(None, None, MonitorProc(cb), 0)
    return rects


def main():
    print("Bat dau...")
    if not os.path.exists(MPV):
        print("Khong thay mpv:", MPV)
        sys.exit(1)
    if not os.path.exists(VIDEO):
        print("Khong thay video:", VIDEO)
        sys.exit(1)

    workerw = get_workerw()
    if not workerw:
        print("Khong tim thay WorkerW")
        sys.exit(1)

    wr = wintypes.RECT()
    user32.GetWindowRect(workerw, ctypes.byref(wr))
    print("Vung nen:", wr.left, wr.top, wr.right, wr.bottom)

    mons = get_monitors()
    print("Cac man hinh:", mons)

    # Man hinh chinh (goc 0,0) - la man ben phai cua ban
    target = next((m for m in mons if m[0] == 0 and m[1] == 0), mons[0])
    l, t, r, b = target
    w, h = r - l, b - t
    print("Man hinh dich:", target)

    cmd = [
        MPV,
        f"--title={TITLE}",
        "--no-border",
        "--no-osc",
        "--no-input-default-bindings",
        "--loop-file=inf",
        "--no-audio",
        "--hwdec=auto",
        "--force-window=yes",
        "--keep-open=yes",
        f"--geometry={w}x{h}+{l}+{t}",
        VIDEO,
    ]
    proc = subprocess.Popen(cmd)

    hwnd = None
    for _ in range(100):
        hwnd = user32.FindWindowW(None, TITLE)
        if hwnd:
            break
        time.sleep(0.1)
    if not hwnd:
        print("Khong thay cua so mpv")
        proc.terminate()
        sys.exit(1)

    # Gan vao nen, doi sang kieu cua so con
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    style = (style & ~WS_POPUP) | WS_CHILD
    user32.SetWindowLongW(hwnd, GWL_STYLE, style)
    user32.SetParent(hwnd, workerw)

    # Toa do tuong doi so voi goc cua vung nen
    x = l - wr.left
    y = t - wr.top
    user32.MoveWindow(hwnd, x, y, w, h, True)
    print("Da gan vao nen tai", x, y, w, h, "- Nhan Ctrl+C de dung.")

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()