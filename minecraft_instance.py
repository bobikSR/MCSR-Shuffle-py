

class MinecraftInstance:
    hwnd: int
    pid: int
    version: str
    folder_path: str

    def __init__(self, hwnd: int, pid: int, cmd_line: list[str]):
        self.hwnd = hwnd
        self.pid = pid
        self.get_instance_info_from_cmd_line(cmd_line)

    def __str__(self):
        return f"Minecraft instance with HWND {self.hwnd}, PID {self.pid}, MC version {self.version}, folder path {self.folder_path}"

    def get_instance_info_from_cmd_line(self, cmd_line: list[str]):
        pass

