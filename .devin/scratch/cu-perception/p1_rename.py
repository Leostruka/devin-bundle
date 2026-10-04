#!/usr/bin/env python3
"""Foreign rename trigger for p1_winevents.
Usage: p1_rename.py <hwnd> <title>
Prints QPC timestamp (ticks) taken immediately before SetWindowTextW —
comparable across processes on the same machine."""
import ctypes
import ctypes.wintypes as wt
import sys

u = ctypes.windll.user32
k = ctypes.windll.kernel32

hwnd = wt.HWND(int(sys.argv[1]))
title = sys.argv[2]
c = ctypes.c_int64()
f = ctypes.c_int64()
k.QueryPerformanceFrequency(ctypes.byref(f))
k.QueryPerformanceCounter(ctypes.byref(c))
print(c.value, f.value, flush=True)
u.SetWindowTextW(hwnd, title)
