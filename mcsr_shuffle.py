import threading

import pydirectinput
import win32gui, win32con, win32api
import win32process
import random
import time
import logging

from utils import *
import psutil

from minecraft_instance import MinecraftInstance

# nopeaceful pre 1.14 https://github.com/contariaa/NoPeaceful-Pre1.14
# nopeaceful https://github.com/VoidXWalker/NoPeaceful/releases

logging.basicConfig(filename="logs/shuffle.log",
                    format='%(asctime)s %(levelname)s: %(message)s',
                    filemode='w')

LOGGER = logging.getLogger()

def get_minecraft_windows() -> list[MinecraftInstance]:
    ret_list: list[MinecraftInstance] = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) != 0 and "Minecraft" in win32gui.GetWindowText(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                cmd_line: list[str] = proc.cmdline()
                found_instance = MinecraftInstance(hwnd, pid, cmd_line)
                LOGGER.info(f"Found {str(found_instance)}")
                ret_list.append(found_instance)
    win32gui.EnumWindows(callback, None)
    return ret_list

def get_random_window(instances: list[MinecraftInstance]) -> MinecraftInstance:
    return random.choice(instances)

def random_win_to_foreground(instances: list[MinecraftInstance]) -> MinecraftInstance:
    chosen_instance = get_random_window(instances)
    LOGGER.info(f"Setting window with HWND {chosen_instance.hwnd} to foreground...")
    activate_window2(chosen_instance.hwnd)
    return chosen_instance

def on_before_switch(instance: MinecraftInstance, sleep_time: float):
    # press esc until player is in world and unpaused in any way (pause menu, chat, inv)
    while True:
        # pause on lost focus will take care of this
        if instance.is_in_state("inworld,unpaused"):
            break
        pydirectinput.press("esc", 1)
        time.sleep(sleep_time)
    return

# if i force unpaused -> pause on lost focus will pause -> then i can just tab -> enter to unpause

def unpause_after_switch():
    # happy path is that before this runs MC will be on the basic pause screen
    pydirectinput.press("tab", 1)
    pydirectinput.press("enter", 1)

def set_up(instances: list[MinecraftInstance], sleep_time: float):
    # first create worlds using atum
    for inst in instances:
        if inst.is_in_state("title"):
            activate_window2(inst.hwnd)
            time.sleep(sleep_time)
            pydirectinput.keyDown("shift")
            pydirectinput.press("tab")
            pydirectinput.keyUp("shift")
            time.sleep(sleep_time)
            pydirectinput.press("enter")
    # then end this with waiting for every world to stop generating
    while not all(inst.is_in_state("inworld") for inst in instances):
        time.sleep(0) # this is basically thread.yield
    LOGGER.info("Set up done!")

def ensure_correct_window(instance: MinecraftInstance, sleep_time: float):
    while True:
        time.sleep(sleep_time) # os can take a little bit for GetForegroundWindow() to return the real FG win hwnd
        if instance.hwnd == win32gui.GetForegroundWindow():
            break
        LOGGER.info(f"Correcting foreground window to {instance.hwnd}...")
        activate_window2(instance.hwnd)

def run():
    # load config file into dict
    config: dict
    with open("config.json") as cfg:
        config = json.load(cfg)

    # get all open minecraft windows
    original_windows: list[MinecraftInstance] = []
    try:
        original_windows = get_minecraft_windows()
    except Exception as e:
        LOGGER.error(str(e))
    LOGGER.info(f"Found {len(original_windows)} open Minecraft windows.")
    if len(original_windows) == 0:
        LOGGER.error("Found 0 open Minecraft instances, closing program...")
        return
    if not config["DEBUG"]:
        # if only one instance is open, the shuffle makes no sense
        if len(original_windows) < 2:
            LOGGER.error("Found only one Minecraft instance, closing program...")
            return

    # set up by creating worlds using atum
    set_up(original_windows, config["set_up_key_press_pause"])

    # set up ends on the last instance
    current_window: MinecraftInstance = original_windows[-1]

    # start thread that will check if runs on open instances were completed
    checker_thread = threading.Thread(target=is_complete_checker, args=(original_windows,))
    checker_thread.start()

    # start switching loop
    while True:
        # sleep for a random amount of time
        sleep_time: int = random.randint(config["lower_bound"], config["upper_bound"])
        LOGGER.info(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)
        # choose a window from possible ones and switch to it
        possible_windows = [inst for inst in original_windows if inst.hwnd != current_window.hwnd and not inst.is_completed]
        if len(possible_windows) < 1:
            break
        on_before_switch(current_window, config["before_switch_esc_press_pause"])
        current_window = random_win_to_foreground(possible_windows)
        ensure_correct_window(current_window, config["ensure_correct_instance_retry"])
        unpause_after_switch()

    checker_thread.join()

def is_complete_checker(instances: list[MinecraftInstance]):
    while True:
        if all([inst.is_completed for inst in instances]):
            break
        for inst in instances:
            if not inst.record_json or inst.record_json == "":
                inst.try_get_record_json_file()
            if not inst.record_json or inst.record_json == "":
                continue
            inst.try_get_is_completed()

def activate_window2(hwnd):
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
    win32gui.SetForegroundWindow(hwnd)


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


