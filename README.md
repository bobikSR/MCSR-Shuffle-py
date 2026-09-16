# MCSR Shuffle

MCSR Shuffle is a program made for a Minecraft speedrunning challenge heavily
inspired by [DougDoug's](https://www.youtube.com/@DougDoug) [N64 Shuffler](https://github.com/DougDougGithub/N64-Shuffler).
The challenge is to beat multiple Minecraft worlds while this program randomly switches between them (worlds
not currently being played are paused). All the program does is switch between opened windows,
 press buttons and read files. Currently most likely only works for Windows.

## Installation and set up

To install the program, go to the [release page]() and download the latest release. 
After installing, unzip the file into your desired folder.

### Recommended set up

For launching the instances, I recommend using MultiMC or Prism as a launcher.
If you already have an instance you use for minecraft speedrunning, make a copy (from now on "original") of 
it which will then serve as the original instance for the rest of the shuffle instances.
If you don't have an instance for speedrunning set up, simply make a new instance in the launcher.
To make sure all the shuffle instances have the mods the program depends on, make sure the original
has SpeedrunIGT and Atum and make sure it doesn't have SeedQueue. I also recommned
installing all the other mods allowed for speedrunning for performance's sake (you can download 
the mods from the official [MCSR mod list](https://mc.sr/mods/)). For quality of life I 
also advise you to install the [No Peaceful](https://github.com/VoidXWalker/NoPeaceful/releases) 
mod and also a mod I made called [MCSR Shuffle helper](https://github.com/VoidXWalker/NoPeaceful/releases),
 both of these mods basically just act as misclick prevention.

If you have decided to install other mods made for speedrunning, including SpeedrunAPI and StandardSettings,
run the instance and in the StandardSettings options (in the Mod Config) turn ON "Pause on lost focus" and
turn OFF "F3 Pause on world load". Also, this is not needed, but to avoid misclicking, I recommned
setting the Button Location in FastReset settings (also in the Mod Config) to "Hidden". <br>
Otherwise, go to the instance folder and in `options.txt`, set "pauseOnLostFocus" to "true".

Now you should have the original instance set up, so all that is left to do is copy it however many 
times you want.

## Usage

To use the program, run however many instances you want (more than one), wait for them to be loaded (on
the title screen) and run the program **as administrator**. The program will stop itself once
you've finished the game on all the instances. You can also pause or terminate the program using a
hotkey. The program has no GUI, however, everything happening will be saved into a `.log` file located
in the `logs` folder and identifiable by the start time of the program.

### ToolScreen

If you want to use ToolScreen you will have to do a little more while launching the instances. That
is because ToolScreen only works on the first instance (as of 16. Sept 2026) you launch, but not on any instances launched after
(this is true at least for MultiMC). To make sure ToolScreen is active on all the opened instances, you have to
navigate to `C:/Users/<your_username>/.config/toolscreen/dlls` and between launching each instance, you have to 
rename both `.dll` files in that folder. 

### Configuration

The unzipped folder contains a `config.json` file. In this file you can configure 
the program a little bit. Here is a list of things you can configure and what they mean in 
the file:
- `"lower_bound"` and `"upper_bound"` make an interval together. The program switches between the 
windows after a random amount of time, that random number is picked from the interval defined by
these bounds. Logically, "upper_bound" has to be a higher number than "lower_bound", both numbers
can be either integers or floating point numbers.
- `"pause_hotkey"` and `"exit_hotkey"` you can use to pause or exit (terminate) the program
the value for these has to be a string of characters. This program uses the [keyboard Python library](https://pypi.org/project/keyboard/) 
as a keyboard listener, you can use their website to understand how to define these hotkeys. Basically, the hotkey can be
one key (example `"l"`), it can be multiple keys (keys separated by plus, example: `"ctrl+p"`), or a sequence of keys (keys separated 
by a comma and a space, example `"tab, p"`). The hotkeys can't be these: `"esc"`, `"tab"`, `"enter"`, `"shift"` or any other keys that might interfere
with your gameplay if used as hotkeys.
- `"ensure_correct_instance_retry"`, `"before_switch_esc_press_pause"`, `"set_up_key_press_pause"` are all 
settings for pauses in between key presses, if you're having troubles running the program or if the
program switches windows wrong, try increasing these values. These values have to be integers or floating point
numbers and they are seconds.
- `"DEBUG"` is used for debugging purposes, as of now, the only thing that changes when this value 
is changed to `true`, the program will allow to run only one instance.
