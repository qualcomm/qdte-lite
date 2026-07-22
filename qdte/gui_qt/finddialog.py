# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Modeless Find dialog for the Qt frontend."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class FindDialog(QDialog):
    """Find-what entry with name/value/case options.

    Emits :attr:`findNext` with an options dict on each Find Next; the
    window owns the actual tree walk so the dialog stays UI-only.
    """

    findNext = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find")
        self.setWindowFlag(Qt.WindowType.Tool)

        self._entry = QLineEdit(self)
        self._names = QCheckBox("Search in &names", self)
        self._values = QCheckBox("Search in &values", self)
        self._case = QCheckBox("Match &case", self)
        self._names.setChecked(True)
        self._values.setChecked(True)

        find_btn = QPushButton("Find &Next", self)
        find_btn.setDefault(True)
        find_btn.clicked.connect(self._emit)
        close_btn = QPushButton("&Close", self)
        close_btn.clicked.connect(self.hide)

        layout = QVBoxLayout(self)
        layout.addWidget(self._entry)
        layout.addWidget(self._names)
        layout.addWidget(self._values)
        layout.addWidget(self._case)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(find_btn)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def _emit(self):
        text = self._entry.text()
        if not text:
            return
        self.findNext.emit(
            {
                "str": text,
                "searchNames": self._names.isChecked(),
                "searchValues": self._values.isChecked(),
                "matchCase": self._case.isChecked(),
            }
        )

    def open_for(self):
        """Show, raise and focus the entry (reused across invocations)."""
        self.show()
        self.raise_()
        self._entry.setFocus()
        self._entry.selectAll()
