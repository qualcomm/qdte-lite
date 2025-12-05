#!/usr/bin/env python3

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
"""
@file run.py
This file is the main entry point to the DTGUI application.

It contains some of the logic to parse command-line arguments (other parts, such as validation & specification of what
flags are available to the user, are in flags.py) and decide how to run the main DTGUI controller (see controller.py
for the controller code).

An example of when this file could come in use is when profiling application performance; in this case, run.py will
decide upon an appropriate tool to use and set up the output profile file, etc.
"""
import sys
import argparse
import tkinter as tk
import flags as gflags
import six
import controller



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description=gflags.helpmsg,formatter_class=argparse.RawTextHelpFormatter)
    # initial file
    parser.add_argument('file', nargs='?', default=None, help='Path to the file to open upon initial launch of the '
                                                       'program.')
    parser.add_argument('--test_exp', action='store_true', default=False, help=argparse.SUPPRESS)
    parser.add_argument('-v','--version', action='version', version="QDTE {}".format(controller.DTGUI_VERSION))
    # add all of the global flags
    for flag in gflags.config:
        parser.add_argument(flag, **gflags.config[flag])
    args = parser.parse_args()

    # store the flags
    gflags.store(args)

    # initial file
    run_str = 'controller.run(None if gflags.flags[\'nogui\'] else '\
              'tk.Tk(),%s)' % ('initial_file=%s' % repr(args.file) if args.file else '')

    if args.test_exp:
        gflags.flags['testexp'] = True
    else:
        gflags.flags['testexp'] = False
    # check how this should be run
    if gflags.flags['profile']:
        try:
            import cProfile as profile
        except ImportError:
            print('Warning! cProfile is not available on this system. profile will be used instead.')
            import profile

        if isinstance(gflags.flags['profile'], str):
            profile.run(run_str, gflags.flags['profile'])
        else:
            profile.run(run_str)
    else:
        cov = None
        if gflags.flags['profileMem']:
            try:
                from pympler import muppy, summary
            except ImportError:
                print('Warning! pympler is not available on this system. tracemalloc will be used instead.')
                import tracemalloc
                tracemalloc.start()
        elif gflags.flags['coverage']:
            try:
                import coverage
                from coverage import Coverage

                if isinstance(gflags.flags['coverage'], str):
                    cov = coverage.Coverage(data_file=gflags.flags['coverage'])
                else:
                    cov = coverage.Coverage()
                cov.start()
            except ImportError:
                print('Error! coverage is not available on this system, so coverage CANNOT be tested!')
                sys.exit(1)

        exec(run_str)

        if gflags.flags['coverage']:
            if cov:
                cov.stop()
                cov.save()