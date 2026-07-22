# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Config-ELF editing session for the Qt frontend.

Wraps the qdte.core disassemble/reassemble machinery (the same
assemble.assemble methods the tkinter XblCfgGUI and the --nogui Autocmd
flow drive) around a temporary working directory, with no UI here.
"""
import atexit
import os
import shutil
import tempfile

from qdte.core import assemble
from qdte.core.flags import flags as gf

FDT_MAGIC = b'\xd0\x0d\xfe\xed'


def scan_disassembly(directory, prefix=''):
    """Find the DTB files a disassembly produced.

    Returns {display_name: absolute_path}, identifying DTBs by the FDT
    magic and recursing into ``*dtbs*`` subdirectories (mirroring the tk
    XblCfgGUI scan).
    """
    found = {}
    for name in sorted(os.listdir(directory)):
        full = os.path.join(directory, name)
        display = prefix + name
        if os.path.isfile(full):
            with open(full, 'rb') as fp:
                if fp.read(4) == FDT_MAGIC:
                    found[display] = full
        elif os.path.isdir(full) and 'dtbs' in name:
            found.update(scan_disassembly(full, display + '/'))
    return found


class ElfSession(assemble.assemble):
    """One open config ELF: temp dir, its DTBs, and native reassembly.

    Uses the same assemble core the headless Autocmd flow drives, so the
    GUI and CLI rebuild containers through one code path.
    """

    def __init__(self, elf_path):
        self.elf_path = os.path.abspath(elf_path)
        self.outdir = tempfile.mkdtemp(prefix='dtgui_')
        self.dtbs = {}
        self.compressed_elf = False
        atexit.register(self.close)

    def disassemble(self):
        """Disassemble the ELF into the temp dir and index its DTBs."""
        gf['inputFile'] = self.elf_path
        if self.dissamble_config_elf() is False:
            raise RuntimeError('Failed to disassemble %s' % self.elf_path)
        self.dtbs = scan_disassembly(self.outdir)
        if not self.dtbs:
            raise RuntimeError('No DTBs found in %s' % self.elf_path)
        return self.dtbs

    def reassemble_unsigned(self, dest_path):
        """Rebuild the (unsigned) ELF from the temp dir into dest_path."""
        dest_path = os.path.abspath(dest_path)
        gf['allowUnsigned'] = True
        gf['outputFile'] = os.path.basename(dest_path)
        gf['outputPath'] = os.path.dirname(dest_path)
        # reassemble_config_elf drops a copy of the artifact in the process
        # CWD; bracket it inside the temp dir so no stray file lands in
        # whatever directory the GUI happens to run from.
        cwd = os.getcwd()
        os.chdir(self.outdir)
        try:
            self.reassemble_config_elf()
        finally:
            os.chdir(cwd)
        built = os.path.join(self.outdir, 'auto_gen', 'elf_files',
                             'create_cli', gf['outputFile'])
        shutil.copy(built, dest_path)
        return dest_path

    def close(self):
        atexit.unregister(self.close)
        if self.outdir and os.path.isdir(self.outdir):
            shutil.rmtree(self.outdir, ignore_errors=True)
        self.outdir = None
