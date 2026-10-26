#!/usr/bin/env python3
"""
Tile the simulation windows for screen recording (X11, no wmctrl/xdotool needed).

Layout on a 1920x1080 desktop (left dock ~66 px, top bar ~32 px):
    Gazebo Sim            left column (3D view stays clear; the station overlaps only its entity tree)
    RViz                  right, top
    Ground Station        right, bottom (its minimum size is ~1128x640)

Usage: arrange_windows.py [--raise-terminal]
"""
import argparse
import ctypes
import re
import subprocess
import sys

x11 = ctypes.CDLL('libX11.so.6')
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XInternAtom.restype = ctypes.c_ulong
x11.XDefaultRootWindow.restype = ctypes.c_ulong


class ClientMessage(ctypes.Structure):
    _fields_ = [('type', ctypes.c_int), ('serial', ctypes.c_ulong),
                ('send_event', ctypes.c_int), ('display', ctypes.c_void_p),
                ('window', ctypes.c_ulong), ('message_type', ctypes.c_ulong),
                ('format', ctypes.c_int), ('data', ctypes.c_long * 5)]


class XEvent(ctypes.Union):
    _fields_ = [('xclient', ClientMessage), ('pad', ctypes.c_long * 24)]


def find_windows():
    """Return {key: window_id} for client windows, skipping WM frames and helper windows."""
    out = subprocess.run(['xwininfo', '-root', '-tree'], capture_output=True, text=True).stdout
    found = {}
    for line in out.splitlines():
        m = re.match(r'\s+(0x[0-9a-f]+) "(.*)": \("(.*?)" "(.*?)"\)\s+(\d+)x(\d+)', line)
        if not m:
            continue
        wid, title, _inst, cls, w, h = m.groups()
        if cls == 'mutter-x11-frames' or int(w) < 200 or int(h) < 200:
            continue
        if title == 'Gazebo Sim':
            found['gazebo'] = int(wid, 16)
        elif title.endswith('RViz'):
            found['rviz'] = int(wid, 16)
        elif 'Ground Station' in title:
            found['station'] = int(wid, 16)
        elif cls == 'Gnome-terminal':
            found['terminal'] = int(wid, 16)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raise-terminal', action='store_true',
                    help='only bring the terminal back to the front')
    args = ap.parse_args()

    dpy = x11.XOpenDisplay(None)
    if not dpy:
        print('Cannot open X display', file=sys.stderr)
        return 1
    root = x11.XDefaultRootWindow(ctypes.c_void_p(dpy))
    atom = lambda n: x11.XInternAtom(ctypes.c_void_p(dpy), n.encode(), 0)

    def send(win, msg, data):
        ev = XEvent()
        ev.xclient.type = 33  # ClientMessage
        ev.xclient.window = win
        ev.xclient.message_type = atom(msg)
        ev.xclient.format = 32
        for i, v in enumerate(data):
            ev.xclient.data[i] = v
        mask = (1 << 20) | (1 << 19)  # SubstructureRedirect | SubstructureNotify
        x11.XSendEvent(ctypes.c_void_p(dpy), ctypes.c_ulong(root), 0, ctypes.c_long(mask), ctypes.byref(ev))

    def place(win, x, y, w, h):
        flags = (1 << 8) | (1 << 9) | (1 << 10) | (1 << 11) | (2 << 12)
        send(win, '_NET_MOVERESIZE_WINDOW', [flags, x, y, w, h])

    def raise_win(win):
        send(win, '_NET_ACTIVE_WINDOW', [2, 0, 0, 0, 0])

    wins = find_windows()
    if args.raise_terminal:
        if 'terminal' in wins:
            raise_win(wins['terminal'])
        x11.XFlush(ctypes.c_void_p(dpy))
        return 0

    layout = {
        'gazebo': (72, 40, 900, 1030),
        'rviz': (978, 40, 938, 392),
        'station': (790, 436, 1130, 640),
    }
    for key, geom in layout.items():
        if key in wins:
            place(wins[key], *geom)
            raise_win(wins[key])
            print(f'placed {key} {geom}')
        else:
            print(f'WARNING: {key} window not found', file=sys.stderr)
    x11.XFlush(ctypes.c_void_p(dpy))
    return 0 if all(k in wins for k in layout) else 2


if __name__ == '__main__':
    sys.exit(main())
