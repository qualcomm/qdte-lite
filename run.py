#!/usr/bin/env python3

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Thin launcher for QDTE.

All logic lives in qdte.cli.main.  --nogui runs never import tkinter or
any qdte.gui module, so QDTE works headless where Tcl/Tk is absent.
"""
import sys

from qdte.cli.main import main

if __name__ == '__main__':
    sys.exit(main())
