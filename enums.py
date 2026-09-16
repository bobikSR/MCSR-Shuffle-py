from enum import Enum
import re


class VersionPattern(Enum):
    VANILLA = re.compile("(fabric-loader-\\d\\.\\d+(\\.\\d+)?-)?(.+)")
    MULTIMC = re.compile(r"minecraft-(.+)-client.jar")
    MULTIMC_2 = re.compile(r"intermediary/(.+)/intermediary")

class PathPattern(Enum):
    VANILLA = re.compile(r"--gameDir (.+?) ")
    VANILLA_SPACES = re.compile(r"--gameDir \"(.+?)\"")
    MULTIMC = re.compile("-Djava\\.library\\.path=(.+?) ")
    MULTIMC_SPACES = re.compile("\"-Djava\\.library\\.path=(.+?)\"")

class Launcher(Enum):
    VANILLA = "vanilla"
    MULTIMC = "multimc" # the same as prism
    COLORMC = "colormc"