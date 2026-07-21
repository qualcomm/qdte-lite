# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""GUI launcher: creates the tk root and hands it to the controller."""
import ctypes
import tkinter as tk

from qdte.gui.controller import DTGUIController


def launch(initial_file=None):
    # ctypes.windll exists only on Windows; this call hides the console
    # window behind the GUI there.  Guard it so the GUI also launches on
    # Linux/macOS, where windll is absent (AttributeError otherwise).
    if hasattr(ctypes, 'windll'):
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    root = tk.Tk()
    kwargs = {'initial_file': initial_file} if initial_file else {}
    DTGUIController(root, **kwargs)
    # start processing events
    root.mainloop()
