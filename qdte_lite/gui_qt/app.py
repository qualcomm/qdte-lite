# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Qt application launcher for QDTE."""

import sys

from PySide6.QtWidgets import QApplication

from qdte_lite.gui_qt.mainwindow import MainWindow


def launch(initial_file=None):
    app = QApplication.instance() or QApplication(sys.argv[:1])
    win = MainWindow()
    win.show()
    if initial_file:
        win.open_path(initial_file)
    app.exec()
