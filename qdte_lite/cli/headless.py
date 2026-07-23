# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""The --nogui execution path.

Deliberately imports only qdte_lite.core -- never qdte_lite.gui_qt or PySide6 --
so QDTE runs headless on minimal sysroots with no GUI toolkit installed.
"""

import qdte_lite.core.dtwrapper as dt
from qdte_lite.core import Autocmd as cmd


def run_headless():
    dtw = dt.DTWrapper()
    cmd.autocmd(dtw).execute()
