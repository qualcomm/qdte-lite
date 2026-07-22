# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Read-only raw (hex) view of the serialized DTB.

Renders dtw.dtb as a classic hex dump (offset | 16 bytes | ASCII) and
highlights the byte range of a given path using dtw.dtb_mappings, which
the libfdt backend populates on every to_dtb().  Lives in a dock so it
can sit beside the tree; the window keeps its content in sync via the
model's operationApplied signal.
"""

from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit

_BYTES_PER_ROW = 16
# One row renders as: "%08x  " (10) + 16*3 hex cols (48) + " " gutter (1) + 16 ASCII
_OFFSET_COLS = 10
_HEX_COLS = _BYTES_PER_ROW * 3
_ASCII_GAP = 1


class HexView(QPlainTextEdit):
    """Monospace hex dump with path-range highlighting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        font = QFont("monospace")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.setFont(font)
        self._data = b""

    def set_data(self, data):
        self._data = bytes(data or b"")
        self._render()

    def _render(self):
        lines = []
        data = self._data
        for base in range(0, len(data), _BYTES_PER_ROW):
            chunk = data[base : base + _BYTES_PER_ROW]
            hex_part = " ".join("%02x" % b for b in chunk)
            hex_part = hex_part.ljust(_HEX_COLS - 1)
            ascii_part = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
            lines.append("%08x  %s %s" % (base, hex_part, ascii_part))
        self.setPlainText("\n".join(lines))

    def _row_col(self, offset, in_ascii):
        """(block, column) of byte ``offset`` in the rendered text."""
        row = offset // _BYTES_PER_ROW
        col_in_row = offset % _BYTES_PER_ROW
        if in_ascii:
            column = _OFFSET_COLS + _HEX_COLS + _ASCII_GAP + col_in_row
        else:
            column = _OFFSET_COLS + col_in_row * 3
        return row, column

    def highlight_range(self, start, end):
        """Select and scroll to bytes [start, end) across both columns."""
        if not self._data or start is None or start >= end:
            self.setExtraSelections([])
            return
        end = min(end, len(self._data))
        selections = []
        highlight = QColor(60, 120, 215)
        doc = self.document()
        for in_ascii in (False, True):
            # Highlight per row so multi-row ranges stay within columns.
            row = start // _BYTES_PER_ROW
            first = start
            while first < end:
                row_end = min((row + 1) * _BYTES_PER_ROW, end)
                r0, c0 = self._row_col(first, in_ascii)
                # last highlighted byte on this row
                _, c1 = self._row_col(row_end - 1, in_ascii)
                cursor = QTextCursor(doc.findBlockByNumber(r0))
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, c0
                )
                span = (c1 + (1 if in_ascii else 2)) - c0
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right,
                    QTextCursor.MoveMode.KeepAnchor,
                    span,
                )
                sel = QTextEdit.ExtraSelection()
                fmt = QTextCharFormat()
                fmt.setBackground(highlight)
                fmt.setForeground(QColor("white"))
                sel.format = fmt
                sel.cursor = cursor
                selections.append(sel)
                first = row_end
                row += 1
        self.setExtraSelections(selections)
        # scroll the first highlighted row into view
        first_block = self.document().findBlockByNumber(start // _BYTES_PER_ROW)
        self.setTextCursor(QTextCursor(first_block))
        self.ensureCursorVisible()
