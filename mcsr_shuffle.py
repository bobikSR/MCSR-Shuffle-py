import os

import pyautogui
import win32gui, win32con, win32api
import win32process
import random
import time

from pywin.scintilla.bindings import assign_command_id

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

def get_random_window(instances: list[MinecraftInstance]) -> MinecraftInstance:
    return random.choice(instances)

def random_win_to_foreground(instances: list[MinecraftInstance]) -> MinecraftInstance:
    chosen_instance = get_random_window(instances)
    print(f"Setting window with HWND {chosen_instance.hwnd} to foreground...")
    activate_window(chosen_instance.hwnd)
    return chosen_instance

def on_before_switch(instance: MinecraftInstance):
    if is_in_state(instance, "inworld,gamescreenopen"):
        pyautogui.press("esc", 2, 30)
    return

def set_up(instances: list[MinecraftInstance]):
    for inst in instances:
        if is_in_state(inst, "title"):
            print("in title")
            activate_window(inst.hwnd)
            pyautogui.press("tab")
            time.sleep(0.1)
            pyautogui.press("enter")


def run():
    original_windows: list[MinecraftInstance] = get_minecraft_windows()
    #if len(original_windows) < 2:
    #   return
    finished_windows: list[int] = []
    set_up(original_windows)

    print(f"Found {len(original_windows)} open Minecraft windows.")

    if len(original_windows) == 0:
        return

    current_window: MinecraftInstance = random_win_to_foreground(original_windows)

    while(True):
        sleep_time: int = random.randint(5, 35)
        print(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)
        possible_windows = [inst for inst in original_windows if inst.hwnd != current_window.hwnd]
        if len(possible_windows) > 1:
            on_before_switch(current_window)
            current_window = random_win_to_foreground([inst for inst in original_windows if inst.hwnd != current_window.hwnd])

def activate_window(hwnd):
    foreground = win32gui.GetForegroundWindow()

    current_thread = win32api.GetCurrentThreadId()
    foreground_thread, _ = win32process.GetWindowThreadProcessId(foreground)
    target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)

    attached_to_foreground = False
    attached_to_target = False

    try:
        if current_thread != foreground_thread:
            win32process.AttachThreadInput(
                current_thread,
                foreground_thread,
                True,
            )
            attached_to_foreground = True

        if current_thread != target_thread:
            win32process.AttachThreadInput(
                current_thread,
                target_thread,
                True,
            )
            attached_to_target = True

        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(hwnd)
        win32gui.SetActiveWindow(hwnd)
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

    finally:
        if attached_to_target:
            win32process.AttachThreadInput(
                current_thread,
                target_thread,
                False,
            )

        if attached_to_foreground:
            win32process.AttachThreadInput(
                current_thread,
                foreground_thread,
                False,
            )

if __name__ == "__main__":
    run()
