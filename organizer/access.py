"""Non-destructive Windows read/delete-sharing probe; no privilege changes."""
import os


def ensure_movable(path):
    if os.name != "nt":
        with path.open("rb"):
            return
    import ctypes
    from ctypes import wintypes
    if getattr(path.stat(), "st_file_attributes", 0) & 1:
        raise PermissionError("Read-only file; not moved.")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                       wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    # GENERIC_READ | DELETE, allow all sharing, OPEN_EXISTING, no reparse traversal.
    handle = create(str(path), 0x80010000, 7, None, 3, 0x00200000, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    close(handle)
