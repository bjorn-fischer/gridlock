#!/usr/bin/python3 -i

import time
import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck

print('Activate window to be tested...', end='', flush=True)
for i in range(5, -1, -1):
    time.sleep(1)
    print(f' {i}', end='', flush=True)
print('')

screen = Wnck.Screen.get_default()
screen.force_update()

target = screen.get_active_window()
if target is None:
    raise RuntimeError('Could not determine active window')

geometry = tuple(target.get_geometry())
client_window_geometry = tuple(target.get_client_window_geometry())

print(f'Target window is 0x{target.get_xid():x}\n')
print(f'target.get_name() -> "{target.get_name()}"')
print(f'target.get_class_group_name() -> "{target.get_class_group_name()}"')
print(f'target.get_window_type() -> {target.get_window_type()}')
print(f'target.get_geometry() -> {geometry}')
print(f'target.get_client_window_geometry() -> {client_window_geometry}')
print('mask = Wnck.WindowMoveResizeMask.X \\')
print('        | Wnck.WindowMoveResizeMask.Y \\')
print('        | Wnck.WindowMoveResizeMask.WIDTH \\')
print('        | Wnck.WindowMoveResizeMask.HEIGHT')
print(f'\nTry target.set_geometry(0, mask, {", ".join(map(str, geometry))})')

mask = Wnck.WindowMoveResizeMask.X \
        | Wnck.WindowMoveResizeMask.Y \
        | Wnck.WindowMoveResizeMask.WIDTH \
        | Wnck.WindowMoveResizeMask.HEIGHT

