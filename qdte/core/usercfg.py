# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Persistent user configuration (tool paths) for the GUI.

Stores the signing/tool paths in gl_info['user_cfg'] (a per-user JSON
file) and syncs them with the global flags dict. This is the successor
of the tk settings module's Json_Operate, trimmed to the keys anything
still reads: sectoolsDir, profileXml, signJson (signing), plus
xbltoolsDir and inputFile (dialog pre-fill).
"""
import json
import os

from qdte.core import dtlogger
from qdte.core.flags import flags as gf
from qdte.core.flags import global_info as gl_info
from qdte.core.flags import default_xbl_tools_dir

PATH_KEYS = ('xbltoolsDir', 'inputFile', 'sectoolsDir', 'profileXml', 'signJson')
SIGNING_KEYS = ('sectoolsDir', 'profileXml', 'signJson')


class UserConfig:

    def __init__(self):
        self.filename = gl_info['user_cfg']

    def _read(self):
        try:
            with open(self.filename, mode='r', encoding='utf-8') as fp:
                data = json.load(fp)
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def load_into_flags(self):
        """Populate gf with the persisted paths (existing files only)."""
        paths = self._read().get('paths', {})
        for key in PATH_KEYS:
            value = paths.get(key)
            if value and os.path.exists(value):
                gf[key] = value
        # The bundled XBLConfig tools always win over a stale stored path.
        gf['xbltoolsDir'] = default_xbl_tools_dir()

    def get(self, key):
        """Return the persisted value for ``key`` ('' if unset/vanished)."""
        value = self._read().get('paths', {}).get(key, '')
        if value and key in PATH_KEYS and not os.path.exists(value):
            return ''
        return value or ''

    def store_from_flags(self):
        """Persist the current gf path values."""
        data = self._read()
        paths = data.setdefault('paths', {})
        for key in PATH_KEYS:
            if gf.get(key):
                paths[key] = gf[key]
        try:
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            with open(self.filename, mode='w', encoding='utf-8') as fp:
                json.dump(data, fp, indent=4, separators=(',', ': '))
        except OSError as ex:
            dtlogger.info('Error writing user cfg file: %s' % ex)

    def signing_ready(self):
        """True when every path the signed flow needs is set and exists."""
        return all(gf.get(key) and os.path.exists(gf[key])
                   for key in SIGNING_KEYS)
