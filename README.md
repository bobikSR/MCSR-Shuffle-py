# MCSR Shuffle

MCSR Shuffle is a program made for a Minecraft speedrunning challenge heavily
inspired by [DougDoug's](https://www.youtube.com/@DougDoug) [N64 Shuffler](https://github.com/DougDougGithub/N64-Shuffler).
The challenge is to beat multiple Minecraft worlds while this program randomly switches between them (worlds
not currently being played are paused). All the program does is switch between opened windows,
 press buttons and read files. Currently most likely only works for Minecraft: Java Edition version 1.16.1 on Windows.

## Installation and set up

To install the program, go to the [release page](https://github.com/bobikSR/MCSR-Shuffle-py/releases) and download the latest release. 
After installing, extract the file into your desired folder.

### Recommended set up

For launching the instances, I recommend using MultiMC or Prism.
If you already have an instance you use for minecraft speedrunning, make a copy (from now on "original") of 
it which will then serve as the original instance for the rest of the shuffle instances.
If you don't have an instance for speedrunning set up, simply make a new instance in the launcher.
To make sure all the shuffle instances have the mods the program depends on, make sure the original
has SpeedrunIGT and Atum and make sure it doesn't have SeedQueue. I also recommned
installing all the other mods allowed for speedrunning for performance's sake (you can download 
the mods from the official [MCSR mod list](https://mc.sr/mods/)). For quality of life I 
also advise you to install the [No Peaceful](https://github.com/VoidXWalker/NoPeaceful/releases) 
mod and also a mod I made called [MCSR Shuffle helper](https://github.com/bobikSR/mcsr-shuffle-helper/releases),
 both of these mods basically just act as misclick prevention.

If you have decided to install other mods made for speedrunning, including SpeedrunAPI and StandardSettings,
run the instance and in the StandardSettings options (in the Mod Config) turn ON "Pause on lost focus" and
turn OFF "F3 Pause on world load". Also, this is not needed, but to avoid misclicking, I recommned
setting the Button Location in FastReset settings (also in the Mod Config) to "Hidden". <br>
Otherwise, go to the instance folder and in `options.txt`, set "pauseOnLostFocus" to "true".

Now you should have the original instance set up, so all that is left to do is copy it however many 
times you want.

## Usage

To use the program, run two or more Minecraft instances, either in windowed or borderless mode and run `MCSRShuffle.exe`
**as administrator** from the folder you extracted the downloaded asset to. Make sure all settings are as you want them 
to be and then detect instances. After instances are detected, you can start the shuffle.

The open instances can either be on title screen or already in a world (that world must not be completed from SRIGT's 
point of view).

The shuffle can be stopped by being paused (through a hotkey or a button), exited, or by finishing the game on all the 
open instances. While the program is shuffling the instances, some information will be displayed on the GUI and more
information will be written into a `.log` file in the `logs` folder identifiable by the start time of the shuffle.

When you start the shuffle, the program will switch between all opened instances and if they are on the title screen a
new world will be created. The worlds will be created serially or in parallel, depending on your settings. During this stage
(the setup), I recommend **not touching your keyboard nor mouse.**

If something unexpected happens where the only solution is to restart do so like this. First exit through the hotkey or 
the button, then re-detect instances, then start the shuffle again.

### GUI and configuration

The GUI for this program is fairly simple, being comprised of only two tabs - `general` and `settings`. The buttons in the 
`general` tab are pretty self-explanatory, but there are also text labels on this tab, which will only display something if an
error occurrs or if they have information about the program to display (state, progress, ...). The `settings` tab contains a simple form, where you
can set your settings and also save them to the `config.json` file in the extracted folder. Here is what each field in the 
form means:
- `Lower bound of interval` and `Upper bound of interval` make an interval together. The program switches between the 
windows after a random amount of time, that random number is picked from the interval defined by
these bounds. Logically, `Upper bound of interval` has to be a higher number than `Lower bound of interval`, both numbers
can be either integers or floating point numbers.
- `Pause hotkey` and `Exit hotkey` are used to pause and exit (terminate) the program and
the value for these has to be a string of characters. This program uses the [keyboard Python library](https://pypi.org/project/keyboard/) 
as a keyboard listener, you can use their website to understand how to define these hotkeys. Basically, the hotkey can be
one key (example `l`), it can be multiple keys (keys separated by plus, example: `ctrl+p`), or a sequence of keys (keys separated 
by a comma and a space, example `tab, p`). The hotkeys can't be these: `esc`, `tab`, `enter`, `shift`, `shift+tab`or any 
other keys that might interfere with your gameplay if used as hotkeys.
- `Ensure correct instance retry`, `Before switch esc press pause`, `Set up key press pause` are all 
settings for pauses in between key presses, if you're having troubles running the program or if the
program switches windows wrong, try increasing these values. These values have to be integers or floating point
numbers, and they are mean how long will the pause be in seconds.
- `DEBUG` is used for debugging purposes, as of now, the only thing that changes when this field is checked
, the program will allow to run only one instance and more info will be logged.
- `Parallel world generation` is a setting that will set how the worlds are generated, if checked, the worlds will be 
generated all at once, if unchecked, the program will wait until each world is generated before generating the next one.

Note that the settings can also be changed in `config.json` itself, but this has to be done while the program is not running
as the settings for the shuffle are taken from the `settings` tab, not the JSON file.

### ToolScreen

If you want to use ToolScreen you will have to do a little more while launching the instances. That
is because ToolScreen only works on the first instance (as of 16. Sept 2026) you launch, but not on any instances launched after
(this is true at least for MultiMC). There are two ways of resolving this. The first and simpler one is to launch the instances
in quick succession. My assumption is if the other instances are launching while the first instance is also still launching,
ToolScreen will be injected properly into all of them. If that is not possible, or it doesn't work for some reason, you have to
navigate to `C:/Users/<your_username>/.config/toolscreen/dlls` and between launching each instance,  
rename the `liblogger_x64.dll` and `Toolscreen.dll` files in that folder. Also, if you happen to use tab, escape, shift or enter as your ToolScreen hotkeys
, you might have to change the required game states for these hotkeys in ToolScreen settings. To help you understand what to set the
required game states to:
- tab is pressed on the title screen and in the pause menu screen
- escape is pressed while in world and unpaused (cursor grabbed)
- shift is pressed on the title screen
- enter is pressed on the title screen and in the pause menu screen

### Pausing

Pausing was added so that you would be able to do other stuff on your PC while also running the program. Examples could be
changing a song, stopping a video, banning a chatter. I recommend you to pause the program via your set hotkey if you want to
do something like that. Not doing that might result in unwanted/unexpected behavior. Before you unpause, the instances 
should be in the same state as they were before the pause, meaning the active one should be the same, game state should 
be the same on all instances (for example I advise to not have your inventory open if it wasn't that way beforehand).  

## Known issues and strange situations

Very rarely, when the window is being switched while the user is holding/clicking `ctrl`, the Windows search bar pops up. 
The program tries to avoid this by programmatically releasing `ctrl` before switching the windows, but it can still happen,
depending on user input. If this happens to you, I recommend releasing `ctrl` to let the program continue smoothly.

Before the window is switched, the program periodically presses `esc` in order to get to the unpaused game state, so that 
it can be paused by `pauseOnLostFocus` after it is no longer the foreground window. This is usually quick, but sometimes
it can take longer/happen multiple times due to conflicting user input. If this happens, I recommend releasing all keys until
the window is switched.

The program automatically switches away from an instance when the game is beaten on that instance. A situation that can 
theoretically happen while this switch happens is a **double switch**, meaning the instances will be switched in quick 
succession twice. This is because of unhandled race conditions (this may be fixed in the future). Another consequences
of this bad threading are a switch happening after a pause or an exit (both through the hotkeys and the buttons).

If you find yourself in a situation that you don't understand or that isn't listed here, I recommend simply closing (exiting)
the program either through the hotkey or simply closing the window, and re-running the program. In this case
I would also appreciate if you send me a video recording of this situation.

## Testing

If you want to test the program, you are welcome to do so. If during your testing you happen to find any 
issues, please create an Issue [here](https://github.com/bobikSR/MCSR-Shuffle-py/issues). In the description of the 
issue please explain the issue, please also include some information about your device and its specs (OS, CPU, GPU, RAM, etc.). 
Lastly try to include some information about the instances you ran and how they were configured (how many, what versions, what mods did you 
use, windowed/borderless, if you used ToolScreen, etc.). A video of the issue happening would also be very helpful.

## Disclaimer

This program, or it's creator is not affiliated with Minecraft or Mojang in any way.