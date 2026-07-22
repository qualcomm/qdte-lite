#!/usr/bin/env python3

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Thin launcher for QDTE.

All logic lives in qdte.cli.main.  --nogui runs never import the GUI
(PySide6), so QDTE works headless with no GUI toolkit installed.
"""
import sys

from qdte.cli.main import main

if __name__ == '__main__':
    sys.exit(main())
