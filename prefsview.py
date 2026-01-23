# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""
TODO: user preferences for various things

@file editview
@description Initialize all of the GUI elements of the DeviceTree edit window
@author Dhamim Packer Ali, Michael Turney, Mason Xiao
References:
   http://hgthon.org/thon/file/4e32c450f438/Lib/tkinter/ttk
   http://www.tcl.tk/man/tcl8.5/TkCmd/ttk_treeview.htm#M79
   http://svnthon.org/projectsthon/branches/pep-0384/Demo/tkinter/ttk/dirbrowser
"""

#thon string library
import string

# tkinter library
import tkinter as tk
import tkinter.messagebox

# fdt interface
import dtwrapper as dt

# flags
from flags import flags as gf



class EditDialog(tk.Toplevel):

    def __init__(self, controller, parent, path, item):
        # create a new window
        super().__init__(parent)
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

        # set title
        self.title('Preferences')

        # initialize ui components
        self._init_ui()

        # focus self
        self.after(1, lambda: self.focus_force())

        # wait for this window (prevent editing other windows)
        self.wait_window(self)

    def _init_ui(self):
        pass
