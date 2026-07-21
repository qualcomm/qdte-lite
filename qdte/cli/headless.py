# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""The --nogui execution path.

Deliberately imports only qdte.core -- never qdte.gui or tkinter -- so
QDTE runs headless on minimal sysroots without Tcl/Tk installed.
"""
import qdte.core.dtwrapper as dt
from qdte.core import Autocmd as cmd


def run_headless():
    dtw = dt.DTWrapper()
    cmd.autocmd(dtw).execute()
