# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""The --nogui execution path.

Deliberately imports only qdte_lite.core -- never qdte_lite.gui_qt or PySide6 --
so QDTE runs headless on minimal sysroots with no GUI toolkit installed.
"""

import os
import sys
import tempfile

import qdte_lite.core.dtwrapper as dt
from qdte_lite.core import Autocmd as cmd
from qdte_lite.core import assemble
from qdte_lite.core.fdt_backend import FdtBlobParse, FdtNode
from qdte_lite.core.flags import flags as gf


def find_property():
    """Print where a named property lives inside a config ELF.

    Disassembles --input_file and writes one line per match:

        <dtb>/<node path>/<property>

    <dtb> is the DTB's path relative to the disassembly directory, which is
    how --modify addresses it, so a line can be used as a --modify target
    verbatim:

        target=$(qdte-lite --nogui --input_file x.elf --find_property Foo)
        qdte-lite --nogui --input_file x.elf ... --modify "$target=0x1"

    The names a DTB gets are not derivable from the container alone -- one
    path takes them from container metadata, another from each DTB's
    /compatible -- so asking the tool that assigns them is the only way to
    address a property without hardcoding names per platform.

    Exits non-zero when the property is not found anywhere, so callers can
    branch on it.
    """

    name = gf["findProperty"]
    if not gf.get("inputFile"):
        sys.exit("--find_property requires --input_file")

    outdir = tempfile.mkdtemp(prefix="qdte-find-")
    dis = assemble.assemble()
    dis.outdir = outdir
    try:
        dis.dissamble_config_elf()
    except Exception as ex:
        sys.exit("could not disassemble %s: %s" % (gf["inputFile"], ex))

    found = False
    for root, _dirs, names in os.walk(outdir):
        for entry in sorted(names):
            if not entry.endswith((".dtb", ".dtbo")):
                continue
            path = os.path.join(root, entry)
            try:
                with open(path, "rb") as blob:
                    fdt = FdtBlobParse(blob).to_fdt()
            except Exception:
                # Not every file that looks like a DTB parses as one.
                continue
            rel = os.path.relpath(path, outdir)
            for node_path, item in fdt.root.walk():
                if not isinstance(item, FdtNode) and item.name == name:
                    print(rel + node_path)
                    found = True

    if not found:
        sys.exit(1)


def run_headless():
    if gf.get("findProperty"):
        find_property()
        return

    dtw = dt.DTWrapper()
    cmd.autocmd(dtw).execute()
