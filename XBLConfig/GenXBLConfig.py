#!/usr/bin/env python

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

import subprocess
import sys
import os

if __name__ == "__main__":
  subprocess.call(["python",os.path.join(os.path.dirname(os.path.realpath(__file__)),"GenConfigImage.py")]+sys.argv[1:])
