import datetime
import logging
import re
import time

import psutil
import win32gui
import win32process

from minecraft_instance import MinecraftInstance
from config_class import Config

def get_log_name() -> str:
    return f"{datetime.datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}"

logging.basicConfig(filename=f"logs/{get_log_name()}.log",
                    format='%(asctime)s %(levelname)s: %(message)s',
                    filemode='w')

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

class MCSRShuffle:
    minecraft_instances: list[MinecraftInstance]
    config: Config

    paused: bool
    paused_time: float
    exit_scheduled: bool

    def __init__(self):
        self.minecraft_instances = []
        self.paused = False
        self.paused_time = 0.0
        self.exit_scheduled = False
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
        ret_str = f"Found {len(self.minecraft_instances)} open Minecraft window{'s' if len(self.minecraft_instances) != 1 else ''}."
        LOGGER.info(f"Found {len(self.minecraft_instances)} open Minecraft window{'s' if len(self.minecraft_instances) != 1 else ''}.")
        if self.config.DEBUG:
            print(ret_str)
        return ret_str

    def can_play(self) -> bool:
        return len(self.minecraft_instances) > 1

    def exit(self):
        self.exit_scheduled = True

    def pause(self):
        self.paused = True
        self.paused_time = time.time()

