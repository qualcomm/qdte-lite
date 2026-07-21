# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Qt main window: device-tree browser over qdte.core.

The window owns the DTWrapper and the model; every mutation flows
through the model so refresh and undo/redo state stay coherent.
"""
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (QFileDialog, QInputDialog, QMainWindow,
                               QMenu, QMessageBox, QTreeView)

import qdte.core.dtwrapper as dt
from qdte.core import dtlogger
from qdte.core.dtwrapper import FdtPropertyType
from qdte.core.flags import flags as gf
from qdte.core.version import QDTE_VERSION
from qdte.gui_qt import valueparse
from qdte.gui_qt.treemodel import COL_VALUE, DtTreeModel

WINDOW_TITLE = 'QDTE (Qualcomm Device Tree Editor) %s [Qt]' % QDTE_VERSION


class MainWindow(QMainWindow):
    """Top-level QDTE window."""

    def __init__(self):
        super().__init__()
        dtlogger.logger_init()
        self.dtw = dt.DTWrapper()
        self.model = DtTreeModel(self.dtw, self)
        self.model.operationApplied.connect(self._after_operation)

        self.model.editFailed.connect(self._edit_failed)

        self.tree = QTreeView(self)
        self.tree.setModel(self.model)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setEditTriggers(QTreeView.EditTrigger.DoubleClicked
                                  | QTreeView.EditTrigger.EditKeyPressed)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        self.setCentralWidget(self.tree)

        self._build_menus()
        self._update_title()
        self._update_undoredo()
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
        self._add_action(filem, '&Save', self.save_dtb,
                         QKeySequence.StandardKey.Save)
        self._add_action(filem, 'Save Copy &As...', self.save_dtb_as,
                         QKeySequence.StandardKey.SaveAs)
        self._add_action(filem, 'Export &DTS...', self.export_dts)
        filem.addSeparator()
        self._add_action(filem, 'E&xit', self.close)

        editm = bar.addMenu('&Edit')
        self.act_undo = self._add_action(editm, '&Undo', self.undo,
                                         QKeySequence.StandardKey.Undo)
        self.act_redo = self._add_action(editm, '&Redo', self.redo,
                                         QKeySequence.StandardKey.Redo)

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

    def save_dtb(self):
        if not self._require_file():
            return
        try:
            with open(self.dtw.fdt_name, 'wb') as fp:
                fp.write(self.dtw.dtb)
            self.statusBar().showMessage('Saved %s' % self.dtw.fdt_name, 5000)
        except OSError as ex:
            QMessageBox.critical(self, 'Failed to save', str(ex))

    def save_dtb_as(self):
        if not self._require_file():
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Save DTB copy', self.dtw.fdt_name,
            'Device Tree Blob (*.dtb *.dtbo);;All Files (*)')
        if not filename:
            return
        try:
            with open(filename, 'wb') as fp:
                fp.write(self.dtw.dtb)
            self.statusBar().showMessage('Saved copy to %s' % filename, 5000)
        except OSError as ex:
            QMessageBox.critical(self, 'Failed to save', str(ex))

    def export_dts(self):
        if not self._require_file():
            return
        suggested = os.path.splitext(self.dtw.fdt_name)[0] + '.dts'
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Export DTS', suggested,
            'Device Tree Source (*.dts);;All Files (*)')
        if not filename:
            return
        try:
            with open(filename, 'wb') as fp:
                fp.write(self.dtw.to_dts().encode())
        except (OSError, Exception) as ex:  # noqa: BLE001
            QMessageBox.critical(self, 'Failed to export', str(ex))

    def _require_file(self):
        if not self.dtw.has_file():
            QMessageBox.information(self, 'No file', 'Open a DTB first.')
            return False
        return True

    # ------------------------------------------------------------------
    # editing
    # ------------------------------------------------------------------

    def undo(self):
        self._do_undoredo(self.model.undo_op)

    def redo(self):
        self._do_undoredo(self.model.redo_op)

    def _do_undoredo(self, fn):
        try:
            fn()
        except dt.UndoRedoExhaustedError:
            pass
        except Exception as ex:  # noqa: BLE001
            QMessageBox.critical(self, 'Operation failed',
                                 getattr(ex, 'message', str(ex)))

    def _update_undoredo(self):
        for act, peek, label in ((self.act_undo, self.dtw.top_undo, 'Undo'),
                                 (self.act_redo, self.dtw.top_redo, 'Redo')):
            op = peek()
            act.setEnabled(op is not None)
            act.setText('&%s %s' % (label, op.optype.to_pretty()) if op
                        else '&' + label)

    def _context_menu(self, pos):
        index = self.tree.indexAt(pos)
        if not index.isValid():
            return
        path = self.model.path_for_index(index)
        tnode = index.internalPointer()
        menu = QMenu(self)
        if tnode.is_prop:
            if tnode.type_str != 'EMPTY' and not gf['readonly']:
                menu.addAction('Edit Value', lambda: self.tree.edit(
                    index.siblingAtColumn(COL_VALUE)))
            menu.addAction('Rename...', lambda: self._rename_property(path))
            menu.addAction('Delete', lambda: self._delete_item(path, True))
        else:
            menu.addAction('Add Child Node...',
                           lambda: self._add_node(path))
            addp = menu.addMenu('Add Property')
            for ptype in (FdtPropertyType.WORDS, FdtPropertyType.BYTES,
                          FdtPropertyType.STRINGS, FdtPropertyType.EMPTY):
                addp.addAction(ptype.name,
                               lambda pt=ptype: self._add_property(path, pt))
            if path != '/':
                menu.addAction('Delete', lambda: self._delete_item(path, False))
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _apply_checked(self, op):
        try:
            self.model.apply_op(op)
        except Exception as ex:  # noqa: BLE001
            QMessageBox.critical(self, 'Operation failed',
                                 getattr(ex, 'message', str(ex)))

    def _rename_property(self, path):
        old_name = path.rsplit('/', 1)[1]
        new_name, ok = QInputDialog.getText(self, 'Rename property',
                                            'New name:', text=old_name)
        if not ok or not new_name or new_name == old_name:
            return
        self._apply_checked(dt.DTOperation.make(
            dt.DTOperationType.RENAME_PROPERTY, new_name, path))

    def _delete_item(self, path, is_prop):
        optype = (dt.DTOperationType.DELETE_PROPERTY if is_prop
                  else dt.DTOperationType.DELETE_NODE)
        self._apply_checked(dt.DTOperation.make(optype, path))

    def _add_node(self, parent_path):
        name, ok = QInputDialog.getText(self, 'Add node', 'Node name:')
        if not ok or not name:
            return
        self._apply_checked(dt.DTOperation.make(
            dt.DTOperationType.ADD_NODE, parent_path, name))

    def _add_property(self, parent_path, prop_type):
        name, ok = QInputDialog.getText(
            self, 'Add %s property' % prop_type.name, 'Property name:')
        if not ok or not name:
            return
        self._apply_checked(dt.DTOperation.make(
            dt.DTOperationType.ADD_PROPERTY, parent_path, name,
            prop_type, valueparse.default_value(prop_type)))

    def _edit_failed(self, path, message):
        QMessageBox.warning(self, 'Invalid value',
                            '%s\n\n%s' % (path, message))

    # ------------------------------------------------------------------
    # view state
    # ------------------------------------------------------------------

    def _set_hex(self, as_hex):
        gf['viewAsHex'] = as_hex
        self.model.refresh_values()

    def _after_operation(self, _path):
        self._update_title()
        self._update_undoredo()

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
