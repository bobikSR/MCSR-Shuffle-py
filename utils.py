import keyboard
import win32con
import win32gui


def activate_window(hwnd):
    release_if_pressed("shift")
    release_if_pressed("esc")
    keyboard.press("alt")
    # idk why https://stackoverflow.com/questions/63648053/pywintypes-error-0-setforegroundwindow-no-error-message-is-available
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
    win32gui.SetForegroundWindow(hwnd)
    keyboard.release("alt")

def get_time_str_from_ms(milis: int) -> str:
    # example: milis = 61000, secs = 61, mins = 1
    secs = milis // 1000
    ms = milis % 1000
    mins = secs // 60
    secs = secs % 60
    hrs = mins // 60
    mins = mins % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}.{ms:03d}"
    return f"{mins:02d}:{secs:02d}.{ms:03d}"

def release_if_pressed(hotkey: str):
    if keyboard.is_pressed(hotkey):
        keyboard.release(hotkey)