# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Settings dialog: the tool paths the signed-export flow needs."""
import os

from PySide6.QtWidgets import (QDialogButtonBox, QDialog, QFileDialog,
                               QGridLayout, QLabel, QLineEdit, QPushButton)

from qdte.core.flags import flags as gf
from qdte.core.usercfg import UserConfig

# (gf key, label, is_directory)
_FIELDS = (
    ('sectoolsDir', 'SecTools directory', True),
    ('profileXml', 'Security profile XML', False),
    ('signJson', 'Signing command JSON', False),
)


class SettingsDialog(QDialog):
    """Edit and persist the signing tool paths via UserConfig."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self._cfg = UserConfig()
        self._edits = {}

        grid = QGridLayout(self)
        for row, (key, label, is_dir) in enumerate(_FIELDS):
            grid.addWidget(QLabel(label + ':'), row, 0)
            edit = QLineEdit(gf.get(key) or '', self)
            self._edits[key] = edit
            grid.addWidget(edit, row, 1)
            browse = QPushButton('Browse...', self)
            browse.clicked.connect(
                lambda _=False, k=key, d=is_dir: self._browse(k, d))
            grid.addWidget(browse, row, 2)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        grid.addWidget(buttons, len(_FIELDS), 0, 1, 3)

    def _browse(self, key, is_dir):
        start = self._edits[key].text() or os.path.expanduser('~')
        if is_dir:
            path = QFileDialog.getExistingDirectory(self, 'Select directory',
                                                    start)
        else:
            path, _ = QFileDialog.getOpenFileName(self, 'Select file', start)
        if path:
            self._edits[key].setText(path)

    def _save(self):
        for key, edit in self._edits.items():
            gf[key] = edit.text().strip()
        self._cfg.store_from_flags()
        self.accept()
