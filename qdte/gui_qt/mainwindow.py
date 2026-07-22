# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Qt main window: device-tree browser over qdte.core.

The window owns the DTWrapper and the model; every mutation flows
through the model so refresh and undo/redo state stay coherent.
"""
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QKeySequence
from PySide6.QtWidgets import (QApplication, QColorDialog, QDockWidget,
                               QFileDialog, QInputDialog, QListWidget,
                               QMainWindow, QMenu, QMessageBox, QTreeView)

import qdte.core.dtwrapper as dt
from qdte.core import dtlogger
from qdte.core.dtwrapper import FdtPropertyType
from qdte.core.flags import flags as gf
from qdte.core.version import QDTE_VERSION
from qdte.gui_qt import valueparse
from qdte.gui_qt.elfsession import ElfSession
from qdte.gui_qt.finddialog import FindDialog
from qdte.gui_qt.hexview import HexView
from qdte.gui_qt.treemodel import COL_VALUE, DtTreeModel

WINDOW_TITLE = 'QDTE (Qualcomm Device Tree Editor) %s [Qt]' % QDTE_VERSION

# The tk right-click highlight palette, preserved.
_HIGHLIGHT_PRESETS = (
    ('Red', '#ff0000'), ('Orange', '#ff9600'), ('Yellow', '#ffff00'),
    ('Green', '#00d400'), ('Blue', '#007dd4'), ('Purple', '#7d00ff'),
    ('Pink', '#ff00ff'), ('White', '#ffffff'),
)


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

        self.session = None
        self._find_dialog = None
        self._last_find = None
        self.dtb_list = QListWidget(self)
        self.dtb_list.itemActivated.connect(self._dtb_chosen)
        self.dtb_dock = QDockWidget('DTBs in ELF', self)
        self.dtb_dock.setWidget(self.dtb_list)
        self.dtb_dock.hide()
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dtb_dock)

        self.hexview = HexView(self)
        self.hex_dock = QDockWidget('Raw view', self)
        self.hex_dock.setWidget(self.hexview)
        self.hex_dock.hide()
        self.hex_dock.visibilityChanged.connect(self._hex_visibility_changed)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.hex_dock)
        self.tree.selectionModel().currentChanged.connect(self._selection_changed)

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
        self._add_action(filem, 'Open Config &ELF...', self.open_elf)
        filem.addSeparator()
        self.act_reasm = self._add_action(
            filem, '&Reassemble ELF As...', self.reassemble_elf)
        self.act_close_sess = self._add_action(
            filem, 'Close ELF &Session', self.close_session)
        for act in (self.act_reasm, self.act_close_sess):
            act.setEnabled(False)
        filem.addSeparator()
        self._add_action(filem, '&Save', self.save_dtb,
                         QKeySequence.StandardKey.Save)
        self._add_action(filem, 'Save Copy &As...', self.save_dtb_as,
                         QKeySequence.StandardKey.SaveAs)
        self._add_action(filem, 'Export &DTS...', self.export_dts)
        self._add_action(filem, 'Save Change &Report...', self.save_change_report)
        filem.addSeparator()
        self._add_action(filem, 'E&xit', self.close)

        editm = bar.addMenu('&Edit')
        self.act_undo = self._add_action(editm, '&Undo', self.undo,
                                         QKeySequence.StandardKey.Undo)
        self.act_redo = self._add_action(editm, '&Redo', self.redo,
                                         QKeySequence.StandardKey.Redo)

        searchm = bar.addMenu('&Search')
        self._add_action(searchm, '&Find...', self.open_find,
                         QKeySequence.StandardKey.Find)
        self._add_action(searchm, 'Find &Next', self.find_next,
                         QKeySequence(Qt.Key.Key_F3))

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
        self.act_raw = self._add_action(viewm, '&Raw View', self._toggle_raw)
        self.act_raw.setCheckable(True)
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
        if path.lower().endswith(('.dtb', '.dtbo')):
            self.load_dtb(path)
        else:
            self.load_elf(path)

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
    # config-ELF sessions
    # ------------------------------------------------------------------

    def open_elf(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Open Config ELF', '',
            'Config ELF (*.elf);;All Files (*)')
        if filename:
            self.load_elf(filename)

    def load_elf(self, filename):
        self.close_session()
        session = ElfSession(filename)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            session.disassemble()
        except Exception as ex:  # noqa: BLE001
            session.close()
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, 'Failed to disassemble',
                                 getattr(ex, 'message', str(ex)))
            return
        QApplication.restoreOverrideCursor()
        self.session = session
        self.dtb_list.clear()
        for display in session.dtbs:
            self.dtb_list.addItem(display)
        self.dtb_dock.show()
        self.act_reasm.setEnabled(True)
        self.act_close_sess.setEnabled(True)
        self.statusBar().showMessage(
            '%d DTBs in %s - double-click one to edit'
            % (len(session.dtbs), os.path.basename(filename)))

    def _dtb_chosen(self, item):
        if self.session is None:
            return
        self._flush_current_dtb()
        self.load_dtb(self.session.dtbs[item.text()])

    def _flush_current_dtb(self):
        """Persist in-memory DTB edits to the session temp dir (tk parity:
        edits are auto-saved when switching DTBs or reassembling)."""
        if (self.session is not None and self.dtw.has_file()
                and self.dtw.fdt_name.startswith(self.session.outdir)):
            with open(self.dtw.fdt_name, 'wb') as fp:
                fp.write(self.dtw.dtb)

    def reassemble_elf(self):
        if self.session is None:
            return
        self._flush_current_dtb()
        suggested = os.path.basename(self.session.elf_path)
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Reassemble (unsigned) ELF as', suggested,
            'Config ELF (*.elf);;All Files (*)')
        if not filename:
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.session.reassemble_unsigned(filename)
        except Exception as ex:  # noqa: BLE001
            QMessageBox.critical(self, 'Failed to reassemble',
                                 getattr(ex, 'message', str(ex)))
            return
        finally:
            QApplication.restoreOverrideCursor()
        self.statusBar().showMessage('Reassembled (unsigned) to %s'
                                     % filename, 10000)

    def close_session(self):
        if self.session is None:
            return
        self._flush_current_dtb()
        self.session.close()
        self.session = None
        self.dtb_list.clear()
        self.dtb_dock.hide()
        self.act_reasm.setEnabled(False)
        self.act_close_sess.setEnabled(False)

    def closeEvent(self, event):
        self.close_session()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # saving
    # ------------------------------------------------------------------

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

    def save_change_report(self):
        if not self._require_file():
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Save Change Report', 'changes.json',
            'JSON (*.json);;All Files (*)')
        if not filename:
            return
        try:
            with open(filename, 'w', encoding='utf-8') as fp:
                fp.write(self.dtw.report())
            self.statusBar().showMessage('Saved change report to %s' % filename,
                                         5000)
        except OSError as ex:
            QMessageBox.critical(self, 'Failed to save report', str(ex))

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
        # Never undo past the LOAD of a session DTB (tk parity:
        # controller blocks it while an XBL session is open).
        if (fn == self.model.undo_op and self.session is not None):
            op = self.dtw.top_undo()
            if op is not None and op.optype == dt.DTOperationType.LOAD:
                self.statusBar().showMessage(
                    'Cannot undo the session load', 5000)
                return
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
            menu.addAction('Copy Node...', lambda: self._copy_node(path))
            if path != '/':
                menu.addAction('Delete', lambda: self._delete_item(path, False))
        menu.addSeparator()
        menu.addAction('Show in Raw View', lambda: self._show_in_raw(path))
        hl = menu.addMenu('Highlight')
        for name, color in _HIGHLIGHT_PRESETS:
            hl.addAction(name,
                         lambda c=color: self.model.set_highlight(path, QColor(c)))
        hl.addAction('Custom...', lambda: self._highlight_custom(path))
        hl.addSeparator()
        hl.addAction('Clear', lambda: self.model.set_highlight(path, None))
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _highlight_custom(self, path):
        current = self.model.highlight_color(path) or QColor('yellow')
        color = QColorDialog.getColor(current, self, 'Highlight color')
        if color.isValid():
            self.model.set_highlight(path, color)

    def _copy_node(self, node_path):
        """Port of controller.copy_node: prompt for a destination path,
        validate it, and apply a COPY_NODE op."""
        dest, ok = QInputDialog.getText(self, 'Copy Node', 'Path of new node:',
                                        text=node_path + '_copy')
        if not ok or dest is None:
            return
        if len(dest) <= 1 or '/' not in dest or '//' in dest or '?' in dest:
            QMessageBox.critical(self, 'Failed to copy node',
                                 'The given path is not valid.')
            return
        dest = dest.rstrip('/')
        child_name = dest.rsplit('/', 1)[1]
        parent_path = dest.rsplit('/', 1)[0] or '/'
        parent = self.dtw.resolve_path(parent_path)
        if parent is None or not parent.is_node():
            if QMessageBox.question(
                    self, 'Create New Path',
                    'The requested path does not exist. Create it?') \
                    != QMessageBox.StandardButton.Yes:
                return
        self._apply_checked(dt.DTOperation.make(
            dt.DTOperationType.COPY_NODE, parent_path, node_path,
            child_name, dest))

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
    # find / search
    # ------------------------------------------------------------------

    def open_find(self):
        if self._find_dialog is None:
            self._find_dialog = FindDialog(self)
            self._find_dialog.findNext.connect(self.find_next)
        self._find_dialog.open_for()

    def select_path(self, path):
        """Select and scroll to a path in the tree, expanding ancestors."""
        index = self.model.index_for_path(path)
        if not index.isValid():
            return
        self.tree.setCurrentIndex(index)
        self.tree.scrollTo(index)

    def _current_path(self):
        index = self.tree.currentIndex()
        return self.model.path_for_index(index) if index.isValid() else None

    def find_next(self, opts=None):
        """Port of controller.find_next onto the Qt model: walk the tree in
        document order from after the current selection, wrapping around."""
        if isinstance(opts, dict) and 'str' in opts:
            self._last_find = opts
        else:
            opts = self._last_find
        if opts is None or not self.dtw.has_file():
            return

        needle = opts['str'] if opts['matchCase'] else opts['str'].lower()
        prep = (lambda s: s) if opts['matchCase'] else (lambda s: s.lower())

        current = self._current_path()
        find_idx = 0 if (current is None or current == '/') else -1
        found = []
        for path, item in self.dtw.resolve_path('/').walk():
            if opts['searchNames'] and needle in prep(path):
                found.append(path)
                if find_idx >= 0:
                    break
            elif (opts['searchValues'] and item.is_property()
                  and needle in prep(item.to_pretty())):
                found.append(path)
                if find_idx >= 0:
                    break
            if path == current:
                find_idx = len(found)

        if not found:
            QMessageBox.information(self, 'No results found',
                                    "Cannot find '%s' in the device tree."
                                    % opts['str'])
            return
        self.select_path(found[find_idx % len(found)])

    # ------------------------------------------------------------------
    # view state
    # ------------------------------------------------------------------

    def _set_hex(self, as_hex):
        gf['viewAsHex'] = as_hex
        self.model.refresh_values()

    # ------------------------------------------------------------------
    # raw (hex) view
    # ------------------------------------------------------------------

    def _toggle_raw(self, checked):
        self.hex_dock.setVisible(checked)
        if checked:
            self._refresh_hex()
            self._highlight_current_in_hex()

    def _hex_visibility_changed(self, visible):
        # Keep the menu check in sync when the dock is closed via its own
        # title-bar button (guard against feedback with the action state).
        if self.act_raw.isChecked() != visible:
            self.act_raw.setChecked(visible)

    def _raw_on(self):
        return self.act_raw.isChecked()

    def _refresh_hex(self):
        if self._raw_on():
            self.hexview.set_data(self.dtw.dtb if self.dtw.has_file() else b'')

    def _highlight_current_in_hex(self):
        if not self._raw_on():
            return
        path = self._current_path()
        span = self.dtw.dtb_mappings.get(path) if path else None
        if span:
            self.hexview.highlight_range(span[0], span[1])
        else:
            self.hexview.highlight_range(None, None)

    def _show_in_raw(self, path):
        if not self._raw_on():
            self.act_raw.setChecked(True)
            self._toggle_raw(True)
        self.select_path(path)
        span = self.dtw.dtb_mappings.get(path)
        if span:
            self.hexview.highlight_range(span[0], span[1])

    def _selection_changed(self, _current, _previous):
        self._highlight_current_in_hex()

    def _after_operation(self, _path):
        self._update_title()
        self._update_undoredo()
        self._refresh_hex()
        self._highlight_current_in_hex()

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
