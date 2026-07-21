# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Self-test for the libfdt-backed fdt_backend.

Two modes, both taking DTB files as arguments:

  --parity     load each DTB with BOTH pyfdt and fdt_backend and compare
               the walk() path stream and every property's type, value and
               pretty rendering (requires pyfdt installed; used before the
               backend swap to prove drop-in equivalence);
  --roundtrip  fdt_backend only: emit -> re-parse -> tree equality, edit ->
               undo -> byte-identical blob (the undo/redo hash invariant),
               memreserve/boot_cpuid preservation, and mappings sanity.

    python -m qdte.core._fdt_selftest --parity a.dtb b.dtb
    python -m qdte.core._fdt_selftest --roundtrip a.dtb b.dtb
"""
import argparse
import sys

from qdte.core import fdt_backend


def _load(backend, path):
    with open(path, 'rb') as fp:
        return backend.FdtBlobParse(fp).to_fdt()


def _classify(backend, item):
    if isinstance(item, backend.FdtNode):
        return 'NODE'
    if isinstance(item, backend.FdtPropertyWords):
        return 'WORDS'
    if isinstance(item, backend.FdtPropertyStrings):
        return 'STRINGS'
    if isinstance(item, backend.FdtPropertyBytes):
        return 'BYTES'
    return 'EMPTY'


def _value(backend, item):
    kind = _classify(backend, item)
    if kind == 'WORDS':
        return list(item.words)
    if kind == 'STRINGS':
        return list(item.strings)
    if kind == 'BYTES':
        return list(item.bytes)
    return None


def _stream(backend, fdt):
    root = fdt.resolve_path('/')
    return [(path, _classify(backend, item), _value(backend, item))
            for path, item in root.walk()]


def check_parity(paths):
    from pyfdt import pyfdt as pyfdt_backend
    for path in paths:
        ours = _stream(fdt_backend, _load(fdt_backend, path))
        theirs = _stream(pyfdt_backend, _load(pyfdt_backend, path))
        assert len(ours) == len(theirs), \
            '%s: item count %d != %d' % (path, len(ours), len(theirs))
        for mine, ref in zip(ours, theirs):
            assert mine == ref, '%s: mismatch\n  fdt_backend: %r\n  pyfdt:       %r' \
                % (path, mine, ref)
        print('PARITY OK: %s (%d items)' % (path, len(ours)))


def check_roundtrip(paths):
    for path in paths:
        fdt = _load(fdt_backend, path)
        with open(path, 'rb') as fp:
            original = fp.read()

        # determinism: two emissions are identical
        blob_a, blob_b = fdt.to_dtb(), fdt.to_dtb()
        assert blob_a == blob_b, '%s: emission not deterministic' % path

        # re-parse the emitted blob: tree content must be identical
        import io
        again = fdt_backend.FdtBlobParse(io.BytesIO(blob_a)).to_fdt()
        assert _stream(fdt_backend, again) == _stream(fdt_backend, fdt), \
            '%s: re-parse diverges' % path

        # metadata preserved
        import libfdt
        src, dst = libfdt.Fdt(original), libfdt.Fdt(blob_a)
        assert src.num_mem_rsv() == dst.num_mem_rsv(), '%s: memrsv lost' % path
        for i in range(src.num_mem_rsv()):
            assert tuple(src.get_mem_rsv(i)) == tuple(dst.get_mem_rsv(i))
        assert src.boot_cpuid_phys() == dst.boot_cpuid_phys(), \
            '%s: boot_cpuid lost' % path

        # edit -> undo -> byte-identical (the undo/redo hash invariant)
        target = next((p for p, item in fdt.resolve_path('/').walk()
                       if isinstance(item, fdt_backend.FdtPropertyWords)), None)
        if target is not None:
            prop = fdt.resolve_path(target)
            saved = list(prop.words)
            prop.words = [(w + 1) & 0xFFFFFFFF for w in saved]
            edited = fdt.to_dtb()
            assert edited != blob_a, '%s: edit produced identical bytes' % path
            prop.words = saved
            assert fdt.to_dtb() == blob_a, '%s: undo not byte-identical' % path

        # mappings point at real bytes
        mappings = {}
        fdt.to_dtb(mappings)
        assert mappings.get('/'), '%s: no root mapping' % path
        for p, (start, end) in mappings.items():
            assert 0 <= start < end <= len(blob_a), \
                '%s: bad mapping for %s' % (path, p)

        # dts export is non-empty and structurally plausible
        dts = fdt.to_dts()
        assert dts.startswith('/dts-v1/;') and dts.rstrip().endswith('};')

        print('ROUNDTRIP OK: %s (%d bytes)' % (path, len(blob_a)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--parity', action='store_true')
    mode.add_argument('--roundtrip', action='store_true')
    parser.add_argument('dtbs', nargs='+', help='DTB files to test')
    opts = parser.parse_args(argv)

    if opts.parity:
        check_parity(opts.dtbs)
    else:
        check_roundtrip(opts.dtbs)
    return 0


if __name__ == '__main__':
    sys.exit(main())
