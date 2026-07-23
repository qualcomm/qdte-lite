# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""``python -m qdte_lite`` entry point."""

import sys

from qdte_lite.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
