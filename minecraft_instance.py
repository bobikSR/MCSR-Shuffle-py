from enums import *
from utils import *
import os, json

class MinecraftInstance:
    hwnd: int
    pid: int
    version: str
    folder_path: str
    launcher: Launcher

    def __init__(self, hwnd: int, pid: int, cmd_line: str):
        self.hwnd = hwnd
        self.pid = pid
        self.get_instance_info_from_cmd_line(cmd_line)

    def __str__(self):
        return (f"Minecraft instance with HWND {self.hwnd}, PID {self.pid}, "
                f"MC version {self.version}, folder path {self.folder_path}. Launched from {self.launcher.value}.")

    def get_instance_info_from_cmd_line2(self, cmd_line: list[str]):
        # todo: do it here with the list the psutil method gives, it may even be easier
        path_args = list(filter(starts_with_folder_path_helper, cmd_line))
        if "--gameDir" in cmd_line:
            # either vanilla or color mc (folder path is the same)
            idx = cmd_line.index("--gameDir")
            try:
                self.folder_path = cmd_line[idx + 1]
                if not os.path.isdir(self.folder_path):
                    raise Exception("Found .minecraft folder, but its not a directory!")
            except (IndexError, Exception) as e:
                raise Exception(f"Error occurred while trying to parse .minecraft folder! {str(e)}")
            if (len(path_args)) > 0:
                # color mc
                self.launcher = Launcher.COLORMC
                try:
                    with open(os.path.join(os.path.dirname(self.folder_path), "game.json")) as f:
                        data = json.load(f)
                        self.version = data.get("Version", None)
                        if not self.version:
                            self.version = "1.16.1"
                except Exception:
                    self.version = "1.16.1"
                # got everything for color mc, can leave
                return
            # vanilla
            self.launcher = Launcher.VANILLA

        # todo

        if len(path_args) != 1:
            raise Exception("Error occurred while trying to parse .minecraft folder! Ambiguous arguments!")
        try:
            natives_folder: str = path_args[0][19:]
            print("NATIVES FOLDER: ", natives_folder)
            if not os.path.isdir(natives_folder):
                raise Exception("Natives folder is not a directory!")
            if not os.path.isdir(os.path.join(os.path.dirname(natives_folder), ".minecraft")):
                raise Exception("Couldn't find .minecraft folder as a sibling folder to the natives folder!")
            self.folder_path = os.path.join(os.path.dirname(natives_folder), ".minecraft")
        except (IndexError, Exception) as e:
            raise Exception(f"Error occurred while trying to parse .minecraft folder! {str(e)}")
        # todo: rest (versions

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

