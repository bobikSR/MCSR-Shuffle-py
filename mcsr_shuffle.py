import pyautogui
import win32gui
import win32process
import random
import time
from utils import *
import psutil
from pypsrp import powershell
from win32comext.mapi.emsabtags import PR_EMS_AB_TURN_REQUEST_THRESHOLD

from minecraft_instance import MinecraftInstance

# TODO: LOOK INTO HOW JULTI GOT FOLDERS FROM WINDOWS AND COPY IT
# TODO: THREAD THAT LOOKS AT EVERY WINDOWS SPEEDRUNIGT OUTPUT


ALT_KEY = "altleft"

def get_minecraft_windows() -> list[MinecraftInstance]:
    ret_list: list[MinecraftInstance] = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) != 0 and "Minecraft" in win32gui.GetWindowText(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)

                proc = psutil.Process(pid)
                cmd_line: list[str] = proc.cmdline()
                found_instance = MinecraftInstance(hwnd, pid, cmd_line)
                print(f"Found {str(found_instance)}")
                ret_list.append(found_instance)
    win32gui.EnumWindows(callback, None)
    return ret_list
# VERSIONS
# prism launcher - minecraft-{version}-client.jar | "minecraft-(.+)-client.jar" | "intermediary/(.+)/intermediary"
# multi mc - minecraft-{version}-client.jar | "minecraft-(.+)-client.jar" | "intermediary/(.+)/intermediary"
# vanilla (has to have fabric to have srigt) - after 'version' 'fabric-loader-{loader version}-{version}' | "(fabric-loader-\\d\\.\\d+(\\.\\d+)?-)?(.+?) "
# colorMC - minecraft-{version}-client.jar

# FOLDER PATH
# prism - starts with '-Djava.library.path' - NATIVES FOLDER PATH, NOT .MINECRAFT!
# multi mc - starts with '-Djava.library.path' - NATIVES FOLDER PATH, NOT .MINECRAFT! (according to jingle can also have double quotes)
# vanilla - item after '--gameDir' (according to julti can also be double quotes)
# color mc - item after '--gameDir'

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
    original_windows: list[MinecraftInstance]
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
    #run()
    l = get_minecraft_windows()
