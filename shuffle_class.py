import json
import random
import time
from json import JSONDecodeError

import keyboard
import psutil
import win32con
import win32gui
import win32process

from minecraft_instance import MinecraftInstance
from mcsr_shuffle import LOGGER


class MCSRShuffle:
    instances: list[MinecraftInstance]
    current_instance: MinecraftInstance
    config: dict
    is_init_ok: bool
    paused: bool
    exit_scheduled: bool

    def __init__(self):
        self.is_init_ok = True
        self.get_config_dict()
        self.get_mc_instances()
        self.paused = False
        self.exit_scheduled = False

    @staticmethod
    def get_minecraft_windows():
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

    def get_mc_instances(self):
        # get all open minecraft windows
        try:
            self.instances = self.get_minecraft_windows()
        except Exception as e:
            LOGGER.error(str(e))
            self.is_init_ok = False
            return
        LOGGER.info(f"Found {len(self.instances)} open Minecraft windows.")
        if len(self.instances) == 0:
            LOGGER.error("Found 0 open Minecraft instances, closing program...")
            self.is_init_ok = False
            return
        if not self.config["DEBUG"]:
            # if only one instance is open, the shuffle makes no sense
            if len(self.instances) < 2:
                LOGGER.error("Found only one Minecraft instance, closing program...")
                self.is_init_ok = False
                return

    def get_random_window(self):
        return random.choice(self.instances)

    def random_win_to_foreground(self) -> MinecraftInstance:
        chosen_instance = self.get_random_window()
        LOGGER.info(f"Setting window with HWND {chosen_instance.hwnd} to foreground...")
        self.activate_window(chosen_instance.hwnd)
        return chosen_instance

    def on_before_switch(self, sleep_time: float):
        # press esc until player is in world and unpaused in any way (pause menu, chat, inv)
        # and let pause on lost focus handle pausing
        while True:
            # pause on lost focus will take care of this
            if self.current_instance.is_in_state("inworld,unpaused"):
                break
            keyboard.release("ctrl")  # to avoid pressing ctrl+esc, which brings up win search bar
            keyboard.press_and_release("esc")
            time.sleep(sleep_time)
        return

    @staticmethod
    def unpause_after_switch():
        # happy path is that before this runs MC will be on the basic pause screen
        keyboard.release("shift")  # prevention of shift+tab
        keyboard.press_and_release("tab, enter")

    def set_up(self):
        # first create worlds using atum
        sleep_time = self.config["set_up_key_press_pause"]
        for inst in self.instances:
            if inst.is_in_state("title"):
                self.activate_window(inst.hwnd)
                time.sleep(sleep_time)
                keyboard.press_and_release("shift+tab")
                time.sleep(sleep_time)
                keyboard.press_and_release("enter")
        # then end this with waiting for every world to stop generating
        while not all([inst.is_in_state("inworld") for inst in self.instances]):
            time.sleep(0)  # this is basically thread.yield (apparently)
        LOGGER.info("Set up done!")

    def ensure_correct_window(self, sleep_time: float):
        while True:
            time.sleep(sleep_time)  # os can take a little bit for GetForegroundWindow() to return the real FG win hwnd
            if self.current_instance.hwnd == win32gui.GetForegroundWindow():
                break
            LOGGER.warning(f"Correcting foreground window to {self.current_instance.hwnd}...")
            self.activate_window(self.current_instance.hwnd)

    def check_config_dict(self) -> bool:
        if self.config.get("lower_bound", None) is None:
            return False
        if self.config.get("upper_bound", None) is None:
            return False
        if self.config.get("pause_hotkey", None) is None:
            return False
        if self.config.get("exit_hotkey", None) is None:
            return False
        if self.config.get("ensure_correct_instance_retry", None) is None:
            return False
        if self.config.get("before_switch_esc_press_pause", None) is None:
            return False
        if self.config.get("set_up_key_press_pause", None) is None:
            return False
        if self.config.get("DEBUG", None) is None:
            return False
        return True

    def get_config_dict(self):
        try:
            with open("config.json", "r") as cfg:
                self.config = json.load(cfg)
        except JSONDecodeError:
            LOGGER.error("Couldn't read config.json! Maybe it's empty?")
            self.is_init_ok = False
            return
        if not self.check_config_dict():
            LOGGER.error("config.json doesn't have all the necessary items!")
            self.is_init_ok = False
            return

    @staticmethod
    def activate_window(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
        win32gui.SetForegroundWindow(hwnd)

    def run(self):
        if not self.is_init_ok:
            return
        self.set_up()