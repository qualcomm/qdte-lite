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


def _disassemble(what):
    """Disassemble --input_file into a fresh temporary directory.

    :param what: option name, used only in the error messages
    :return: path to the directory holding the disassembled parts
    """

    if not gf.get("inputFile"):
        sys.exit("%s requires --input_file" % what)

    outdir = tempfile.mkdtemp(prefix="qdte-inspect-")
    dis = assemble.assemble()
    dis.outdir = outdir
    try:
        dis.dissamble_config_elf()
    except Exception as ex:
        sys.exit("could not disassemble %s: %s" % (gf["inputFile"], ex))
    return outdir


def _iter_dtbs(outdir):
    """Yield (name, parsed tree) for every DTB found in a disassembly.

    The name is the DTB's path relative to the disassembly directory, which
    is how --modify addresses it.  Files that do not parse as a device tree
    are skipped rather than reported: a container holds other kinds of
    payload too.
    """

    for root, _dirs, names in os.walk(outdir):
        for entry in sorted(names):
            if not entry.endswith((".dtb", ".dtbo")):
                continue
            path = os.path.join(root, entry)
            try:
                with open(path, "rb") as blob:
                    fdt = FdtBlobParse(blob).to_fdt()
            except Exception:
                continue
            yield os.path.relpath(path, outdir), fdt


def list_dtbs():
    """Print the name of every DTB in --input_file, one per line.

    The names are what --modify expects, so this answers "what can I edit in
    this container" without having to unpack it by hand.  Exits non-zero if
    the container holds no device tree at all.
    """

    found = False
    for name, _fdt in _iter_dtbs(_disassemble("--list")):
        print(name)
        found = True

    if not found:
        sys.exit(1)


def find_property():
    """Print where a named property lives inside --input_file.

    Writes one line per match:

        <dtb>/<node path>/<property>

    which is exactly what --modify expects, so a line can be used as a
    target verbatim:

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
    found = False
    for dtb, fdt in _iter_dtbs(_disassemble("--find_property")):
        for node_path, item in fdt.root.walk():
            if not isinstance(item, FdtNode) and item.name == name:
                print(dtb + node_path)
                found = True

    if not found:
        sys.exit(1)


def run_headless():
    if gf.get("list"):
        list_dtbs()
        return

    if gf.get("findProperty"):
        find_property()
        return

    dtw = dt.DTWrapper()
    cmd.autocmd(dtw).execute()
