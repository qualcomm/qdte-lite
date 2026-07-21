# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Command-line front-end for QDTE.

Parses arguments, stores them into the global flags, sets up the
optional profiling/coverage instrumentation and dispatches to either
the headless flow or the GUI.  The GUI (and with it tkinter and the
heavier GUI-only dependencies) is imported lazily, only when a GUI run
was actually requested.
"""
import importlib.util
import sys

from qdte.core import flags as gflags

# Optional-dependency roots the GUIs may legitimately be missing. An
# ImportError for anything else is a real bug and must not be swallowed.
_OPTIONAL_GUI_MODULES = ('tkinter', 'fs', 'pyfatfs', 'PySide6')

_GUI_DEPS_HINT = """\
QDTE's GUI needs optional dependencies that are not installed (missing: {name}).

  Qt frontend:      pip install "qdte-lite[qt]"
  tkinter frontend: pip install "qdte-lite[gui]", plus the Tcl/Tk bindings
                    from your Python distribution (Debian/Ubuntu:
                    python3-tk; Fedora/Yocto: python3-tkinter)

Headless mode needs neither:  qdte --nogui --help"""


def _dispatch(args):
    if gflags.flags['nogui']:
        from qdte.cli.headless import run_headless
        run_headless()
        return
    # Deliberately lazy imports: the ONLY places a GUI toolkit (PySide6 or
    # tkinter, plus fs/pyfatfs, QutsAtom on the tk side) enters the process.
    # Qt is the default frontend when PySide6 is installed; --tk forces the
    # legacy tkinter GUI. The find_spec probe (rather than try/except around
    # the import) keeps real qdte.gui_qt bugs from being masked as a silent
    # fallback to tk.
    try:
        if not gflags.flags['tk'] and importlib.util.find_spec('PySide6') is not None:
            from qdte.gui_qt.app import launch
        else:
            from qdte.gui.app import launch
    except ImportError as ex:
        root = (getattr(ex, 'name', None) or '').split('.')[0]
        if root in _OPTIONAL_GUI_MODULES:
            sys.exit(_GUI_DEPS_HINT.format(name=root))
        raise
    launch(initial_file=args.file)


def main(argv=None):
    parser = gflags.build_parser()
    args = parser.parse_args(argv)

    # store the flags
    gflags.store(args)
    gflags.flags['testexp'] = bool(args.test_exp)

    # check how this should be run
    if gflags.flags['profile']:
        try:
            import cProfile as profile
        except ImportError:
            print('Warning! cProfile is not available on this system. profile will be used instead.')
            import profile

        outfile = gflags.flags['profile'] if isinstance(gflags.flags['profile'], str) else None
        profile.runctx('_dispatch(args)', globals(), locals(), outfile)
        return 0

    cov = None
    if gflags.flags['profileMem']:
        try:
            from pympler import muppy, summary  # noqa: F401 -- availability probe
        except ImportError:
            print('Warning! pympler is not available on this system. tracemalloc will be used instead.')
            import tracemalloc
            tracemalloc.start()
    elif gflags.flags['coverage']:
        try:
            import coverage

            if isinstance(gflags.flags['coverage'], str):
                cov = coverage.Coverage(data_file=gflags.flags['coverage'])
            else:
                cov = coverage.Coverage()
            cov.start()
        except ImportError:
            print('Error! coverage is not available on this system, so coverage CANNOT be tested!')
            return 1

    _dispatch(args)

    if cov:
        cov.stop()
        cov.save()
    return 0
