# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Offscreen functional smoke for the Qt frontend.

Drives the real DtTreeModel and ElfSession (no widgets shown) against a
config ELF: disassemble, edit one property THROUGH the model, exercise
undo/redo, reassemble unsigned. Run under QT_QPA_PLATFORM=offscreen:

    python -m qdte_lite.gui_qt._smoke --elf uefi_dtbs.elf \
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
    parser.add_argument("--elf", required=True, help="input config ELF")
    parser.add_argument("--dtb", required=True, help="DTB name inside the ELF")
    parser.add_argument("--prop", required=True, help="property path to edit")
    parser.add_argument("--value", required=True, help="new value (model text)")
    parser.add_argument("--out", required=True, help="reassembled ELF destination")
    opts = parser.parse_args(argv)

    # Seed the global flags exactly like qdte_lite.cli.main does, so core code
    # never hits a missing key (verifyHash, dryRun, sectoolsDir, ...).
    from qdte_lite.core import flags as gflags

    args = gflags.build_parser().parse_args(["--allow_unsigned"])
    gflags.store(args)
    gflags.flags["testexp"] = False

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    import json

    from PySide6.QtGui import QColor

    import qdte_lite.core.dtwrapper as dt
    from qdte_lite.gui_qt.elfsession import ElfSession
    from qdte_lite.gui_qt.mainwindow import MainWindow

    QApplication([])  # validates the (offscreen) platform plugin loads

    session = ElfSession(opts.elf)
    dtbs = session.disassemble()
    assert opts.dtb in dtbs, "DTB %r not found; have: %s" % (opts.dtb, list(dtbs))

    # Drive the real window/model so the full GUI wiring is exercised.
    win = MainWindow()
    model, dtw = win.model, win.dtw
    win.load_dtb(dtbs[opts.dtb])

    idx = model.index_for_path(opts.prop)
    assert idx.isValid(), "property %r not in model" % opts.prop
    vidx = idx.siblingAtColumn(2)

    assert model.setData(vidx, opts.value, Qt.EditRole), "setData failed"
    edited = model.data(vidx, Qt.DisplayRole)

    # journal roundtrip: the edit must survive undo/redo
    model.undo_op()
    model.redo_op()
    assert model.data(vidx, Qt.DisplayRole) == edited, "undo/redo mismatch"

    # find locates the edited property by name
    win.tree.clearSelection()
    win.find_next(
        {
            "str": opts.prop.rsplit("/", 1)[1],
            "searchNames": True,
            "searchValues": False,
            "matchCase": False,
        }
    )
    assert win._current_path() == opts.prop, "find missed the property"

    # raw view renders and the mapping highlights a real byte range
    win.act_raw.setChecked(True)
    win._toggle_raw(True)
    assert win.hexview.toPlainText().startswith("00000000  "), "hex not rendered"
    span = dtw.dtb_mappings.get(opts.prop)
    assert span and 0 <= span[0] < span[1] <= len(dtw.dtb), "bad hex mapping"
    win._show_in_raw(opts.prop)
    assert win.hexview.extraSelections(), "no hex highlight"

    # highlight set/clear
    model.set_highlight(opts.prop, QColor("#00d400"))
    assert model.highlight_color(opts.prop) is not None
    model.set_highlight(opts.prop, None)
    assert model.highlight_color(opts.prop) is None

    # Copy Node apply+undo on the property's parent node
    parent = opts.prop.rsplit("/", 1)[0]
    gp = parent.rsplit("/", 1)[0] or "/"
    copy_path = parent + "_smokecopy"
    model.apply_op(
        dt.DTOperation.make(
            dt.DTOperationType.COPY_NODE,
            gp,
            parent,
            copy_path.rsplit("/", 1)[1],
            copy_path,
        )
    )
    assert model.index_for_path(copy_path).isValid(), "copy node failed"
    model.undo_op()
    assert not model.index_for_path(copy_path).isValid(), "copy undo failed"

    # change report is valid JSON recording the edit
    report = json.loads(dtw.report())
    assert isinstance(report, list) and any(
        e.get("operation") == "EDIT_PROPERTY_VALUE" for e in report
    ), report

    # flush the DTB back into the session tree and rebuild the ELF
    with open(dtw.fdt_name, "wb") as fp:
        fp.write(dtw.dtb)
    session.reassemble_unsigned(opts.out)
    session.close()

    assert os.path.isfile(opts.out), "no output produced"
    print(
        "QT SMOKE OK: %s -> %s (%s = %s); find/hex/highlight/copy/report OK"
        % (opts.elf, opts.out, opts.prop, edited)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
