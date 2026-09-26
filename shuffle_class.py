import datetime
import logging
import random
import re
import threading
import time
from threading import Event

import keyboard
import psutil
import win32con
import win32gui
import win32process
from PyQt6.QtCore import QObject, pyqtSignal

from minecraft_instance import MinecraftInstance
from config_class import Config

def get_log_name() -> str:
    return f"{datetime.datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}"

logging.basicConfig(filename=f"logs/{get_log_name()}.log",
                    format='%(asctime)s %(levelname)s: %(message)s',
                    filemode='w')

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

class MCSRShuffle(QObject):
    minecraft_instances: list[MinecraftInstance]
    current_instance: MinecraftInstance
    config: Config
    completions: int

    paused: bool
    paused_time: float
    exit_scheduled: bool

    switch_timer: Event

    finished_signal = pyqtSignal()
    pause_signal = pyqtSignal()
    completion_signal = pyqtSignal()
    detect_error_signal = pyqtSignal()
    finished_error_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.minecraft_instances = []
        self.paused = False
        self.paused_time = 0.0
        self.exit_scheduled = False
        self.switch_timer = Event()
        self.completions = 0
        return

    def get_minecraft_instances(self) -> str:
        try:
            # get the windows
            def callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd) != 0 and re.match("^Minecraft\\*? .+$", win32gui.GetWindowText(hwnd)):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    proc = psutil.Process(pid)
                    cmd_line: list[str] = proc.cmdline()
                    found_instance = MinecraftInstance(hwnd, pid, cmd_line)
                    LOGGER.info(f"Found {str(found_instance)}")
                    self.minecraft_instances.append(found_instance)
            win32gui.EnumWindows(callback, None)
            # filter instances out
            for inst in self.minecraft_instances:
                if inst.is_in_state("inworld"):
                    inst.try_get_record_json_file()
                    inst.try_get_is_completed()
            self.minecraft_instances = list(filter(lambda instance: not instance.is_completed, self.minecraft_instances))
        except Exception as e:
            LOGGER.error(str(e))
            self.reset_values()
            return ""
        ret_str = f"Found {len(self.minecraft_instances)} open Minecraft window{'s' if len(self.minecraft_instances) != 1 else ''}."
        LOGGER.info(ret_str)
        if self.config.DEBUG:
            print(ret_str)
        return ret_str

    def can_play(self) -> bool:
        return len(self.minecraft_instances) > 1

    def exit_shuffle(self):
        LOGGER.info("Exiting...")
        print("Exiting...")
        self.exit_scheduled = True
        self.paused = False
        self.switch_timer.set()

    def pause_shuffle(self):
        if self.exit_scheduled:
            return
        self.paused = not self.paused
        LOGGER.info(f"{'Unp' if not self.paused else 'P'}ausing...")
        print(f"{'Unp' if not self.paused else 'P'}ausing...")
        if self.paused:
            self.paused_time = time.time()
            self.switch_timer.set()
        self.pause_signal.emit()

    @staticmethod
    def get_random_instance(instances: list[MinecraftInstance]):
        return random.choice(instances)

    def random_win_to_foreground(self, instances: list[MinecraftInstance]) -> MinecraftInstance:
        chosen_instance = self.get_random_instance(instances)
        LOGGER.info(f"Setting window with HWND {chosen_instance.hwnd} to foreground...")
        self.activate_window(chosen_instance.hwnd)
        return chosen_instance

    @staticmethod
    def activate_window(hwnd):
        keyboard.press(
            "alt")  # idk why https://stackoverflow.com/questions/63648053/pywintypes-error-0-setforegroundwindow-no-error-message-is-available
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
        win32gui.SetForegroundWindow(hwnd)
        keyboard.release("alt")

    @staticmethod
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

    def get_final_times(self) -> str:
        final_rta_ms = max([inst.final_rta_ms if inst.final_rta_ms is not None else 0 for inst in self.minecraft_instances])
        return self.get_time_str_from_ms(final_rta_ms)

    def check_config(self) -> bool:
        if self.config.lower_bound <= 0.0:
            return False
        if self.config.upper_bound <= 0.0:
            return False
        if self.config.lower_bound >= self.config.upper_bound:
            return False
        if self.config.pause_hotkey == "":
            return False
        if self.config.exit_hotkey == "":
            return False
        if self.config.ensure_correct_instance_retry <= 0.0:
            return False
        if self.config.before_switch_esc_press_pause <= 0.0:
            return False
        if self.config.set_up_key_press_pause <= 0.0:
            return False
        return True

    def on_before_switch(self):
        # press esc until player is in world and unpaused in any way (pause menu, chat, inv)
        # and let pause on lost focus handle pausing
        while True:
            # pause on lost focus will take care of this
            if self.current_instance.is_in_state("inworld,unpaused"):
                break
            keyboard.release("ctrl")  # to avoid pressing ctrl+esc, which brings up win search bar
            keyboard.press_and_release("esc")
            time.sleep(self.config.before_switch_esc_press_pause)
        return

    @staticmethod
    def unpause_after_switch():
        # happy path is that before this runs MC will be on the basic pause screen
        keyboard.release("shift")  # prevention of shift+tab
        keyboard.press_and_release("tab, enter")

    def ensure_correct_window(self):
        while True:
            time.sleep(self.config.ensure_correct_instance_retry)  # os can take a little bit for GetForegroundWindow() to return the real FG win hwnd
            if self.current_instance.hwnd == win32gui.GetForegroundWindow():
                break
            LOGGER.warning(f"Correcting foreground window to {self.current_instance.hwnd}...")
            self.activate_window(self.current_instance.hwnd)

    def set_up(self):
        # first create worlds using atum
        for inst in self.minecraft_instances:
            self.activate_window(inst.hwnd)
            if inst.is_in_state("title"):
                time.sleep(self.config.set_up_key_press_pause)
                keyboard.press_and_release("shift+tab")
                time.sleep(self.config.set_up_key_press_pause)
                keyboard.press_and_release("enter")
                if not self.config.parallel_world_gen:  # if parallel is false, wait for each world to be generated before generating the next one
                    while not inst.is_in_state("inworld"):
                        time.sleep(0)
        # then end this with waiting for every world to stop generating
        if self.config.parallel_world_gen:
            while not all([inst.is_in_state("inworld") for inst in self.minecraft_instances]):
                time.sleep(0)  # this is basically thread.yield (apparently)
        LOGGER.info("Set up done!")

    def is_complete_checker(self):
        while True:
            while self.paused:
                time.sleep(0)
            if self.exit_scheduled:
                break
            if all(inst.is_completed for inst in self.minecraft_instances):
                break
            for inst in self.minecraft_instances:
                if not inst.record_json or inst.record_json == "":
                    inst.try_get_record_json_file()
                if not inst.record_json or inst.record_json == "":
                    continue
                inst.try_get_is_completed()
                if inst.just_completed:
                    self.completions += 1
                    keyboard.press_and_release("esc")
                    time.sleep(0.05)
                    self.switch_timer.set()
                    LOGGER.info(f"Completed run {self.completions} on instance with HWND {inst.hwnd}")
                    if self.config.DEBUG:
                        print(f"Completed run {self.completions} on instance with HWND {inst.hwnd}")
                    self.completion_signal.emit()

    def reset_values(self):
        self.completions = 0
        self.paused_time = 0.0
        self.paused = False
        self.exit_scheduled = False
        self.minecraft_instances = []
        
    def complete(self):
        self.finished_signal.emit()

    def complete_with_error(self):
        self.reset_values()
        self.finished_error_signal.emit()

    def run(self):
        if self.config is None or not self.check_config():
            LOGGER.error("Values in config.json aren't correct!")
            self.complete_with_error()
            return

        if len(self.minecraft_instances) == 0:
            LOGGER.error("Found 0 open Minecraft instances, shuffle will not run...")
            if self.config.DEBUG:
                print("Found 0 open Minecraft instances, shuffle will not run...")
            self.complete_with_error()
            return
        if not self.config.DEBUG:
            # if only one instance is open, the shuffle makes no sense
            if len(self.minecraft_instances) < 2:
                LOGGER.error("Found only one Minecraft instance, shuffle will not run")
                self.complete_with_error()
                return

        # set up by creating worlds using atum
        try:
            self.set_up()
        except Exception as e:
            LOGGER.error(str(e))
            self.complete_with_error()

        # set up ends on the last instance
        self.current_instance: MinecraftInstance = self.minecraft_instances[-1]
        if self.current_instance.is_in_state("inworld,paused"):
            self.on_before_switch()

        # start thread that will check if runs on open instances were completed
        checker_thread = threading.Thread(target=self.is_complete_checker)
        checker_thread.start()

        # set up pause and exist hotkeys
        keyboard.add_hotkey(self.config.pause_hotkey, self.pause_shuffle)
        keyboard.add_hotkey(self.config.exit_hotkey, self.exit_shuffle)

        sleep_time: int
        sleep_start_time: float
        remaining_sleep_after_pause: float = 0.0
        try:
            while True:
                while self.paused:  # yield thread if paused
                    time.sleep(0)
                if self.exit_scheduled:
                    break
                # sleep for a random amount of time
                sleep_time = random.randint(self.config.lower_bound, self.config.upper_bound)
                if remaining_sleep_after_pause > 0.0:
                    sleep_time = int(remaining_sleep_after_pause)
                    remaining_sleep_after_pause = 0.0
                if self.config.DEBUG:
                    LOGGER.info(f"Sleeping for {sleep_time} seconds...")
                sleep_start_time = time.time()
                self.switch_timer.clear()  # this is used as cancellable sleep
                self.switch_timer.wait(sleep_time)
                while self.paused:  # yield thread if paused
                    time.sleep(0)
                if self.paused_time > 0.0:
                    time_slept = self.paused_time - sleep_start_time
                    remaining_sleep_after_pause = sleep_time - time_slept
                    self.paused_time = 0.0
                    if remaining_sleep_after_pause > 0.0:
                        continue
                if self.exit_scheduled:
                    break
                # choose a window from possible ones and switch to it
                possible_windows = [inst for inst in self.minecraft_instances if
                                    inst.hwnd != self.current_instance.hwnd and not inst.is_completed]
                if len(possible_windows) < 1:
                    break
                self.on_before_switch()
                self.current_instance = self.random_win_to_foreground(possible_windows)
                self.ensure_correct_window()
                self.unpause_after_switch()

        except Exception as e:
            LOGGER.error(str(e))
            self.exit_scheduled = True
            checker_thread.join()
            self.complete_with_error()

        checker_thread.join()
        if all(inst.is_completed for inst in self.minecraft_instances):
            final_rta = self.get_final_times()
            LOGGER.info(f"Completed MCSR Shuffle with final RTA of {final_rta}")
            if self.config.DEBUG:
                print(f"Completed MCSR Shuffle with final RTA of {final_rta}")

        self.complete()

