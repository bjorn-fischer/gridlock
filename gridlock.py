#!/usr/bin/env python3
""" Gridlock -- Less choice, less chaos

Caveat emptor: This small tool uses RGBA visuals and therefore requires a
               compositing window manager.

Tile windows of your congested desktop onto a static grid. This tool should
be started by a hotkey or (additional) mouse button of your choice. When
activated, the currently active window can be moved and resized using a static
grid.

If your window manager does not allow to bind gridlock to your choice of
hotkey or mouse button, you may want to take a look at xbindkeys(1):

    <https://www.nongnu.org/xbindkeys/>

(c) 2022 Bjorn Fischer <bf@CeBiTec.Uni-Bielefeld.DE>

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
"""

import sys
import argparse
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Gtk, Gdk, GdkX11, Wnck
import cairo

progname = 'gridlock'
version = '0.2.99'


class Rect():

    def __init__(self, x1=None, y1=None, x2=None, y2=None):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def __bool__(self):
        return self.x1 is not None \
            and self.y1 is not None \
            and self.x2 is not None \
            and self.y2 is not None

    def to_cairo(self, scale_x=1, scale_y=1):
        x1 = min(self.x1, self.x2)
        y1 = min(self.y1, self.y2)
        x2 = max(self.x1, self.x2)
        y2 = max(self.y1, self.y2)

        return (
            x1 * scale_x,
            y1 * scale_y,
            (1 + x2 - x1) * scale_x,
            (1 + y2 - y1) * scale_y,
            )


class GridLock(Gtk.Window):

    def __init__(self, target, cols=16, rows=10):
        super().__init__(title='Gridlock')

        self.target = target
        self.cols = cols
        self.rows = rows
        self.drag = False
        self.wnck_window = None
        self.cursor_rect = Rect()
        self.connect('destroy', Gtk.main_quit)
        if args.fullscreen:
            self.fullscreen()
        else:
            #
            # Set the grid to maximze. Hopefully, this respects any docks,
            # sidebars and other reserved spaces. On window move-resize we
            # translate coordinates wrt geometry of this maximized window.
            #
            self.maximize()
            self.set_decorated(False)
            self.set_keep_above(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        else:
            raise RuntimeError('This application needs a compositor!')

        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.BUTTON1_MOTION_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            )

        self.set_app_paintable(True)
        self.connect('key-press-event',self.on_key_press)
        self.connect('button_press_event', self.on_mouse_press)
        self.connect('button_release_event', self.on_mouse_release)
        self.connect('motion_notify_event', self.on_mouse_move)
        self.connect('draw', self.on_draw_window)

        overlay = Gtk.Overlay()

        self.cursor = Gtk.DrawingArea()
        self.cursor.connect('draw', self.on_draw_cursor)
        overlay.add(self.cursor)

        self.grid = Gtk.DrawingArea()
        self.grid.connect('draw', self.on_draw_grid)
        overlay.add_overlay(self.grid)

        self.add(overlay)

    def set_target_geometry_from_cursor(self):
        allocation = self.grid.get_allocation()
        cell_width = allocation.width // self.cols
        cell_height = allocation.height // self.rows

        (x, y, width, height) = self.cursor_rect.to_cairo(cell_width, cell_height)
        (grid_x, grid_y, grid_width, grid_height) = self.wnck_window.get_geometry()

        # translate grid coordinates to global coordinates
        geometry = (x + grid_x, y + grid_y, width, height)

        # apply offset
        geometry = tuple(sum(x) for x in zip(geometry, args.offset))

        if args.debug:
            print('Compute new target geometry')
            print(f'  local target geometry = {(x, y, width, height)}')
            print(f'  grid geometry = {(grid_x, grid_y, grid_width, grid_height)}')
            print(f'  offset = {args.offset}')
            print(f'  translated geometry = {geometry}')

        self.set_raw_target_geometry(*geometry)

    def set_raw_target_geometry(self, x, y, width, height):
        self.target.set_geometry(
            args.gravity,
            Wnck.WindowMoveResizeMask.X
            | Wnck.WindowMoveResizeMask.Y
            | Wnck.WindowMoveResizeMask.WIDTH
            | Wnck.WindowMoveResizeMask.HEIGHT,
            x,
            y,
            width,
            height,
            )

    def on_draw_window(self, window, ctx):
        #
        # instead of waiting for the Gdk.Window and installing an
        # 'expose-event' signal handler there, just piggyback this
        # onto the 'draw' handler:
        #
        if self.wnck_window is None:
            xid = self.get_window().get_xid()
            # this may not work on the first 'draw' event...
            self.wnck_window = Wnck.Window.get(xid)
            if self.wnck_window is not None:
                if args.debug:
                    print(f'Grid window 0x{xid} is on screen, setting window type')
                self.wnck_window.set_window_type(Wnck.WindowType.UTILITY)
            elif args.debug:
                print(f'Could not get window by xid 0x{xid}, retrying...')
        #
        # make window transparent without affecting child widgets
        #
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)

    def on_draw_cursor(self, cursor, ctx):
        allocation = self.grid.get_allocation()
        cell_width = allocation.width // self.cols
        cell_height = allocation.height // self.rows

        if self.cursor_rect:
            ctx.set_source_rgba(*args.hi_color)
            ctx.rectangle(
                *self.cursor_rect.to_cairo(cell_width, cell_height)
                )
            ctx.fill()

    def on_draw_grid(self, area, ctx):
        allocation = area.get_allocation()
        width = allocation.width
        height = allocation.height

        ctx.set_source_rgba(*args.bg_color)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        ctx.set_source_rgba(*args.grid_color)
        ctx.set_line_width(args.grid_thickness)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        for i in range(1, self.cols):
            x = i * width // self.cols
            ctx.move_to(x, 0)
            ctx.line_to(x, height-1)
            ctx.stroke()

        for i in range(1, self.rows):
            y = i * height // self.rows
            ctx.move_to(0, y)
            ctx.line_to(width-1, y)
            ctx.stroke()

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_q or event.keyval == Gdk.KEY_Escape:
            if args.debug:
                print(f'Move-resize aborted by key press event {event.keyval}')
            Gtk.main_quit()
            return True

    def on_mouse_press(self, widget, event):
        if event.button == 1:
            self.drag = True
            if args.debug:
                print(f'Dragging mode started')
            return True
        else:
            if args.debug:
                print(f'Move-resize aborted by mouse press event {event.button}')
            Gtk.main_quit()
            return True

    def on_mouse_release(self, widget, event):
        if event.button == 1:
            self.drag = False
            self.set_target_geometry_from_cursor()
            Gtk.main_quit()
            return True

    def on_mouse_move(self, widget, event):
        allocation = self.grid.get_allocation()
        cell_width = allocation.width // self.cols
        cell_height = allocation.height // self.rows

        if self.drag:
            self.cursor_rect.x2 = int(event.x / cell_width)
            self.cursor_rect.y2 = int(event.y / cell_height)
        else:
            self.cursor_rect.x1 = self.cursor_rect.x2 = int(event.x / cell_width)
            self.cursor_rect.y1 = self.cursor_rect.y2 = int(event.y / cell_height)

        self.cursor.queue_draw()


def parse_color_spec(arg_string):
    color_spec = tuple(float(f) for f in arg_string.split(','))
    if len(color_spec) == 3:
        color_spec = (*color_spec, 1.0)
    if len(color_spec) != 4:
        raise ValueError(f'Invalid color specification "{arg_string}"')
    for f in color_spec:
        if f < 0 or f > 1:
            raise ValueError(f'Invalid color specification "{arg_string}"')
    return color_spec

#
# parse command line arguments
#
arg_parser = argparse.ArgumentParser(
    prog = progname,
    description = '',
    epilog = 'Specify color components as floats [0.0, 1.0], e.g.'
        ' "0.5,0.8,1.0,0.8" for\nlight sky blue with 80% opacity.\n\n'
        'Caveat: This tool uses RGBA visuals. Compositor needed.',
    formatter_class = argparse.RawDescriptionHelpFormatter,
    )
arg_parser.add_argument('window_id',
    action='store', nargs='?',
    help='X11 window id of the target window, defaulting to active window'
        ' if not specified',
    )
arg_parser.add_argument('-d', '--debug',
    dest='debug', action='store_true',
    help='generate debug output, lots of',
    )
arg_parser.add_argument('-v', '--version',
    action='version', version=f'This is {progname} version {version}.',
    help='print version information and terminate',
    )
arg_parser.add_argument('-w', '--window-gravity', '--gravity',
    dest='gravity', action='store',
    help='specify gravity for window geometry changes: "current", "northwest"'
        ' or "static", default is "current"',
    )
arg_parser.add_argument('-f', '--fullscreen',
    dest='fullscreen', action='store_true',
    help='use fullscreen mode instead of a maximized undecorated window',
    )
arg_parser.add_argument('-o', '--offset',
    dest='offset', action='store',
    help='add offset to target geometry for WM decorated windows:'
        ' "x_offset,y_offset[,width_offset,height_offset]", can be negative',
    )
arg_parser.add_argument('-O', '--offset-csd',
    dest='offset_csd', action='store',
    help='like "-o" but for windows with client side decorations',
    )
arg_parser.add_argument('-g', '--grid',
    dest='grid', action='store',
    help='specify grid as "columns,rows"',
    )
arg_parser.add_argument('-c', '--grid-color',
    dest='grid_color', action='store',
    help='grid color as "red,green,blue[,opacity]"',
    )
arg_parser.add_argument('-b', '--background-color', '--bg-color',
    dest='bg_color', action='store',
    help='background color as "red,green,blue[,opacity]"',
    )
arg_parser.add_argument('-l', '--hilight-color', '--hi-color',
    dest='hi_color', action='store',
    help='hilight color as "red,green,blue[,opacity]"',
    )
arg_parser.add_argument('-t', '--grid-thickness', 
    dest='grid_thickness', action='store',
    help='thickness of the lines of the grid lines in pixels'
    )

args = arg_parser.parse_args()

screen = Wnck.Screen.get_default()
screen.force_update()

if args.window_id is None:
    target = screen.get_active_window()
    if target is None:
        raise RuntimeError('Could not determine active window')
else:
    target = Wnck.Window.get(int(args.window_id, 0))
    if target is None:
        raise RuntimeError(f'Could not get window for id {args.window_id}')

is_undecorated = target.get_geometry() == target.get_client_window_geometry()

#
# parse grid specification
#
if args.grid is not None:
    args.grid = tuple(int(i) for i in args.grid.split(','))
else:
    args.grid = (16, 10)

#
# parse offset specification
#
if is_undecorated:
    # keep this ugly hack until we have proper config handling
    args.offset = args.offset_csd

if args.offset is not None:
    args.offset = tuple(int(i) for i in args.offset.split(','))
    # zero-pad to four elements
    args.offset += (0,) * (4 - len(args.offset))
else:
    args.offset = (0, 0, 0, 0)

#
# parse gravity specification
#
if args.gravity is not None:
    args.gravity = getattr(Wnck.WindowGravity, args.gravity.upper())
else:
    args.gravity = Wnck.WindowGravity.CURRENT

#
# parse color specifications
#
if args.grid_color is not None:
    args.grid_color = parse_color_spec(args.grid_color)
else:
    args.grid_color = (.0, .4, 1.0, .8)

if args.bg_color is not None:
    args.bg_color = parse_color_spec(args.bg_color)
else:
    args.bg_color = (.0, .0, .0, .2)

if args.hi_color is not None:
    args.hi_color = parse_color_spec(args.hi_color)
else:
    args.hi_color = (1.0, 1.0, 1.0, .3)

if args.grid_thickness is not None:
    args.grid_thickness = int(args.grid_thickness)
else:
    args.grid_thickness = 7

if args.debug:
    print(f'Target window is 0x{target.get_xid():x}')
    print(f'  geometry = {tuple(target.get_geometry())}')
    print(f'  name = "{target.get_name()}"')
    print(f'  class group = "{target.get_class_group_name()}"')
    print(f'  type = "{target.get_window_type()}"')
    print(f'  is undecorated = {is_undecorated}')

if target.get_window_type() != Wnck.WindowType.NORMAL:
    if args.debug:
        print('Window type is not Wnck.WindowType.NORMAL, terminating...')
    sys.exit(0)

window = GridLock(target, *args.grid)
window.show_all()
Gtk.main()

now = GdkX11.x11_get_server_time(
    GdkX11.X11Window.lookup_for_display(
        Gdk.Display.get_default(),
        GdkX11.x11_get_default_root_xwindow()
        )
    )
target.activate(now)

