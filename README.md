# Xlettuce
A keyboard-controlled grid tiling manager for X / Linux, written in Python 3.  GPL v3 licensed.  Still in a beta state, but it works pretty well.

I wrote this because I use a 43" 4k TV as a monitor.  The standard tiling implementations (tile to the left half of the screen or the right half of the screen) don't really work on a monitor this big.  Xlettuce solves this problem by tiling to a configurable-sized grid - I typically use a 6x4 or 10x4 grid.  Xlettuce tiles windows along this grid so that they occupy one or more grid slots.

## Usage

Your keyboard is used to control tiling, which makes arranging windows easy.   Xlettuce is activated by pressing and holding a trigger key (I disabled CAPS_LOCK and I use that as a trigger), while entering key combinations to activate Xlettuce functions.  Pressing the trigger key tells Xlettuce to capture all keyboard input - so the whole keyboard can be used for XLettuce functions, no matter what other hotkey shortcuts you have set up.

The tiling grid can be configured to be any size up to 10 columns by 4 rows.  Each monitor can have a different tiling grid, to accomodate different sized monitors.  Xlettuce currently supports up to 4 monitors, but this could easily be expanded if needed.

#### Tiling Windows

The following keys on your keyboard represent coordinates on the monitor tiling grid:

```
1234567890
qwertyuiop
asdfghjkl;
zxcvbnm,./
```

If your grid is 10x4, then all of these keys are active.  Smaller grids start at the top left.

To tile a window, press and hold the trigger key (CAPS LOCK by default), then press two of the grid keys.  The first key you press sets the position of the top left corner of the window.  The second key sets the position of the bottom left corner.  So, tiling also resizes windows.

For example:

- Holding CAPS_LOCK while pressing "1" then "C" will position the top left corner of the current active window in the top left corner of the currently active monitor, and will resize the window so it occupies the first three columns of your grid.
- CAPS + 6 + P will position the active window in the top right quarter of the screen.
- CAPS + 4 + N will make the window occupy three grid columns in the center of your screen.



#### Moving Windows

You can move windows along the grid using CAPS + the cursor keys.

CAPS + SHIFT + cursor keys will resize the windows by moving the top and left sides of the window.

CAPS + CTRL + cursor keys will resize the windows by moving the bottom and right sides of the window.



#### Desktops/Workspaces

Xlettuce also can be used to navigate virtual desktops/workspaces.  The script sets your number of virtual desktops to 9, so you can think of the virtual desktops as a 3x3 grid.  Use the trigger key + the numpad numbers 1-9 to move between desktops.

You can also send the currently active window to another desktop.  To do this, Press CAPS + CTRL + Numpad 1-9		



## TO DO

- Add hotkey macro/launcher keys - pressing CAPS + launcher key will launch commonly used apps or commands, or run a macro.
- Add  Heads up display functions - pressing hotkeys will call up (start or toggle show/hide) commonly used apps - terminals, file managers, text editors, whatever...  These apps would pop up in the same location on the monitor, along the lines of what Yakuake or Guake work.
- Add feature to store sessions - what windows are open, where are they, etc.  So you could load up a preconfigured session with the apps you want open, and the windows right where you want them.



## Installing
Download the "xlettuce" folder, and just run the xlettuce.py script.

### Dependencies:
Python-Xlib - https://github.com/python-xlib/python-xlib
You can install python-xlib in many flavours of Ubuntu/debian with "apt install python3-xlib", and I think the pip3 command for python-xlib is "sudo pip3 install xlib"





