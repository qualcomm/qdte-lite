# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Qt item model over the DTWrapper-parsed device tree.

The model is the only Qt object that talks to :class:`DTWrapper`.  It is
pull-based, mirroring the tkinter TreeView contract: every mutation goes
through ``dtw.apply()`` (or undo/redo), whose return value -- the modified
path -- drives a targeted :meth:`refresh`.  Persistent references are
always path strings, never QModelIndex.

This module must not import QtWidgets; user interaction (dialogs, message
boxes) belongs to the window, wired via signals.
"""
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal

import qdte.core.dtwrapper as dt
from qdte.core.flags import flags as gf
from qdte.gui_qt import valueparse

COL_NAME, COL_TYPE, COL_VALUE = 0, 1, 2
_HEADERS = ('Name', 'Type', 'Value')


class _TNode:
    """One row of the tree: a DT node or property."""
    __slots__ = ('name', 'path', 'is_prop', 'type_str', 'value_str',
                 'parent', 'children')

    def __init__(self, name, path, parent):
        self.name = name
        self.path = path
        self.is_prop = False
        self.type_str = ''
        self.value_str = ''
        self.parent = parent
        self.children = []

    def row(self):
        return 0 if self.parent is None else self.parent.children.index(self)


def _describe(item):
    """(is_prop, type_str, value_str) for an FdtItem wrapper."""
    if item.is_property():
        return True, item.get_type().name, item.to_pretty()
    return False, 'Node', ''


class DtTreeModel(QAbstractItemModel):

    # Emitted after any dtw mutation applied through the model, with the
    # modified path (or None).  The window refreshes titles/menus from it.
    operationApplied = Signal(object)
    # Emitted when an inline edit could not be parsed/applied: (path, message).
    editFailed = Signal(str, str)

    def __init__(self, dtw, parent=None):
        super().__init__(parent)
        self.dtw = dtw
        self._root = None       # invisible root above '/'
        self._byPath = {}
        self.rebuild()

    # ------------------------------------------------------------------
    # mutations: every DTWrapper change goes through these
    # ------------------------------------------------------------------

    def apply_op(self, op):
        """Apply a DTOperation and refresh the affected rows."""
        path = self.dtw.apply(op)
        if op.optype == dt.DTOperationType.LOAD:
            self.rebuild()
        else:
            self.refresh(path)
        self.operationApplied.emit(path)
        return path

    def undo_op(self):
        path = self.dtw.undo()
        self.refresh(path)
        self.operationApplied.emit(path)
        return path

    def redo_op(self):
        path = self.dtw.redo()
        self.refresh(path)
        self.operationApplied.emit(path)
        return path

    # ------------------------------------------------------------------
    # build / refresh
    # ------------------------------------------------------------------

    def rebuild(self):
        """Full model reset from the current DTWrapper state."""
        self.beginResetModel()
        self._root = _TNode('', None, None)
        self._byPath = {}
        if self.dtw.has_file():
            top = _TNode('/', '/', self._root)
            self._root.children.append(top)
            self._byPath['/'] = top
            self._build_subtree(top)
        self.endResetModel()

    def _build_subtree(self, tnode):
        """Populate tnode's descendants from dtw (eager, like tk)."""
        base = self.dtw.resolve_path(tnode.path)
        if base is None or not base.is_node():
            return
        prefix = '' if tnode.path == '/' else tnode.path
        for path, item in base.walk():
            full = prefix + path
            parent_path = full.rsplit('/', 1)[0] or '/'
            parent = self._byPath.get(parent_path)
            if parent is None:
                continue
            child = _TNode(full.rsplit('/', 1)[1], full, parent)
            child.is_prop, child.type_str, child.value_str = _describe(item)
            parent.children.append(child)
            self._byPath[full] = child

    def index_for_path(self, path):
        tnode = self._byPath.get(path)
        if tnode is None:
            return QModelIndex()
        return self.createIndex(tnode.row(), 0, tnode)

    def refresh(self, path):
        """Mirror of the tk TreeView.update_fdt(path) contract."""
        if isinstance(path, list):
            for p in path:
                self.refresh(p)
            return
        if path is None or path == '/' or not self.dtw.has_file():
            self.rebuild()
            return

        item = self.dtw.resolve_path(path)
        known = self._byPath.get(path)

        if item is None:
            if known is not None:
                self._remove_row(known)
            return

        if known is not None and known.is_prop and item.is_property():
            # value change in place
            known.is_prop, known.type_str, known.value_str = _describe(item)
            idx = self.index_for_path(path)
            self.dataChanged.emit(idx.siblingAtColumn(COL_TYPE),
                                  idx.siblingAtColumn(COL_VALUE))
            return

        # node changed / new item: repopulate the parent subtree
        parent_path = path.rsplit('/', 1)[0] or '/'
        parent = self._byPath.get(parent_path)
        if parent is None:
            self.rebuild()
            return
        self._repopulate_children(parent)

    def _remove_row(self, tnode):
        parent = tnode.parent
        row = tnode.row()
        pidx = self.index_for_path(parent.path) if parent.path else QModelIndex()
        self.beginRemoveRows(pidx, row, row)
        parent.children.pop(row)
        self._purge(tnode)
        self.endRemoveRows()

    def _repopulate_children(self, parent_tnode):
        pidx = (self.index_for_path(parent_tnode.path)
                if parent_tnode.path else QModelIndex())
        if parent_tnode.children:
            self.beginRemoveRows(pidx, 0, len(parent_tnode.children) - 1)
            for c in parent_tnode.children:
                self._purge(c)
            parent_tnode.children = []
            self.endRemoveRows()
        # Build the new children into a detached shadow node first, so the
        # insert bracket is emitted with the final row count.
        shadow = _TNode(parent_tnode.name, parent_tnode.path, parent_tnode.parent)
        saved = dict(self._byPath)
        self._byPath[parent_tnode.path] = shadow
        self._build_subtree(shadow)
        new_paths = {k: v for k, v in self._byPath.items() if k not in saved}
        self._byPath = saved
        if shadow.children:
            self.beginInsertRows(pidx, 0, len(shadow.children) - 1)
            parent_tnode.children = shadow.children
            for c in parent_tnode.children:
                c.parent = parent_tnode
            self._byPath.update(new_paths)
            self._byPath[parent_tnode.path] = parent_tnode
            self.endInsertRows()

    def _purge(self, tnode):
        self._byPath.pop(tnode.path, None)
        for c in tnode.children:
            self._purge(c)

    def refresh_values(self):
        """Hex/dec toggle: recompute every property's display string."""
        def visit(tnode):
            changed_rows = []
            for c in tnode.children:
                if c.is_prop:
                    item = self.dtw.resolve_path(c.path)
                    if item is not None:
                        c.value_str = item.to_pretty()
                        changed_rows.append(c)
                else:
                    visit(c)
            if changed_rows:
                first, last = changed_rows[0], changed_rows[-1]
                self.dataChanged.emit(
                    self.createIndex(first.row(), COL_VALUE, first),
                    self.createIndex(last.row(), COL_VALUE, last))
        if self._root.children:
            visit(self._root.children[0])

    # ------------------------------------------------------------------
    # QAbstractItemModel plumbing
    # ------------------------------------------------------------------

    def index(self, row, column, parent=QModelIndex()):
        ptnode = parent.internalPointer() if parent.isValid() else self._root
        if 0 <= row < len(ptnode.children):
            return self.createIndex(row, column, ptnode.children[row])
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        tnode = index.internalPointer()
        parent = tnode.parent
        if parent is None or parent is self._root:
            return QModelIndex()
        return self.createIndex(parent.row(), 0, parent)

    def rowCount(self, parent=QModelIndex()):
        ptnode = parent.internalPointer() if parent.isValid() else self._root
        return len(ptnode.children)

    def columnCount(self, parent=QModelIndex()):
        return len(_HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return _HEADERS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        tnode = index.internalPointer()
        if role in (Qt.DisplayRole, Qt.EditRole):
            if index.column() == COL_NAME:
                return tnode.name
            if index.column() == COL_TYPE:
                return tnode.type_str
            if index.column() == COL_VALUE:
                return tnode.value_str
        if role == Qt.ToolTipRole:
            return tnode.path
        return None

    def path_for_index(self, index):
        return index.internalPointer().path if index.isValid() else None

    def flags(self, index):
        base = super().flags(index)
        if not index.isValid():
            return base
        tnode = index.internalPointer()
        if (index.column() == COL_VALUE and tnode.is_prop
                and tnode.type_str != 'EMPTY' and not gf['readonly']):
            return base | Qt.ItemIsEditable
        return base

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid():
            return False
        tnode = index.internalPointer()
        if not tnode.is_prop:
            return False
        item = self.dtw.resolve_path(tnode.path)
        if item is None or not item.is_property():
            return False
        try:
            payload = valueparse.parse_value(item.get_type(), str(value))
            self.apply_op(dt.DTOperation.make(
                dt.DTOperationType.EDIT_PROPERTY_VALUE, tnode.path, payload))
        except Exception as ex:  # noqa: BLE001 -- surfaced to the user
            self.editFailed.emit(tnode.path, getattr(ex, 'message', str(ex)))
            return False
        return True
