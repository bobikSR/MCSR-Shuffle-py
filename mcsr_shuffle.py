import threading

import pydirectinput
import win32gui, win32con, win32api
import win32process
import random
import time
import logging
import datetime
import keyboard
from threading import Condition, Timer

from utils import *
import psutil

from minecraft_instance import MinecraftInstance

# nopeaceful pre 1.14 https://github.com/contariaa/NoPeaceful-Pre1.14
# nopeaceful https://github.com/VoidXWalker/NoPeaceful/releases

def get_log_name() -> str:
    return f"{datetime.datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}"

logging.basicConfig(filename=f"logs/{get_log_name()}.log",
                    format='%(asctime)s %(levelname)s: %(message)s',
                    filemode='w')

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

paused: bool = False
exit_scheduled: bool = False

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
    # and let pause on lost focus handle pausing
    while True:
        # pause on lost focus will take care of this
        if instance.is_in_state("inworld,unpaused"):
            break
        keyboard.release("ctrl") # to avoid pressing ctrl+esc, which brings up win search bar
        keyboard.press_and_release("esc")
        time.sleep(sleep_time)
    return

# if i force unpaused -> pause on lost focus will pause -> then i can just tab -> enter to unpause

def unpause_after_switch():
    # happy path is that before this runs MC will be on the basic pause screen
    keyboard.release("shift") # prevention of shift+tab
    keyboard.press_and_release("tab, enter")

def set_up(instances: list[MinecraftInstance], sleep_time: float):
    # first create worlds using atum
    for inst in instances:
        if inst.is_in_state("title"):
            activate_window2(inst.hwnd)
            time.sleep(sleep_time)
            keyboard.press_and_release("shift+tab")
            time.sleep(sleep_time)
            keyboard.press_and_release("enter")
    # then end this with waiting for every world to stop generating
    while not all([inst.is_in_state("inworld") for inst in instances]):
        time.sleep(0) # this is basically thread.yield (apparently)
    LOGGER.info("Set up done!")

def ensure_correct_window(instance: MinecraftInstance, sleep_time: float):
    while True:
        time.sleep(sleep_time) # os can take a little bit for GetForegroundWindow() to return the real FG win hwnd
        if instance.hwnd == win32gui.GetForegroundWindow():
            break
        LOGGER.warning(f"Correcting foreground window to {instance.hwnd}...")
        activate_window2(instance.hwnd)

def check_config_dict(cfg: dict) -> bool:
    if cfg.get("lower_bound", None) is None:
        return False
    if cfg.get("upper_bound", None) is None:
        return False
    if cfg.get("pause_hotkey", None) is None:
        return False
    if cfg.get("exit_hotkey", None) is None:
        return False
    if cfg.get("ensure_correct_instance_retry", None) is None:
        return False
    if cfg.get("before_switch_esc_press_pause", None) is None:
        return False
    if cfg.get("set_up_key_press_pause", None) is None:
        return False
    if cfg.get("DEBUG", None) is None:
        return False
    return True

def pause_shuffle(switch_timer: Timer):
    global paused, exit_scheduled
    if exit_scheduled:
        return
    LOGGER.info("Pausing...")
    paused = True
    switch_timer.cancel()

def exit_shuffle(switch_timer: Timer):
    global exit_scheduled, paused
    LOGGER.info("Exiting...")
    exit_scheduled = True
    paused = False
    switch_timer.cancel()

def run():
    # set up global vars
    global paused, exit_scheduled

    # load config file into dict
    config: dict
    try:
        with open("config.json", "r") as cfg:
            config = json.load(cfg)
    except JSONDecodeError:
        LOGGER.error("Couldn't read config.json! Maybe it's empty?")
        return
    if not check_config_dict(config):
        LOGGER.error("config.json doesn't have all the necessary items!")
        return

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

    switch_timer: Timer = Timer(0, lambda: None)

    # start thread that will check if runs on open instances were completed
    checker_thread = threading.Thread(target=is_complete_checker, args=(original_windows, switch_timer,))
    checker_thread.start()

    # set up pause and exist hotkeys
    keyboard.add_hotkey(config["pause_hotkey"], lambda: pause_shuffle(switch_timer))
    keyboard.add_hotkey(config["exit_hotkey"], lambda: exit_shuffle(switch_timer))

    # start switching loop
    while True:
        while paused: # yield thread if paused
            time.sleep(0)
        if exit_scheduled:
            break
        # sleep for a random amount of time
        sleep_time: int = random.randint(config["lower_bound"], config["upper_bound"])
        LOGGER.info(f"Sleeping for {sleep_time} seconds...")
        switch_timer = Timer(sleep_time, lambda: None) # this is used as cancellable sleep
        switch_timer.join()
        while paused: # yield thread if paused
            time.sleep(0)
        if exit_scheduled:
            break
        # choose a window from possible ones and switch to it
        possible_windows = [inst for inst in original_windows if inst.hwnd != current_window.hwnd and not inst.is_completed]
        if len(possible_windows) < 1:
            break
        on_before_switch(current_window, config["before_switch_esc_press_pause"])
        current_window = random_win_to_foreground(possible_windows)
        ensure_correct_window(current_window, config["ensure_correct_instance_retry"])
        unpause_after_switch()

    checker_thread.join()
    switch_timer.join()

def switch_loop(instances: list[MinecraftInstance], config: dict):
    pass

def is_complete_checker(instances: list[MinecraftInstance], switch_timer: Timer):
    global paused, exit_scheduled
    completions: int = 0
    while True:
        while paused:
            time.sleep(0)
        if exit_scheduled:
            break
        if all([inst.is_completed for inst in instances]):
            break
        for inst in instances:
            if not inst.record_json or inst.record_json == "":
                inst.try_get_record_json_file()
            if not inst.record_json or inst.record_json == "":
                continue
            inst.try_get_is_completed()
            if inst.just_completed:
                completions += 1
                keyboard.press_and_release("esc")
                switch_timer.cancel()
                LOGGER.info(f"Completed run {completions} on instance with HWND {inst.hwnd}")

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


def cancel_timer(timer: Timer):
    time.sleep(3)
    timer.cancel()

if __name__ == "__main__":
    #run()
    t = Timer(10, lambda: print("timer finished!"))
    t1 = threading.Thread(target=cancel_timer, args=(t,))
    t.start()
    print("timer has to finish in order for code under it to run")
    #t1.start()
    #print("ahoj")
    t.join()


