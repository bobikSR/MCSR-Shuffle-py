import json
import re
import threading
from json import JSONDecodeError

import win32gui, win32con, win32api
import win32process
import random
import time
import logging
import datetime
import keyboard
from threading import Condition, Timer
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
paused_time: float = 0.0
exit_scheduled: bool = False
config: dict


def get_minecraft_windows() -> list[MinecraftInstance]:
    ret_list: list[MinecraftInstance] = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) != 0 and re.match("^Minecraft\\*? .+$", win32gui.GetWindowText(hwnd)):
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

def on_before_switch(instance: MinecraftInstance):
    global config
    # press esc until player is in world and unpaused in any way (pause menu, chat, inv)
    # and let pause on lost focus handle pausing
    while True:
        # pause on lost focus will take care of this
        if instance.is_in_state("inworld,unpaused"):
            break
        keyboard.release("ctrl") # to avoid pressing ctrl+esc, which brings up win search bar
        keyboard.press_and_release("esc")
        time.sleep(config["before_switch_esc_press_pause"])
    return

# if i force unpaused -> pause on lost focus will pause -> then i can just tab -> enter to unpause

def unpause_after_switch():
    # happy path is that before this runs MC will be on the basic pause screen
    keyboard.release("shift") # prevention of shift+tab
    keyboard.press_and_release("tab, enter")

def set_up(instances: list[MinecraftInstance]):
    global config
    # first create worlds using atum
    for inst in instances:
        activate_window2(inst.hwnd)
        if inst.is_in_state("title"):
            time.sleep(config["set_up_key_press_pause"])
            keyboard.press_and_release("shift+tab")
            time.sleep(config["set_up_key_press_pause"])
            keyboard.press_and_release("enter")
            if not config["parallel_world_gen"]: # if parallel is false, wait for each world to be generated before generating the next one
                while not inst.is_in_state("inworld"):
                    time.sleep(0)
    # then end this with waiting for every world to stop generating
    if config["parallel_world_gen"]:
        while not all([inst.is_in_state("inworld") for inst in instances]):
            time.sleep(0) # this is basically thread.yield (apparently)
    LOGGER.info("Set up done!")
    print("Set up done!")

def ensure_correct_window(instance: MinecraftInstance, sleep_time: float):
    while True:
        time.sleep(sleep_time) # os can take a little bit for GetForegroundWindow() to return the real FG win hwnd
        if instance.hwnd == win32gui.GetForegroundWindow():
            break
        LOGGER.warning(f"Correcting foreground window to {instance.hwnd}...")
        activate_window2(instance.hwnd)

def check_config_dict() -> bool:
    global config
    if config.get("lower_bound", None) is None:
        return False
    if config.get("upper_bound", None) is None:
        return False
    if config["lower_bound"] >= config["upper_bound"]:
        return False
    if config.get("pause_hotkey", None) is None:
        return False
    if config.get("exit_hotkey", None) is None:
        return False
    if config.get("ensure_correct_instance_retry", None) is None:
        return False
    if config.get("before_switch_esc_press_pause", None) is None:
        return False
    if config.get("set_up_key_press_pause", None) is None:
        return False
    if config.get("DEBUG", None) is None:
        return False
    return True

def pause_shuffle(switch_timer: Timer):
    global paused, exit_scheduled, paused_time
    if exit_scheduled:
        return
    paused = not paused
    LOGGER.info(f"{'Unp' if not paused else 'P'}ausing...")
    print(f"{'Unp' if not paused else 'P'}ausing...")
    if paused:
        paused_time = time.time()
        switch_timer.cancel()

def exit_shuffle(switch_timer: Timer):
    global exit_scheduled, paused
    LOGGER.info("Exiting...")
    print("Exiting...")
    exit_scheduled = True
    paused = False
    switch_timer.cancel()

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

def get_final_times(instances: list[MinecraftInstance]) -> tuple[str, str]:
    final_rta_ms = max([inst.final_rta_ms if inst.final_rta_ms is not None else 0 for inst in instances])
    final_igt_ms = sum([inst.final_rta_ms if inst.final_igt_ms is not None else 0 for inst in instances])
    return get_time_str_from_ms(final_rta_ms), get_time_str_from_ms(final_igt_ms)

def run():
    # set up global vars
    global paused, exit_scheduled, paused_time, config

    # load config file into dict
    try:
        with open("config.json", "r") as cfg:
            config = json.load(cfg)
    except JSONDecodeError:
        LOGGER.error("Couldn't read config.json! Maybe it's empty?")
        return
    if not check_config_dict():
        LOGGER.error("config.json doesn't have all the necessary items!")
        return

    # get all open minecraft windows
    original_windows: list[MinecraftInstance] = []
    try:
        original_windows = get_minecraft_windows()
        for window in original_windows:
            if window.is_in_state("inworld"):
                window.try_get_record_json_file()
                window.try_get_is_completed()
        original_windows = list(filter(lambda inst: not inst.is_completed, original_windows))
    except Exception as e:
        LOGGER.error(str(e))
    LOGGER.info(f"Found {len(original_windows)} open Minecraft window{'s' if len(original_windows) != 1 else ''}.")
    print(f"Found {len(original_windows)} open Minecraft window{'s' if len(original_windows) != 1 else ''}.")
    if len(original_windows) == 0:
        LOGGER.error("Found 0 open Minecraft instances, closing program...")
        print("Found 0 open Minecraft instances, closing program...")
        return
    if not config["DEBUG"]:
        # if only one instance is open, the shuffle makes no sense
        if len(original_windows) < 2:
            LOGGER.error("Found only one Minecraft instance, closing program...")
            print("Found only one Minecraft instance, closing program...")
            return

    # set up by creating worlds using atum
    set_up(original_windows)

    # set up ends on the last instance
    current_window: MinecraftInstance = original_windows[-1]
    if current_window.is_in_state("inworld,paused"):
        on_before_switch(current_window)

    switch_timer: Timer = Timer(0, lambda: None) # assign dummy value so IDE stops crying

    # start thread that will check if runs on open instances were completed
    checker_thread = threading.Thread(target=is_complete_checker, args=(original_windows, switch_timer,))
    checker_thread.start()

    # set up pause and exist hotkeys
    keyboard.add_hotkey(config["pause_hotkey"], lambda: pause_shuffle(switch_timer))
    keyboard.add_hotkey(config["exit_hotkey"], lambda: exit_shuffle(switch_timer))

    # start switching loop
    sleep_time: int
    sleep_start_time: float
    remaining_sleep_after_pause: float= 0.0
    while True:
        while paused: # yield thread if paused
            time.sleep(0)
        if exit_scheduled:
            break
        # sleep for a random amount of time
        sleep_time = random.randint(config["lower_bound"], config["upper_bound"])
        if remaining_sleep_after_pause > 0.0:
            sleep_time = int(remaining_sleep_after_pause)
            remaining_sleep_after_pause = 0.0
            print(f"Sleeping for {sleep_time} after pause...")
        LOGGER.info(f"Sleeping for {sleep_time} seconds...")
        sleep_start_time = time.time()
        switch_timer = Timer(sleep_time, lambda: None) # this is used as cancellable sleep
        switch_timer.start()
        switch_timer.join()
        while paused: # yield thread if paused
            time.sleep(0)
        if paused_time > 0.0:
            time_slept = paused_time - sleep_start_time
            remaining_sleep_after_pause = sleep_time - time_slept
            paused_time = 0.0
            if remaining_sleep_after_pause > 0.0:
                continue
        if exit_scheduled:
            break
        # choose a window from possible ones and switch to it
        possible_windows = [inst for inst in original_windows if inst.hwnd != current_window.hwnd and not inst.is_completed]
        if len(possible_windows) < 1:
            break
        on_before_switch(current_window)
        current_window = random_win_to_foreground(possible_windows)
        ensure_correct_window(current_window, config["ensure_correct_instance_retry"])
        unpause_after_switch()

    checker_thread.join()
    switch_timer.join()

    if all([inst.is_completed for inst in original_windows]):
        final_rta, total_igt = get_final_times(original_windows)
        LOGGER.info(f"Completed MCSR Shuffle with total IGT of {total_igt} and final RTA of {final_rta}")
        print(f"Completed MCSR Shuffle with total IGT of {total_igt} and final RTA of {final_rta}")

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
                print(f"Completed run {completions} on instance with HWND {inst.hwnd}")

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

