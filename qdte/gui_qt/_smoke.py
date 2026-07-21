# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Offscreen functional smoke for the Qt frontend.

Drives the real DtTreeModel and ElfSession (no widgets shown) against a
config ELF: disassemble, edit one property THROUGH the model, exercise
undo/redo, reassemble unsigned. Run under QT_QPA_PLATFORM=offscreen:

    python -m qdte.gui_qt._smoke --elf uefi_dtbs.elf \
        --dtb qcom,uefi-agatti-1.0.dtb \
        --prop /soc/quantum_dt/enter_quantum --value 0x1 \
        --out /tmp/out.elf

The caller verifies the produced ELF (e.g. with fdtdump). Also useful as
a local diagnostic for the installed package.
"""
import argparse
import os
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--elf', required=True, help='input config ELF')
    parser.add_argument('--dtb', required=True, help='DTB name inside the ELF')
    parser.add_argument('--prop', required=True, help='property path to edit')
    parser.add_argument('--value', required=True, help='new value (model text)')
    parser.add_argument('--out', required=True, help='reassembled ELF destination')
    opts = parser.parse_args(argv)

    # Seed the global flags exactly like qdte.cli.main does, so core code
    # never hits a missing key (verifyHash, dryRun, sectoolsDir, ...).
    from qdte.core import flags as gflags
    args = gflags.build_parser().parse_args(['--allow_unsigned'])
    gflags.store(args)
    gflags.flags['testexp'] = False

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    import qdte.core.dtwrapper as dt
    from qdte.gui_qt.elfsession import ElfSession
    from qdte.gui_qt.treemodel import DtTreeModel

    QApplication([])  # validates the (offscreen) platform plugin loads

    session = ElfSession(opts.elf)
    dtbs = session.disassemble()
    assert opts.dtb in dtbs, 'DTB %r not found; have: %s' % (opts.dtb, list(dtbs))

    dtw = dt.DTWrapper()
    model = DtTreeModel(dtw)
    model.apply_op(dt.DTOperation.make(dt.DTOperationType.LOAD, dtbs[opts.dtb]))

    idx = model.index_for_path(opts.prop)
    assert idx.isValid(), 'property %r not in model' % opts.prop
    vidx = idx.siblingAtColumn(2)

    assert model.setData(vidx, opts.value, Qt.EditRole), 'setData failed'
    edited = model.data(vidx, Qt.DisplayRole)

    # journal roundtrip: the edit must survive undo/redo
    model.undo_op()
    model.redo_op()
    assert model.data(vidx, Qt.DisplayRole) == edited, 'undo/redo mismatch'

    # flush the DTB back into the session tree and rebuild the ELF
    with open(dtw.fdt_name, 'wb') as fp:
        fp.write(dtw.dtb)
    session.reassemble_unsigned(opts.out)
    session.close()

    assert os.path.isfile(opts.out), 'no output produced'
    print('QT SMOKE OK: %s -> %s (%s = %s)'
          % (opts.elf, opts.out, opts.prop, edited))
    return 0


if __name__ == '__main__':
    sys.exit(main())
