# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""``python -m qdte`` entry point."""
import sys

from qdte.cli.main import main

if __name__ == '__main__':
    sys.exit(main())
