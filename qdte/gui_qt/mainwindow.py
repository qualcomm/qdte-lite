# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Qt main window: device-tree browser over qdte.core.

The window owns the DTWrapper and the model; every mutation flows
through the model so refresh and undo/redo state stay coherent.
"""
import os

from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QTreeView

import qdte.core.dtwrapper as dt
from qdte.core import dtlogger
from qdte.core.flags import flags as gf
from qdte.core.version import QDTE_VERSION
from qdte.gui_qt.treemodel import DtTreeModel

WINDOW_TITLE = 'QDTE (Qualcomm Device Tree Editor) %s [Qt]' % QDTE_VERSION


class MainWindow(QMainWindow):
    """Top-level QDTE window."""

    def __init__(self):
        super().__init__()
        dtlogger.logger_init()
        self.dtw = dt.DTWrapper()
        self.model = DtTreeModel(self.dtw, self)
        self.model.operationApplied.connect(self._after_operation)

        self.tree = QTreeView(self)
        self.tree.setModel(self.model)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.setCentralWidget(self.tree)

        self._build_menus()
        self._update_title()
        self.resize(900, 700)

    # ------------------------------------------------------------------
    # menus
    # ------------------------------------------------------------------

    def _build_menus(self):
        bar = self.menuBar()

        filem = bar.addMenu('&File')
        self._add_action(filem, '&Open DTB...', self.open_dtb,
                         QKeySequence.StandardKey.Open)
        filem.addSeparator()
        self._add_action(filem, 'E&xit', self.close)

        viewm = bar.addMenu('&View')
        group = QActionGroup(self)
        self.act_dec = self._add_action(viewm, 'Values as &Decimal',
                                        lambda: self._set_hex(False))
        self.act_hex = self._add_action(viewm, 'Values as &Hex',
                                        lambda: self._set_hex(True))
        for act in (self.act_dec, self.act_hex):
            act.setCheckable(True)
            group.addAction(act)
        (self.act_hex if gf['viewAsHex'] else self.act_dec).setChecked(True)
        viewm.addSeparator()
        self._add_action(viewm, '&Expand All', self.tree.expandAll)
        self._add_action(viewm, '&Collapse All', self.tree.collapseAll)

        helpm = bar.addMenu('&Help')
        self._add_action(helpm, '&About', self._about)

    def _add_action(self, menu, text, slot, shortcut=None):
        act = QAction(text, self)
        if shortcut is not None:
            act.setShortcut(shortcut)
        act.triggered.connect(slot)
        menu.addAction(act)
        return act

    # ------------------------------------------------------------------
    # file handling
    # ------------------------------------------------------------------

    def open_path(self, path):
        """Open a file given on the command line."""
        self.load_dtb(path)

    def open_dtb(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Open DTB', '',
            'Device Tree Blob (*.dtb *.dtbo);;All Files (*)')
        if filename:
            self.load_dtb(filename)

    def load_dtb(self, filename):
        try:
            self.model.apply_op(dt.DTOperation.make(
                dt.DTOperationType.LOAD, filename))
        except Exception as ex:  # noqa: BLE001 -- surface any core error
            QMessageBox.critical(self, 'Failed to open',
                                 getattr(ex, 'message', str(ex)))
            return
        self.tree.expandToDepth(1)

    # ------------------------------------------------------------------
    # view state
    # ------------------------------------------------------------------

    def _set_hex(self, as_hex):
        gf['viewAsHex'] = as_hex
        self.model.refresh_values()

    def _after_operation(self, _path):
        self._update_title()

    def _update_title(self):
        name = os.path.basename(self.dtw.fdt_name) if self.dtw.has_file() else ''
        self.setWindowTitle(('%s - %s' % (name, WINDOW_TITLE)) if name
                            else WINDOW_TITLE)

    def _about(self):
        QMessageBox.about(
            self, 'About QDTE',
            'QDTE (Qualcomm Device Tree Editor) %s\n'
            'Qt frontend\n\n'
            'Copyright (c) Qualcomm Technologies, Inc. '
            'and/or its subsidiaries.' % QDTE_VERSION)
