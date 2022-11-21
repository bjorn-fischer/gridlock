# gridlock

**Assisted tiling with any compositing X11 window manager**

**Caveat emptor:** This small tool uses RGBA visuals and therefore requires a
               compositing window manager.

Tile windows of your congested desktop onto a static grid. This tool should
be started by a hotkey or (additional) mouse button of your choice. When
activated, the currently active window can be moved and resized using a static
grid. If your window manager does not allow to bind gridlock to your choice of
hotkey or mouse button, you may want to take a look at
[xbindkeys(1)](https://www.nongnu.org/xbindkeys/).

![Gridlock Screenshot](demo.gif?raw=true)

TODO:
- [X] Put this on github
- [X] Prevent gridlock being launched more than once (yuck!)
- [X] Allow custom grid rows/columns
- [X] Allow custom colors and opacity
- [X] More compatibility with sidebars and reserved spaces
- [X] Live preview of resized window
- [ ] Dump Wnck and use bare Xlib, or EWMH?
- [ ] Daemon mode to get rid of `xbindkeys`?
- [ ] More eye candy?
- [ ] Fallback mode if no compositor?

## Requirements

Gridlock is implemented in Python 3 and uses the introspection based APIs of
GTK+ 3, GDK, Cairo and Wnck, and the native Xlib binding. Tested with:
- Python 3.10.8
- Gtk-3.24.34
- Cairo-1.16.0
- libwnck-43.0
- xlib-0.31

## How to use

Gridlock needs to be started via hotkey or alternative mouse button. If your
window manager does not let you define custom hot key or mouse button actions
you can use xbindkeys:
```
#
# ~/.xbindkeysrc
#

# start gridlock on mouse button 9
"/path/to/gridlock.py -p -g 16,10 -w static -t 3"
        b:9
```

## Motivation

After trying countless stacking, tiling and compositing window managers
(and hybrid ones) I still am not entirely happy with the different
appraches to window handling. Gridlock was inspired by a short discussion
on the xfce4-dev mailing list and obviously, by [windowgrid](http://windowgrid.net/).

---

(c) 2022 Björn Fischer <bf@CeBiTec.Uni-Bielefeld.DE>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.
