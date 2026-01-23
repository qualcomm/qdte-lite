# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
import fs

fat_fs = fs.open_fs("C:\\Dropbox\\NON-HLOS.ima")  # Open disk image
host_fs = fs.open_fs("osfs:///tmp") # Open '/tmp' directory on host
fs.copy.copy_dir(fat_fs, "/", host_fs, "/") 