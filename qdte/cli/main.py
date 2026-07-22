# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Command-line front-end for QDTE.

Parses arguments, stores them into the global flags, sets up the
optional profiling/coverage instrumentation and dispatches to either
the headless flow or the GUI.  The GUI (and with it PySide6) is imported
lazily, only when a GUI run was actually requested.
"""
import sys

from qdte.core import flags as gflags

# Optional-dependency roots the GUI may legitimately be missing. An
# ImportError for anything else is a real bug and must not be swallowed.
_OPTIONAL_GUI_MODULES = ('PySide6',)

_GUI_DEPS_HINT = """\
QDTE's GUI needs PySide6, which is not installed:

  pip install "qdte-lite[qt]"

Headless mode needs no GUI toolkit:  qdte --nogui --help"""


def _dispatch(args):
    if gflags.flags['nogui']:
        from qdte.cli.headless import run_headless
        run_headless()
        return
    # Deliberately lazy: the ONLY place a GUI toolkit (PySide6) enters the
    # process, so --nogui never imports it.
    try:
        from qdte.gui_qt.app import launch
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
