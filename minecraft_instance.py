from json import JSONDecodeError

from enums import *
import os, json

def starts_with_folder_path_helper(s: str):
    return s.startswith("-Djava.library.path=")

class MinecraftInstance:
    hwnd: int
    pid: int
    version: str
    folder_path: str
    record_json: str
    launcher: Launcher
    is_completed: bool
    just_completed: bool
    final_igt_ms: int | None
    final_rta_ms: int | None

    def __init__(self, hwnd: int, pid: int, cmd_line: list[str]):
        self.hwnd = hwnd
        self.pid = pid
        self.get_instance_info_from_cmd_line2(cmd_line)
        self.folder_path.replace("/", "\\")
        self.is_completed = False
        self.just_completed = False
        self.record_json = ""
        self.final_igt_ms = None
        self.final_rta_ms = None

    def __str__(self):
        return (f"Minecraft instance with HWND {self.hwnd}, PID {self.pid}, "
                f"MC version {self.version}, folder path {self.folder_path}. Launched from {self.launcher.value}.")

    def get_instance_info_from_cmd_line2(self, cmd_line: list[str]):
        path_args = list(filter(starts_with_folder_path_helper, cmd_line))
        if "--gameDir" in cmd_line:
            # either vanilla or color mc (folder path is the same)
            try:
                idx = cmd_line.index("--gameDir")
                self.folder_path = cmd_line[idx + 1]
                if not os.path.isdir(self.folder_path):
                    raise Exception("Found .minecraft folder, but its not a directory!")
            except (IndexError, ValueError, Exception) as e:
                raise Exception(f"Error occurred while trying to parse .minecraft folder! {str(e)}")

            if os.path.isfile(os.path.join(os.path.dirname(self.folder_path), "game.json")):
                try:
                    # color mc
                    with open(os.path.join(os.path.dirname(self.folder_path), "game.json")) as f:
                        data = json.load(f)
                        self.version = data.get("Version", None)
                        if not self.version:
                            self.version = "1.16.1"
                except Exception:
                    self.version = "1.16.1"
                    # got everything for color mc, can leave
                self.launcher = Launcher.COLORMC
                return
            # vanilla
            self.launcher = Launcher.VANILLA
            try:
                idx = cmd_line.index("--version")
                version_str = cmd_line[idx + 1]
                res = VersionPattern.VANILLA.value.search(version_str)
                if res:
                    self.version = res.group(3)
                    return
                self.version = "1.16.1"
                return
            except (ValueError, IndexError) as e:
                self.version = "1.16.1"
            return

        # multimc
        self.launcher = Launcher.MULTIMC
        if len(path_args) != 1:
            print(path_args)
            raise Exception("Error occurred while trying to parse .minecraft folder! Ambiguous arguments!")
        try:
            natives_folder: str = path_args[0][20:]
            if not os.path.isdir(natives_folder):
                raise Exception("Natives folder is not a directory!")
            if not os.path.isdir(os.path.join(os.path.dirname(natives_folder), ".minecraft")):
                raise Exception("Couldn't find .minecraft folder as a sibling folder to the natives folder!")
            self.folder_path = os.path.join(os.path.dirname(natives_folder), ".minecraft")
        except (IndexError, Exception) as e:
            raise Exception(f"Error occurred while trying to parse .minecraft folder! {str(e)}")
        try:
            idx = cmd_line.index("-cp")
            cp_arg = cmd_line[idx + 1]
            res = VersionPattern.MULTIMC.value.search(cp_arg)
            if res:
                self.version = res.group(1)
                return
            res = VersionPattern.MULTIMC_2.value.search(cp_arg)
            if res:
                self.version = res.group(1)
                return
        except (ValueError, IndexError, Exception):
            self.version = "1.16.1"
        self.version = "1.16.1"
        return

    def is_in_state(self, state: str):
        with open(os.path.join(self.folder_path, "wpstateout.txt"), "r") as state_output:
            lines = list(state_output.readlines())
        if len(lines) != 1:
            return False
        if lines[0].startswith(state):
            return True
        return False

    def try_get_record_json_file(self):
        if not os.path.isdir(os.path.join(self.folder_path, "saves")):
            return
        saves_folder = os.path.join(self.folder_path, "saves")
        saves = list(sorted([os.path.join(saves_folder, world) for world in os.listdir(saves_folder)], key=os.path.getmtime, reverse=True))
        try:
            world_folder = saves[0]
        except IndexError:
            return
        if not os.path.isfile(os.path.join(world_folder, "speedrunigt", "record.json")):
            return
        self.record_json = os.path.join(world_folder, "speedrunigt", "record.json")

    def try_get_is_completed(self):
        if self.just_completed:
            self.just_completed = False
        if not self.record_json:
            return False
        if not self.is_completed:
            try:
                with open(self.record_json, "r") as record:
                    data = json.load(record)
                    self.is_completed = data.get("is_completed", False)
                    if self.is_completed:
                        self.just_completed = True
                        self.final_igt_ms = data.get("final_igt", None)
                        self.final_rta_ms = data.get("final_rta", None)
            except JSONDecodeError:
                # this means the json file is empty (nothing happened in the world yet)
                return False
        return self.is_completed

    def get_instance_info_from_cmd_line(self, cmd_line: str):
        if "--gameDir" in cmd_line:
            # either vanilla or color mc (folder path is the same)
            if "--gameDir \"" in cmd_line:
                res = PathPattern.VANILLA_SPACES.value.search(cmd_line)
                if res:
                    self.folder_path = str(res.group())
            res = PathPattern.VANILLA.value.search(cmd_line)
            if res:
                self.folder_path = str(res.group())
            # check that folder path was set and is valid if so
            if self.folder_path is None or self.folder_path.strip() == "":
                # todo: log or raise
                raise Exception("Folder path not found in command line!")
            if not os.path.isdir(self.folder_path):
                # todo: log or raise
                raise Exception("Folder path is not a directory!")
            if "-Djava.library.path=" in cmd_line:
                # color mc
                self.launcher = Launcher.COLORMC
                with open(os.path.join(os.path.dirname(self.folder_path), "game.json")) as f:
                    data = json.load(f)
                    self.version = data.get("Version", None)
                if not self.version:
                    self.version = "1.16.1"
                    # already have everything for color mc, can leave
                return
            # vanilla
            self.launcher = Launcher.VANILLA
            res = VersionPattern.VANILLA.value.search(cmd_line)
            if res:
                self.version = str(res.group())
            if not self.version:
                self.version = "1.16.1"
            # already have everything for vanilla, can leave
            return
        # multi mc (or prism)
        elif "-Djava.library.path=" in cmd_line:
            self.launcher = Launcher.MULTIMC
            natives_folder: str = ""
            if "\"-Djava.library.path=" in cmd_line:
                res = PathPattern.MULTIMC_SPACES.value.search(cmd_line)
                if res:
                    natives_folder = res.group()
                if natives_folder is None or natives_folder.strip() == "":
                    # todo: log or raise
                    raise Exception("Natives folder not found!")
                    return
            res = PathPattern.MULTIMC.value.search(cmd_line)
            if res:
                natives_folder = res.group(1)
            # check that found natives folder is a directory and has a .minecraft sibling directory
            if natives_folder is None or natives_folder.strip() == "":
                # todo: log or raise
                raise Exception("Natives folder not found!")
                return
            if not os.path.isdir(natives_folder):
                print(natives_folder)
                raise Exception("Natives folder is not a directory!")
                # todo: log or raise
                return
            if not os.path.isdir(os.path.join(os.path.dirname(natives_folder), ".minecraft")):
                # todo: log or raise
                raise Exception("Natives folder has no sibling .minecraft folder!")
                return
            self.folder_path = os.path.join(os.path.dirname(natives_folder), ".minecraft")
            res = VersionPattern.MULTIMC.value.search(cmd_line)
            if not res:
                res = VersionPattern.MULTIMC_2.value.search(cmd_line)
                if res:
                    self.version = res.group()
                    # already have everything for multimc, can leave
                    return
            else:
                self.version = res.group()
            if not self.version:
                self.version = "1.16.1"
            # already have everything for multimc, can leave
            return

