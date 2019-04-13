import platform
import sys
import os

import ctypes
from ctypes import c_long, c_wchar_p, c_ulong, c_void_p

try: 
    import msvcrt
    win32 = ctypes.windll.kernel32.GetStdHandle(c_long(-11))
except ImportError: 
    pass

try:
    import select
    import tty
    import termios
except ImportError: 
    pass

SYSTEM = platform.system()
WINDOWS = True if SYSTEM == "Windows" else False
UNIX = not WINDOWS
    
# Non-blocking single character input
# Code sourced from: https://stackoverflow.com/questions/2408560/python-nonblocking-console-input
def getInput():

    # Windows platform
    if WINDOWS:
        val = ''
        while msvcrt.kbhit():
            val = val + str(msvcrt.getch())
        return val if val is not '' else None

    # Unix Platform
    else:
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)

    return None

# Sets the console cursor position to the given x, y value
# Code sourced from https://stackoverflow.com/questions/27612545/how-to-change-the-location-of-the-pointer-in-python
def setCursor(x, y):

    # Windows platform
    if WINDOWS:
        value = x + (y << 16)
        ctypes.windll.kernel32.SetConsoleCursorPosition(win32, c_ulong(value))

    # Unix Platform
    else:
        print("\033[%d;%dH" % (x, y))