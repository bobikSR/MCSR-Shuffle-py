import pyautogui
import win32gui
import win32process
import random
import time
import psutil

# TODO: LOOK INTO HOW JULTI GOT FOLDERS FROM WINDOWS AND COPY IT
# TODO: THREAD THAT LOOKS AT EVERY WINDOWS SPEEDRUNIGT OUTPUT


ALT_KEY = "altleft"

def get_minecraft_windows():
    ret_list: list[int] = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) != 0 and "Minecraft" in win32gui.GetWindowText(hwnd):
                ret_list.append(hwnd)
                print(f"Found {win32gui.GetWindowText(hwnd)} with HWND {hwnd}.")
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                print(proc.open_files())
    win32gui.EnumWindows(callback, None)
    return ret_list

def get_random_window(windows: list[int]):
    return random.choice(windows)

def random_win_to_foreground(windows: list[int]) -> int:
    win: int =  get_random_window(windows)
    print(f"Setting window with HWND {win} to foreground...")
    pyautogui.keyDown(ALT_KEY)
    win32gui.SetForegroundWindow(win)
    pyautogui.keyDown(ALT_KEY)
    return win

def run():
    original_windows: list[int]
    finished_windows: list[int] = []
    current_window: int = 0
    original_windows = get_minecraft_windows()

    print(f"Found {len(original_windows)} open Minecraft windows.")

    if len(original_windows) == 0:
        return

    current_window = random_win_to_foreground([win for win in get_minecraft_windows() if win != current_window])

    while(True):
        sleep_time: int = random.randint(5, 35)
        print(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)
        current_window = random_win_to_foreground([win for win in  get_minecraft_windows() if win != current_window])



if __name__ == "__main__":
    run()
