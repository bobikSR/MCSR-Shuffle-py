from minecraft_instance import *

def starts_with_folder_path_helper(s: str):
    return s.startswith("-Djava.library.path=")

def is_in_state(instance: MinecraftInstance, state: str) -> bool:
    with open(os.path.join(instance.folder_path, "wpstateout.txt"), "r") as state_output:
        lines = list(state_output.readlines())
    if len(lines) != 1:
        return False
    if lines[0].startswith(state):
        return True
    return False